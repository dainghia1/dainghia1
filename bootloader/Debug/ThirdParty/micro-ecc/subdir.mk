################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../ThirdParty/micro-ecc/uECC.c 

OBJS += \
./ThirdParty/micro-ecc/uECC.o 

C_DEPS += \
./ThirdParty/micro-ecc/uECC.d 


# Each subdirectory must supply rules for building sources it contributes
ThirdParty/micro-ecc/%.o ThirdParty/micro-ecc/%.su ThirdParty/micro-ecc/%.cyclo: ../ThirdParty/micro-ecc/%.c ThirdParty/micro-ecc/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F103xB -DuECC_SUPPORTS_secp160r1=0 -DuECC_SUPPORTS_secp192r1=0 -DuECC_SUPPORTS_secp224r1=0 -DuECC_SUPPORTS_secp256r1=1 -DuECC_SUPPORTS_secp256k1=0 -DuECC_VLI_NATIVE_LITTLE_ENDIAN=0 -c -I../Core/Inc -I../ThirdParty/tinycrypt/include -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"

clean: clean-ThirdParty-2f-micro-2d-ecc

clean-ThirdParty-2f-micro-2d-ecc:
	-$(RM) ./ThirdParty/micro-ecc/uECC.cyclo ./ThirdParty/micro-ecc/uECC.d ./ThirdParty/micro-ecc/uECC.o ./ThirdParty/micro-ecc/uECC.su

.PHONY: clean-ThirdParty-2f-micro-2d-ecc

