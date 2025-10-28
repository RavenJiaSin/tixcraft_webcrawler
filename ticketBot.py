from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests
import time
import os

# 初始化 Chrome
options = Options()
options.add_argument("--start-maximized")
service = Service()  # 若系統有 chromedriver 於 PATH 可省略參數
driver = webdriver.Chrome(service=service, options=options)
waitTime = 0.5

# 開啟目標網站
driver.get("https://ticket-training.onrender.com/")

try:
    driver.find_element(By.XPATH, "/html/body/div[7]/div/div/input").click()
    driver.find_element(By.XPATH, "/html/body/div[7]/div/button").click()
except:
    True


# 在輸入框中輸入 3
driver.find_element(By.XPATH, "/html/body/div[6]/input").send_keys("3")

# 按下開啟到計時按鈕
driver.find_element(By.XPATH, "/html/body/div[6]/button").click()
time.sleep(3)

# 按下 /html/body/div[8]/div[1]/button[1]
driver.find_element(By.XPATH, "/html/body/div[8]/div[1]/button[1]").click()
time.sleep(waitTime)

# 按下 /html/body/div[8]/div[2]/table/tbody/tr/td[4]/a/button
driver.find_element(By.XPATH, "/html/body/div[8]/div[2]/table/tbody/tr/td[4]/a/button").click()
time.sleep(waitTime)

# 在 /html/body/div[3]/div[2]/form/input 輸入 BR123456789
driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/form/input").send_keys("BR123456789")
time.sleep(waitTime)

# 按下送出
driver.find_element(By.XPATH, "/html/body/div[3]/div[2]/form/p/button").click()
time.sleep(waitTime)

# 處理彈出視窗，按下「確定」
alert = Alert(driver)
alert.accept()
time.sleep(waitTime)

# 按下 /html/body/div[5]/div[3]/div[4]/div[1]/div[1]
driver.find_element(By.XPATH, "/html/body/div[5]/div[3]/div[4]/div[1]/div[1]").click()
time.sleep(waitTime)

# 選擇票數
Select(driver.find_element(By.XPATH, "/html/body/div[5]/form/table/tbody/tr/td[2]/select")).select_by_visible_text("1")
time.sleep(waitTime)

# 勾選同意書
driver.find_element(By.XPATH, "/html/body/div[5]/form/div[2]/input").click()
time.sleep(waitTime)

# 下載驗證碼圖片
save_path = "captcha.png"
try:
    response = requests.get(driver.find_element(By.ID, "captcha-image").get_attribute("src"))
    response.raise_for_status()  # 若下載失敗會丟出例外
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"✅ 驗證碼圖片已下載：{os.path.abspath(save_path)}")
except Exception as e:
    print("❌ 下載驗證碼圖片失敗:", e)

# 


# 保留瀏覽器視窗可觀察結果
# driver.quit()  # 若要結束可解除註解
