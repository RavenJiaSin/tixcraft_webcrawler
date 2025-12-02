import os
import time
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 嘗試匯入 config，這樣才能知道網址
try:
    import config
except ImportError:
    config = None
    print("⚠️ [警告] 找不到 config.py，請確保檔案在同一目錄")

class TixCraftMonitor:
    def __init__(self):
        self.driver = None

    def start_driver(self):
        """啟動瀏覽器 """
        if self.driver is not None: return self.driver

        print("🔴 [系統] 啟動瀏覽器 (Undetected Mode)...")
        options = uc.ChromeOptions()
        
        # 使用者資料夾 (保留登入狀態)
        profile_path = os.path.join(os.getcwd(), "tix_profile")
        os.makedirs(profile_path, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_path}")

        # 關鍵參數
        options.add_argument('--no-first-run')
        options.add_argument('--password-store=basic')
        options.add_argument('--lang=zh-TW')
        options.add_argument("--window-size=1024,768") # 確保視窗夠大，避免RWD隱藏元件

        try:
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            
            # 允許下載
            params = {"behavior": "allow", "downloadPath": os.path.realpath(".")}
            self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
            
            print("🟢 [系統] 瀏覽器啟動成功！")
            return self.driver
        except Exception as e:
            print(f"❌ [致命錯誤] 啟動失敗: {e}")
            return None

    def navigate(self, url):
        if not self.driver: return
        print(f"🔵 [導航] 前往目標: {url}")
        try:
            self.driver.get(url)
            # 簡單處理彈窗
            self._close_popups()
        except Exception as e:
            print(f"❌ [導航失敗] {e}")

    def _close_popups(self):
        """暴力關閉所有可能的干擾視窗"""
        js_close = """
        try { document.getElementById('onetrust-accept-btn-handler').click(); } catch(e){}
        try { document.querySelector('.close-alert').click(); } catch(e){}
        try { document.querySelector('.btn-close').click(); } catch(e){}
        """
        try:
            self.driver.execute_script(js_close)
        except: pass

    def scan_for_tickets(self, target_keywords: list) -> str:
        """
        暴力掃描頁面上的所有可點擊元素，尋找票券，並將結果存檔 (CSV - 只存區域名稱與張數)
        """
        if not self.driver: return None

        # 雖然 CSV 不存時間，但螢幕顯示還是需要時間方便您看
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n🔍 [掃描] {time.strftime('%H:%M:%S')} | URL: {self.driver.current_url}")

        # 1. 檢查是否還在首頁 (略，保持原樣)
        if "ticket/area" not in self.driver.current_url:
            try:
                buy_btns = self.driver.find_elements(By.XPATH, "//*[contains(text(), '立即購票') or contains(text(), 'Buy Ticket')]")
                for btn in buy_btns:
                    if btn.is_displayed() and btn.is_enabled():
                        print("   -> ⚠️ 偵測到還在活動首頁，嘗試點擊「立即購票」...")
                        btn.click()
                        time.sleep(2)
                        return None
            except: pass

        # 2. 抓取所有可能的區域按鈕
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, ".zone .area-list a")
            if not buttons:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, "ul.area-list li a")
            
            print(f"   -> 找到 {len(buttons)} 個區域按鈕")

            if len(buttons) == 0:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text[:100].replace('\n', ' ')
                print(f"   -> ❌ 異常：找不到任何按鈕。頁面文字預覽: {body_text}...")
                return None
            
            # --- [CSV 寫入邏輯] ---
            log_file = "ticket_log.csv"
            file_exists = os.path.isfile(log_file)
            
            # 使用 with 開啟檔案
            with open(log_file, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # [修改 1] 標題欄只留兩項
                if not file_exists:
                    writer.writerow(["區域名稱", "剩餘張數"])
            
                # 3. 逐一檢查
                for btn in buttons:
                    text = btn.text.strip().replace("\n", " ")
                    if not text: continue 

                    # [解析文字] 拆分區域名稱與張數
                    area_name = text
                    ticket_count = "N/A" # 預設值

                    if "剩餘" in text:
                        try:
                            # 範例: "紅218區 剩餘 12" -> 切割
                            parts = text.split("剩餘")
                            area_name = parts[0].strip()
                            ticket_count = parts[1].strip()
                        except:
                            pass 
                    elif "售完" in text or "Sold out" in text:
                        ticket_count = "0"

                    # 狀態檢查 (僅用於判斷是否要搶票，不寫入 CSV)
                    class_attr = btn.get_attribute("class") or ""
                    is_disabled = "disabled" in class_attr or not btn.is_enabled()
                    status_msg = "🔴 鎖定" if is_disabled else "🟢 可買"
                    
                    if any(x in text for x in ["已售完", "選購一空", "Sold out", "暫停販售"]):
                        status_msg = "⚫ 售完"

                    # [修改 2] 只寫入兩個欄位
                    writer.writerow([area_name, ticket_count])

                    # 螢幕上還是顯示完整資訊比較好除錯
                    print(f"   -> [{area_name}] 剩餘: {ticket_count} | {status_msg}")

                    # 4. 判斷是否搶票
                    if "可買" in status_msg:
                        if target_keywords:
                            if not any(k in text for k in target_keywords):
                                continue
                        
                        print(f"🔥🔥🔥 [鎖定目標] 發現票券：{area_name}")
                        
                        # 成功紀錄維持詳細版 (建議保留時間)
                        with open("success_log.txt", "a", encoding="utf-8") as sf:
                            sf.write(f"[{current_time}] 觸發點擊: {area_name} ({ticket_count}張)\n")

                        try:
                            self.driver.execute_script("arguments[0].click();", btn)
                        except:
                            btn.click()
                        return text

        except Exception as e:
            print(f"❌ [掃描錯誤] {e}")
            import traceback
            traceback.print_exc()

        return None

    def close(self):
        if self.driver:
            self.driver.quit()

# ==========================================
# 自動化測試區塊
# ==========================================
if __name__ == "__main__":
    bot = TixCraftMonitor()
    
    # 1. 啟動瀏覽器
    driver = bot.start_driver()
    
    if driver:
        # 2. 嘗試從 config 讀取網址
        target_url = ""
        if config and hasattr(config, 'MONITOR_URL') and config.MONITOR_URL:
            target_url = config.MONITOR_URL
            print(f"📋 讀取到 Config 設定網址: {target_url}")
        else:
            # 如果沒 config，才叫人輸入
            target_url = input("請輸入拓元搶票網址: ")

        # 3. 自動導航
        bot.navigate(target_url)
        
        print("\n=================================================")
        print("⚠️  請確認瀏覽器是否已登入？(未登入可能看不到票)")
        print("👉 如果還沒，請現在手動登入，程式會每 3 秒掃描一次。")
        print("=================================================\n")

        # 4. 開始無限迴圈掃描
        while True:
            # 從 config 讀取關鍵字，沒有就全區
            keywords = config.TARGET_AREAS if (config and hasattr(config, 'TARGET_AREAS')) else []
            
            result = bot.scan_for_tickets(keywords)
            
            if result:
                print("✅ 測試結束：成功點擊票券！")
                break
            
            # 隨機等待，避免被太快鎖 IP
            time.sleep(2)