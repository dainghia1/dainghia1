/*
 * app_ota.h
 *
 *  Created on: Oct 5, 2026
 *      Author: Admin
 */

#ifndef INC_APP_OTA_H_
#define INC_APP_OTA_H_

#include "type_config.h"

#define SOF 	0xA5
#define EOF 	0x5A
#define SYNC 	0x55
#define ACK 	0x79
#define NACK 	0x1F


#define CHUNK_MAX   1024
#define FRAME_PAYLOAD_MAX	(4 + CHUNK_MAX)

typedef enum {
	CMD_START = 1,   /*start_playload_t: xóa Flash, bắt đầu phiên nạp*/
	CMD_DATA = 2,		/* data_payload_t : ghi 1 gói dữ liệu */
	CMD_END = 3,		/*				: kiểm CRC32 toàn anh, ghi header */
	CMD_JUMP = 4		/*				: nhảy sang ứng dụng */
}cmd_id_t;


/* Mã trạng thái trả về trong gói phản hồi
 *
 */

typedef enum {
    ST_OK = 0,
    ST_ERR_FRAME,         /* 1: sai khung / CRC16 / EOF (loi duong truyen -> PC gui lai) */
    ST_ERR_UNKNOWN_CMD,   /* 2 */
    ST_ERR_PARAM,         /* 3: size/len/offset khong hop le */
    ST_ERR_STATE,         /* 4: chua START, hoac chua nhan du du lieu khi END */
    ST_ERR_OFFSET,        /* 5: offset khong noi tiep goi truoc */
    ST_ERR_ERASE,         /* 6: xoa Flash that bai */
    ST_ERR_WRITE,         /* 7: ghi Flash that bai */
    ST_ERR_CRC,           /* 8: CRC32 toan anh sai */
    ST_ERR_APP,           /* 9: JUMP nhung app_valid() != 0 */
    ST_ERR_SIGNATURE      /* 10: firmware signature khong hop le */
} status_t;

typedef struct __attribute__((packed))
{
	u8 sof;
	u8 cmd;
	u16 len;
}frame_hdr_t;

/*
 * Khung nhận: header + playload. CRC 16 và EOF nằm ngay sau playload that su
 * (vị trí phu thuoc len) nên đọc riêng sau khi biết len, không khai báo trong struct cố định.
 */
typedef struct __attribute__((packed)) {
    frame_hdr_t hdr;
    uint8_t     payload[FRAME_PAYLOAD_MAX];
} rx_frame_t;

typedef struct __attribute__((packed)) {      /* payload cua CMD_START */
    uint32_t size;
    uint32_t crc;
    uint32_t version;
    uint8_t signature[64];
} start_payload_t;

typedef struct __attribute__((packed)) {      /* payload cua CMD_DATA (data[] chi len-4 byte dau co nghia) */
    uint32_t offset;
    uint8_t  data[CHUNK_MAX];
} data_payload_t;

/* Kich thuoc struct = kich thuoc tren day truyen. Sai thi bao loi luc bien dich. */

_Static_assert(sizeof(frame_hdr_t)     == 4,  "frame_hdr_t phai 4 byte");
_Static_assert(sizeof(start_payload_t) == 76, "start_payload_t phai 76 byte");
_Static_assert(sizeof(data_payload_t)  == 4 + CHUNK_MAX, "data_payload_t sai kich thuoc");

void loader(void);

#endif /* INC_APP_OTA_H_ */
