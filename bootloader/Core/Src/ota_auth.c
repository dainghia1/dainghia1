/*
 * ota_auth.c
 *
 *  Created on: Oct 12, 2026
 *      Author: Admin
 */

#include "ota_auth.h"
#include "ota_public_key.h"
#include "../../ThirdParty/tinycrypt/include/tinycrypt/constants.h"
#include "../../ThirdParty/tinycrypt/include/tinycrypt/sha256.h"
#include "../../ThirdParty/micro-ecc/uECC.h"

static int sha256_update_checked(TCSha256State_t state,
                                 const uint8_t *data, uint32_t size)
{
    return tc_sha256_update(state, data, size) == TC_CRYPTO_SUCCESS;
}

int ota_auth_verify(const uint8_t *image, uint32_t size, uint32_t version,
                    const uint8_t signature[OTA_SIGNATURE_SIZE])
{
    static const uint8_t domain[] = "STM32-OTA-SIGNATURE-V1";
    static const uint8_t target[] = "STM32F103C8";
    struct tc_sha256_state_struct state;
    uint8_t digest[OTA_SHA256_SIZE];
    uint8_t metadata[8];

    if (image == 0 || signature == 0 || size == 0) return 0;
    if (OTA_PUBLIC_KEY_PROVISIONED != 1U) return 0;

    metadata[0] = (uint8_t)size;
    metadata[1] = (uint8_t)(size >> 8);
    metadata[2] = (uint8_t)(size >> 16);
    metadata[3] = (uint8_t)(size >> 24);
    metadata[4] = (uint8_t)version;
    metadata[5] = (uint8_t)(version >> 8);
    metadata[6] = (uint8_t)(version >> 16);
    metadata[7] = (uint8_t)(version >> 24);

    if (tc_sha256_init(&state) != TC_CRYPTO_SUCCESS ||
        !sha256_update_checked(&state, domain, sizeof domain) ||
        !sha256_update_checked(&state, target, sizeof target) ||
        !sha256_update_checked(&state, metadata, sizeof metadata) ||
        !sha256_update_checked(&state, image, size) ||
        tc_sha256_final(digest, &state) != TC_CRYPTO_SUCCESS) {
        return 0;
    }

    return uECC_verify(OTA_PUBLIC_KEY, digest, sizeof digest, signature,
                       uECC_secp256r1()) == 1;
}
