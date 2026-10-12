import os
import struct
import time


import serial

SOF = 0xA5
EOF = 0x5A
SYNC = 0x55
SYNC_ACK = 0x79

CMD_START, CMD_DATA, CMD_END, CMD_JUMP = 1, 2, 3, 4
CMD_REBOOT_BL = 5

ST_OK = 0
ST_ERR_FRAME = 1
ST_ERR_CRC = 8

BAUD_RATE = 115200
CHUNK_SIZE = 128
APP_HEADER_SIZE = 1024
APP_HEADER_MAGIC = 0xABCDEFAB
APP_START_ADDR = 0x08004400
APP_MAX_SIZE = 47 * 1024
RAM_START_ADDR = 0x20000000
RAM_END_ADDR = 0x20005000

MAX_RETRY = 3
INITIAL_SYNC_TIMEOUT = 0.75
APP_REBOOT_TIMEOUT = 1.0
SYNC_TIMEOUT = 8.0
RESPONSE_TIMEOUT = 1.0
START_TIMEOUT = 8.0
MAX_RESPONSE_TEXT_SIZE = 96


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
    """CRC phần cứng STM32: poly 0x04C11DB7, init 0xFFFFFFFF, theo từ 32-bit LE."""
    if len(data) % 4:
        data += b"\xFF" * (4 - len(data) % 4)
    crc = 0xFFFFFFFF
    for (word,) in struct.iter_unpack("<I", data):
        crc ^= word
        for _ in range(32):
            crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF if crc & 0x80000000 \
                  else (crc << 1) & 0xFFFFFFFF
    return crc


def frame(cmd: int, payload: bytes = b"") -> bytes:
    if len(payload) > 132:
        raise ValueError("Payload vượt quá bộ đệm của bootloader.")
    body = bytes([cmd]) + struct.pack("<H", len(payload)) + payload
    checksum = crc16(body)
    return bytes([SOF]) + body + struct.pack("<H", checksum) + bytes([EOF])


def _read_exact(ser, size: int, deadline: float, stop_event=None) -> bytes | None:
    result = bytearray()
    while len(result) < size:
        if stop_event is not None and stop_event.is_set():
            return None
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        ser.timeout = min(remaining, 0.1) if stop_event is not None else remaining
        part = ser.read(size - len(result))
        if not part:
            if stop_event is None:
                return None
            continue
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


def _wait_app_reboot_ack(ser, timeout: float, stop_event=None) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if stop_event is not None and stop_event.is_set():
            return False
        first = _read_exact(ser, 1, deadline, stop_event)
        if first is None:
            if stop_event is not None and stop_event.is_set():
                return False
            continue
        if first[0] == SYNC_ACK:
            return True
        if first[0] == SOF:
            # If the target was already in the bootloader, it may report the
            # app-only reboot request as a framed protocol error. Skip it.
            _read_exact(ser, 5, deadline, stop_event)
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
<<<<<<< Updated upstream
    ser, expected_cmd: int, timeout: float
) -> tuple[int, str] | None:
=======
    ser, expected_cmd: int, timeout: float, stop_event
) -> int | None:
>>>>>>> Stashed changes
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if stop_event.is_set():
            return None
        first = _read_exact(ser, 1, deadline, stop_event)
        if first is None:
            if stop_event.is_set():
                return None
            continue
        if first[0] != SOF:
            continue
<<<<<<< Updated upstream
        header = _read_exact(ser, 3, deadline)
        if header is None:
=======
        rest = _read_exact(ser, 5, deadline, stop_event)
        if rest is None:
            if stop_event.is_set():
                return None
>>>>>>> Stashed changes
            return None

        cmd, status, text_size = header
        if text_size > MAX_RESPONSE_TEXT_SIZE:
            raise ProtocolError(
                f"Độ dài thông báo phản hồi không hợp lệ: {text_size}."
            )
        tail = _read_exact(ser, text_size + 3, deadline)
        if tail is None:
            return None

        text = tail[:text_size]
        received_crc = struct.unpack("<H", tail[text_size:text_size + 2])[0]
        body = bytes([cmd, status, text_size]) + text
        if tail[-1] != EOF or received_crc != crc16(body):
            raise ProtocolError("Phản hồi bootloader sai CRC16/EOF.")
        if cmd != expected_cmd and not (cmd == 0 and status == ST_ERR_FRAME):
            raise ProtocolError(
                f"CMD phản hồi không khớp (nhận {cmd}, cần {expected_cmd})."
            )
<<<<<<< Updated upstream
        return status, text.decode("utf-8", errors="replace")
=======
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
    }
    return messages.get(status, f"Mã trạng thái không xác định: {status}")


def _send_command(
    ser, cmd: int, payload: bytes, timeout: float, stop_event
) -> int | None:
    packet = frame(cmd, payload)
    for attempt in range(MAX_RETRY + 1):
        if stop_event.is_set():
            return None
        ser.write(packet)
        response = _read_response(ser, cmd, timeout, stop_event)
        if stop_event.is_set():
            return None
        if response is None:
            if attempt < MAX_RETRY:
                continue
            return None

        if response == ST_OK:
            return response
        if response == ST_ERR_FRAME and attempt < MAX_RETRY:
            continue
        return response
>>>>>>> Stashed changes
    return None


def _is_app_vector(image: bytes, offset: int = 0) -> bool:
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
        if magic == APP_HEADER_MAGIC and _is_app_vector(image, APP_HEADER_SIZE):
            return image[APP_HEADER_SIZE:], True

    return image, False


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
    }
    return messages.get(status, f"Mã trạng thái không xác định: {status}")


def _send_command(
    ser, cmd: int, payload: bytes, timeout: float
) -> tuple[int, str] | None:
    packet = frame(cmd, payload)
    for attempt in range(MAX_RETRY + 1):
        ser.write(packet)
        response = _read_response(ser, cmd, timeout)
        if response is None:
            if attempt < MAX_RETRY:
                continue
            return None

        status, _ = response
        if status == ST_OK:
            return response
        if status == ST_ERR_FRAME and attempt < MAX_RETRY:
            continue
        return response
    return None


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

    expected_crc = crc32_stm32(image)
    if corrupt:
        damaged = bytearray(image)
        damaged[len(damaged) // 2] ^= 0xFF
        image = bytes(damaged)
        on_log("[Thử lỗi CRC] Đã đổi một byte, giữ CRC gốc để bootloader từ chối.")

    packets = [
        ("START", CMD_START, struct.pack("<III", len(image), expected_crc, 0)),
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
        if stop_event.is_set():
            on_log("Đã hủy bởi người dùng.")
        else:
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
                if _wait_app_reboot_ack(ser, APP_REBOOT_TIMEOUT, stop_event):
                    on_log("Application đã nhận lệnh và đang reset.")
                elif not stop_event.is_set():
                    on_log("Không nhận ACK từ Application; tiếp tục dò bootloader.")

                if not stop_event.is_set():
                    synced = _wait_sync_ack(ser, stop_event)
        except serial.SerialException as exc:
            if stop_event.is_set():
                on_log("Đã hủy bởi người dùng.")  
            else:  
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
                response = _send_command(ser, cmd, payload, timeout, stop_event)
            except ProtocolError as exc:
                if stop_event.is_set():
                    on_log("Đã hủy bởi người dùng.")
                else:
                    on_log(f"Lỗi giao thức tại {name}: {exc}")
                return False
            except serial.SerialException as exc:
                if stop_event.is_set():
                    on_log("Đã hủy bởi người dùng.")
                else:
                    on_log(f"Lỗi truyền UART tại {name}: {exc}")
                return False

            if stop_event.is_set():
                on_log("Đã hủy bởi người dùng; dừng truyền firmware.")
                return False

            if response is None:
                status = None
                device_message = ""
            else:
                status, device_message = response

            if status != ST_OK:
                if name == "END" and status == ST_ERR_CRC:
                    on_log(
                        f"STM32 báo lỗi: {device_message or _status_message(status)}; "
                        "bootloader từ chối firmware; "
                        "không gửi JUMP, board ở lại bootloader."
                    )
                elif status is None:
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
                        f"{device_message or _status_message(status)} "
                        f"(status={status})."
                    )
                return False

            on_progress(int(100 * (index + 1) / len(packets)))

<<<<<<< Updated upstream
    on_log("Nạp và kiểm tra CRC thành công; bootloader đã xác nhận lệnh JUMP.")
=======
        on_log("Nạp và kiểm tra CRC thành công; bootloader đã xác nhận lệnh JUMP.")
        try:
            _log_application_output(ser, on_log, stop_event)
        except serial.SerialException as exc:
            on_log(f"Không đọc tiếp được UART từ Application: {exc}")

    if stop_event.is_set():
        on_log("Đã hủy theo dõi UART bởi người dùng.")
        return False
>>>>>>> Stashed changes
    return True
