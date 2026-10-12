import os
import struct
import time

import serial
from firmware_auth import (
    APP_HEADER_SIZE,
    APP_MAX_SIZE,
    SIGNATURE_SIZE,
    decode_signature_file,
    is_app_vector as _is_app_vector,
    prepare_image,
    signature_path_for_firmware,
)

SOF = 0xA5
EOF = 0x5A
SYNC = 0x55
SYNC_ACK = 0x79

CMD_START, CMD_DATA, CMD_END, CMD_JUMP = 1, 2, 3, 4
CMD_REBOOT_BL = 5

ST_OK = 0
ST_ERR_FRAME = 1
ST_ERR_CRC = 8
ST_ERR_SIGNATURE = 10

BAUD_RATE = 115200
CHUNK_SIZE = 1024

MAX_RETRY = 3
INITIAL_SYNC_TIMEOUT = 0.75
APP_REBOOT_TIMEOUT = 1.0
SYNC_TIMEOUT = 8.0
RESPONSE_TIMEOUT = 1.0
START_TIMEOUT = 8.0
APP_OUTPUT_CAPTURE_SECONDS = 3.5


class ProtocolError(Exception):
    """Raised when the bootloader response does not match the wire protocol."""


def crc16(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 \
                else (crc << 1) & 0xFFFF
    return crc


def crc32_stm32(data: bytes) -> int:
    """Match STM32F1 CRC peripheral writes of one zero-extended byte per word."""
    crc = 0xFFFFFFFF
    for byte in data:
        word = byte
        for bit in range(31, -1, -1):
            feedback = ((crc >> 31) ^ (word >> bit)) & 1
            crc = (crc << 1) & 0xFFFFFFFF
            if feedback:
                crc ^= 0x04C11DB7
    return crc


def frame(cmd: int, payload: bytes = b"") -> bytes:
    if len(payload) > 4 + CHUNK_SIZE:
        raise ValueError("Payload vượt quá bộ đệm của bootloader.")
    body = bytes([cmd]) + struct.pack("<H", len(payload)) + payload
    checksum = crc16(body)
    return bytes([SOF]) + body + struct.pack("<H", checksum) + bytes([EOF])


def _read_exact(ser, size: int, deadline: float) -> bytes | None:
    result = bytearray()
    while len(result) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        ser.timeout = remaining
        part = ser.read(size - len(result))
        if not part:
            return None
        result.extend(part)
    return bytes(result)


def _wait_sync_ack(
    ser,
    stop_event,
    timeout: float = SYNC_TIMEOUT,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if stop_event.is_set():
            return False
        ser.write(bytes([SYNC]))
        ser.timeout = min(0.25, max(0.01, deadline - time.monotonic()))
        response = ser.read(1)
        if response == bytes([SYNC_ACK]):
            return True
    return False


def _wait_app_reboot_ack(ser, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        first = _read_exact(ser, 1, deadline)
        if first is None:
            return False
        if first[0] == SYNC_ACK:
            return True
        if first[0] == SOF:
            # If the target was already in the bootloader, it may report the
            # app-only reboot request as a framed protocol error. Skip it.
            _read_exact(ser, 5, deadline)
    return False


def _request_app_reboot(ser) -> None:
    body = bytes([CMD_REBOOT_BL, 0, 0])
    request = (
        bytes([SOF])
        + body
        + struct.pack("<H", crc16(body))
    )
    ser.write(request)


def _read_response(
    ser, expected_cmd: int, timeout: float
) -> int | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        first = _read_exact(ser, 1, deadline)
        if first is None:
            return None
        if first[0] != SOF:
            continue
        rest = _read_exact(ser, 5, deadline)
        if rest is None:
            return None

        cmd, status = rest[0], rest[1]
        received_crc = struct.unpack("<H", rest[2:4])[0]
        if rest[4] != EOF or received_crc != crc16(bytes([cmd, status])):
            raise ProtocolError("Phản hồi bootloader sai CRC16/EOF.")
        if cmd != expected_cmd and not (cmd == 0 and status == ST_ERR_FRAME):
            raise ProtocolError(
                f"CMD phản hồi không khớp (nhận {cmd}, cần {expected_cmd})."
            )
        return status
    return None


def _status_message(status: int) -> str:
    messages = {
        1: "Lỗi frame/CRC16",
        2: "Lệnh không được hỗ trợ",
        3: "Tham số hoặc kích thước không hợp lệ",
        4: "Lệnh không đúng trạng thái phiên nạp",
        5: "Offset dữ liệu không liên tiếp",
        6: "Xóa Flash thất bại",
        7: "Ghi Flash thất bại",
        8: "CRC32 ảnh không khớp",
        9: "Ứng dụng không hợp lệ",
        10: "Chữ ký firmware không hợp lệ hoặc public key chưa được cấu hình",
    }
    return messages.get(status, f"Mã trạng thái không xác định: {status}")


def _send_command(
    ser, cmd: int, payload: bytes, timeout: float
) -> int | None:
    packet = frame(cmd, payload)
    for attempt in range(MAX_RETRY + 1):
        ser.write(packet)
        response = _read_response(ser, cmd, timeout)
        if response is None:
            if attempt < MAX_RETRY:
                continue
            return None

        if response == ST_OK:
            return response
        if response == ST_ERR_FRAME and attempt < MAX_RETRY:
            continue
        return response
    return None


def _log_application_output(ser, on_log, stop_event) -> None:
    deadline = time.monotonic() + APP_OUTPUT_CAPTURE_SECONDS
    line_buffer = bytearray()
    received = False

    while time.monotonic() < deadline and not stop_event.is_set():
        ser.timeout = min(0.1, max(0.01, deadline - time.monotonic()))
        chunk = ser.read(ser.in_waiting or 1)
        if not chunk:
            continue

        received = True
        line_buffer.extend(chunk)
        while b"\n" in line_buffer:
            line, _, remaining = line_buffer.partition(b"\n")
            line_buffer = bytearray(remaining)
            text = line.rstrip(b"\r").decode("utf-8", errors="replace")
            if text:
                on_log(f"Application UART: {text}")

        if len(line_buffer) >= 512:
            text = line_buffer.decode("utf-8", errors="replace")
            on_log(f"Application UART: {text}")
            line_buffer.clear()

    if line_buffer:
        text = line_buffer.decode("utf-8", errors="replace")
        on_log(f"Application UART: {text}")
    elif not received:
        on_log(
            "Không nhận được dữ liệu UART từ Application "
            f"trong {APP_OUTPUT_CAPTURE_SECONDS:g} giây."
        )


def flash(port, baud, path, corrupt, on_progress, on_log, stop_event):
    """Nạp một file ứng dụng qua giao thức UART của bootloader."""
    if baud != BAUD_RATE:
        on_log(f"Baud không hợp lệ: bootloader cố định ở {BAUD_RATE}.")
        return False

    try:
        image, header_removed = prepare_image(path)
    except OSError as exc:
        on_log(f"Không đọc được file firmware: {exc}")
        return False

    if header_removed:
        on_log(f"Đã bỏ trang header linker {APP_HEADER_SIZE} byte khỏi file .bin.")
    if not image:
        on_log("File firmware rỗng.")
        return False
    if len(image) > APP_MAX_SIZE:
        on_log(f"Firmware quá lớn: {len(image)} byte (tối đa {APP_MAX_SIZE}).")
        return False
    if len(image) & 3:
        on_log("Kích thước firmware phải chia hết cho 4 byte.")
        return False
    if not _is_app_vector(image):
        on_log(
            "Vector table không hợp lệ: kiểm tra .bin có bắt đầu bằng vector "
            "ứng dụng tại 0x08004400 hay không."
        )
        return False

    sig_path = signature_path_for_firmware(path)
    try:
        with open(sig_path, "rb") as file:
            version, signature = decode_signature_file(file.read())
    except (OSError, ValueError) as exc:
        on_log(f"Không đọc được chữ ký firmware ({sig_path}): {exc}")
        return False
    if len(signature) != SIGNATURE_SIZE:
        on_log("Sidecar chữ ký không chứa chữ ký ECDSA P-256 hợp lệ.")
        return False

    expected_crc = crc32_stm32(image)
    if corrupt:
        damaged = bytearray(image)
        damaged[len(damaged) // 2] ^= 0xFF
        image = bytes(damaged)
        on_log("[Thử lỗi CRC] Đã đổi một byte, giữ CRC gốc để bootloader từ chối.")

    packets = [
        (
            "START",
            CMD_START,
            struct.pack("<III", len(image), expected_crc, version) + signature,
        ),
    ]
    for offset in range(0, len(image), CHUNK_SIZE):
        chunk = image[offset:offset + CHUNK_SIZE]
        payload = struct.pack("<I", offset) + chunk
        packets.append(("DATA", CMD_DATA, payload))
    packets.append(("END", CMD_END, b""))
    packets.append(("JUMP", CMD_JUMP, b""))

    on_log(
        f"File: {os.path.basename(path)} - {len(image)} byte - "
        f"CRC32=0x{expected_crc:08X}"
    )
    on_log(f"Mở {port} @ {baud}; đang bắt tay SYNC với bootloader...")

    try:
        ser = serial.Serial(port, baud, timeout=0.1, write_timeout=1)
    except serial.SerialException as exc:
        on_log(f"Không mở được cổng COM: {exc}")
        return False

    with ser:
        try:
            ser.reset_input_buffer()
            synced = _wait_sync_ack(
                ser, stop_event, timeout=INITIAL_SYNC_TIMEOUT
            )
            if not synced and not stop_event.is_set():
                on_log("Chưa thấy bootloader; gửi yêu cầu app chuyển sang bootloader...")
                _request_app_reboot(ser)
                if _wait_app_reboot_ack(ser, APP_REBOOT_TIMEOUT):
                    on_log("Application đã nhận lệnh và đang reset.")
                elif not stop_event.is_set():
                    on_log("Không nhận ACK từ Application; tiếp tục dò bootloader.")

                if not stop_event.is_set():
                    synced = _wait_sync_ack(ser, stop_event)
        except serial.SerialException as exc:
            on_log(f"Lỗi UART khi bắt tay bootloader: {exc}")
            return False
        if not synced:
            if stop_event.is_set():
                on_log("Đã hủy bởi người dùng.")
            else:
                on_log("Không nhận SYNC ACK. Reset board và thử lại trong boot window.")
            return False
        on_log("Đã kết nối bootloader.")

        for index, (name, cmd, payload) in enumerate(packets):
            if stop_event.is_set():
                on_log("Đã hủy bởi người dùng.")
                return False

            timeout = START_TIMEOUT if name == "START" else RESPONSE_TIMEOUT
            try:
                response = _send_command(ser, cmd, payload, timeout)
            except ProtocolError as exc:
                on_log(f"Lỗi giao thức tại {name}: {exc}")
                return False
            except serial.SerialException as exc:
                on_log(f"Lỗi truyền UART tại {name}: {exc}")
                return False

            if response != ST_OK:
                if name == "END" and response == ST_ERR_CRC:
                    on_log(
                        "CRC32 ảnh không khớp: bootloader từ chối firmware; "
                        "không gửi JUMP, board ở lại bootloader."
                    )
                elif name == "END" and response == ST_ERR_SIGNATURE:
                    on_log(
                        "Chữ ký firmware không hợp lệ: bootloader từ chối ảnh; "
                        "không gửi JUMP, board ở lại bootloader."
                    )
                elif response is None:
                    if name == "JUMP":
                        on_log(
                            "Không nhận được phản hồi JUMP; firmware đã qua bước CRC "
                            "và board có thể đã chuyển sang ứng dụng."
                        )
                    else:
                        on_log(
                            f"Hết thời gian chờ phản hồi {name}; "
                            "kiểm tra kết nối rồi thử lại."
                        )
                else:
                    on_log(
                        f"{name} thất bại: "
                        f"{_status_message(response)} (status={response})."
                    )
                return False

            on_progress(int(100 * (index + 1) / len(packets)))

        on_log(
            "Nạp, CRC và chữ ký firmware hợp lệ; "
            "bootloader đã xác nhận lệnh JUMP."
        )
        try:
            _log_application_output(ser, on_log, stop_event)
        except serial.SerialException as exc:
            on_log(f"Không đọc tiếp được UART từ Application: {exc}")

    return True
