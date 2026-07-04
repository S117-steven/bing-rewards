# -*- coding: utf-8 -*-
"""测试脚本 v3：处理 iframe 内的 Daily Set"""
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
print("Bing Rewards 侧边栏测试 v3 (iframe)")
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

    print("    已切换到 iframe")
    print(f"    iframe 内 URL: {driver.current_url}")

    # 分析 iframe 内容
    print("\n[4] 分析 iframe 内容...")
    html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
    print(f"    body HTML 长度: {len(html)} 字符")
    print(f"    前 3000 字符:\n{html[:3000]}")

    # 搜索 daily 相关
    import re
    daily_matches = re.findall(r'(?i)(daily[^"<]{0,150})', html)
    print(f"\n    包含 'daily' 的片段:")
    for m in daily_matches[:10]:
        print(f"      - {m[:100]}")

    # 找所有 a 标签
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"\n    <a> 标签数量: {len(links)}")
    for idx, link in enumerate(links[:20]):
        text = link.text[:60] if link.text else "(空)"
        href = link.get_attribute("href") or ""
        vis = link.is_displayed()
        print(f"      [{idx}] vis={vis} text='{text}' href={href[:80]}")

    # 尝试滚动
    print("\n[5] 滚动 iframe 内容...")
    body = driver.find_element(By.TAG_NAME, "body")
    for i in range(8):
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(0.3)
    time.sleep(2)

    # 截图
    driver.save_screenshot(str(REPO_DIR / "test_iframe_scrolled.png"))
    print("    滚动后截图已保存")

    # 重新找链接
    links2 = driver.find_elements(By.TAG_NAME, "a")
    print(f"\n    滚动后 <a> 标签数量: {len(links2)}")
    for idx, link in enumerate(links2[:20]):
        text = link.text[:60] if link.text else "(空)"
        href = link.get_attribute("href") or ""
        vis = link.is_displayed()
        print(f"      [{idx}] vis={vis} text='{text}' href={href[:80]}")

    # 搜索 DAILY SET 文本
    print("\n[6] 搜索 DAILY SET 文本...")
    all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Daily') or contains(text(), 'DAILY') or contains(text(), '每日')]")
    print(f"    找到 {len(all_elements)} 个包含关键词的元素")
    for el in all_elements:
        tag = el.tag_name
        text = el.text[:80] if el.text else "(空)"
        cls = el.get_attribute("class") or ""
        print(f"      <{tag}> class='{cls[:50]}' text='{text}'")

    # 回到主页面
    driver.switch_to.default_content()

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    try:
        driver.save_screenshot(str(REPO_DIR / "test_error.png"))
    except:
        pass

finally:
    print("\n10 秒后关闭...")
    time.sleep(10)
    driver.quit()
