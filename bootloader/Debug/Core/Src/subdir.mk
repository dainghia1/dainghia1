################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/Src/app_header.c \
../Core/Src/app_ota.c \
../Core/Src/bl_jump.c \
../Core/Src/crc.c \
../Core/Src/crc32.c \
../Core/Src/flash_operations.c \
../Core/Src/flash_prog.c \
../Core/Src/gpio.c \
../Core/Src/main.c \
../Core/Src/ota_auth.c \
../Core/Src/stm32f1xx_hal_msp.c \
../Core/Src/stm32f1xx_it.c \
../Core/Src/syscalls.c \
../Core/Src/sysmem.c \
../Core/Src/system_stm32f1xx.c \
../Core/Src/usart.c 

OBJS += \
./Core/Src/app_header.o \
./Core/Src/app_ota.o \
./Core/Src/bl_jump.o \
./Core/Src/crc.o \
./Core/Src/crc32.o \
./Core/Src/flash_operations.o \
./Core/Src/flash_prog.o \
./Core/Src/gpio.o \
./Core/Src/main.o \
./Core/Src/ota_auth.o \
./Core/Src/stm32f1xx_hal_msp.o \
./Core/Src/stm32f1xx_it.o \
./Core/Src/syscalls.o \
./Core/Src/sysmem.o \
./Core/Src/system_stm32f1xx.o \
./Core/Src/usart.o 

C_DEPS += \
./Core/Src/app_header.d \
./Core/Src/app_ota.d \
./Core/Src/bl_jump.d \
./Core/Src/crc.d \
./Core/Src/crc32.d \
./Core/Src/flash_operations.d \
./Core/Src/flash_prog.d \
./Core/Src/gpio.d \
./Core/Src/main.d \
./Core/Src/ota_auth.d \
./Core/Src/stm32f1xx_hal_msp.d \
./Core/Src/stm32f1xx_it.d \
./Core/Src/syscalls.d \
./Core/Src/sysmem.d \
./Core/Src/system_stm32f1xx.d \
./Core/Src/usart.d 


# Each subdirectory must supply rules for building sources it contributes
Core/Src/%.o Core/Src/%.su Core/Src/%.cyclo: ../Core/Src/%.c Core/Src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F103xB -DuECC_SUPPORTS_secp160r1=0 -DuECC_SUPPORTS_secp192r1=0 -DuECC_SUPPORTS_secp224r1=0 -DuECC_SUPPORTS_secp256r1=1 -DuECC_SUPPORTS_secp256k1=0 -DuECC_VLI_NATIVE_LITTLE_ENDIAN=0 -c -I../Core/Inc -I../ThirdParty/tinycrypt/include -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"

clean: clean-Core-2f-Src

clean-Core-2f-Src:
	-$(RM) ./Core/Src/app_header.cyclo ./Core/Src/app_header.d ./Core/Src/app_header.o ./Core/Src/app_header.su ./Core/Src/app_ota.cyclo ./Core/Src/app_ota.d ./Core/Src/app_ota.o ./Core/Src/app_ota.su ./Core/Src/bl_jump.cyclo ./Core/Src/bl_jump.d ./Core/Src/bl_jump.o ./Core/Src/bl_jump.su ./Core/Src/crc.cyclo ./Core/Src/crc.d ./Core/Src/crc.o ./Core/Src/crc.su ./Core/Src/crc32.cyclo ./Core/Src/crc32.d ./Core/Src/crc32.o ./Core/Src/crc32.su ./Core/Src/flash_operations.cyclo ./Core/Src/flash_operations.d ./Core/Src/flash_operations.o ./Core/Src/flash_operations.su ./Core/Src/flash_prog.cyclo ./Core/Src/flash_prog.d ./Core/Src/flash_prog.o ./Core/Src/flash_prog.su ./Core/Src/gpio.cyclo ./Core/Src/gpio.d ./Core/Src/gpio.o ./Core/Src/gpio.su ./Core/Src/main.cyclo ./Core/Src/main.d ./Core/Src/main.o ./Core/Src/main.su ./Core/Src/ota_auth.cyclo ./Core/Src/ota_auth.d ./Core/Src/ota_auth.o ./Core/Src/ota_auth.su ./Core/Src/stm32f1xx_hal_msp.cyclo ./Core/Src/stm32f1xx_hal_msp.d ./Core/Src/stm32f1xx_hal_msp.o ./Core/Src/stm32f1xx_hal_msp.su ./Core/Src/stm32f1xx_it.cyclo ./Core/Src/stm32f1xx_it.d ./Core/Src/stm32f1xx_it.o ./Core/Src/stm32f1xx_it.su ./Core/Src/syscalls.cyclo ./Core/Src/syscalls.d ./Core/Src/syscalls.o ./Core/Src/syscalls.su ./Core/Src/sysmem.cyclo ./Core/Src/sysmem.d ./Core/Src/sysmem.o ./Core/Src/sysmem.su ./Core/Src/system_stm32f1xx.cyclo ./Core/Src/system_stm32f1xx.d ./Core/Src/system_stm32f1xx.o ./Core/Src/system_stm32f1xx.su ./Core/Src/usart.cyclo ./Core/Src/usart.d ./Core/Src/usart.o ./Core/Src/usart.su

.PHONY: clean-Core-2f-Src

