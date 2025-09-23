#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
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
# 如果要儲存在特定資料夾可改成 "path/to/dir"
OUTPUT_DIR = "./captcha_raw"

def get_filename_from_url(url):
    """
    從 URL 擷取檔名（處理相對路徑與 query string）
    例如 /captcha/ciws.png -> ciws.png
    """
    parsed = urlparse(url)
    # parsed.path 會是 /captcha/ciws.png
    base = os.path.basename(parsed.path)
    if not base:
        raise ValueError(f"無法從 URL 擷取檔名: {url}")
    return base

def get_captcha():
    # 設定 Chrome（必要時可移除 headless 觀察行為）
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

        src = img.get_attribute("src")
        if not src:
            raise RuntimeError("找不到 img 的 src 屬性")

        absolute_url = urljoin(driver.current_url, src)

        # 取得檔名（保留網站上的檔名）
        filename = get_filename_from_url(absolute_url)
        out_path = os.path.join(OUTPUT_DIR, filename)

        # 將 Selenium 的 cookie 傳給 requests session
        session = requests.Session()
        for c in driver.get_cookies():
            # requests 的 cookie domain 不一定需要 'domain'，但保留以防
            cookie_kwargs = {'name': c.get('name'), 'value': c.get('value')}
            # 如果 domain 存在就加上
            if c.get('domain'):
                session.cookies.set(c['name'], c['value'], domain=c.get('domain'))
            else:
                session.cookies.set(c['name'], c['value'])

        # 下載圖片
        resp = session.get(absolute_url, timeout=20)
        resp.raise_for_status()

        with open(out_path, "wb") as f:
            f.write(resp.content)

        print(f"已下載並儲存: {out_path}")

    finally:
        driver.quit()

if __name__ == "__main__":
    get_captcha()
