# -*- coding: utf-8 -*-
"""测试脚本 v2：验证侧边栏滚动 + Daily Set 选择器"""
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

REPO_DIR = Path(__file__).resolve().parent.parent
_config = json.loads((REPO_DIR / "config.json").read_text(encoding="utf-8"))
USER_DATA = _config.get("edge_user_data_path", "")

print("=" * 50)
print("Bing Rewards 侧边栏测试 v2")
print("=" * 50)

opts = Options()
opts.add_argument(f"user-data-dir={USER_DATA}_Bot_Profile")
opts.add_argument("profile-directory=Default")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--remote-debugging-port=9223")

print("\n[1] 启动 Edge...")
driver = webdriver.Edge(options=opts)
driver.set_page_load_timeout(30)

try:
    print("\n[2] 打开 Bing 搜索...")
    driver.get("https://www.bing.com/search?q=test")
    time.sleep(5)

    print("\n[3] 点击金牌图标...")
    medal = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-rewards-widget] .b_clickarea"))
    )
    medal.click()
    time.sleep(4)

    print("\n[4] 分析侧边栏结构...")
    flyout = driver.find_element(By.ID, "rewid-f")

    # 打印 flyout 的 innerHTML 前 3000 字符
    html = flyout.get_attribute("innerHTML")
    print(f"    flyout HTML 长度: {len(html)} 字符")
    print(f"    前 2000 字符:\n{html[:2000]}")

    # 尝试滚动 flyout 内部
    print("\n[5] 尝试在 flyout 内部滚动...")
    # 找到 flyout 内可滚动的容器
    scroll_containers = flyout.find_elements(By.CSS_SELECTOR, "*")
    scrollable = None
    for el in scroll_containers:
        overflow = driver.execute_script(
            "var s = window.getComputedStyle(arguments[0]); return s.overflowY;", el
        )
        if overflow in ("auto", "scroll"):
            scrollable = el
            tag = el.tag_name
            cls = el.get_attribute("class") or ""
            print(f"    找到可滚动元素: <{tag}> class='{cls[:60]}'")
            break

    if scrollable:
        # 向下滚动
        for i in range(5):
            driver.execute_script("arguments[0].scrollTop += 300;", scrollable)
            time.sleep(0.5)
        time.sleep(2)
        print("    滚动完成")

        # 截图
        driver.save_screenshot(str(REPO_DIR / "test_scrolled.png"))
        print("    滚动后截图已保存")

        # 重新分析滚动后的 HTML
        html2 = flyout.get_attribute("innerHTML")
        print(f"\n    滚动后 HTML 长度: {len(html2)} 字符")

        # 搜索 daily 相关内容
        import re
        daily_matches = re.findall(r'(?i)(daily[^"<]{0,100})', html2)
        print(f"    包含 'daily' 的文本片段:")
        for m in daily_matches[:10]:
            print(f"      - {m}")

        # 搜索所有 a 标签
        links = flyout.find_elements(By.TAG_NAME, "a")
        print(f"\n    flyout 内 <a> 标签数量: {len(links)}")
        for idx, link in enumerate(links[:15]):
            text = link.text[:50] if link.text else "(空)"
            href = link.get_attribute("href") or ""
            vis = link.is_displayed()
            print(f"      [{idx}] vis={vis} text='{text}' href={href[:80]}")

        # 搜索所有可点击元素
        clickables = flyout.find_elements(By.CSS_SELECTOR, "[onclick], [role='button'], button, [tabindex]")
        print(f"\n    可点击元素数量: {len(clickables)}")
        for idx, el in enumerate(clickables[:15]):
            text = el.text[:50] if el.text else "(空)"
            tag = el.tag_name
            cls = el.get_attribute("class") or ""
            print(f"      [{idx}] <{tag}> class='{cls[:50]}' text='{text}'")

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

except Exception as e:
    print(f"\n[错误] {e}")
    import traceback
    traceback.print_exc()
    driver.save_screenshot(str(REPO_DIR / "test_error.png"))

finally:
    print("\n10 秒后关闭...")
    time.sleep(10)
    driver.quit()
