# config.py

# --- 監票模組設定 (for ticket_monitor.py) ---

# 1. 監控的目標 Tixcraft 網址
# 範例: "https://tixcraft.com/ticket/area/23_tanya/13966"
MONITOR_URL = "https://tixcraft.com/ticket/area/26_della/21450"

# 2. 想要鎖定的票區名稱 (請填寫網頁上顯示的完整名稱)
# 範例: ["搖滾A區", "搖滾B區"]
# 注意: 如果票區名稱包含「已售完」，監控器會忽略它
TARGET_AREAS = ["紅218區"]

# 3. 每次檢查的間隔秒數 (建議 1-5 秒，避免對伺服器造成過大壓力)
CHECK_INTERVAL_SECONDS = 2


# --- 搶票模組設定 (for the purchasing bot) ---

# 4. 找到票後，Selenium 要開啟的網址 (通常與 MONITOR_URL 相同)
PURCHASE_URL = "https://ticket-training.onrender.com/"

# 5. 搶票時要點擊的票區 CSS Selector
# 這是從 ticketBot.py 來的範例，請根據您的實際目標修改
SEAT_SELECTOR = "div.seat-item[onclick*='A1區']"

# 6. 購買的票券數量
QUANTITY = 1

# 7. AI 模型辨識時的 K 值 (如果需要調整)
K_VALUE = 22
