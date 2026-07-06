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
    """模块2: 通过搜索页面的 rewards 侧边栏完成 Daily Set"""
    print("\n" + "=" * 30)
    print(">>> 阶段 2: 开始执行每日任务 (Daily Set)")
    print("=" * 30)

    def open_sidebar():
        """点击金牌图标，切换到 iframe"""
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
        """在 iframe 中查找 Daily Set 任务链接"""
        links = driver.find_elements(By.TAG_NAME, "a")
        daily = []
        print(f"    [debug] iframe 内共 {len(links)} 个 <a> 标签")
        for idx, link in enumerate(links):
            href = link.get_attribute("href") or ""
            text = link.text.strip() if link.text else ""
            has_search = "bing.com/search" in href
            long_enough = len(text) > 5
            print(f"    [debug] [{idx}] href={href[:60]} text='{text[:40]}' search={has_search} len_ok={long_enough}")
            if has_search and text and long_enough:
                daily.append(link)
        print(f"    [debug] 匹配到 {len(daily)} 个 Daily Set 任务")
        return daily

    try:
        # 确保在搜索页面
        print("正在打开 Bing 搜索页...")
        driver.get("https://www.bing.com")
        time.sleep(3)

        completed = 0
        for task_num in range(3):
            try:
                print(f"\n>>> [任务 {task_num + 1}] 打开侧边栏...")
                open_sidebar()

                daily_links = find_daily_links()
                print(f"    找到 {len(daily_links)} 个 Daily Set 任务")

                if task_num >= len(daily_links):
                    print(f"    没有更多任务了，共完成 {completed} 个")
                    break

                title = daily_links[task_num].text.split('\n')[0]
                print(f"    点击: {title}")

                # 强制同一标签页打开
                driver.execute_script("arguments[0].target = '_self';", daily_links[task_num])
                daily_links[task_num].click()
                time.sleep(6)

                # 回到主页面
                driver.switch_to.default_content()
                print(f"    [状态] 跳转成功: {driver.current_url[:60]}...")

                # 浏览页面
                driver.execute_script("window.scrollTo(0, 200);")
                time.sleep(random.uniform(3, 5))

                completed += 1
                print(f"    [状态] 任务 {task_num + 1} 完成")

                # 返回搜索页准备下一个
                driver.get("https://www.bing.com")
                time.sleep(3)

            except Exception as e:
                print(f"    [错误] 任务 {task_num + 1} 异常: {e}")
                driver.switch_to.default_content()
                try:
                    driver.get("https://www.bing.com")
                    time.sleep(3)
                except:
                    pass

        print(f"\n>>> Daily Set 完成: {completed} 个任务")

    except Exception as e:
        print(f"每日任务全局错误: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass


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