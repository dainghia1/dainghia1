/*
 * bl_jump.c
 *
 *  Created on: Sep 29, 2026
 *      Author: Admin
 */
#include "bl_jump.h"
#include "app_header.h"
#include "crc32.h"
#include "flash_prog.h"


typedef void (*pFunction)(void);

void JumptoApplication(void)
{
	uint32_t appStack;
	uint32_t appResetHandler;
	pFunction appEntry;

	appStack = *(volatile uint32_t*)APP_START_ADDR;
	appResetHandler = *(volatile uint32_t*)(APP_START_ADDR + 4);
	appEntry = (pFunction)appResetHandler;

	__disable_irq();

	/* Do not carry the bootloader's interrupt-driven UART receive into the app. */
	USART1->CR1 &= ~(USART_CR1_RXNEIE | USART_CR1_TXEIE | USART_CR1_TCIE);
	USART1->CR3 &= ~(USART_CR3_EIE | USART_CR3_DMAR);
	(void)USART1->SR;
	(void)USART1->DR;
	NVIC_DisableIRQ(USART1_IRQn);
	NVIC_ClearPendingIRQ(USART1_IRQn);

	SysTick->CTRL = 0;
	SysTick->LOAD = 0;
	SysTick->VAL = 0;

	__set_MSP(appStack);

	appEntry();
}

int bootloader_is_app_valid(void)
{
	uint32_t HDR_ADDR = APP_HEADER_ADDR;
	const app_header_t *app_hdr = (const app_header_t *)HDR_ADDR;

	/*1. Magic */
	if(app_hdr->magic != APP_MAGIC)
	{
		return 1;
	}

	uint32_t reset_handler = *(uint32_t*)(APP_START_ADDR + 4);
	if((reset_handler & 0xFF000000) != 0x08000000)
		return 2;

	if(app_hdr->size == 0 || app_hdr->size > APP_MAX_SIZE)
	{
		return 3;
	}

	uint32_t calc_crc = crc32((const uint8_t *)APP_START_ADDR, app_hdr->size);
	if(calc_crc != app_hdr->crc)
	{
		return 4;
	}
	return 0;
}
