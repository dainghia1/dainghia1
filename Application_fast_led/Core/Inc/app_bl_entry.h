/*
 * app_bl_entry.h
 *
 *  Created on: Oct 10, 2026
 *      Author: Admin
 */

#ifndef INC_APP_BL_ENTRY_H_
#define INC_APP_BL_ENTRY_H_

#include "stm32f1xx_hal.h"
#include "bl_flag.h"
#include "usart.h"

#define CMD_REBOOT_BL  0x05U
#define BL_ACK         0x79U

static inline uint16_t bl_crc16(
    uint16_t crc,
    const uint8_t *data,
    uint32_t length)
{
    while (length--) {
        crc ^= (uint16_t)(*data++) << 8;

        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x8000U)
                crc = (uint16_t)((crc << 1) ^ 0x1021U);
            else
                crc = (uint16_t)(crc << 1);
        }
    }

    return crc;
}

static inline void bl_reboot_to_bootloader(void)
{
    uint8_t ack = BL_ACK;

    /* Đợi byte ACK được gửi xong trước khi reset. */
    (void)HAL_UART_Transmit(&huart1, &ack, 1, 100);

    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_RCC_BKP_CLK_ENABLE();
    HAL_PWR_EnableBkUpAccess();

    BKP->DR1 = BL_FLAG;
    NVIC_SystemReset();
}

static inline void bl_poll(void)
{
    static uint8_t window[6];

    /* Đọc không chờ; gọi thường xuyên từ vòng lặp chính. */
    if (!(USART1->SR & USART_SR_RXNE))
        return;

    uint8_t byte = (uint8_t)USART1->DR;

    for (uint8_t i = 0; i < 5; i++)
        window[i] = window[i + 1];

    window[5] = byte;

    if (window[0] != 0xA5U ||
        window[1] != CMD_REBOOT_BL ||
        window[2] != 0U ||
        window[3] != 0U)
        return;

    uint16_t received_crc =
        (uint16_t)window[4] | ((uint16_t)window[5] << 8);

    if (bl_crc16(0, &window[1], 3) == received_crc)
        bl_reboot_to_bootloader();
}

#endif /* INC_APP_BL_ENTRY_H_ */
