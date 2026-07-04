# -*- coding: utf-8 -*-
"""测试脚本 v5：点击前两个 Daily Set 任务，完整流程"""
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

REPO_DIR = Path(__file__).resolve().parent.parent
_config = json.loads((REPO_DIR / "config.json").read_text(encoding="utf-8"))
USER_DATA = _config.get("edge_user_data_path", "")

print("=" * 50)
print("Daily Set 完整流程测试 (点击 2 个任务)")
print("=" * 50)

opts = Options()
opts.add_argument(f"user-data-dir={USER_DATA}_Bot_Profile")
opts.add_argument("profile-directory=Default")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--remote-debugging-port=9223")

driver = webdriver.Edge(options=opts)
driver.set_page_load_timeout(30)

def open_sidebar():
    """打开侧边栏并切换到 iframe，返回是否成功"""
    medal = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-rewards-widget] .b_clickarea"))
    )
    medal.click()
    time.sleep(4)
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#rewid-f iframe"))
    )
    driver.switch_to.frame(iframe)
    time.sleep(2)

def find_daily_links():
    """在 iframe 中查找 Daily Set 链接"""
    links = driver.find_elements(By.TAG_NAME, "a")
    daily = []
    for link in links:
        href = link.get_attribute("href") or ""
        text = link.text.strip() if link.text else ""
        if "bing.com/search" in href and text and len(text) > 5:
            daily.append(link)
    return daily

try:
    # === 任务 1 ===
    print("\n>>> [任务 1]")
    print("[1] 打开 Bing 搜索...")
    driver.get("https://www.bing.com/search?q=test1")
    time.sleep(5)

    print("[2] 打开侧边栏...")
    open_sidebar()

    print("[3] 查找 Daily Set...")
    daily_links = find_daily_links()
    print(f"    找到 {len(daily_links)} 个任务")
    if len(daily_links) >= 1:
        title1 = daily_links[0].text.split('\n')[0]
        print(f"[4] 点击: {title1}")
        driver.execute_script("arguments[0].target = '_self';", daily_links[0])
        daily_links[0].click()
        time.sleep(6)
        driver.switch_to.default_content()
        print(f"[5] 跳转成功! URL: {driver.current_url[:80]}")
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(3)
    else:
        print("    没找到任务，跳过")

    # === 任务 2 ===
    print("\n>>> [任务 2]")
    print("[1] 返回 Bing 搜索...")
    driver.get("https://www.bing.com/search?q=test2")
    time.sleep(5)

    print("[2] 打开侧边栏...")
    open_sidebar()

    print("[3] 查找 Daily Set...")
    daily_links = find_daily_links()
    print(f"    找到 {len(daily_links)} 个任务")
    if len(daily_links) >= 2:
        title2 = daily_links[1].text.split('\n')[0]
        print(f"[4] 点击: {title2}")
        driver.execute_script("arguments[0].target = '_self';", daily_links[1])
        daily_links[1].click()
        time.sleep(6)
        driver.switch_to.default_content()
        print(f"[5] 跳转成功! URL: {driver.current_url[:80]}")
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(3)
    else:
        print(f"    只找到 {len(daily_links)} 个任务，不够")

    print("\n" + "=" * 50)
    print("两个任务测试完成!")
    print("=" * 50)

except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n10 秒后关闭...")
    time.sleep(10)
    driver.quit()
