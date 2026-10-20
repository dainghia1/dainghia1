# Bootloader STM32 – Cập nhật firmware qua UART

## Mục tiêu

Bootloader cho STM32 nhận firmware từ máy tính qua UART, kiểm tra dữ liệu, xóa và ghi vùng Flash ứng dụng, sau đó chuyển sang chạy firmware mới. Dự án cũng có các hàm đọc, ghi, xóa Flash ở mức thanh ghi.

## Sơ đồ trực quan

### Thao tác Flash: đọc, ghi, xóa trang và xóa toàn bộ

![Các thuật toán thao tác Flash](docs/images/flash-thuat-toan.svg)

### Luồng khởi động Bootloader

![Luồng khởi động Bootloader](docs/images/bootloader-flow.svg)

### Khung UART và trình tự nạp firmware

![Giao thức UART](docs/images/uart-protocol.svg)

Các phần bên dưới là lưu đồ Mermaid và phần giải thích chi tiết tương ứng với các sơ đồ ảnh phía trên.

## 1. Thuật toán đọc Flash

```mermaid
flowchart TD
    A[Đặt số chu kỳ chờ LATENCY trong FLASH_ACR] --> B{BSY = 1 trong FLASH_SR?}
    B -- Có --> B
    B -- Không --> C[Đọc trực tiếp từ địa chỉ Flash]
    C --> D[Trả dữ liệu đã đọc]
```

Việc đọc Flash không cần mở khóa Flash. Trước khi đọc, chương trình chờ bit `BSY` về `0` để bảo đảm không có thao tác ghi hoặc xóa đang diễn ra. Dữ liệu được đọc trực tiếp từ địa chỉ vùng Flash.

## 2. Thuật toán ghi Flash 16-bit

```mermaid
flowchart TD
    A[Đọc bit LOCK trong FLASH_CR] --> B{LOCK = 1?}
    B -- Có --> C[Ghi KEY1 = 0x45670123 vào FLASH_KEYR]
    C --> D[Ghi KEY2 = 0xCDEF89AB vào FLASH_KEYR]
    D --> E[Đặt PG = 1 trong FLASH_CR]
    B -- Không --> E
    E --> F[Ghi 16 bit vào địa chỉ Flash cần ghi]
    F --> G{BSY = 1 trong FLASH_SR?}
    G -- Có --> G
    G -- Không --> H[Đọc lại đúng địa chỉ vừa ghi]
    H --> I{Dữ liệu đọc lại khớp?}
    I -- Có --> J[Báo ghi thành công]
    I -- Không --> K[Báo lỗi ghi]
```

Khi Flash đang bị khóa, hai khóa `KEY1` và `KEY2` được ghi liên tiếp vào `FLASH_KEYR` để mở khóa. Bit `PG` cho phép chế độ lập trình. Mỗi lần ghi là một nửa từ 16-bit; chương trình chờ `BSY = 0` rồi đọc lại để xác minh giá trị.

## 3. Thuật toán xóa một trang Flash

```mermaid
flowchart TD
    A[Đọc bit LOCK trong FLASH_CR] --> B{LOCK = 1?}
    B -- Có --> C[Ghi KEY1 = 0x45670123 vào FLASH_KEYR]
    C --> D[Ghi KEY2 = 0xCDEF89AB vào FLASH_KEYR]
    D --> E[Đặt PER = 1 trong FLASH_CR]
    B -- Không --> E
    E --> F[Ghi địa chỉ trang cần xóa vào FLASH_AR/FAR]
    F --> G[Đặt STRT = 1 trong FLASH_CR]
    G --> H{BSY = 1 trong FLASH_SR?}
    H -- Có --> H
    H -- Không --> I[Đọc toàn bộ trang để kiểm tra]
    I --> J{Mọi nửa từ đều là 0xFFFF?}
    J -- Có --> K[Báo xóa trang thành công]
    J -- Không --> L[Báo lỗi xóa trang]
```

Bit `PER` chọn xóa theo trang. Địa chỉ của trang cần xóa được nạp vào thanh ghi địa chỉ Flash, sau đó đặt `STRT` để bắt đầu. Khi `BSY` trở về `0`, chương trình kiểm tra toàn bộ trang: Flash đã xóa phải có giá trị `0xFFFF` tại từng đơn vị 16-bit.

## 4. Thuật toán xóa toàn bộ Flash

```mermaid
flowchart TD
    A[Đọc bit LOCK trong FLASH_CR] --> B{LOCK = 1?}
    B -- Có --> C[Ghi KEY1 = 0x45670123 vào FLASH_KEYR]
    C --> D[Ghi KEY2 = 0xCDEF89AB vào FLASH_KEYR]
    D --> E[Đặt MER = 1 trong FLASH_CR]
    B -- Không --> E
    E --> F[Đặt STRT = 1 trong FLASH_CR]
    F --> G{BSY = 1 trong FLASH_SR?}
    G -- Có --> G
    G -- Không --> H[Đọc toàn bộ vùng cần kiểm tra]
    H --> I{Mọi nửa từ đều là 0xFFFF?}
    I -- Có --> J[Báo xóa toàn bộ thành công]
    I -- Không --> K[Báo lỗi xóa]
```

Bit `MER` chọn chế độ xóa hàng loạt. Sau khi xóa hoàn tất, nội dung vùng Flash được kiểm tra để bảo đảm không còn dữ liệu cũ trước khi nhận firmware mới.

## 5. Luồng khởi động của Bootloader

```mermaid
flowchart TD
    A([Bật nguồn / Reset cứng]) --> B[Khởi tạo Clock, GPIO, USART1, CRC, PWR/BKP]
    B --> C{BKP_DR1 = 0xB007?}
    C -- Có --> D[Ở lại Bootloader và chờ lệnh nạp]
    C -- Không --> E[Khởi động bộ đếm 3000 ms]
    E --> F{Nhận được byte SYNC 0x55 trong 3000 ms?}
    F -- Có --> G[Trả ACK 0x79 và vào hàm loader]
    F -- Không --> H[Kiểm tra bootloader_is_app_valid]
    H -- Firmware hợp lệ --> I[Dọn dẹp ngoại vi, đặt MSP, nhảy sang App]
    H -- Firmware không hợp lệ --> J[Ở lại Bootloader, báo lỗi]
```

Sau reset, bootloader có thể được giữ lại bằng cờ `BKP_DR1 = 0xB007`. Nếu không có cờ này, bootloader chờ byte đồng bộ `SYNC = 0x55` trong 3 giây. Nếu không có yêu cầu nạp và firmware ứng dụng hợp lệ, MCU sẽ nhảy sang ứng dụng; ngược lại vẫn ở bootloader.

## 6. Định dạng khung UART

### Khung yêu cầu từ máy tính

```text
┌─────┬─────┬─────┬─────────┬───────┬─────┐
│ SOF │ CMD │ LEN │ PAYLOAD │ CRC16 │ EOF │
└─────┴─────┴─────┴─────────┴───────┴─────┘
```

### Khung phản hồi từ bootloader

```text
┌─────┬─────┬────────┬───────┬─────┐
│ SOF │ CMD │ STATUS │ CRC16 │ EOF │
└─────┴─────┴────────┴───────┴─────┘
```

- `SOF` / `EOF`: đánh dấu đầu và cuối khung.
- `CMD`: mã lệnh, ví dụ `START`, `DATA`, `END`, `JUMP`.
- `LEN`: độ dài trường dữ liệu.
- `PAYLOAD`: dữ liệu lệnh hoặc một khối firmware.
- `CRC16`: kiểm tra lỗi của khung truyền.
- `STATUS`: trạng thái xử lý, `0` là thành công; giá trị khác `0` là lỗi.

## 7. Trình tự nạp firmware qua UART

```mermaid
sequenceDiagram
    participant PC as PC / Chương trình nạp
    participant BL as STM32 / Bootloader

    PC->>BL: SYNC: 0x55
    BL-->>PC: ACK: 0x79
    PC->>BL: START frame
    BL-->>PC: Phản hồi START: STATUS = 0
    loop Mỗi khối firmware
        PC->>BL: DATA frame #N: offset, dữ liệu
        Note right of BL: Kiểm tra CRC16, xóa/ghi Flash và xác minh
        BL-->>PC: Phản hồi DATA: STATUS = 0
    end
    PC->>BL: END frame
    Note right of BL: Kiểm tra CRC32 toàn bộ firmware<br/>và ghi header ứng dụng
    BL-->>PC: Phản hồi END: STATUS = 0
    PC->>BL: JUMP frame
    BL-->>PC: Phản hồi JUMP: STATUS = 0
    Note right of BL: MCU chuyển sang ứng dụng
```

Quá trình bắt đầu bằng `SYNC 0x55`; bootloader đáp lại `ACK 0x79`. Máy tính gửi `START`, rồi truyền các khung `DATA` chứa firmware. Với từng khung, bootloader kiểm tra CRC16, xử lý Flash và trả `STATUS`. Khi nhận `END`, bootloader kiểm tra CRC32 toàn bộ firmware, ghi header ứng dụng và chỉ cho phép `JUMP` khi firmware hợp lệ.
