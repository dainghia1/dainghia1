/*
 * app_header.h
 *
 *  Created on: Sep 30, 2026
 *      Author: Admin
 */

#ifndef INC_APP_HEADER_H_
#define INC_APP_HEADER_H_
#include "flash_layout.h"

typedef struct {
    uint32_t reserved;
    uint32_t magic;
    uint32_t size;
    uint32_t crc;
    uint32_t version;
    uint8_t signature[64]; /* ECDSA P-256 r||s, big-endian */
} app_header_t;

_Static_assert(sizeof(app_header_t) == 84, "app_header_t must be 84 bytes");

#endif /* INC_APP_HEADER_H_ */
