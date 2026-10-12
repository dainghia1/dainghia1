import hashlib
import struct
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from firmware_auth import (
    SIGNATURE_DOMAIN,
    SIGNATURE_FILE_SIZE,
    SIGNATURE_TARGET,
    decode_signature_file,
    encode_signature_file,
    signature_digest,
)
from sign_firmware import generate_key_files, raw_signature, sign_firmware_file


class FirmwareAuthTests(unittest.TestCase):
    def test_sidecar_round_trip_and_strict_size(self):
        signature = bytes(range(64))
        sidecar = encode_signature_file(7, signature)
        self.assertEqual(len(sidecar), SIGNATURE_FILE_SIZE)
        self.assertEqual(decode_signature_file(sidecar), (7, signature))
        with self.assertRaises(ValueError):
            decode_signature_file(sidecar[:-1])

    def test_digest_binds_firmware_version_and_target(self):
        image = b"firmware bytes"
        digest = signature_digest(image, 7)
        expected = hashlib.sha256(
            SIGNATURE_DOMAIN
            + SIGNATURE_TARGET
            + struct.pack("<II", len(image), 7)
            + image
        ).digest()
        self.assertEqual(digest, expected)
        private_key = ec.generate_private_key(ec.SECP256R1())
        signature = raw_signature(private_key, digest)
        r = int.from_bytes(signature[:32], "big")
        s = int.from_bytes(signature[32:], "big")
        public_key = private_key.public_key()

        public_key.verify(
            utils.encode_dss_signature(r, s),
            digest,
            ec.ECDSA(utils.Prehashed(hashes.SHA256())),
        )
        with self.assertRaises(InvalidSignature):
            changed_digest = signature_digest(image + b"x", 7)
            public_key.verify(
                utils.encode_dss_signature(r, s),
                changed_digest,
                ec.ECDSA(utils.Prehashed(hashes.SHA256())),
            )
        with self.assertRaises(InvalidSignature):
            public_key.verify(
                utils.encode_dss_signature(r, s),
                signature_digest(image, 8),
                ec.ECDSA(utils.Prehashed(hashes.SHA256())),
            )
        with self.assertRaises(ValueError):
            signature_digest(image, -1)

    def test_keygen_and_firmware_signing(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            firmware = root / "app.bin"
            private_path = root / "ota_private.pem"
            public_header = root / "ota_public_key.h"
            image = bytearray(16)
            image[0:8] = (0x20001000).to_bytes(4, "little") + \
                (0x08004401).to_bytes(4, "little")
            firmware.write_bytes(image)

            generate_key_files(private_path, public_header, b"test passphrase")
            self.assertIn(
                "OTA_PUBLIC_KEY_PROVISIONED 1U",
                public_header.read_text(encoding="ascii"),
            )
            sidecar = sign_firmware_file(
                firmware, private_path, 3, b"test passphrase"
            )
            version, signature = decode_signature_file(sidecar.read_bytes())
            private_key = serialization.load_pem_private_key(
                private_path.read_bytes(), password=b"test passphrase"
            )
            r = int.from_bytes(signature[:32], "big")
            s = int.from_bytes(signature[32:], "big")
            digest = signature_digest(bytes(image), version)
            private_key.public_key().verify(
                utils.encode_dss_signature(r, s),
                digest,
                ec.ECDSA(utils.Prehashed(hashes.SHA256())),
            )


if __name__ == "__main__":
    unittest.main()
