/*
 * app_header.h
 *
 *  Created on: Sep 30, 2026
 *      Author: Admin
 */

#ifndef INC_APP_HEADER_H_
#define INC_APP_HEADER_H_
#include "flash_layout.h"

typedef struct
{
	uint32_t reserved;
	uint32_t magic;
	uint32_t size;		// app size in bytes
	uint32_t crc;		//CRC32 of APPLICATION
	uint32_t version;
}app_header_t;

#endif /* INC_APP_HEADER_H_ */
