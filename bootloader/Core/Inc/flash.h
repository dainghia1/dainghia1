#ifndef INC_FLASH_H_
#define INC_FLASH_H_

#include "stm32f1xx_hal.h"

int flash_unlock(void);
void flash_lock(void);
int flash_read(uint32_t addr, void *buffer, uint32_t len);
int flash_erase(uint32_t addr, uint32_t pages);
int flash_write(uint32_t addr, const void *data, uint32_t len);

#endif /* INC_FLASH_H_ */
