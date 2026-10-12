/*
 * ota_auth.h
 *
 *  Created on: Oct 12, 2026
 *      Author: Admin
 */

#ifndef INC_OTA_AUTH_H_
#define INC_OTA_AUTH_H_

#include <stdint.h>

#define OTA_SHA256_SIZE 32U
#define OTA_SIGNATURE_SIZE 64U

int ota_auth_verify(const uint8_t *image, uint32_t size, uint32_t version,
                    const uint8_t signature[OTA_SIGNATURE_SIZE]);

#endif /* INC_OTA_AUTH_H_ */
