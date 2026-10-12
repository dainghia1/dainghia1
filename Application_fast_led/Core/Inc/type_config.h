/*
 * type_config.h
 *
 *  Created on: Oct 5, 2026
 *      Author: Admin
 */

#ifndef INC_TYPE_CONFIG_H_
#define INC_TYPE_CONFIG_H_

#include "stdint.h"

typedef uint16_t u16;
typedef uint8_t u8;
typedef uint32_t u32;

typedef int		i32;

/* khung giao thuc : A5 |CMD|len|playload|crc16
 *
 * playload {
 * 	size
 * 	crc32
 * 	version
 * }
 * or{
 * 	len = 4 byte offset + data;
 * 	// offet : vi tri cua firmware hien tai
 * 	--> dia chi ghi = APP_ADDR + offset
 * }
 */

/* Khung giao thuc, lenh, ma trang thai: xem protocol_frame.h */
#define BOOT_WAIT_MS 3000U

#endif /* INC_TYPE_CONFIG_H_ */
