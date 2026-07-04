# -*- coding: utf-8 -*-
"""测试脚本：验证 Bing Rewards 侧边栏 Daily Set 选择器"""
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
PROFILE = _config.get("edge_source_profile", "Profile 1")

print("=" * 50)
print("Bing Rewards 侧边栏测试")
print("=" * 50)

# 启动浏览器
opts = Options()
opts.add_argument(f"user-data-dir={USER_DATA}_Bot_Profile")
opts.add_argument("profile-directory=Default")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--remote-debugging-port=9223")

print("\n[1] 启动 Edge 浏览器...")
driver = webdriver.Edge(options=opts)
driver.set_page_load_timeout(30)

try:
    # 步骤1：打开 Bing 搜索页
    print("\n[2] 打开 Bing 搜索页...")
    driver.get("https://www.bing.com/search?q=test")
    time.sleep(5)
    print(f"    当前页面: {driver.title}")

    # 步骤2：查找金牌图标
    print("\n[3] 查找 Microsoft Rewards 金牌图标...")
    selectors_to_try = [
        "div[data-rewards-widget] .b_clickarea",
        "div[data-rewards-widget]",
        "#id_rh_w",
        ".medallion",
        "[class*='medal']",
    ]

    medal = None
    for sel in selectors_to_try:
        try:
            medal = driver.find_element(By.CSS_SELECTOR, sel)
            print(f"    找到! 选择器: {sel}")
            print(f"    元素标签: {medal.tag_name}, class: {medal.get_attribute('class')}")
            break
        except:
            continue

    if not medal:
        print("    未找到金牌图标! 保存页面截图...")
        driver.save_screenshot(str(REPO_DIR / "test_no_medal.png"))
        print("    截图已保存到 test_no_medal.png")
        # 打印页面上所有 data-rewards-widget 相关元素
        widgets = driver.find_elements(By.CSS_SELECTOR, "[data-rewards-widget]")
        print(f"    找到 {len(widgets)} 个 rewards-widget 元素")
        for w in widgets:
            print(f"      - {w.tag_name} class={w.get_attribute('class')}")

    # 步骤3：点击金牌图标
    if medal:
        print("\n[4] 点击金牌图标...")
        medal.click()
        time.sleep(4)

        # 步骤4：检查侧边栏是否打开
        print("\n[5] 检查侧边栏...")
        flyout_selectors = [
            "#rewid-f",
            "[class*='flyout']",
            "[class*='RewardsFlyout']",
            "[id*='rewid']",
            "[class*='sidebar']",
        ]

        flyout = None
        for sel in flyout_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                visible = [e for e in elements if e.is_displayed()]
                if visible:
                    flyout = visible[0]
                    print(f"    找到侧边栏! 选择器: {sel}")
                    print(f"    元素: {flyout.tag_name} id={flyout.get_attribute('id')}")
                    break
            except:
                continue

        if not flyout:
            print("    未找到可见侧边栏，尝试其他方式...")
            # 检查是否有 iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"    页面有 {len(iframes)} 个 iframe")
            for idx, iframe in enumerate(iframes):
                src = iframe.get_attribute("src") or ""
                print(f"      iframe[{idx}]: src={src[:100]}")

            # 检查所有打开的窗口
            print(f"    当前窗口数: {len(driver.window_handles)}")
            for h in driver.window_handles:
                driver.switch_to.window(h)
                print(f"      窗口: {driver.current_url[:80]}")

        # 步骤5：在侧边栏中查找 Daily Set
        if flyout:
            print("\n[6] 查找 DAILY SET 区域...")
            # 尝试在侧边栏中查找各种卡片
            card_selectors = [
                "a[href*='rewards']",
                "[class*='card'] a",
                "[class*='daily'] a",
                "a",
            ]

            for sel in card_selectors:
                try:
                    cards = flyout.find_elements(By.CSS_SELECTOR, sel)
                    cards = [c for c in cards if c.is_displayed()]
                    print(f"    选择器 '{sel}': 找到 {len(cards)} 个元素")
                    for idx, card in enumerate(cards[:5]):
                        text = card.text[:60] if card.text else "(空)"
                        href = card.get_attribute("href") or ""
                        print(f"      [{idx}] text='{text}' href={href[:80]}")
                except Exception as e:
                    print(f"    选择器 '{sel}': 错误 {e}")

            # 也尝试用 XPATH 查找包含特定文本的元素
            print("\n    尝试文本搜索...")
            try:
                daily_text = flyout.find_elements(By.XPATH, "//*[contains(text(), 'DAILY') or contains(text(), 'Daily')]")
                print(f"    找到 {len(daily_text)} 个包含 'Daily' 的元素")
                for el in daily_text:
                    print(f"      - {el.tag_name}: '{el.text[:60]}'")
            except:
                pass

            # 截图
            driver.save_screenshot(str(REPO_DIR / "test_flyout.png"))
            print("\n    侧边栏截图已保存到 test_flyout.png")

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

except Exception as e:
    print(f"\n[错误] {e}")
    driver.save_screenshot(str(REPO_DIR / "test_error.png"))
    print("错误截图已保存到 test_error.png")

finally:
    print("\n10 秒后关闭浏览器...")
    time.sleep(10)
    driver.quit()
