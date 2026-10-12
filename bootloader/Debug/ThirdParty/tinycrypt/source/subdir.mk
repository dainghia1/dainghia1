################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../ThirdParty/tinycrypt/source/sha256.c \
../ThirdParty/tinycrypt/source/utils.c 

OBJS += \
./ThirdParty/tinycrypt/source/sha256.o \
./ThirdParty/tinycrypt/source/utils.o 

C_DEPS += \
./ThirdParty/tinycrypt/source/sha256.d \
./ThirdParty/tinycrypt/source/utils.d 


# Each subdirectory must supply rules for building sources it contributes
ThirdParty/tinycrypt/source/%.o ThirdParty/tinycrypt/source/%.su ThirdParty/tinycrypt/source/%.cyclo: ../ThirdParty/tinycrypt/source/%.c ThirdParty/tinycrypt/source/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F103xB -DuECC_SUPPORTS_secp160r1=0 -DuECC_SUPPORTS_secp192r1=0 -DuECC_SUPPORTS_secp224r1=0 -DuECC_SUPPORTS_secp256r1=1 -DuECC_SUPPORTS_secp256k1=0 -DuECC_VLI_NATIVE_LITTLE_ENDIAN=0 -c -I../Core/Inc -I../ThirdParty/tinycrypt/include -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"

clean: clean-ThirdParty-2f-tinycrypt-2f-source

clean-ThirdParty-2f-tinycrypt-2f-source:
	-$(RM) ./ThirdParty/tinycrypt/source/sha256.cyclo ./ThirdParty/tinycrypt/source/sha256.d ./ThirdParty/tinycrypt/source/sha256.o ./ThirdParty/tinycrypt/source/sha256.su ./ThirdParty/tinycrypt/source/utils.cyclo ./ThirdParty/tinycrypt/source/utils.d ./ThirdParty/tinycrypt/source/utils.o ./ThirdParty/tinycrypt/source/utils.su

.PHONY: clean-ThirdParty-2f-tinycrypt-2f-source

