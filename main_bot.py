import sys
import time
import config
import ticket_monitor
from ticketBot import initial_setup, perform_purchase, driver # 從 ticketBot 匯入函式和 driver 物件

def main():
    print("--- 啟動監票與搶票機器人 ---")

    # 1. 執行監票模組
    print("\n--- 進入監票階段 ---")
    # 為了測試，暫時跳過監票，直接進入搶票
    # tickets_found = ticket_monitor.monitor_for_tickets(
    #     config.MONITOR_URL,
    #     config.TARGET_AREAS,
    #     config.CHECK_INTERVAL_SECONDS
    # )
    tickets_found = True # 直接假設找到票

    if tickets_found:
        print("\n--- 監票階段完成：已發現目標票券！ ---")
        print("\n--- 進入搶票階段 ---")
        try:
            # 2. 執行初始設定
            initial_setup()

            # 3. 執行搶票流程
            perform_purchase(
                config.SEAT_SELECTOR,
                config.QUANTITY,
                config.K_VALUE
            )
            print("\n--- 搶票流程執行完畢 ---")
        except Exception as e:
            print(f"\n❌ 搶票流程啟動失敗或執行中斷: {e}")
    else:
        print("\n--- 監票階段完成：未發現目標票券。 ---")
        print("機器人將結束運行。")

    # 無論搶票是否成功，最後都關閉瀏覽器
    if driver:
        print("\n--- 關閉瀏覽器 ---")
        driver.quit()
    
    print("\n--- 機器人運行結束 ---")

if __name__ == '__main__':
    main()
