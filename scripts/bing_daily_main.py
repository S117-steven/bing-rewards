import time
import random
import string
import os
import json
import re
import subprocess
from datetime import datetime
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
    # 不固定远程调试端口，避免重复运行或双号并发时复用旧 Edge 会话。

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
        """关闭旧侧边栏，点击金牌图标，切换到新 iframe"""
        # 先回到主页面
        try:
            driver.switch_to.default_content()
        except:
            pass
        # 用 JS 关闭 flyout
        try:
            driver.execute_script("""
                // 方法1：点击关闭按钮
                var closeBtn = document.querySelector('#rewid-f .close_rewards_panel, #rewid-f button[class*=close]');
                if (closeBtn) closeBtn.click();
                // 方法2：移除 flyout 内容
                var flyout = document.getElementById('rewid-f');
                if (flyout) {
                    var iframe = flyout.querySelector('iframe');
                    if (iframe) iframe.remove();
                    flyout.style.display = 'none';
                }
            """)
            time.sleep(1)
        except:
            pass
        # 如果还有遮挡，点击页面空白处关闭
        try:
            driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(0.5)
        except:
            pass

        medal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-rewards-widget] .b_clickarea"))
        )
        driver.execute_script("arguments[0].click();", medal)
        time.sleep(4)
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#rewid-f iframe"))
        )
        driver.switch_to.frame(iframe)
        time.sleep(2)

    def find_daily_links():
        """在 iframe 中查找 Daily Set 任务链接（兼容大号和小号两种结构）"""
        # 先滚动到每日设置区域
        try:
            driver.execute_script("var el = document.getElementById('DailySet'); if(el) el.scrollIntoView({block:'start'});")
            time.sleep(1)
        except:
            pass

        def is_task_link(link):
            """判断链接是否是可见的 Daily Set 搜索/购物任务链接"""
            try:
                href = (link.get_attribute("href") or "").lower()
                return link.is_displayed() and ("bing.com/search" in href or "bing.com/shop" in href)
            except:
                return False

        def extract_react_daily_set_tasks():
            """从新版 Rewards 的 React 数据中提取当天真正的 Daily Set 任务。"""
            try:
                source = driver.page_source
                # Rewards 页面把 RSC 数据放在 script 中，JSON 引号会被反斜杠转义。
                pattern = re.compile(
                    r'\\"date\\":\\"(?P<date>.*?)\\",\\"description\\":\\"(?P<description>.*?)'
                    r'\\",\\"destination\\":\\"(?P<destination>.*?)\\",\\"hash\\":.*?'
                    r'\\",\\"isCompleted\\":(?P<completed>true|false).*?'
                    r'\\",\\"offerId\\":\\"(?P<offer>Global_DailySet_[0-9]+_Child[0-9]+)\\",'
                    r'\\"points\\":(?P<points>[0-9]+),\\"title\\":\\"(?P<title>.*?)\\"'
                )
                matches = [m for m in pattern.finditer(source)
                           if m.group("date") == datetime.now().strftime("%m/%d/%Y")]
                if not matches:
                    return None

                def decode(value):
                    try:
                        return json.loads('"' + value + '"')
                    except Exception:
                        return value.replace(r"\u0026", "&").replace(r'\"', '"')

                tasks = []
                for match in matches:
                    if match.group("completed") == "true":
                        continue
                    href = decode(match.group("destination"))
                    title = decode(match.group("title"))
                    if href and title:
                        tasks.append({
                            "href": href,
                            "text": title,
                            "offer_id": match.group("offer"),
                        })

                print(f"    [debug] 新版 Rewards 数据找到 {len(tasks)} 个当天未完成 Daily Set 任务")
                # 返回 [] 也表示已成功解析当天数据，不能再回退到无关的 React 日常任务。
                return tasks
            except Exception as e:
                print(f"    [debug] 解析新版 Daily Set 数据失败: {e}")
                return None

        react_tasks = extract_react_daily_set_tasks()
        if react_tasks is not None:
            return react_tasks

        # 方法0：新版 Rewards React 面板中的「日常任务」卡片
        # 新版任务可能指向 Bing 首页活动（例如 Visual Search），不能只按 URL 判断。
        headers = driver.find_elements(By.TAG_NAME, "h2")
        for header in headers:
            header_text = " ".join((header.text or "").split())
            if header_text != "日常任务" and "daily" not in header_text.lower():
                continue
            panel = driver.execute_script("""
                var header = arguments[0];
                var disclosure = header.closest('.react-aria-Disclosure');
                return disclosure ? disclosure.querySelector('.react-aria-DisclosurePanel') : null;
            """, header)
            if not panel:
                continue

            task_links = []
            for link in panel.find_elements(By.TAG_NAME, "a"):
                try:
                    if not link.is_displayed():
                        continue
                    href = (link.get_attribute("href") or "").lower()
                    text = " ".join((link.text or "").split())
                except:
                    continue
                if not text or "已完成" in text or "completed" in text.lower():
                    continue
                if "referandearn" in href or "/refer/" in href:
                    continue
                task_links.append(link)

            if task_links:
                print(f"    [debug] 方法0: 新版日常任务面板找到 {len(task_links)} 个待完成任务")
                return task_links

        # 方法1：找 dailycheckin_partnercard 中的「每日集」卡片
        cards = driver.find_elements(By.CSS_SELECTOR, ".dailycheckin_partnercard")
        for card in cards:
            text = card.text.strip() if card.text else ""
            if "每日集" in text or "Daily Set" in text.upper():
                links = card.find_elements(By.TAG_NAME, "a")
                # 只保留指向搜索页的真正任务链接，排除导航链接
                task_links = []
                for l in links:
                    if is_task_link(l):
                        task_links.append(l)
                if task_links:
                    print(f"    [debug] 方法1: 找到每日集卡片，{len(task_links)} 个任务链接")
                    return task_links

        # 方法2：找 promo-title 元素，然后在其父容器中找链接。
        # 标题会随账号、语言和日期变化，不能依赖固定关键词。
        promo_titles = driver.find_elements(By.CSS_SELECTOR, ".promo-title, [class*='promo']")
        for pt in promo_titles:
            text = pt.text.strip() if pt.text else ""
            if text and len(text) > 3:
                parent = driver.execute_script("""
                    var el = arguments[0];
                    for (var i = 0; i < 5; i++) {
                        el = el.parentElement;
                        if (el && el.querySelectorAll('a').length > 0) return el;
                    }
                    return null;
                """, pt)
                if parent:
                    links = parent.find_elements(By.TAG_NAME, "a")
                    task_links = [l for l in links if is_task_link(l)]
                    if task_links:
                        print(f"    [debug] 方法2: 通过 promo-title 找到 {len(task_links)} 个任务链接")
                        return task_links

        # 方法3：全局搜索所有指向搜索页的链接
        all_links = driver.find_elements(By.TAG_NAME, "a")
        task_links = []
        for l in all_links:
            text = l.text.strip() if l.text else ""
            if is_task_link(l) and text and len(text) > 3:
                task_links.append(l)
        if task_links:
            print(f"    [debug] 方法3: 全局搜索找到 {len(task_links)} 个任务链接")
            return task_links

        print("    [debug] 未找到 Daily Set 任务")
        return []

    def click_react_daily_task(task):
        """在完整 Rewards dashboard 上点击新版任务卡片，触发官方完成追踪。"""
        driver.switch_to.default_content()
        driver.get("https://rewards.bing.com/dashboard")

        expected_href = (task.get("href") or "").replace("&amp;", "&").rstrip("/").lower()
        expected_title = " ".join((task.get("text") or "").split()).lower()

        def click_current_task(current_driver):
            return current_driver.execute_script("""
                var offerId = arguments[0].toLowerCase();
                var expectedHref = arguments[1].toLowerCase();
                var expectedTitle = arguments[2].toLowerCase();
                var normalize = function(value) {
                    return (value || '').replace(/&amp;/g, '&').replace(/\\/$/, '').toLowerCase();
                };
                var anchors = Array.from(document.querySelectorAll('a'));
                var taskAnchor = anchors.find(function(anchor) {
                    var href = normalize(anchor.href);
                    var text = (anchor.innerText || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                    var matches = href.indexOf(offerId) >= 0 ||
                        (expectedHref && href === expectedHref) ||
                        (expectedTitle && text.indexOf(expectedTitle) >= 0);
                    var completed = text.indexOf('已完成') >= 0 || text.indexOf('completed') >= 0;
                    var rect = anchor.getBoundingClientRect();
                    return matches && !completed && rect.width > 0 && rect.height > 0;
                });
                if (!taskAnchor) return false;
                taskAnchor.target = '_self';
                taskAnchor.scrollIntoView({block: 'center'});
                taskAnchor.click();
                return true;
            """, task["offer_id"], expected_href, expected_title)

        WebDriverWait(driver, 20).until(click_current_task)

    try:
        # 确保在搜索页面
        print("正在打开 Bing 搜索页...")
        driver.get("https://www.bing.com")
        time.sleep(3)

        completed = 0
        react_mode = False
        react_queue = []
        for task_num in range(3):
            try:
                if react_mode:
                    # 新版页面一次读取后连续处理，避免每项任务之间重复切换 Rewards iframe。
                    daily_links = react_queue
                    print(f"\n>>> [任务 {task_num + 1}] 继续处理新版 Daily Set 队列...")
                else:
                    print(f"\n>>> [任务 {task_num + 1}] 打开侧边栏...")
                    open_sidebar()
                    daily_links = find_daily_links()
                    if daily_links and isinstance(daily_links[0], dict):
                        react_mode = True
                        react_queue = daily_links
                print(f"    找到 {len(daily_links)} 个 Daily Set 任务")

                if not daily_links:
                    print(f"    没有更多任务了，共完成 {completed} 个")
                    break

                if isinstance(daily_links[0], dict):
                    # 新版页面完成一项后会把它从待办列表移除，因此取第一个剩余任务。
                    task = daily_links.pop(0)
                else:
                    if task_num >= len(daily_links):
                        print(f"    没有更多任务了，共完成 {completed} 个")
                        break
                    task = daily_links[task_num]

                title = task["text"] if isinstance(task, dict) else task.text.split('\n')[0]
                print(f"    点击: {title}")

                if isinstance(task, dict):
                    click_react_daily_task(task)
                else:
                    # 用当前标签页的 JS 点击绕过元素遮挡和 target=_blank
                    driver.execute_script("arguments[0].target='_self'; arguments[0].click();", task)
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
                if not isinstance(task, dict):
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
