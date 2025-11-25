import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QListWidget, QListWidgetItem, QPushButton, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# -----------------------------
# Placeholder / Integration API
# -----------------------------
# These functions are stubs to be replaced by the monitoring system.
# The GUI will call these functions (or the worker thread) when integrated.

def fetch_sessions():
    """Stub: return a list of available sessions.

    Replace this function to call the real monitoring system and return
    a list of dicts: [{"id": ..., "name": ...}, ...]
    """
    return [
        {"id": 1, "name": "2025/12/01 19:30 台北小巨蛋 - 場次 A"},
        {"id": 2, "name": "2025/12/02 19:30 台北小巨蛋 - 場次 B"},
        {"id": 3, "name": "2025/12/03 14:00 台北小巨蛋 - 場次 C"},
    ]


def fetch_seats(session_id):
    """Stub: return available seat areas for a given session.

    Replace this with a call into your ticket_monitor module.
    Should return a list of strings, e.g. ["A 區", "B 區", ...]
    """
    # Return mock seat areas depending on session_id (for demonstration)
    base = ["A 區", "B 區", "C 區", "D 區", "E 區"]
    if session_id == 2:
        return ["A 區", "C 區", "E 區"]
    return base


# -----------------------------
# Worker thread skeleton
# -----------------------------
class PurchaseWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, session, seat_priority, quantity, parent=None):
        super().__init__(parent)
        self.session = session
        self.seat_priority = seat_priority
        self.quantity = quantity
        self._running = True

    def run(self):
        # This is where you'll integrate the ticketBot logic.
        # For now, emit logs to simulate activity.
        self.log_signal.emit(f"開始自動購票：場次={self.session}, 張數={self.quantity}")
        self.log_signal.emit("依序嘗試座位志願序：" + ", ".join(self.seat_priority))

        # Simulate steps
        import time
        steps = ["初始化 WebDriver", "開啟購票頁面", "處理彈窗", "開始選票", "處理驗證碼", "送出訂單"]
        for i, s in enumerate(steps, start=1):
            if not self._running:
                self.log_signal.emit("使用者已停止流程，終止工作。")
                self.finished_signal.emit(False)
                return
            self.log_signal.emit(f"[{i}/{len(steps)}] {s} ...")
            time.sleep(0.8)

        # Simulate a seat selection attempt following priority
        for seat in self.seat_priority:
            if not self._running:
                self.log_signal.emit("使用者已停止流程，終止工作。")
                self.finished_signal.emit(False)
                return
            self.log_signal.emit(f"嘗試座位: {seat} ...")
            time.sleep(0.6)
            # fake success on first available (for demo, pick A 區 success)
            if seat.startswith("A"):
                self.log_signal.emit(f"已選到座位: {seat}。進行下一步...")
                break
            else:
                self.log_signal.emit(f"座位 {seat} 無法選到，嘗試下一順位。")

        # finalizing
        self.log_signal.emit("驗證碼辨識... (呼叫 ai_core.crack_captcha)")
        time.sleep(1.0)
        self.log_signal.emit("訂單已送出，等待結果...")
        time.sleep(0.8)

        # finished
        self.log_signal.emit("購票流程完成。")
        self.finished_signal.emit(True)

    def stop(self):
        self._running = False


# -----------------------------
# Main GUI
# -----------------------------
class TicketApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自動購票系統")
        self.resize(700, 420)
        self.worker = None
        self._build_ui()
        self._load_sessions()

    def _build_ui(self):
        layout = QHBoxLayout(self)

        # Left column: controls
        left = QVBoxLayout()

        # Session selector
        left.addWidget(QLabel("選擇場次："))
        self.session_combo = QComboBox()
        self.session_combo.currentIndexChanged.connect(self._on_session_changed)
        left.addWidget(self.session_combo)

        # Seat priority list (draggable)
        left.addWidget(QLabel("座位志願序（拖曳以重新排序）："))
        self.seat_list = QListWidget()
        self.seat_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.seat_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.seat_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        left.addWidget(self.seat_list)

        # Quantity
        qbox = QHBoxLayout()
        qbox.addWidget(QLabel("購買張數："))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(10)
        self.quantity_spin.setValue(1)
        qbox.addWidget(self.quantity_spin)
        left.addLayout(qbox)

        # Buttons: start / stop
        btn_box = QHBoxLayout()
        self.start_btn = QPushButton("開始自動購票")
        self.start_btn.clicked.connect(self._on_start)
        btn_box.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        btn_box.addWidget(self.stop_btn)

        left.addLayout(btn_box)

        layout.addLayout(left, 40)

        # Right column: logs / status
        right = QVBoxLayout()
        right.addWidget(QLabel("狀態 / 日誌："))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right.addWidget(self.log_text)

        layout.addLayout(right, 60)

    def _load_sessions(self):
        # load sessions (from monitoring system in future)
        sessions = fetch_sessions()
        self.sessions = sessions
        self.session_combo.clear()
        for s in sessions:
            self.session_combo.addItem(s["name"], s["id"])
        if sessions:
            self.session_combo.setCurrentIndex(0)

    def _on_session_changed(self, idx):
        # when session changes, fetch seats for that session
        if idx < 0:
            return
        session_id = self.session_combo.currentData()
        self._append_log(f"選擇場次: {self.session_combo.currentText()} (id={session_id})")
        seats = fetch_seats(session_id)
        self._populate_seats(seats)

    def _populate_seats(self, seats):
        self.seat_list.clear()
        for seat in seats:
            item = QListWidgetItem(seat)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.seat_list.addItem(item)

    def _get_seat_priority(self):
        return [self.seat_list.item(i).text() for i in range(self.seat_list.count())]

    def _on_start(self):
        session_name = self.session_combo.currentText()
        session_id = self.session_combo.currentData()
        seat_priority = self._get_seat_priority()
        quantity = self.quantity_spin.value()

        if not session_name or not seat_priority:
            self._append_log("請先選擇場次與座位志願序。")
            return

        # lock UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.session_combo.setEnabled(False)
        self.seat_list.setEnabled(False)
        self.quantity_spin.setEnabled(False)

        # start worker thread
        self.worker = PurchaseWorker(session_name, seat_priority, quantity)
        self.worker.log_signal.connect(self._append_log)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()
        self._append_log("購票工作已啟動。")

    def _on_stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self._append_log("已要求停止工作，請稍候...")
            self.stop_btn.setEnabled(False)

    def _on_finished(self, success):
        self._append_log(f"工作結束，結果: {'成功' if success else '失敗 / 中止'}")
        # unlock UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.session_combo.setEnabled(True)
        self.seat_list.setEnabled(True)
        self.quantity_spin.setEnabled(True)

    def _append_log(self, text: str):
        self.log_text.append(text)
        # auto-scroll to bottom
        self.log_text.ensureCursorVisible()


# -----------------------------
# Entrypoint
# -----------------------------
def main():
    app = QApplication(sys.argv)
    w = TicketApp()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
import tkinter as tk
from tkinter import ttk

# Placeholder for future integration with monitoring system
# --------------------------------------------------------
# def fetch_sessions():
#     # TODO: Integrate with monitoring system to fetch live sessions
#     return []
#
# def fetch_seats(session_id):
#     # TODO: Integrate with monitoring system to fetch seat availability
#     return []

# Temporary mock data
MOCK_SESSIONS = [
    {"id": 1, "name": "場次 A - 10:00"},
    {"id": 2, "name": "場次 B - 14:00"},
    {"id": 3, "name": "場次 C - 18:00"},
]

MOCK_SEATS = ["A1", "A2", "A3", "B1", "B2", "C1", "C2"]

class TicketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("自動購票系統 GUI")
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.grid(row=0, column=0)

        # Session selection
        ttk.Label(frame, text="選擇場次:").grid(row=0, column=0, sticky=tk.W)
        self.session_var = tk.StringVar()
        self.session_combo = ttk.Combobox(frame, textvariable=self.session_var, state="readonly")
        self.session_combo["values"] = [s["name"] for s in MOCK_SESSIONS]
        self.session_combo.grid(row=0, column=1, pady=5)

        # Seat priority ordering
        ttk.Label(frame, text="座位志願序:").grid(row=1, column=0, sticky=tk.W)
        self.seat_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=7)
        for seat in MOCK_SEATS:
            self.seat_listbox.insert(tk.END, seat)
        self.seat_listbox.grid(row=1, column=1, pady=5)

        # Ticket count
        ttk.Label(frame, text="購買張數:").grid(row=2, column=0, sticky=tk.W)
        self.ticket_var = tk.IntVar(value=1)
        ttk.Entry(frame, textvariable=self.ticket_var).grid(row=2, column=1, pady=5)

        # Start button
        self.start_button = ttk.Button(frame, text="開始自動購票", command=self.start_purchase)
        self.start_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Status display
        ttk.Label(frame, text="狀態:").grid(row=4, column=0, sticky=tk.W)
        self.status_var = tk.StringVar(value="等待開始...")
        ttk.Label(frame, textvariable=self.status_var).grid(row=4, column=1, sticky=tk.W)

    def start_purchase(self):
        session = self.session_var.get()
        selected_indices = self.seat_listbox.curselection()
        seats = [self.seat_listbox.get(i) for i in selected_indices]
        ticket_count = self.ticket_var.get()

        # TODO: call actual ticket purchasing logic + monitoring system functions
        self.status_var.set(f"執行中... 選擇場次: {session}, 座位: {seats}, 張數: {ticket_count}")


def main():
    root = tk.Tk()
    app = TicketGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
