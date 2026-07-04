# -*- coding: utf-8 -*-
"""测试脚本 v4：实际点击 Daily Set 任务"""
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
print("Bing Rewards Daily Set 点击测试")
print("=" * 50)

opts = Options()
opts.add_argument(f"user-data-dir={USER_DATA}_Bot_Profile")
opts.add_argument("profile-directory=Default")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--remote-debugging-port=9223")

driver = webdriver.Edge(options=opts)
driver.set_page_load_timeout(30)

try:
    print("\n[1] 打开 Bing 搜索...")
    driver.get("https://www.bing.com/search?q=test")
    time.sleep(5)

    print("\n[2] 点击金牌图标...")
    medal = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-rewards-widget] .b_clickarea"))
    )
    medal.click()
    time.sleep(4)

    print("\n[3] 切换到 iframe...")
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#rewid-f iframe"))
    )
    driver.switch_to.frame(iframe)
    time.sleep(2)

    print("\n[4] 查找 Daily Set 任务链接...")
    # 找所有 a 标签
    links = driver.find_elements(By.TAG_NAME, "a")
    daily_links = []
    for link in links:
        text = link.text.strip() if link.text else ""
        href = link.get_attribute("href") or ""
        # Daily Set 任务的链接指向 bing.com/search，且包含中文
        if "bing.com/search" in href and text and len(text) > 5:
            daily_links.append(link)
            print(f"    找到: '{text[:50]}'")

    print(f"\n    共找到 {len(daily_links)} 个 Daily Set 任务")

    if daily_links:
        print(f"\n[5] 点击第一个任务: '{daily_links[0].text[:50]}'...")
        # 设置 target="_self" 避免新窗口
        driver.execute_script("arguments[0].target = '_self';", daily_links[0])
        daily_links[0].click()
        time.sleep(5)

        # 回到主页面查看是否跳转成功
        driver.switch_to.default_content()
        current_url = driver.current_url
        print(f"    点击后 URL: {current_url}")

        if "bing.com/search" in current_url:
            print("    [成功] 跳转到搜索页面!")
        else:
            print(f"    [意外] URL 不是搜索页: {current_url}")

        # 等几秒模拟浏览
        print("\n[6] 模拟浏览 5 秒...")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(2)

        print(f"\n[7] 完成! 当前 URL: {driver.current_url}")

    print("\n" + "=" * 50)
    print("点击测试完成!")
    print("=" * 50)

except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n10 秒后关闭...")
    time.sleep(10)
    driver.quit()
