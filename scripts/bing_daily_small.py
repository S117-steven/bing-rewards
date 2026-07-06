import time
import random
import string
import os
import json
import shutil
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
SOURCE_PROFILE_NAME = _config.get("edge_source_profile", "Profile 1")
SEARCH_COUNT = _config.get("search_count", 23)

# ===========================================

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


def ignore_cache_files(dir, files):
    """复制时忽略缓存文件，加快速度并减小体积"""
    return [f for f in files if f in ['Cache', 'Code Cache', 'GPUCache', 'Service Worker']]


def clone_profile():
    """将指定的 Edge 配置克隆到本地脚本目录"""
    current_folder = os.path.dirname(os.path.abspath(__file__))
    # 这是我们克隆出来的目标文件夹
    target_user_data_dir = os.path.join(current_folder, "Edge_Cloned_Profile")
    # 这里的 Default 对应的是 User Data 结构下的默认配置文件夹
    target_profile_dir = os.path.join(target_user_data_dir, "Default")

    # 原始配置的完整路径
    source_profile_path = os.path.join(YOUR_USER_DATA_PATH, SOURCE_PROFILE_NAME)

    # 检查是否已经克隆过
    if os.path.exists(target_profile_dir):
        print(f"--> 检测到已存在克隆配置: {target_user_data_dir}")
        print("--> 将直接使用该配置 (如需更新登录状态，请手动删除 Edge_Cloned_Profile 文件夹)")
        return target_user_data_dir

    print("\n" + "=" * 50)
    print(f"正在克隆配置 '{SOURCE_PROFILE_NAME}' ...")
    print("这可能需要几秒钟，请稍候。")
    print("注意：如果报错权限不足，请先暂时关闭所有 Edge 浏览器窗口。")
    print("=" * 50 + "\n")

    if not os.path.exists(source_profile_path):
        raise FileNotFoundError(f"找不到源配置路径: {source_profile_path}\n请检查 SOURCE_PROFILE_NAME 是否填写正确！")

    try:
        # 复制文件
        shutil.copytree(source_profile_path, target_profile_dir, ignore=ignore_cache_files)
        print("✅ 克隆成功！")
    except Exception as e:
        print(f"❌ 克隆失败: {e}")
        print("建议：请先关闭所有 Edge 浏览器窗口，然后删除 'Edge_Cloned_Profile' 文件夹重试。")
        raise e

    return target_user_data_dir


def generate_random_query():
    num_words = random.randint(2, 4)
    selected_words = random.sample(WORD_LIST, num_words)
    return ' '.join(selected_words)


def highlight_element(driver, element):
    try:
        driver.execute_script("arguments[0].style.border='3px solid red';", element)
        time.sleep(0.5)
    except:
        pass


def setup_driver():
    print("正在初始化浏览器 (克隆版)...")

    # 1. 执行克隆操作
    try:
        cloned_data_path = clone_profile()
    except Exception as e:
        print(f"无法继续：{e}")
        return None

    edge_options = Options()

    # 2. 指向克隆出来的文件夹
    edge_options.add_argument(f"user-data-dir={cloned_data_path}")
    # 注意：我们将源配置的内容复制到了新目录下的 "Default" 文件夹里
    # 所以这里必须固定写 "Default"，而不是原来的 Profile 1
    edge_options.add_argument("profile-directory=Default")

    # 基础配置
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option("useAutomationExtension", False)
    edge_options.add_argument("--remote-debugging-port=9222")

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
    print("\n" + "=" * 30)
    print(">>> [小号] 阶段 1: 开始每日搜索")
    print("=" * 30)

    try:
        driver.get("https://www.bing.com")
    except Exception as e:
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

            print(f"[小号 {i + 1}/{SEARCH_COUNT}] 搜索: {query}")

            time.sleep(random.uniform(8, 15))
            if (i + 1) % 5 == 0:
                print("  -> 休息一会儿...")
                time.sleep(random.uniform(5, 10))

        except Exception as e:
            print(f"搜索出错: {e}")
            try:
                driver.get("https://www.bing.com")
                time.sleep(5)
            except:
                pass
    print(">>> 小号搜索完成！")


def complete_daily_set(driver):
    """通过搜索页面的 rewards 侧边栏完成 Daily Set"""
    print("\n" + "=" * 30)
    print(">>> [小号] 阶段 2: 开始每日任务")
    print("=" * 30)

    def open_sidebar():
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
        cards = driver.find_elements(By.CSS_SELECTOR, ".dailycheckin_partnercard")
        for card in cards:
            text = card.text.strip() if card.text else ""
            if "每日集" in text or "Daily Set" in text.upper():
                links = card.find_elements(By.TAG_NAME, "a")
                visible_links = [l for l in links if l.is_displayed()]
                print(f"    [debug] 找到每日集卡片，内含 {len(visible_links)} 个链接")
                for i, l in enumerate(visible_links):
                    print(f"    [debug]   [{i}] href={l.get_attribute('href')[:60]} text='{l.text[:40]}'")
                return visible_links

        header = driver.find_elements(By.CSS_SELECTOR, "#DailySet, [id='DailySet']")
        if header:
            parent = driver.execute_script("""
                var el = arguments[0];
                for (var i = 0; i < 5; i++) {
                    el = el.parentElement;
                    if (el && el.querySelectorAll('.dailycheckin_partnercard').length > 0) return el;
                }
                return null;
            """, header[0])
            if parent:
                cards = parent.find_elements(By.CSS_SELECTOR, ".dailycheckin_partnercard")
                for card in cards:
                    text = card.text.strip() if card.text else ""
                    if "每日集" in text or "Daily Set" in text.upper():
                        links = card.find_elements(By.TAG_NAME, "a")
                        visible_links = [l for l in links if l.is_displayed()]
                        print(f"    [debug] 通过标题找到每日集卡片，内含 {len(visible_links)} 个链接")
                        return visible_links

        print("    [debug] 未找到每日集卡片")
        return []

    try:
        print("正在打开 Bing 搜索页...")
        driver.get("https://www.bing.com")
        time.sleep(3)

        completed = 0
        for task_num in range(3):
            try:
                print(f"\n>>> [小号任务 {task_num + 1}] 打开侧边栏...")
                open_sidebar()

                daily_links = find_daily_links()
                print(f"    找到 {len(daily_links)} 个 Daily Set 任务")

                if task_num >= len(daily_links):
                    print(f"    没有更多任务了，共完成 {completed} 个")
                    break

                title = daily_links[task_num].text.split('\n')[0]
                print(f"    点击: {title}")

                driver.execute_script("arguments[0].target = '_self';", daily_links[task_num])
                daily_links[task_num].click()
                time.sleep(6)

                driver.switch_to.default_content()
                print(f"    [状态] 跳转成功: {driver.current_url[:60]}...")

                driver.execute_script("window.scrollTo(0, 200);")
                time.sleep(random.uniform(3, 5))

                completed += 1
                print(f"    [状态] 任务 {task_num + 1} 完成")

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

        print(f"\n>>> [小号] Daily Set 完成: {completed} 个任务")

    except Exception as e:
        print(f"每日任务全局错误: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass


def main():
    driver = None
    try:
        driver = setup_driver()
        if driver:
            perform_daily_searches(driver)
            complete_daily_set(driver)
    except Exception as e:
        print(f"脚本出错: {e}")
    finally:
        if driver:
            print("\n小号任务完成，10秒后退出...")
            time.sleep(10)
            try:
                driver.quit()
            except:
                pass


if __name__ == "__main__":
    main()