import time
import random
import string
import os
import json
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= 配置加载 =================

REPO_DIR = Path(__file__).resolve().parent.parent
_cfg_path = REPO_DIR / "config.json"
_config = json.loads(_cfg_path.read_text(encoding="utf-8")) if _cfg_path.exists() else {}

YOUR_USER_DATA_PATH = _config.get("edge_user_data_path", r"C:\Users\Default\AppData\Local\Microsoft\Edge\User Data")
SEARCH_COUNT = _config.get("search_count", 23)

# 基础词库
WORD_LIST = [
    "weather", "news", "map", "translate", "calculator", "calendar", "dictionary",
    "movies", "speed test", "flights", "hotels", "restaurants", "recipes",
    "sports", "finance", "tech", "science", "history", "art", "music",
    "travel", "education", "health", "fitness", "gaming", "coding",
    "python", "selenium", "automation", "microsoft", "rewards", "points",
    "bing", "google", "edge", "browser", "internet", "wifi", "network",
    "computer", "laptop", "phone", "tablet", "keyboard", "mouse", "screen",
    "camera", "headphones", "speaker", "microphone", "battery", "charger",
    "cable", "usb", "bluetooth", "wireless", "cloud", "server", "database",
    "algorithm", "software", "hardware", "app", "website", "blog", "forum",
    "social", "media", "video", "audio", "image", "photo", "graphic",
    "design", "development", "project", "task", "job", "work", "office",
    "home", "family", "friend", "love", "life", "world", "nature",
    "animal", "plant", "food", "drink", "water", "coffee", "tea",
    "best", "top", "how to", "guide", "review", "tips", "tutorial"
]


# ===========================================

def generate_random_query():
    """生成由2-4个英文单词组成的随机短语"""
    num_words = random.randint(2, 4)
    selected_words = random.sample(WORD_LIST, num_words)
    return ' '.join(selected_words)


def highlight_element(driver, element):
    """给元素加上红框，方便肉眼调试"""
    try:
        driver.execute_script("arguments[0].style.border='3px solid red';", element)
        time.sleep(0.5)
    except:
        pass


def setup_driver():
    """初始化 Edge 驱动"""
    print("正在初始化浏览器...")
    edge_options = Options()

    # === 关键修改：使用独立的 Bot 专用配置文件夹 ===
    # 这样可以与主浏览器共存，互不干扰
    bot_profile_path = YOUR_USER_DATA_PATH + "_Bot_Profile"
    print(f"--> 使用独立配置文件路径: {bot_profile_path}")

    # 检查是否可能是第一次运行 (文件夹不存在)
    if not os.path.exists(bot_profile_path):
        print("\n" + "!" * 50)
        print("注意：检测到这是第一次运行独立模式！")
        print("请在脚本打开的浏览器窗口中，手动登录你的微软/Bing账号。")
        print("登录一次后，下次运行脚本会自动记住登录状态。")
        print("!" * 50 + "\n")

    edge_options.add_argument(f"user-data-dir={bot_profile_path}")
    edge_options.add_argument("profile-directory=Default")

    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option("useAutomationExtension", False)
    edge_options.add_argument("--remote-debugging-port=9223")

    current_folder = os.path.dirname(os.path.abspath(__file__))
    local_driver_path = os.path.join(current_folder, "msedgedriver.exe")

    service = None

    if os.path.exists(local_driver_path):
        print(f"--> 使用本地驱动: {local_driver_path}")
        service = Service(executable_path=local_driver_path)
        driver = webdriver.Edge(service=service, options=edge_options)
    else:
        print("--> 未发现本地驱动，尝试 Selenium 自动管理...")
        try:
            driver = webdriver.Edge(options=edge_options)
        except Exception as e:
            print("\n!!! 启动失败，请检查是否需要手动下载 msedgedriver.exe !!!")
            raise e

    driver.set_page_load_timeout(30)
    return driver


def perform_daily_searches(driver):
    """模块1: 执行每日搜索任务"""
    print("\n" + "=" * 30)
    print(">>> 阶段 1: 开始执行每日搜索")
    print("=" * 30)

    try:
        driver.get("https://www.bing.com")
    except Exception as e:
        print("访问 Bing 首页超时或失败，尝试刷新...")
        driver.refresh()

    time.sleep(3)

    for i in range(SEARCH_COUNT):
        try:
            query = generate_random_query()

            try:
                search_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
            except:
                try:
                    search_box = driver.find_element(By.ID, "sb_form_q")
                except:
                    search_box = driver.find_element(By.XPATH, "//textarea[@name='q'] | //input[@name='q']")

            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)

            print(f"[{i + 1}/{SEARCH_COUNT}] 搜索: {query}")

            # 随机等待 8 到 15 秒
            sleep_time = random.uniform(8, 15)
            time.sleep(sleep_time)

            if (i + 1) % 5 == 0:
                print("  -> 休息一会儿...")
                time.sleep(random.uniform(5, 10))

        except Exception as e:
            print(f"搜索出错 (第 {i + 1} 次): {e}")
            try:
                driver.get("https://www.bing.com")
                time.sleep(5)
            except:
                pass

    print(">>> 搜索任务完成！")


def complete_daily_set(driver):
    """模块2: 执行每日任务 (Daily Set)"""
    print("\n" + "=" * 30)
    print(">>> 阶段 2: 开始执行每日任务 (Daily Set)")
    print("=" * 30)

    try:
        driver.get("https://rewards.bing.com/")
        time.sleep(5)

        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(2)

        print("正在定位 Daily Set 专属区域...")

        try:
            daily_set_container = driver.find_element(By.XPATH, "//div[@id='daily-sets']")
            print("--> 成功锁定 id='daily-sets' 区域！")
        except:
            print("--> 警告：未找到 id='daily-sets'，尝试备用容器...")
            try:
                daily_set_container = driver.find_element(By.XPATH, "//mee-rewards-daily-set-section-content")
            except:
                print("--> 错误：根本找不到 Daily Set 区域，停止运行以免误触。")
                return

        potential_cards = daily_set_container.find_elements(By.XPATH, ".//mee-card")
        valid_cards = [c for c in potential_cards if c.is_displayed()]

        card_count = len(valid_cards)
        print(f"--> 区域内发现 {card_count} 个任务卡片。")

        for i in range(min(card_count, 3)):
            try:
                print(f"\n>>> [任务 {i + 1}] 准备执行...")

                try:
                    container_now = driver.find_element(By.XPATH,
                                                        "//div[@id='daily-sets'] | //mee-rewards-daily-set-section-content")
                    cards_now = container_now.find_elements(By.XPATH, ".//mee-card")
                    cards_now = [c for c in cards_now if c.is_displayed()]
                except:
                    print("  定位丢失，跳过此任务")
                    continue

                if i >= len(cards_now):
                    break

                card_item = cards_now[i]
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", card_item)
                time.sleep(1.5)

                try:
                    target_link = card_item.find_element(By.TAG_NAME, "a")
                except:
                    target_link = card_item

                highlight_element(driver, target_link)

                # 强制在同一标签页打开，避免新窗口路由到其他 Edge 进程
                try:
                    driver.execute_script("arguments[0].target = '_self';", target_link)
                except:
                    pass

                click_success = False
                try:
                    ActionChains(driver).move_to_element(target_link).click().perform()
                    click_success = True
                    print("  -> 鼠标点击")
                except:
                    try:
                        driver.execute_script("arguments[0].click();", target_link)
                        click_success = True
                        print("  -> JS点击")
                    except Exception as e:
                        print(f"  -> 点击失败: {e}")

                if not click_success: continue

                # 同一标签页内浏览
                time.sleep(random.uniform(5, 8))
                driver.execute_script("window.scrollTo(0, 200);")
                time.sleep(random.uniform(2, 4))
                print("  [状态] 任务浏览完成，返回 rewards 页面")

                # 直接导航回 rewards 页面
                driver.get("https://rewards.bing.com/")
                time.sleep(3)

            except Exception as e:
                print(f"  [错误] 任务 {i + 1} 异常: {e}")
                try:
                    driver.get("https://rewards.bing.com/")
                    time.sleep(3)
                except:
                    pass

    except Exception as e:
        print(f"每日任务全局错误: {e}")


def main():
    # 移除了 kill_edge_processes()，现在可以和你的主浏览器共存了

    driver = None
    try:
        driver = setup_driver()

        perform_daily_searches(driver)
        complete_daily_set(driver)

    except Exception as e:
        print(f"脚本运行出错: {e}")
    finally:
        if driver:
            print("\n所有自动化任务完成，10秒后退出...")
            time.sleep(10)
            try:
                # 只关闭脚本打开的那个窗口，不会影响你的其他窗口
                driver.quit()
            except:
                pass


if __name__ == "__main__":
    main()