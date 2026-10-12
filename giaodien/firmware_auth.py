import hashlib
import os
import struct


APP_HEADER_SIZE = 1024
APP_HEADER_MAGIC = 0xABCDEFAB
APP_START_ADDR = 0x08004400
APP_MAX_SIZE = 47 * 1024
RAM_START_ADDR = 0x20000000
RAM_END_ADDR = 0x20005000

SIGNATURE_SIZE = 64
SIGNATURE_FILE_MAGIC = b"STM32SG1"
SIGNATURE_FILE_SIZE = len(SIGNATURE_FILE_MAGIC) + 4 + SIGNATURE_SIZE
SIGNATURE_DOMAIN = b"STM32-OTA-SIGNATURE-V1\0"
SIGNATURE_TARGET = b"STM32F103C8\0"
UINT32_MAX = 0xFFFFFFFF


def is_app_vector(image: bytes, offset: int = 0) -> bool:
    if len(image) < offset + 8:
        return False
    stack, reset = struct.unpack_from("<II", image, offset)
    reset_addr = reset & ~1
    return (
        RAM_START_ADDR <= stack <= RAM_END_ADDR
        and APP_START_ADDR <= reset_addr < APP_START_ADDR + APP_MAX_SIZE
        and bool(reset & 1)
    )


def prepare_image(path: str) -> tuple[bytes, bool]:
    with open(path, "rb") as file:
        image = file.read()

    if len(image) >= APP_HEADER_SIZE + 8:
        magic = struct.unpack_from("<I", image, 4)[0]
        if magic == APP_HEADER_MAGIC and is_app_vector(image, APP_HEADER_SIZE):
            return image[APP_HEADER_SIZE:], True

    return image, False


def signature_digest(image: bytes, version: int) -> bytes:
    if not image or len(image) > UINT32_MAX:
        raise ValueError("Kích thước firmware không hợp lệ.")
    if not 0 <= version <= UINT32_MAX:
        raise ValueError("Version phải nằm trong khoảng uint32.")

    digest = hashlib.sha256()
    digest.update(SIGNATURE_DOMAIN)
    digest.update(SIGNATURE_TARGET)
    digest.update(struct.pack("<II", len(image), version))
    digest.update(image)
    return digest.digest()


def encode_signature_file(version: int, signature: bytes) -> bytes:
    if not 0 <= version <= UINT32_MAX:
        raise ValueError("Version phải nằm trong khoảng uint32.")
    if len(signature) != SIGNATURE_SIZE:
        raise ValueError("Chữ ký ECDSA P-256 phải dài đúng 64 byte.")
    return SIGNATURE_FILE_MAGIC + struct.pack("<I", version) + signature


def decode_signature_file(data: bytes) -> tuple[int, bytes]:
    if len(data) != SIGNATURE_FILE_SIZE:
        raise ValueError(
            f"Sidecar chữ ký phải dài {SIGNATURE_FILE_SIZE} byte."
        )
    if data[:len(SIGNATURE_FILE_MAGIC)] != SIGNATURE_FILE_MAGIC:
        raise ValueError("Sidecar chữ ký sai magic/định dạng.")
    version = struct.unpack_from("<I", data, len(SIGNATURE_FILE_MAGIC))[0]
    signature = data[len(SIGNATURE_FILE_MAGIC) + 4:]
    return version, signature


def signature_path_for_firmware(path: str) -> str:
    return os.fspath(path) + ".sig"
