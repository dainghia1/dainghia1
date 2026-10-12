/*
 * flash_operations.h
 *
 *  Created on: Oct 5, 2026
 *      Author: Admin
 */

#ifndef INC_FLASH_OPERATIONS_H_
#define INC_FLASH_OPERATIONS_H_

#include "stm32f1xx_hal.h"
#include "type_config.h"


void flash_read_page(u32 addr, u32 *buffer, u32 n_word);
int flash_erase_page(u32 page_addr);
int flash_write_page(u32 addr, u32 *buffer, u32 n_word);


#endif /* INC_FLASH_OPERATIONS_H_ */
