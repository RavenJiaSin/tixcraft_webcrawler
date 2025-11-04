# 檔案: ticketBot.py
# (已修改為「下載」驗證碼圖片，而不是「截圖」)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# --- ▼▼▼ 匯入智慧等待工具 ▼▼▼ ---
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# --- ▲▲▲ ---
import requests
import time
import os
import sys # 用於檢查 AI 核心

# 【步驟 1】匯入您的 AI 核心
try:
    import ai_core
    print("✅ AI 核心 (ai_core.py) 載入成功。")
except ImportError:
    print("❌ 錯誤：找不到 ai_core.py 檔案，AI 功能將無法使用。")
    ai_core = None
    sys.exit() # 缺少 AI 核心，直接退出

# 檢查 AI 核心是否成功載入模型
if ai_core.model is None:
    print("❌ 錯誤：AI 模型 (cnn_model.pth) 未能成功載入，請檢查檔案是否存在。")
    sys.exit() # 缺少模型，直接退出

# 初始化 Chrome
options = Options()
options.add_argument("--start-maximized")
try:
    service = Service() 
    driver = webdriver.Chrome(service=service, options=options)
except Exception as e:
    print(f"❌ 嚴重錯誤：無法啟動 Selenium WebDriver。")
    print("請檢查您的 chromedriver.exe 是否存在，且版本是否與您的 Chrome 瀏覽器匹配。")
    print(f"錯誤訊息: {e}")
    sys.exit() # 瀏覽器啟動失敗，直接退出

# --- 網站自動化流程開始 ---
print("...正在開啟目標網站...")
driver.get("https://ticket-training.onrender.com/")

try:
    # 處理 Cookie 彈窗
    driver.find_element(By.XPATH, "/html/body/div[7]/div/div/input").click()
    driver.find_element(By.XPATH, "/html/body/div[7]/div/button").click()
except:
    print("...未發現 Cookie 彈窗，繼續...")

print("...開始執行自動化流程...")

try:
    # --- 這是您舊程式碼中正確的部分 ---
    driver.find_element(By.XPATH, "/html/body/div[6]/input").send_keys("3")
    driver.find_element(By.XPATH, "/html/body/div[6]/button").click()
    print("...等待 3 秒倒數...")
    time.sleep(3.1) # 網站的固定倒數，這裡保留 time.sleep 是合適的
    
    # --- 以下是根據您 7 張圖片重建的流程 ---
    
    # 圖片 1: 點擊 "立即購票" (id="purchaseButton")
    print("...[1/7] 等待並點擊 '立即購票'...")
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "purchaseButton"))
    ).click()

    # 圖片 2: 點擊 "立即訂購" (class="purchase-button")
    print("...[2/7] 等待並點擊 '立即訂購'...")
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "purchase-button"))
    ).click()

    # 圖片 3: 點擊 "B2層特A1區" (class="seat-item")
    print("...[3/7] 等待並點擊 'B2層特A1區'...")
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.seat-item[onclick*='B2層特A1區']"))
    ).click()

    # 圖片 4: 選擇票數 "1" (name="quantity")
    print("...[4/7] 等待並選擇票數 '1'...")
    quantity_select_el = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "quantity"))
    )
    Select(quantity_select_el).select_by_visible_text("1")

    # 圖片 5: 勾選 "同意條款" (id="terms-checkbox")
    print("...[5/7] 等待並勾選 '同意條款'...")
    terms_checkbox = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "terms-checkbox"))
    )
    # 使用 JavaScript 點擊，可避免元素被遮擋導致點擊失敗
    driver.execute_script("arguments[0].click();", terms_checkbox)

    # -----------------------------------------------------
    # 【步驟 6: 破解驗證碼 (改為下載模式)】
    # -----------------------------------------------------
    print("...[6/7] 正在下載驗證碼圖片...")
    captcha_image_bytes = None
    try:
        # 1. 找到驗證碼圖片元素
        captcha_element = WebDriverWait(driver, 10).until(
             EC.presence_of_element_located((By.ID, "captcha-image"))
        )
        
        # 2. 取得圖片的絕對網址 (src)
        image_url = captcha_element.get_attribute("src")
        
        # 3. 準備 requests session
        http_session = requests.Session()
        
        # 4. 取得 Selenium 瀏覽器的所有 Cookies
        all_cookies = driver.get_cookies()
        
        # 5. 將 Selenium Cookies 複製到 requests session 中
        for cookie in all_cookies:
            http_session.cookies.set(cookie['name'], cookie['value'])
            
        # 6. 攜帶 Cookies 下載圖片
        response = http_session.get(image_url)
        
        if response.status_code == 200:
            captcha_image_bytes = response.content
            print("✅ 驗證碼圖片已透過 requests 下載。")
        else:
            print(f"❌ 下載驗證碼圖片失敗，狀態碼: {response.status_code}")

    except Exception as e:
        print(f"❌ 獲取驗證碼網址或下載時失敗: {e}")

    # 如果成功取得圖片，就呼叫 AI
    if captcha_image_bytes and ai_core:
        print("...正在呼叫 AI 核心進行辨識...")
        # 呼叫 ai_core 裡的函式
        captcha_answer = ai_core.crack_captcha(image_bytes=captcha_image_bytes, k_value=22)
        
        if "FAIL" not in captcha_answer and "EMPTY" not in captcha_answer and "MODEL" not in captcha_answer:
            print(f"🤖 AI 辨識結果: {captcha_answer}")
            
            # 自動填入答案
            driver.find_element(By.ID, "captcha-input").send_keys(captcha_answer)
            print("✅ 驗證碼已填入。")
            
            # 圖片 7: 點擊 "確認張數" (class="btn confirm-btn")
            print("...[7/7] 點擊 '確認張數' 送出...")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.confirm-btn"))
            ).click()
            
        else:
            print(f"❌ AI 辨識失敗，結果: {captcha_answer}")
    else:
        print("❌ 未能取得驗證碼圖片或 AI 核心載入失敗，無法繼續。")

except Exception as e:
    print(f"\n❌ 流程執行時發生未預期的錯誤: {e}")
    print("--- 流程已中斷 ---")
    # driver.quit() # 發生錯誤時可以取消註解此行來自動關閉

print("\n--- 流程執行完畢，請檢查瀏覽器 ---")
# driver.quit()