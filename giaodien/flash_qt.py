import os
import sys
import threading

from PySide6.QtCore import QObject, Signal, QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from serial.tools import list_ports

from flash_core import BAUD_RATE, flash

STYLE = """
QWidget { font-family: 'Segoe UI'; font-size: 10pt; }
QGroupBox { font-weight: bold; border: 1px solid #c8c8c8; border-radius: 6px; margin-top: 10px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QPushButton { background: #2d7ff9; color: white; border: none; border-radius: 5px; padding: 6px 12px; }
QPushButton:hover { background: #1f6de0; }
QPushButton:disabled { background: #b0b0b0; }
QPushButton#btnError { background: #e67e22; }
QPushButton#btnCancel { background: #c0392b; }
QProgressBar { border: 1px solid #c8c8c8; border-radius: 5px; text-align: center; height: 20px; }
QProgressBar::chunk { background: #27ae60; border-radius: 4px; }
QPlainTextEdit { background: #1e1e1e; color: #d4d4d4; font-family: Consolas; }
"""


class Bridge(QObject):
    """Cầu nối: thread nạp phát tín hiệu, giao diện nhận và cập nhật."""
    progress = Signal(int)
    log = Signal(str)
    done = Signal(bool)


class Main:
    def __init__(self):
        base = os.path.dirname(os.path.abspath(__file__))
        f = QFile(os.path.join(base, "flash_ui.ui"))
        if not f.open(QIODevice.OpenModeFlag.ReadOnly):
            raise SystemExit("Không mở được flash_ui.ui (kiểm tra tên file và thư mục)")
        self.ui = QUiLoader().load(f)
        f.close()

        self.stop_event = threading.Event()
        self.br = Bridge()
        self.br.progress.connect(self.ui.pgBar.setValue)
        self.br.log.connect(self.ui.tedt.appendPlainText)
        self.br.done.connect(self.on_done)

        self.ui.tedt.setReadOnly(True)
        self.ui.pgBar.setValue(0)
        self.ui.lbStatus.setText(
            "Sẵn sàng. Bấm Flash; tool sẽ tự yêu cầu app vào bootloader."
        )

        self.ui.cbBaud.addItem(str(BAUD_RATE))
        self.ui.cbBaud.setCurrentText(str(BAUD_RATE))
        self.ui.cbBaud.setEnabled(False)
        self.ui.edtA.setText(os.path.join(base, "appA.bin"))
        self.ui.edtB.setText(os.path.join(base, "appB.bin"))

        self.ui.btnRefresh.clicked.connect(self.refresh_ports)
        self.ui.btnBrowseA.clicked.connect(lambda: self.browse(self.ui.edtA))
        self.ui.btnBrowseB.clicked.connect(lambda: self.browse(self.ui.edtB))
        self.ui.btnFlashA.clicked.connect(lambda: self.start(self.ui.edtA.text(), False))
        self.ui.btnFlashB.clicked.connect(lambda: self.start(self.ui.edtB.text(), False))
        self.ui.btnError.clicked.connect(lambda: self.start(self.ui.edtA.text(), True))   # nạp ảnh lỗi
        self.ui.btnCancel.clicked.connect(self.stop_event.set)
        self.ui.btnCancel.setEnabled(False)
        self.refresh_ports()
        self.ui.show()

    def refresh_ports(self):
        self.ui.cbPort.clear()
        self.ui.cbPort.addItems([p.device for p in list_ports.comports()])

    def browse(self, edit):
        p, _ = QFileDialog.getOpenFileName(self.ui, "Chọn file .bin", "", "Binary (*.bin);;All (*)")
        if p:
            edit.setText(p)

    def set_busy(self, busy):
        for b in (self.ui.btnFlashA, self.ui.btnFlashB, self.ui.btnError):
            b.setEnabled(not busy)
        self.ui.btnCancel.setEnabled(busy)

    def start(self, path, corrupt):
        port = self.ui.cbPort.currentText()
        if not port:
            QMessageBox.warning(self.ui, "Thiếu cổng", "Chưa chọn cổng COM.")
            return
        if not os.path.isfile(path):
            QMessageBox.critical(self.ui, "Không có file", f"Không tìm thấy:\n{path}")
            return
        try:
            baud = int(self.ui.cbBaud.currentText())
        except ValueError:
            QMessageBox.critical(self.ui, "Sai baud", "Baud phải là số.")
            return

        self.stop_event.clear()
        self.ui.pgBar.setValue(0)
        self.ui.lbStatus.setText("Đang nạp...")
        self.set_busy(True)

        def job():
            ok = flash(port, baud, path, corrupt,
                       self.br.progress.emit, self.br.log.emit, self.stop_event)
            self.br.done.emit(ok)

        threading.Thread(target=job, daemon=True).start()

    def on_done(self, ok):
        self.set_busy(False)
        self.ui.lbStatus.setText(
            "THÀNH CÔNG - bootloader đã chấp nhận lệnh chạy ứng dụng"
            if ok else "THẤT BẠI - xem nhật ký để biết trạng thái thiết bị"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    m = Main()
    sys.exit(app.exec())