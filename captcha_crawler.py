from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import requests
import time

# 瀏覽器設定
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 無頭模式
driver = webdriver.Chrome(options=options)

# 目標網址
url = "https://ticket-training.onrender.com/checking?seat=B2%E5%B1%A4%E7%89%B9A1%E5%8D%80&price=6880&color=%2305134b"
driver.get(url)

# 設定下載資料夾
download_folder = "captcha_raw"
os.makedirs(download_folder, exist_ok=True)

# 最大允許連續重複次數
MAX_REPEAT = 5
repeat_count = 0

while True:
    try:
        # 找到圖片元素
        img_element = driver.find_element(By.ID, "captcha-image")
        img_url = img_element.get_attribute("src")

        # 拼接完整網址
        if img_url.startswith("/"):
            img_url = "https://ticket-training.onrender.com" + img_url

        # 取得檔名（保留網站上的檔名）
        filename = os.path.basename(img_url)
        filepath = os.path.join(download_folder, filename)

        if os.path.exists(filepath):
            repeat_count += 1
            print(f"[!] 發現重複檔案 {filename} (連續 {repeat_count} 次)")
            if repeat_count >= MAX_REPEAT:
                print(f"[X] 連續 {MAX_REPEAT} 次重複，程式終止。")
                break
        else:
            # 下載圖片
            response = requests.get(img_url)
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"[+] 已下載 {filename}")
            repeat_count = 0  # 重置連續計數

        # 模擬等待刷新（假設驗證碼會更新）
        time.sleep(2)
        driver.refresh()

    except Exception as e:
        print(f"錯誤: {e}")
        break

driver.quit()
