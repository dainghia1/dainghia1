/*
 * app_ota.c
 *
 *  Created on: Oct 5, 2026
 *      Author: Admin
 */


#include "flash_layout.h"
#include "main.h"
#include "app_ota.h"
#include "flash_operations.h"
#include "flash_prog.h"
#include "type_config.h"
#include "bl_jump.h"
#include "crc32.h"
#include "usart.h"
#include "ota_auth.h"
#include <string.h>
#include "app_header.h"
//#define OTA_FLAG_START 1

//u32 flash_buffer[5];
/*
void enable_ota_request(void)
{
	HAL_FLASH_Unlock();
	flash_read_page(APP_HEADER_ADDR, flash_buffer, n_word);

	flash_buffer[0] = OTA_FLAG_START;
	flash_erase_page(APP_HEADER_ADDR);
	flash_write_page(APP_HEADER_ADDR, flash_buffer, n_word);
	HAL_FLASH_Lock();
	NVIC_SystemReset();
}
*/
/* Khung: A5 | cmd | len(2,LE) | payload | crc16(2,LE) tren cmd,len,payload
 * return 0 ok, 1 chua co SOF, -1 loi khung/checksum */


/* Trang thai cua 1 phien nap, tu START den END. */
typedef struct {
    int      started;    /* da nhan START hop le */
    int      finished;   /* END da thanh cong: END gui lai (do mat phan hoi) van tra OK */
    uint32_t size;       /* kich thuoc anh (byte) */
    uint32_t crc;        /* CRC32 mong doi cua toan anh */
    uint32_t version;
    uint8_t  signature[OTA_SIGNATURE_SIZE];
    uint32_t next;       /* offset ke tiep dang cho; next == size nghia la da nhan du */
} session_t;

/* ---------- Phan hoi ---------- */
/* A5 | CMD | STATUS | CRC16(CMD..STATUS) | 5A */
static void send_resp(uint8_t cmd, status_t st)
{
    uint8_t response[6];
    response[0] = SOF;
    response[1] = cmd;
    response[2] = (uint8_t)st;

    uint16_t checksum = crc16(0, &response[1], 2);
    response[3] = (uint8_t)checksum;
    response[4] = (uint8_t)(checksum >> 8);
    response[5] = EOF;
    uart_send(response, sizeof response);
}

/* ---------- Nhan khung ----------
 * return 0 = khung hop le, 1 = chua co SOF (ranh), -1 = loi khung (timeout/CRC16/EOF) */
static int rx_frame(rx_frame_t *f)
{
    uint8_t *raw = (uint8_t *)f;
    uint8_t tail[3];                               /* CRC16 (2 byte) + EOF (1 byte) */

    if (!rx_byte_timeout(&raw[0], 10) || raw[0] != SOF) return 1;
    for (unsigned i = 1; i < sizeof(frame_hdr_t); i++)
        if (!rx_byte_timeout(&raw[i], 200)) return -1;
    if (f->hdr.len > FRAME_PAYLOAD_MAX) return -1;
    for (unsigned i = 0; i < f->hdr.len; i++)
        if (!rx_byte_timeout(&f->payload[i], 500)) return -1;
    for (unsigned i = 0; i < sizeof tail; i++)
        if (!rx_byte_timeout(&tail[i], 200)) return -1;

    /* cmd va len nam lien nhau ngay sau sof (struct packed) -> 3 byte */
    uint16_t calc = crc16(crc16(0, &raw[1], 3), f->payload, f->hdr.len);
    uint16_t got  = (uint16_t)(tail[0] | (tail[1] << 8));
    return (calc == got && tail[2] == EOF) ? 0 : -1;
}

/* ---------- Xu ly tung lenh ---------- */
static status_t on_start(session_t *s, const uint8_t *p, uint16_t len)
{
    const start_payload_t *sp = (const start_payload_t *)p;
    memset(s, 0, sizeof *s);
    if (len != sizeof *sp || sp->size == 0 || sp->size > APP_MAX_SIZE || (sp->size & 3)) return ST_ERR_PARAM;

    s->size = sp->size; s->crc = sp->crc; s->version = sp->version;
    memcpy(s->signature, sp->signature, sizeof s->signature);
    /* Xoa trang header (truoc app) roi cac trang code (sau header); thu tu khong quan trong */
    if (flash_erase_page(APP_HEADER_ADDR) ||
        flash_erase(APP_START_ADDR, (s->size + PAGE_SZ - 1) / PAGE_SZ)) return ST_ERR_ERASE;
    s->started = 1;
    return ST_OK;
}

static status_t on_data(session_t *s, const uint8_t *p, uint16_t len)
{
    const data_payload_t *dp = (const data_payload_t *)p;
    if (!s->started || s->finished) return ST_ERR_STATE;
    if (len < sizeof dp->offset + 4) return ST_ERR_PARAM;      /* it nhat 1 word du lieu */

    uint32_t n = len - sizeof dp->offset, off = dp->offset;
    if ((n & 3) || off > s->size || n > s->size - off) return ST_ERR_PARAM;
    if (off + n == s->next) return ST_OK;                       /* goi lap do mat phan hoi */
    if (off != s->next) return ST_ERR_OFFSET;
    if (flash_write(APP_START_ADDR + off, dp->data, n)) return ST_ERR_WRITE;

    s->next += n;
    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
    return ST_OK;
}

static status_t on_end(session_t *s)
{
    if (s->finished) return ST_OK;                              /* END lap */
    if (!s->started || s->next != s->size) return ST_ERR_STATE;
    if (crc32((const uint8_t *)APP_START_ADDR, s->size) != s->crc) return ST_ERR_CRC;
    if (!ota_auth_verify((const uint8_t *)APP_START_ADDR, s->size,
                         s->version, s->signature)) return ST_ERR_SIGNATURE;

    app_header_t hdr = { .reserved = 0, .magic = APP_MAGIC,
                         .size = s->size, .crc = s->crc, .version = s->version };
    memcpy(hdr.signature, s->signature, sizeof hdr.signature);
    if (flash_write_page(APP_HEADER_ADDR, (u32 *)&hdr, sizeof hdr / 4)) return ST_ERR_WRITE;
    s->finished = 1;
    return ST_OK;
}

static status_t on_jump(void)
{
    return bootloader_is_app_valid() == 0 ? ST_OK : ST_ERR_APP;
}

/* ---------- Vong lap xu ly mot phien nap ---------- */
void loader(void)
{
    rx_frame_t f;
    session_t  s = {0};

    for (;;) {
        int r = rx_frame(&f);
        if (r == 1) continue;
        if (r < 0) { send_resp(0, ST_ERR_FRAME); continue; }

        status_t st;
        switch (f.hdr.cmd) {
        case CMD_START: st = on_start(&s, f.payload, f.hdr.len); break;
        case CMD_DATA:  st = on_data(&s, f.payload, f.hdr.len);  break;
        case CMD_END:   st = (f.hdr.len == 0) ? on_end(&s)  : ST_ERR_PARAM; break;
        case CMD_JUMP:  st = (f.hdr.len == 0) ? on_jump() : ST_ERR_PARAM; break;
        default:        st = ST_ERR_UNKNOWN_CMD;
        }
        send_resp(f.hdr.cmd, st);

        if (f.hdr.cmd == CMD_JUMP && st == ST_OK) { HAL_Delay(5); JumptoApplication(); }
    }
}
