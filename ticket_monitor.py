import requests
import random
import time
from bs4 import BeautifulSoup
import config # 匯入我們自己的 config 檔案

# --- 輔助函式：發送 HTTP 請求 ---
def _request_page(url: str, headers: dict = {}) -> BeautifulSoup:
    """
    發送 GET 請求並回傳 BeautifulSoup 物件。
    若請求失敗會自動重試。
    """
    while True:
        try:
            # 這裡不使用 cookies，因為監票階段不需要登入狀態
            response_text = requests.get(url, headers=headers).text
            return BeautifulSoup(response_text, "html.parser")
        except Exception as e:
            delay = random.randint(2, 5)
            print(f"❌ 請求 {url} 失敗，將在 {delay} 秒後重試。錯誤: {e}")
            time.sleep(delay)

# --- 輔助函式：解析票區資訊 ---
def _parse_zone_info(soup: BeautifulSoup) -> dict:
    """
    從 BeautifulSoup 物件中解析票區資訊。
    回傳字典格式: { "票區名稱": "狀態文字" }
    """
    # 尋找所有代表票區的 <a> 標籤
    # 這些標籤通常有 id 屬性，且 id 格式為 "活動ID_區域ID"
    ticket_area_links = soup.find_all("a", id=lambda x: x and "_" in x)
    
    parsed_zones = {}
    for link in ticket_area_links:
        full_text = link.get_text(strip=True) # 獲取所有文字內容，例如 "1F 站位區 熱賣中"
        
        # 改為尋找 <span class="status">
        status_span = link.find("span", class_="status")
        status_text = status_span.get_text(strip=True) if status_span else ""
        
        # 將票區名稱和狀態分開
        area_name = full_text.replace(status_text, "").strip() if status_text else full_text

        if area_name:
            parsed_zones[area_name] = status_text
    return parsed_zones

# --- 主要監票函式 ---
def monitor_for_tickets(monitor_url: str, target_areas: list, check_interval_seconds: int) -> bool:
    """
    持續監控指定網址的票券狀態，直到目標票區有票為止。
    有票時回傳 True，否則持續監控。
    """
    print(f"🚀 開始監控網址: {monitor_url}")
    print(f"🎯 目標票區: {', '.join(target_areas)}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Connection': 'keep-alive',
    }

    while True:
        print(f"\n--- 正在檢查票券狀態 ({time.strftime('%H:%M:%S')}) ---")
        soup = _request_page(monitor_url, headers=headers)
        zone_info = _parse_zone_info(soup)

        if not zone_info:
            print("⚠️ 未能解析到票區資訊，請檢查網址或網頁結構是否改變。")
            print(f"將在 {check_interval_seconds} 秒後重試。")
            time.sleep(check_interval_seconds)
            continue

        found_ticket = False
        # 新的檢查邏輯：迭代解析出的票區和狀態
        for area_name, status in zone_info.items():
            # 檢查此票區是否為我們的目標之一
            for target_area in target_areas:
                if target_area in area_name:
                    print(f"🔍 找到目標票區 '{area_name}'，狀態為 '{status}'。")
                    # 檢查狀態是否不是「已售完」或類似的無票狀態
                    if status and "已售完" not in status and "Sold Out" not in status:
                        print(f"🎉🎉🎉 恭喜！目標票區 '{area_name}' 有票了！狀態: '{status}' 🎉🎉🎉")
                        found_ticket = True
                        break
            if found_ticket:
                break
        
        if found_ticket:
            return True # 有票了，回傳 True 結束監控

        print(f"😴 暫無目標票區有票，將在 {check_interval_seconds} 秒後再次檢查。")
        time.sleep(check_interval_seconds)

# --- 獨立測試區塊 ---
if __name__ == '__main__':
    # 這裡使用 config.py 中的設定進行測試
    # 請確保 config.py 中的 MONITOR_URL 和 TARGET_AREAS 已正確設定
    print("--- 正在獨立測試 ticket_monitor.py 模組 ---")
    
    # 為了測試，可以暫時修改 config 中的設定
    # config.MONITOR_URL = "https://ticket-training.onrender.com/lesson/1"
    # config.TARGET_AREAS = ["B2層特A1區"]
    # config.CHECK_INTERVAL_SECONDS = 5

    if monitor_for_tickets(config.MONITOR_URL, config.TARGET_AREAS, config.CHECK_INTERVAL_SECONDS):
        print("\n監控結束，已發現目標票券！")
    else:
        print("\n監控結束，未發現目標票券 (此訊息通常不會出現，除非監控被中斷)。")
