#include "flash.h"
#include "flash_layout.h"

#define FLASH_TIMEOUT_MS 5000U

int flash_unlock(void)
{
    uint32_t tickstart = HAL_GetTick();

    while ((FLASH->SR & (1UL << 0)) != 0U) {
        if ((HAL_GetTick() - tickstart) > FLASH_TIMEOUT_MS) {
            return -1;
        }
    }

    if ((FLASH->CR & (1UL << 7)) != 0U) {
        FLASH->KEYR = FLASH_KEY1;
        FLASH->KEYR = FLASH_KEY2;
    }
    return ((FLASH->CR & (1UL << 7)) == 0U) ? 0 : -1;
}

void flash_lock(void)
{
    FLASH->CR |= 1UL << 7;
}

int flash_read(uint32_t addr, void *buffer, uint32_t len)
{
    if (addr < FLASH_BASE || addr > FLASH_LIMIT ||
        len > FLASH_LIMIT - addr || (len != 0U && buffer == NULL)) {
        return -1;
    }

    volatile const uint8_t *source = (volatile const uint8_t *)addr;
    uint8_t *destination = (uint8_t *)buffer;
    for (uint32_t i = 0; i < len; i++) {
        destination[i] = source[i];
    }
    return 0;
}

int flash_erase(uint32_t addr, uint32_t pages)
{
    if (addr < APP_HEADER_ADDR || addr > FLASH_LIMIT ||(addr & (PAGE_SZ - 1U)) != 0U || pages == 0U ||pages > (FLASH_LIMIT - addr) / PAGE_SZ) {
        return -1;
    }

    if (flash_unlock() != 0) {
        flash_lock();
        return -1;
    }

    int result = 0;
    for (uint32_t page = 0; page < pages; page++) {
        uint32_t tickstart = HAL_GetTick();
        while ((FLASH->SR & (1UL << 0)) != 0U) {
            if ((HAL_GetTick() - tickstart) > FLASH_TIMEOUT_MS) {
                result = -1;
                break;
            }
        }
        if (result != 0) {
            break;
        }

        FLASH->SR = (1UL << 5) | (1UL << 2) | (1UL << 4);
        FLASH->CR |= 1UL << 1;
        FLASH->AR = addr + page * PAGE_SZ;
        FLASH->CR |= 1UL << 6;

        tickstart = HAL_GetTick();
        while ((FLASH->SR & (1UL << 0)) != 0U) {
            if ((HAL_GetTick() - tickstart) > FLASH_TIMEOUT_MS) {
                result = -1;
                break;
            }
        }
        uint32_t status = FLASH->SR;
        FLASH->SR = (1UL << 5) | (1UL << 2) | (1UL << 4);
        if (result != 0 || (status & ((1UL << 2) | (1UL << 4))) != 0U ||(status & (1UL << 5)) == 0U) {
            result = -1;
            FLASH->CR &= ~(1UL << 1);
            break;
        }
        FLASH->CR &= ~(1UL << 1);
    }

    flash_lock();
    return result;
}

int flash_write(uint32_t addr, const void *data, uint32_t len)
{
    const uint8_t *source = (const uint8_t *)data;

    if (addr < APP_HEADER_ADDR || addr > FLASH_LIMIT ||(addr & 3U) != 0U || (len & 3U) != 0U ||len > FLASH_LIMIT - addr || (len != 0U && source == NULL)) {
        return -1;
    }
    if (len == 0U) {
        return 0;
    }
    if (flash_unlock() != 0) {
        flash_lock();
        return -1;
    }

    int result = 0;
    for (uint32_t i = 0; i < len; i += 2U) {
        uint32_t tickstart = HAL_GetTick();
        while ((FLASH->SR & (1UL << 0)) != 0U) {
            if ((HAL_GetTick() - tickstart) > FLASH_TIMEOUT_MS) {
                result = -1;
                break;
            }
        }
        if (result != 0) {
            break;
        }

        uint16_t halfword = (uint16_t)source[i] | ((uint16_t)source[i + 1U] << 8);
        uint32_t target = addr + i;

        FLASH->SR = (1UL << 5) | (1UL << 2) | (1UL << 4);
        FLASH->CR |= 1UL << 0;
        *(volatile uint16_t *)target = halfword;

        tickstart = HAL_GetTick();
        while ((FLASH->SR & (1UL << 0)) != 0U) {
            if ((HAL_GetTick() - tickstart) > FLASH_TIMEOUT_MS) {
                result = -1;
                break;
            }
        }
        uint32_t status = FLASH->SR;
        FLASH->SR = (1UL << 5) | (1UL << 2) | (1UL << 4);
        if (result != 0 ||
            (status & ((1UL << 2) | (1UL << 4))) != 0U ||
            (status & (1UL << 5)) == 0U ||
            *(volatile uint16_t *)target != halfword) {
            result = -1;
            FLASH->CR &= ~(1UL << 0);
            break;
        }
        FLASH->CR &= ~(1UL << 0);
    }

    flash_lock();
    return result;
}
