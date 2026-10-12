import argparse
import getpass
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from firmware_auth import (
    APP_MAX_SIZE,
    SIGNATURE_SIZE,
    encode_signature_file,
    is_app_vector,
    prepare_image,
    signature_digest,
    signature_path_for_firmware,
)


def raw_signature(private_key, digest: bytes) -> bytes:
    der_signature = private_key.sign(
        digest, ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )
    r, s = utils.decode_dss_signature(der_signature)
    signature = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    if len(signature) != SIGNATURE_SIZE:
        raise ValueError("ECDSA tạo ra chữ ký sai kích thước.")
    return signature


def public_key_header(public_key) -> str:
    numbers = public_key.public_numbers()
    raw_key = numbers.x.to_bytes(32, "big") + numbers.y.to_bytes(32, "big")
    entries = ",\n    ".join(
        ", ".join(f"0x{byte:02X}" for byte in raw_key[index:index + 8])
        for index in range(0, len(raw_key), 8)
    )
    return (
        "#ifndef OTA_PUBLIC_KEY_H_\n"
        "#define OTA_PUBLIC_KEY_H_\n\n"
        "#include <stdint.h>\n\n"
        "#define OTA_PUBLIC_KEY_PROVISIONED 1U\n"
        "static const uint8_t OTA_PUBLIC_KEY[64] = {\n"
        f"    {entries}\n"
        "};\n\n"
        "#endif\n"
    )


def generate_key_files(private_path: Path, public_header_path: Path,
                       passphrase: bytes) -> None:
    if private_path.exists():
        raise FileExistsError(f"Private key đã tồn tại: {private_path}")
    if public_header_path.exists():
        current = public_header_path.read_text(encoding="utf-8")
        if "OTA_PUBLIC_KEY_PROVISIONED 1U" in current:
            raise FileExistsError(
                f"Public key đã được provision; không ghi đè: {public_header_path}"
            )
    if not passphrase:
        raise ValueError("Cần đặt passphrase để mã hóa private key.")

    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_header_path.parent.mkdir(parents=True, exist_ok=True)
    private_key = ec.generate_private_key(ec.SECP256R1())
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase),
    )
    private_path.write_bytes(pem)
    public_header_path.write_text(
        public_key_header(private_key.public_key()), encoding="ascii"
    )


def sign_firmware_file(firmware_path: Path, private_path: Path, version: int,
                       passphrase: bytes, output_path: Path | None = None) -> Path:
    image, header_removed = prepare_image(os.fspath(firmware_path))
    if header_removed:
        print(f"Removed {1024}-byte linker header before signing.")
    if not image:
        raise ValueError("Firmware rỗng.")
    if len(image) > APP_MAX_SIZE:
        raise ValueError(f"Firmware vượt quá giới hạn {APP_MAX_SIZE} byte.")
    if len(image) & 3:
        raise ValueError("Kích thước firmware phải chia hết cho 4 byte.")
    if not is_app_vector(image):
        raise ValueError("Vector table firmware không hợp lệ tại APP_START_ADDR.")

    private_key = serialization.load_pem_private_key(
        private_path.read_bytes(), password=passphrase
    )
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise ValueError("Private key không phải khóa EC.")
    if not isinstance(private_key.curve, ec.SECP256R1):
        raise ValueError("Private key phải dùng đường cong NIST P-256.")

    signature = raw_signature(private_key, signature_digest(image, version))
    output = output_path or Path(signature_path_for_firmware(os.fspath(firmware_path)))
    output.write_bytes(encode_signature_file(version, signature))
    return output


def _password(prompt: str) -> bytes:
    first = getpass.getpass(prompt).encode("utf-8")
    if not first:
        raise ValueError("Passphrase không được để trống.")
    return first


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tạo khóa ECDSA P-256 và ký firmware STM32F103."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    keygen = commands.add_parser("keygen", help="Tạo private key và header public key.")
    keygen.add_argument("--private-key", type=Path, required=True)
    keygen.add_argument("--public-header", type=Path, required=True)

    sign = commands.add_parser("sign", help="Ký firmware, tạo file .bin.sig.")
    sign.add_argument("firmware", type=Path)
    sign.add_argument("--private-key", type=Path, required=True)
    sign.add_argument("--version", type=int, required=True)
    sign.add_argument("--output", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "keygen":
            password = _password("Private-key passphrase: ")
            if _password("Repeat passphrase: ") != password:
                raise ValueError("Hai passphrase không khớp.")
            generate_key_files(args.private_key, args.public_header, password)
            print(f"Private key (giữ bí mật): {args.private_key}")
            print(f"Public key header: {args.public_header}")
        else:
            if not 0 <= args.version <= 0xFFFFFFFF:
                raise ValueError("Version phải nằm trong khoảng uint32.")
            password = _password("Private-key passphrase: ")
            output = sign_firmware_file(
                args.firmware, args.private_key, args.version,
                password, args.output
            )
            print(f"Signature sidecar: {output}")
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Lỗi: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
