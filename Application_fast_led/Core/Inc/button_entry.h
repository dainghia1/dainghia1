#ifndef BUTTON_ENTRY_H
#define BUTTON_ENTRY_H

#include "stm32f1xx_hal.h"
#include "bl_flag.h"

#define BTN_PORT          GPIOB
#define BTN_PIN           GPIO_PIN_0
#define BTN_DEBOUNCE_MS   50U
#define BTN_HOLD_MS       2000U

static inline void btn_init(void)
{
    __HAL_RCC_GPIOB_CLK_ENABLE();

    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = BTN_PIN;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(BTN_PORT, &gpio);
}

static inline void btn_poll(void)
{
    static uint8_t raw_down = 0;
    static uint8_t stable_down = 0;
    static uint8_t fired = 0;
    static uint32_t raw_changed_at = 0;
    static uint32_t pressed_at = 0;
    static uint32_t led_toggled_at = 0;

    uint32_t now = HAL_GetTick();
    uint8_t sample_down =
        (HAL_GPIO_ReadPin(BTN_PORT, BTN_PIN) == GPIO_PIN_RESET);

    if (sample_down != raw_down) {
        raw_down = sample_down;
        raw_changed_at = now;
    }

    if ((now - raw_changed_at) >= BTN_DEBOUNCE_MS &&
        stable_down != raw_down) {
        stable_down = raw_down;
        if (stable_down) {
            pressed_at = now;
            fired = 0;
        } else {
            fired = 0;
        }
    }

    if (!stable_down || fired)
        return;

    uint32_t held_ms = now - pressed_at;
    if (held_ms < BTN_HOLD_MS) {
        uint32_t period_ms =
            250U - (held_ms * 180U) / BTN_HOLD_MS;
        if ((now - led_toggled_at) >= period_ms) {
            led_toggled_at = now;
            HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_1);
        }
        return;
    }

    fired = 1;
    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_RCC_BKP_CLK_ENABLE();
    HAL_PWR_EnableBkUpAccess();
    BKP->DR1 = BL_FLAG;
    NVIC_SystemReset();
}

#endif /* BUTTON_ENTRY_H */
