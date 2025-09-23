#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from urllib.parse import urljoin, urlparse

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://ticket-training.onrender.com/checking?seat=B2%E5%B1%A4%E7%89%B9A1%E5%8D%80&price=6880&color=%2305134b"
OUTPUT_DIR = "./captcha_raw"

WAIT_NEW_CAPTCHA_TIMEOUT = 15
LOOP_PAUSE_SECONDS = 0.5
MAX_REPEAT = 5   # 允許重複檔名的最大次數

def ensure_output_dir():
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_filename_from_url(url):
    parsed = urlparse(url)
    base = os.path.basename(parsed.path)
    if not base:
        raise ValueError(f"無法從 URL 擷取檔名: {url}")
    return base

def download_image_with_cookies(session, url, out_path):
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)

def build_requests_session_from_selenium(driver):
    session = requests.Session()
    for c in driver.get_cookies():
        if c.get('domain'):
            session.cookies.set(c['name'], c['value'], domain=c.get('domain'))
        else:
            session.cookies.set(c['name'], c['value'])
    return session

def main():
    ensure_output_dir()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(TARGET_URL)

        wait = WebDriverWait(driver, 20)
        img = wait.until(EC.presence_of_element_located((By.ID, "captcha-image")))

        print("開始循環下載，按 Ctrl+C 可手動停止。")

        last_filename = None
        repeat_count = 0

        while True:
            img = wait.until(EC.presence_of_element_located((By.ID, "captcha-image")))
            src = img.get_attribute("src")
            if not src:
                print("找不到 img 的 src 屬性，跳過。")
                time.sleep(LOOP_PAUSE_SECONDS)
                continue

            absolute_url = urljoin(driver.current_url, src)
            filename = get_filename_from_url(absolute_url)
            out_path = os.path.join(OUTPUT_DIR, filename)

            # 判斷是否與上次檔名相同
            if filename == last_filename:
                repeat_count += 1
                print(f"警告：檔名 {filename} 與上次相同（已重複 {repeat_count} 次）")
                if repeat_count >= MAX_REPEAT:
                    print(f"檔名連續重複超過 {MAX_REPEAT} 次，終止程式。")
                    break
            else:
                repeat_count = 0
                last_filename = filename

            # 下載
            session = build_requests_session_from_selenium(driver)
            try:
                download_image_with_cookies(session, absolute_url, out_path)
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 已下載並覆蓋：{out_path}")
            except Exception as e:
                print(f"下載失敗：{e}")

            # 點擊刷新
            try:
                img.click()
            except Exception:
                driver.execute_script("arguments[0].click();", img)

            # 等待 src 改變
            try:
                WebDriverWait(driver, WAIT_NEW_CAPTCHA_TIMEOUT).until(
                    lambda d: d.find_element(By.ID, "captcha-image").get_attribute("src") != src
                )
            except Exception:
                print("等待新 captcha 超時，繼續下一輪。")

            time.sleep(LOOP_PAUSE_SECONDS)

    except KeyboardInterrupt:
        print("\n收到 Ctrl+C，中止程式。")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
