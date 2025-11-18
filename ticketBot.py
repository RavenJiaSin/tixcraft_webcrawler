import requests
import time
import os
import sys # 用於檢查 AI 核心

import config # 匯入 config 檔案
import ticket_monitor # 匯入監票模組
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
# from selenium.webdriver.common.alert import Alert # 未使用到，可移除
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 全域變數初始化 ---
# 【步驟 1】匯入您的 AI 核心
ai_core = None
try:
    import ai_core
    print("✅ AI 核心 (ai_core.py) 載入成功。")
    if ai_core.model is None:
        print("❌ 錯誤：AI 模型 (cnn_model.pth) 未能成功載入，請檢查檔案是否存在。")
        sys.exit("AI 模型載入失敗，程式退出。")
except ImportError:
    print("❌ 錯誤：找不到 ai_core.py 檔案，AI 功能將無法使用。")
    sys.exit("AI 核心載入失敗，程式退出。")

# 初始化 Chrome WebDriver
driver = None
try:
    options = Options()
    options.add_argument("--start-maximized")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    print("✅ Selenium WebDriver 啟動成功。")
except Exception as e:
    print(f"❌ 嚴重錯誤：無法啟動 Selenium WebDriver。")
    print("請檢查您的 chromedriver.exe 是否存在，且版本是否與您的 Chrome 瀏覽器匹配。")
    print(f"錯誤訊息: {e}")
    sys.exit("WebDriver 啟動失敗，程式退出。")

# --- 搶票函式 ---
def perform_purchase(target_seat_area: str, quantity: int, k_value: int):
    """
    執行自動化搶票流程。
    Args:
        target_seat_area (str): 目標座位區的文字，例如 "A1區".
        quantity (int): 欲購買的票數。
        k_value (int): 驗證碼辨識的 k 值。
    """
    print(f"\n--- 開始執行搶票流程 ---")

    try:
        # 由於頁面已由主流程開啟，這裡不再需要 driver.get()

        # 嘗試處理 Cookie 彈窗 (這可能在主流程中已經處理過，但再次檢查是安全的)
        try:
            WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div/div/input"))
            ).click()
            WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div/button"))
            ).click()
            print("...Cookie 彈窗已處理...")
        except:
            # print("...未發現 Cookie 彈窗，繼續...") # 在此階段，彈窗可能不存在，無需提示
            pass

        # --- 以下是根據您 7 張圖片重建的流程 ---
        
        # 圖片 1: 點擊 "立即購票" (id="purchaseButton")
        print("...[1/7] 等待並點擊 '立即購票'...")
        WebDriverWait(driver, 15).until( # 增加等待時間
            EC.element_to_be_clickable((By.ID, "purchaseButton"))
        ).click()

        # 圖片 2: 點擊 "立即訂購" (class="purchase-button")
        print("...[2/7] 等待並點擊 '立即訂購'...")
        WebDriverWait(driver, 15).until( # 增加等待時間
            EC.element_to_be_clickable((By.CLASS_NAME, "purchase-button"))
        ).click()

        # 圖片 3: 點擊目標座位區 (使用 target_seat_area)
        print(f"...[3/7] 等待並點擊座位區 '{target_seat_area}'...")
        seat_xpath = f"//div[@class='seat-item' and contains(., '{target_seat_area}')]"
        WebDriverWait(driver, 15).until( # 增加等待時間
            EC.element_to_be_clickable((By.XPATH, seat_xpath))
        ).click()

        # 圖片 4: 選擇票數 (使用 quantity)
        print(f"...[4/7] 等待並選擇票數 '{quantity}'...")
        quantity_select_el = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "quantity"))
        )
        Select(quantity_select_el).select_by_visible_text(str(quantity))

        # 圖片 5: 勾選 "同意條款" (id="terms-checkbox")
        print("...[5/7] 等待並勾選 '同意條款'...")
        terms_checkbox = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "terms-checkbox"))
        )
        driver.execute_script("arguments[0].click();", terms_checkbox) # 使用 JavaScript 點擊，可避免元素被遮擋導致點擊失敗
        print("...已勾選 '同意條款'...")

        # -----------------------------------------------------
        # 【步驟 6: 破解驗證碼】
        # -----------------------------------------------------
        print("...[6/7] 正在處理驗證碼...")
        captcha_image_bytes = None
        try:
            captcha_element = WebDriverWait(driver, 20).until( # 增加等待時間
                 EC.presence_of_element_located((By.ID, "captcha-image"))
            )
            image_url = captcha_element.get_attribute("src")
            
            http_session = requests.Session()
            all_cookies = driver.get_cookies()
            for cookie in all_cookies:
                http_session.cookies.set(cookie['name'], cookie['value'])
                
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
            captcha_answer = ai_core.crack_captcha(image_bytes=captcha_image_bytes, k_value=k_value)
            
            if "FAIL" not in captcha_answer and "EMPTY" not in captcha_answer and "MODEL" not in captcha_answer:
                print(f"🤖 AI 辨識結果: {captcha_answer}")
                driver.find_element(By.ID, "captcha-input").send_keys(captcha_answer)
                print("✅ 驗證碼已填入。")
                
                # 圖片 7: 點擊 "確認張數" (class="btn confirm-btn")
                print("...[7/7] 點擊 '確認張數' 送出...")
                WebDriverWait(driver, 15).until( # 增加等待時間
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.confirm-btn"))
                ).click()
                print("✅ 已點擊 '確認張數'。流程結束。")
                
            else:
                print(f"❌ AI 辨識失敗，結果: {captcha_answer}")
        else:
            print("❌ 未能取得驗證碼圖片或 AI 核心載入失敗，無法繼續。")

    except Exception as e:
        print(f"\n❌ 搶票流程執行時發生未預期的錯誤: {e}")
        print("--- 流程已中斷 ---")
    finally:
        pass
        # driver.quit() # 搶票成功後，您可以取消註解此行來自動關閉瀏覽器

def initial_setup():
    """
    執行搶票前的初始設定流程，包括開啟網頁、處理彈窗、設定倒數等。
    """
    print("--- 開始執行初始設定流程 ---")
    
    # 開啟目標網站
    print(f"開啟目標網站: {config.PURCHASE_URL}")
    driver.get(config.PURCHASE_URL)

    # 1. 處理彈窗 (Modal Handling)
    try:
        print("嘗試處理彈窗...")
        # 點擊 "我已閱讀並了解" 勾選框
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "confirmRead"))
        ).click()
        # 點擊 "確認" 按鈕
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "closeModal"))
        ).click()
        print("彈窗已關閉。")
        time.sleep(0.5) # 等待動畫

    except Exception as e:
        # 彈窗可能已經被 sessionStorage 關閉，或未出現
        print("彈窗元素未找到，假定已處理或未出現。")

    # 2. 開始倒數計時 (Start Countdown)
    try:
        countdown_seconds = "3" # 您要模擬的倒數秒數
        
        # 在輸入框中輸入秒數 (使用 ID)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "countdownInput"))
        ).send_keys(countdown_seconds)

        # 按下開始倒數計時按鈕 (使用 ID)
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "startButton"))
        ).click()
        print(f"已開始倒數計時：{countdown_seconds} 秒。")

        # 等待計時結束 (3秒倒數 + 0.2秒緩衝)
        wait_time = int(countdown_seconds) + 0.2
        time.sleep(wait_time)
        print("倒數結束，準備進入購票階段。")

    except Exception as e:
        print(f"❌ 啟動倒數時發生錯誤: {e}")
        driver.quit()
        sys.exit(1) # 遇到錯誤退出

    print("--- 初始設定流程結束 ---")

# --- 程式主要進入點 ---
if __name__ == '__main__':
    try:
        # 步驟 1: 監控票券
        # 呼叫監票函式，直到有票為止
        print("--- 啟動監票程序 ---")
        tickets_found = ticket_monitor.monitor_for_tickets(
            monitor_url=config.MONITOR_URL,
            target_areas=config.TARGET_AREAS,
            check_interval_seconds=config.CHECK_INTERVAL_SECONDS
        )

        # 步驟 2: 如果有票，則執行搶票
        if tickets_found:
            print("\n✅ 監控到有票，開始執行搶票流程！")
            # 執行初始設定 (開啟搶票頁面、處理彈窗、倒數等)
            initial_setup()
            
            # 執行搶票流程
            perform_purchase(
                target_seat_area=config.TARGET_SEAT_AREA, # 改為使用目標區域名稱
                quantity=config.QUANTITY,
                k_value=config.K_VALUE
            )
        else:
            # 理論上 monitor_for_tickets 會一直執行直到有票，所以不太會跑到這裡
            print("\n監控結束，未發現目標票券。")

    except Exception as e:
        print(f"❌ 執行 ticketBot.py 時發生嚴重錯誤: {e}")
    finally:
        # 可以在此處加入一個 input() 來防止瀏覽器自動關閉，方便觀察結果
        input("按 Enter 鍵結束程式...")
        # 確保 driver 物件存在才執行 quit
        if 'driver' in locals() and driver:
            driver.quit()