import sys
import time
import os
import subprocess  # [新增] 用來執行外部檔案
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QGroupBox, QSpinBox
)
from PyQt6.QtCore import QThread, pyqtSignal

# 匯入核心模組
import bot_core
import config

# ---------------------------------------------------------
# 背景工作：監控執行緒
# ---------------------------------------------------------
class MonitorWorker(QThread):
    log_signal = pyqtSignal(str)
    ticket_found_signal = pyqtSignal(object, str) # 傳遞 (driver, area_name)

    def __init__(self, bot, url, target_keywords):
        super().__init__()
        self.bot = bot
        self.url = url
        self.target_keywords = target_keywords
        self.running = True

    def run(self):
        self.log_signal.emit(f"🎯 監控目標: {self.url}")
        self.log_signal.emit(f"🔍 關鍵字: {self.target_keywords if self.target_keywords else '全部 (有票就搶)'}")
        
        # 導航到目標頁面
        self.bot.navigate(self.url)
        time.sleep(1)

        while self.running:
            # 呼叫 bot_core 進行掃描
            found_ticket_text = self.bot.scan_for_tickets(self.target_keywords)

            if found_ticket_text:
                self.log_signal.emit(f"🔥🔥🔥 發現票券：{found_ticket_text}")
                # 發送訊號
                self.ticket_found_signal.emit(self.bot.driver, found_ticket_text)
                self.running = False # 停止監控
                break
            
            # 沒找到，休息一下
            time.sleep(1.5)

    def stop(self):
        self.running = False

# ---------------------------------------------------------
# 主視窗
# ---------------------------------------------------------
class TicketApp(QWidget):
    def __init__(self):
        super().__init__()
        self.bot = bot_core.TixCraftMonitor() # 實體化監控核心
        self.worker = None
        self.setWindowTitle("拓元實體監控 -> 虛擬搶票觸發器")
        self.resize(700, 550)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- 區塊 1: 瀏覽器初始化 ---
        group_init = QGroupBox("1. 瀏覽器初始化")
        layout_init = QHBoxLayout()
        
        self.btn_browser = QPushButton("啟動隱身瀏覽器 (Undetected Chrome)")
        self.btn_browser.clicked.connect(self._on_launch_browser)
        self.btn_browser.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        layout_init.addWidget(self.btn_browser)
        
        lbl_note = QLabel("⚠️ 啟動後請手動登入拓元帳號，並保持瀏覽器開啟")
        lbl_note.setStyleSheet("color: red;")
        layout_init.addWidget(lbl_note)
        
        group_init.setLayout(layout_init)
        layout.addWidget(group_init)

        # --- 區塊 2: 監控設定 ---
        group_settings = QGroupBox("2. 監控設定")
        layout_settings = QVBoxLayout()

        # 網址
        layout_settings.addWidget(QLabel("監控網址 (區域選擇頁面):"))
        self.input_url = QLineEdit()
        if hasattr(config, 'MONITOR_URL'):
            self.input_url.setText(config.MONITOR_URL)
        layout_settings.addWidget(self.input_url)

        # 關鍵字
        layout_settings.addWidget(QLabel("區域關鍵字 (逗號分隔，留空代表全搶):"))
        self.input_keywords = QLineEdit()
        if hasattr(config, 'TARGET_AREAS'):
            self.input_keywords.setText(",".join(config.TARGET_AREAS))
        layout_settings.addWidget(self.input_keywords)
        
        # 張數 (這裡僅作顯示，實際張數設定在 ticketBot.py 或 config 中)
        layout_settings.addWidget(QLabel("購買張數 (將傳遞給搶票程式):"))
        self.spin_quantity = QSpinBox()
        self.spin_quantity.setRange(1, 4)
        if hasattr(config, 'QUANTITY'):
            self.spin_quantity.setValue(config.QUANTITY)
        layout_settings.addWidget(self.spin_quantity)

        group_settings.setLayout(layout_settings)
        layout.addWidget(group_settings)

        # --- 區塊 3: 控制面板 ---
        group_ctrl = QGroupBox("3. 執行控制")
        layout_ctrl = QHBoxLayout()
        
        self.btn_start = QPushButton("開始監控")
        self.btn_start.clicked.connect(self._on_start_monitor)
        self.btn_start.setEnabled(False) # 需先開瀏覽器
        
        self.btn_stop = QPushButton("停止監控")
        self.btn_stop.clicked.connect(self._on_stop_monitor)
        self.btn_stop.setEnabled(False)

        layout_ctrl.addWidget(self.btn_start)
        layout_ctrl.addWidget(self.btn_stop)
        group_ctrl.setLayout(layout_ctrl)
        layout.addWidget(group_ctrl)

        # --- 區塊 4: 系統日誌 ---
        layout.addWidget(QLabel("系統日誌:"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

    def _log(self, msg):
        self.log_box.append(msg)
        self.log_box.ensureCursorVisible()

    def _on_launch_browser(self):
        self._log("正在啟動瀏覽器... 請稍候")
        driver = self.bot.start_driver()
        if driver:
            self._log("✅ 瀏覽器啟動成功！")
            self._log("👉 請在跳出的視窗中登入拓元。")
            self.btn_start.setEnabled(True)
            self.btn_browser.setEnabled(False)
        else:
            self._log("❌ 瀏覽器啟動失敗，請檢查環境。")

    def _on_start_monitor(self):
        url = self.input_url.text().strip()
        if not url:
            self._log("❌ 請輸入網址")
            return

        keywords_str = self.input_keywords.text().strip()
        keywords = [k.strip() for k in keywords_str.split(',')] if keywords_str else []

        self.worker = MonitorWorker(self.bot, url, keywords)
        self.worker.log_signal.connect(self._log)
        self.worker.ticket_found_signal.connect(self._on_ticket_found)
        self.worker.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.input_url.setEnabled(False)

    def _on_stop_monitor(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self._log("🛑 監控已手動停止。")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.input_url.setEnabled(True)

    def _on_ticket_found(self, driver, area_name):
        self._log(f"⚡️ 觸發！目標區域：{area_name}")
        self._log("🚀 正在啟動 ticketBot.py (虛擬搶票)...")
        
        # [核心修改] 使用 subprocess 啟動外部檔案
        try:
            # 這行指令等同於在 CMD 輸入 "python ticketBot.py"
            # 使用 sys.executable 確保用的是當前的 Python 環境
            subprocess.Popen([sys.executable, "ticketBot.py"])
            
            self._log("✅ ticketBot.py 已成功啟動！請查看新跳出的視窗。")
            
        except Exception as e:
            self._log(f"❌ 啟動 ticketBot 失敗: {e}")

    def closeEvent(self, event):
        if self.worker: self.worker.stop()
        self.bot.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TicketApp()
    window.show()
    sys.exit(app.exec())