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

try:
    from run_result import emit_result, extract_react_daily_set_state
except ImportError:  # pragma: no cover - supports package-style test imports
    from scripts.run_result import emit_result, extract_react_daily_set_state

# ================= 配置加载 =================

REPO_DIR = Path(__file__).resolve().parent.parent
_cfg_path = REPO_DIR / "config.json"
_config = json.loads(_cfg_path.read_text(encoding="utf-8")) if _cfg_path.exists() else {}

YOUR_USER_DATA_PATH = _config.get("edge_user_data_path", r"C:\Users\Default\AppData\Local\Microsoft\Edge\User Data")
SEARCH_COUNT = _config.get("search_count", 23)
ACCOUNT_LABEL = "main"
DASHBOARD_URL = "https://rewards.bing.com/dashboard"
BOT_PROFILE_PATH = YOUR_USER_DATA_PATH + "_Bot_Profile"

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
    bot_profile_path = BOT_PROFILE_PATH
    print(f"[账号] {ACCOUNT_LABEL} | Edge 配置: {os.path.abspath(bot_profile_path)} | profile=Default")
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
    """模块1: 执行每日搜索任务，并返回可供管理器判断的统计结果。"""
    stats = {"requested": SEARCH_COUNT, "completed": 0, "failed": 0}
    print("\n" + "=" * 30)
    print(">>> 阶段 1: 开始执行每日搜索")
    print("=" * 30)

    try:
        driver.get("https://www.bing.com")
    except Exception as e:
        print("访问 Bing 首页超时或失败，尝试刷新...")
        try:
            driver.refresh()
        except Exception as refresh_error:
            stats["failed"] = SEARCH_COUNT
            print(f"搜索首页无法打开: {refresh_error}")
            return stats

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

            stats["completed"] += 1

        except Exception as e:
            print(f"搜索出错 (第 {i + 1} 次): {e}")
            stats["failed"] += 1
            try:
                driver.get("https://www.bing.com")
                time.sleep(5)
            except:
                pass

    print(
        f">>> 搜索阶段结束：成功 {stats['completed']}/{stats['requested']}，"
        f"失败 {stats['failed']}"
    )
    return stats


def complete_daily_set(driver):
    """完成 Daily Set，并在 Rewards 页面确认每项任务已记账。"""
    print("\n" + "=" * 30)
    print(">>> 阶段 2: 开始执行每日任务 (Daily Set)")
    print("=" * 30)

    stats = {
        "expected": 0,
        "detected": 0,
        "completed": 0,
        "pending": 0,
        "status": "not_started",
        "success": False,
    }
    discovery = {"source": None, "parsed": False, "total": 0, "pending": 0}

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
        discovery.update({"source": None, "parsed": False, "total": 0, "pending": 0})

        # Prefer the shared parser so the same state can be used after a click
        # to verify that Bing actually marked the offer as completed.
        try:
            react_state = extract_react_daily_set_state(driver.page_source)
        except Exception as e:
            print(f"    [debug] 解析新版 Daily Set 数据失败: {e}")
            react_state = None
        if react_state is not None:
            discovery.update({
                "source": "react",
                "parsed": True,
                "total": react_state["total"],
                "pending": react_state["pending"],
            })
            print(
                f"    [debug] 新版 Rewards 数据找到 {react_state['pending']} 个当天未完成 "
                f"Daily Set 任务（总数 {react_state['total']}）"
            )
            return react_state["pending_tasks"]

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
            discovery.update({
                "source": "react",
                "parsed": True,
                "total": len(react_tasks),
                "pending": len(react_tasks),
            })
            return react_tasks

        # 方法0：新版 Rewards React 面板中的「日常任务」卡片
        # 新版任务可能指向 Bing 首页活动（例如 Visual Search），不能只按 URL 判断。
        dom_container_seen = False
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
            dom_container_seen = True

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
                discovery.update({
                    "source": "dom",
                    "parsed": True,
                    "total": len(task_links),
                    "pending": len(task_links),
                })
                print(f"    [debug] 方法0: 新版日常任务面板找到 {len(task_links)} 个待完成任务")
                return task_links

        # 方法1：找 dailycheckin_partnercard 中的「每日集」卡片
        cards = driver.find_elements(By.CSS_SELECTOR, ".dailycheckin_partnercard")
        for card in cards:
            text = card.text.strip() if card.text else ""
            if "每日集" in text or "Daily Set" in text.upper():
                dom_container_seen = True
                links = card.find_elements(By.TAG_NAME, "a")
                # 只保留指向搜索页的真正任务链接，排除导航链接
                task_links = []
                for l in links:
                    if is_task_link(l):
                        task_links.append(l)
                if task_links:
                    discovery.update({
                        "source": "dom",
                        "parsed": True,
                        "total": len(task_links),
                        "pending": len(task_links),
                    })
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
                        discovery.update({
                            "source": "dom",
                            "parsed": True,
                            "total": len(task_links),
                            "pending": len(task_links),
                        })
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
            discovery.update({
                "source": "dom",
                "parsed": True,
                "total": len(task_links),
                "pending": len(task_links),
            })
            print(f"    [debug] 方法3: 全局搜索找到 {len(task_links)} 个任务链接")
            return task_links

        if dom_container_seen:
            discovery.update({"source": "dom", "parsed": True})
            print("    [debug] Daily Set 区域已找到，但当前没有待完成任务")
            return []

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

    def task_snapshot(task):
        if isinstance(task, dict):
            return dict(task)
        try:
            return {
                "href": task.get_attribute("href") or "",
                "text": " ".join((task.text or "").split()),
            }
        except Exception:
            return {"href": "", "text": ""}

    def tasks_match(left, right):
        """Compare a task before/after navigation without relying on WebElement identity."""
        left_offer = str(left.get("offer_id") or "").lower()
        right_offer = str(right.get("offer_id") or "").lower()
        if left_offer and right_offer and left_offer == right_offer:
            return True

        def normalize(value):
            return (value or "").replace("&amp;", "&").rstrip("/").strip().lower()

        left_href = normalize(left.get("href"))
        right_href = normalize(right.get("href"))
        if left_href and right_href and left_href == right_href:
            return True

        left_title = " ".join((left.get("text") or "").split()).lower()
        right_title = " ".join((right.get("text") or "").split()).lower()
        return bool(left_title and right_title and (left_title in right_title or right_title in left_title))

    def verify_react_task(task):
        """Reload the dashboard until the target offer is no longer pending."""
        deadline = time.time() + 30
        target_offer = str(task.get("offer_id") or "").lower()
        while time.time() < deadline:
            try:
                driver.switch_to.default_content()
                driver.get(DASHBOARD_URL)
                time.sleep(2)
                state = extract_react_daily_set_state(driver.page_source)
            except Exception as e:
                print(f"    [校验] 刷新 Rewards 状态失败: {e}")
                state = None

            if state is not None:
                matches = [
                    item for item in state["tasks"]
                    if str(item.get("offer_id") or "").lower() == target_offer
                ]
                if not matches or all(item.get("completed") for item in matches):
                    print("    [校验] Rewards 已确认该任务完成")
                    return True
                print("    [校验] 任务仍显示未完成，继续等待...")
            else:
                # Some Edge versions expose the React data only inside the
                # Rewards iframe.  Fall back to the pending-list comparison
                # instead of treating that page-source variant as success.
                try:
                    driver.get("https://www.bing.com")
                    time.sleep(3)
                    open_sidebar()
                    pending = find_daily_links()
                    if discovery.get("parsed"):
                        pending_snapshots = [task_snapshot(item) for item in pending]
                        if not any(tasks_match(task, item) for item in pending_snapshots):
                            print("    [校验] Rewards 待办列表已移除该任务")
                            return True
                except Exception as e:
                    print(f"    [校验] iframe 状态读取失败: {e}")

            time.sleep(2)
        return False

    def verify_dom_task(task):
        """Reload the legacy panel and confirm the clicked task left the pending list."""
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                driver.switch_to.default_content()
                driver.get("https://www.bing.com")
                time.sleep(3)
                open_sidebar()
                pending = find_daily_links()
            except Exception as e:
                print(f"    [校验] 刷新 Daily Set 状态失败: {e}")
                pending = None

            if pending is not None and discovery.get("parsed"):
                pending_snapshots = [task_snapshot(item) for item in pending]
                if not any(tasks_match(task, item) for item in pending_snapshots):
                    print("    [校验] Rewards 已确认该任务完成")
                    return True
                print("    [校验] 任务仍显示未完成，继续等待...")

            time.sleep(2)
        return False

    try:
        # 确保在搜索页面
        print("正在打开 Bing 搜索页...")
        driver.get("https://www.bing.com")
        time.sleep(3)

        completed = 0
        for task_num in range(3):
            print(f"\n>>> [任务 {task_num + 1}] 打开侧边栏...")
            driver.switch_to.default_content()
            driver.get("https://www.bing.com")
            time.sleep(3)
            open_sidebar()
            daily_links = find_daily_links()
            print(f"    找到 {len(daily_links)} 个 Daily Set 任务")

            stats["expected"] = max(stats["expected"], discovery.get("total", 0))
            stats["detected"] = max(stats["detected"], discovery.get("total", 0))

            if not daily_links:
                if discovery.get("parsed"):
                    print(f"    当前没有待完成任务，已验证完成 {completed} 个")
                    break
                stats.update({"status": "not_detected", "success": False})
                print("    [失败] 未能可靠读取 Daily Set 状态，不能判定为成功")
                return stats

            task = daily_links[0]
            snapshot = task_snapshot(task)
            title = snapshot.get("text") or "未命名任务"
            print(f"    点击: {title}")

            verified = False
            for attempt in range(1, 3):
                try:
                    if isinstance(task, dict):
                        click_react_daily_task(task)
                    else:
                        # 用当前标签页的 JS 点击绕过元素遮挡和 target=_blank
                        driver.execute_script(
                            "arguments[0].target='_self'; arguments[0].click();", task
                        )
                    time.sleep(6)

                    driver.switch_to.default_content()
                    print(f"    [状态] 跳转成功: {driver.current_url[:60]}...")
                    driver.execute_script("window.scrollTo(0, 200);")
                    time.sleep(random.uniform(3, 5))

                    if isinstance(task, dict):
                        verified = verify_react_task(snapshot)
                    else:
                        verified = verify_dom_task(snapshot)
                    if verified:
                        break
                    print(f"    [校验] 第 {attempt} 次未确认完成，准备重试...")
                except Exception as e:
                    print(f"    [错误] 任务 {task_num + 1} 第 {attempt} 次异常: {e}")
                    try:
                        driver.switch_to.default_content()
                        driver.get("https://www.bing.com")
                        time.sleep(3)
                    except Exception:
                        pass

            if not verified:
                stats.update({"status": "verification_failed", "success": False})
                print(f"    [失败] 任务“{title}”未通过 Rewards 完成校验")
                return stats

            completed += 1
            stats["completed"] = completed
            print(f"    [状态] 任务 {task_num + 1} 已确认完成")

        # 最后再读一次待办列表，防止固定处理三项后仍有任务未完成。
        driver.switch_to.default_content()
        driver.get("https://www.bing.com")
        time.sleep(3)
        open_sidebar()
        remaining = find_daily_links()
        if not discovery.get("parsed"):
            stats.update({"status": "not_detected", "success": False})
            print("[失败] 最终校验无法读取 Daily Set 状态")
            return stats
        stats["pending"] = len(remaining)
        stats["expected"] = max(stats["expected"], completed + stats["pending"])
        stats["detected"] = max(stats["detected"], stats["expected"])
        if remaining:
            stats.update({"status": "pending", "success": False})
            print(f"[失败] 仍有 {len(remaining)} 个 Daily Set 任务未完成")
            return stats

        stats.update({
            "status": "already_completed" if completed == 0 else "completed",
            "success": True,
        })
        print(
            f"\n>>> Daily Set 已验证完成：本次确认 {completed} 个，"
            f"当前剩余 {stats['pending']} 个"
        )
        return stats

    except Exception as e:
        print(f"每日任务全局错误: {e}")
        stats.update({"status": "error", "success": False, "error": str(e)})
        try:
            driver.switch_to.default_content()
        except:
            pass
        return stats


def main():
    # 移除了 kill_edge_processes()，现在可以和你的主浏览器共存了

    driver = None
    started_at = datetime.now()
    search_stats = {"requested": SEARCH_COUNT, "completed": 0, "failed": SEARCH_COUNT}
    daily_stats = {
        "expected": 0,
        "detected": 0,
        "completed": 0,
        "pending": 0,
        "status": "not_started",
        "success": False,
    }
    errors = []
    success = False
    try:
        driver = setup_driver()
        if driver is None:
            raise RuntimeError("Edge 驱动初始化失败")

        search_stats = perform_daily_searches(driver)
        daily_stats = complete_daily_set(driver)
        success = bool(search_stats.get("failed", 1) == 0 and daily_stats.get("success"))
        if not success:
            print("[结果] 大号任务未全部通过校验，不允许报告成功")

    except Exception as e:
        print(f"脚本运行出错: {e}")
        errors.append(str(e))
    finally:
        if driver:
            print("\n浏览器将在 10 秒后退出...")
            time.sleep(10)
            try:
                # 只关闭脚本打开的那个窗口，不会影响你的其他窗口
                driver.quit()
            except:
                pass

        result = {
            "schema": 1,
            "account": ACCOUNT_LABEL,
            "profile": {
                "user_data_dir": os.path.abspath(BOT_PROFILE_PATH),
                "profile_directory": "Default",
            },
            "started_at": started_at.isoformat(timespec="seconds"),
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "success": bool(success),
            "search": search_stats,
            "daily_set": daily_stats,
            "errors": errors,
        }
        emit_result(result)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
