/*
 * flash_operations.c
 *
 *  Created on: Oct 5, 2026
 *      Author: Admin
 */

#include "flash_operations.h"


void flash_read_page(u32 addr, u32 *buffer, u32 n_word)
{
	u32 *p = (u32*)addr;
	for(u32 i = 0;i<n_word;i++)
	{
		buffer[i] = p[i];
	}
}

int flash_erase_page(u32 page_addr)
{
	FLASH_EraseInitTypeDef erase;
	u32 error;
	HAL_StatusTypeDef st;
	erase.TypeErase = FLASH_TYPEERASE_PAGES;
	erase.PageAddress = page_addr;
	erase.NbPages = 1;
	HAL_FLASH_Unlock();
	st = HAL_FLASHEx_Erase(&erase, &error);
	HAL_FLASH_Lock();
	return (st == HAL_OK) ? 0 : -1;
}

int flash_write_page(u32 addr, u32 *buffer, u32 n_word)
{
	HAL_FLASH_Unlock();
	for(u32 i = 0; i< n_word; i++)
	{
		if(HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD, addr, buffer[i]) != HAL_OK || *(volatile u32 *)addr != buffer[i])
		{
			HAL_FLASH_Lock();
			return -1;
		}
		addr += 4;
	}
	HAL_FLASH_Lock();

	return 0;
}

