# Firmware signing

The bootloader verifies every application with ECDSA P-256 and SHA-256. Only
the public key is stored in firmware; the encrypted private key stays on the
PC used to sign releases.

Install the signing dependency in the Python environment used by this tool:

```powershell
python -m pip install -r requirements-auth.txt
```

Generate a key pair once. Keep the private-key file and its passphrase secure;
the generated public-key header belongs in the bootloader source:

```powershell
python sign_firmware.py keygen `
  --private-key keys\ota_private.pem `
  --public-header ..\bootloader\Core\Inc\ota_public_key.h
```

Build and flash that bootloader before signing firmware for it. The tool
rejects firmware until a public key has been provisioned.

Sign each application binary with a monotonically increasing version:

```powershell
python sign_firmware.py sign appA.bin `
  --private-key keys\ota_private.pem `
  --version 1
```

The command creates `appA.bin.sig` beside the firmware. The GUI expects this
exact sidecar name and sends its version and 64-byte raw `r || s` signature in
the `START` command. Sign the same `.bin` file that will be selected in the
GUI; if it contains the 1 KiB linker header, both tools remove it before
calculating the signature.

The signed digest is SHA-256 over, in order:

1. `STM32-OTA-SIGNATURE-V1` followed by a NUL byte
2. `STM32F103C8` followed by a NUL byte
3. image size as uint32 little-endian
4. firmware version as uint32 little-endian
5. the application image bytes

The bootloader first checks the transfer CRC and signature before writing the
application header. It repeats CRC and signature verification on every boot
before jumping to the application. CRC detects accidental transfer errors;
the signature authenticates the firmware publisher.

The current bootloader build links to about 13.3 KiB of flash in its 16 KiB
region. Recheck the linker result after future changes; increase the
bootloader region/layout if the linker reports overflow.
