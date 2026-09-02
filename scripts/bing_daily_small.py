import time
import random
import string
import os
import json
import shutil
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
SOURCE_PROFILE_NAME = _config.get("edge_source_profile", "Profile 1")
SEARCH_COUNT = _config.get("search_count", 23)
ACCOUNT_LABEL = "small"
DASHBOARD_URL = "https://rewards.bing.com/dashboard"
CLONED_PROFILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Edge_Cloned_Profile")

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
    target_user_data_dir = CLONED_PROFILE_PATH
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
    print(
        f"[账号] {ACCOUNT_LABEL} | 源配置: {os.path.abspath(YOUR_USER_DATA_PATH)}"
        f"\\{SOURCE_PROFILE_NAME} | 克隆配置: {os.path.abspath(CLONED_PROFILE_PATH)} | profile=Default"
    )

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
    """执行每日搜索并返回统计结果。"""
    stats = {"requested": SEARCH_COUNT, "completed": 0, "failed": 0}
    print("\n" + "=" * 30)
    print(">>> [小号] 阶段 1: 开始每日搜索")
    print("=" * 30)

    try:
        driver.get("https://www.bing.com")
    except Exception as e:
        try:
            driver.refresh()
        except Exception as refresh_error:
            stats["failed"] = SEARCH_COUNT
            print(f"小号搜索首页无法打开: {refresh_error}")
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

            print(f"[小号 {i + 1}/{SEARCH_COUNT}] 搜索: {query}")

            time.sleep(random.uniform(8, 15))
            if (i + 1) % 5 == 0:
                print("  -> 休息一会儿...")
                time.sleep(random.uniform(5, 10))

            stats["completed"] += 1

        except Exception as e:
            print(f"搜索出错: {e}")
            stats["failed"] += 1
            try:
                driver.get("https://www.bing.com")
                time.sleep(5)
            except:
                pass
    print(
        f">>> 小号搜索阶段结束：成功 {stats['completed']}/{stats['requested']}，"
        f"失败 {stats['failed']}"
    )
    return stats


def complete_daily_set(driver):
    """完成 Daily Set，并在 Rewards 页面确认每项任务已记账。

    rewards.bing.com 仪表盘的 React 数据是唯一能可靠反映任务记账状态的数据源
    （旧版 bing.com 侧边栏面板不含该数据，且内容刷新滞后），因此发现、点击、
    校验都优先走仪表盘，读不到时才回退到旧版侧边栏的 DOM 探测。
    """
    print("\n" + "=" * 30)
    print(">>> [小号] 阶段 2: 开始每日任务")
    print("=" * 30)

    stats = {
        "date": None,
        "expected": 0,
        "detected": 0,
        "completed": 0,
        "pending": 0,
        "status": "not_started",
        "success": False,
    }
    discovery = {"source": None, "parsed": False, "total": 0, "pending": 0}

    def open_sidebar():
        try:
            driver.switch_to.default_content()
        except:
            pass
        try:
            driver.execute_script("""
                var closeBtn = document.querySelector('#rewid-f .close_rewards_panel, #rewid-f button[class*=close]');
                if (closeBtn) closeBtn.click();
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
                f"Daily Set 任务（总数 {react_state['total']}，结算日 {react_state['date']}）"
            )
            return react_state["pending_tasks"]

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
            """从新版 Rewards 的 React 数据中提取当前有效的 Daily Set 任务。"""
            try:
                state = extract_react_daily_set_state(driver.page_source)
                if state is None:
                    return None
                tasks = state["pending_tasks"]
                print(
                    f"    [debug] 新版 Rewards 数据找到 {len(tasks)} 个未完成 "
                    f"Daily Set 任务（结算日 {state['date']}）"
                )
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

        # 方法2：找 promo-title 元素。
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

        # 方法3：全局搜索所有指向搜索页的链接。
        # 卡片标题不一定出现在 <a> 的可见文本里（链接文本可能为空），
        # 侧边栏面板中指向 bing.com/search|shop 的可见链接就是任务卡片。
        all_links = driver.find_elements(By.TAG_NAME, "a")
        task_links = []
        seen_hrefs = set()
        for l in all_links:
            try:
                if not is_task_link(l):
                    continue
                href = (l.get_attribute("href") or "").split("#")[0]
            except Exception:
                continue
            if href.lower() in seen_hrefs:
                continue
            seen_hrefs.add(href.lower())
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
        driver.get(DASHBOARD_URL)
        time.sleep(1)
        # 部分账号的「每日」区块默认折叠，先展开再找任务卡片
        driver.execute_script("""
            var toggles = document.querySelectorAll('button[aria-expanded="false"]');
            for (var i = 0; i < toggles.length; i++) {
                var label = ((toggles[i].innerText || '') + ' ' +
                    (toggles[i].getAttribute('aria-label') || '')).toLowerCase();
                if (label.indexOf('每日') >= 0 || label.indexOf('daily') >= 0) {
                    toggles[i].click();
                    break;
                }
            }
        """)
        time.sleep(1)

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

    def load_dashboard_state(attempts=3):
        """打开 Rewards 仪表盘并解析当天 Daily Set 状态；解析失败返回 None。"""
        for _ in range(attempts):
            try:
                driver.switch_to.default_content()
                driver.get(DASHBOARD_URL)
                time.sleep(3)
                state = extract_react_daily_set_state(driver.page_source)
            except Exception as e:
                print(f"    [debug] 读取 Rewards 仪表盘失败: {e}")
                state = None
            if state is not None:
                return state
            time.sleep(2)
        return None

    def verify_task_completed(snapshot):
        """确认任务已在 Rewards 记账：仪表盘数据优先，读不到时对比侧边栏待办。

        旧版侧边栏面板的内容刷新滞后，任务完成后仍可能显示未完成，
        因此只有仪表盘数据不可用时才把它作为依据。
        """
        target_offer = str(snapshot.get("offer_id") or "").lower()
        deadline = time.time() + 45
        while time.time() < deadline:
            state = None
            if target_offer:
                try:
                    driver.switch_to.default_content()
                    driver.get(DASHBOARD_URL)
                    time.sleep(3)
                    state = extract_react_daily_set_state(driver.page_source)
                except Exception as e:
                    print(f"    [校验] 读取 Rewards 状态失败: {e}")

            if state is not None:
                matches = [
                    item for item in state["tasks"]
                    if str(item.get("offer_id") or "").lower() == target_offer
                ]
                if not matches or all(item.get("completed") for item in matches):
                    print("    [校验] Rewards 已确认该任务完成")
                    return True
                print(f"    [校验] 任务仍显示未完成，继续等待...（今日剩余 {state['pending']} 个）")
                time.sleep(3)
                continue

            # 没有 offer_id（旧版侧边栏元素）或本次仪表盘解析失败时，
            # 才用侧边栏待办列表对比作为后备依据。
            try:
                driver.get("https://www.bing.com")
                time.sleep(3)
                open_sidebar()
                pending = find_daily_links()
                if discovery.get("parsed"):
                    pending_snapshots = [task_snapshot(item) for item in pending]
                    if not any(tasks_match(snapshot, item) for item in pending_snapshots):
                        print("    [校验] Rewards 待办列表已移除该任务")
                        return True
                    print("    [校验] 任务仍显示未完成，继续等待...")
            except Exception as e:
                print(f"    [校验] 侧边栏状态读取失败: {e}")
            time.sleep(3)
        return False

    def rediscover_dom_task(snapshot):
        """重新打开侧边栏并定位与快照匹配的任务元素，避免点击失效的旧引用。"""
        driver.switch_to.default_content()
        driver.get("https://www.bing.com")
        time.sleep(3)
        open_sidebar()
        for item in find_daily_links():
            if tasks_match(snapshot, task_snapshot(item)):
                return item
        return None

    def run_react_mode(state):
        """仪表盘模式：逐个点击待办卡片，并在仪表盘上复核记账。

        单个任务校验失败只跳过该任务，不再中断剩余任务。
        返回 (已确认完成数, 最终仪表盘状态或 None)。
        """
        completed = 0
        pending = list(state["pending_tasks"])
        for _ in range(3):  # 最多重扫 3 轮，防止异常数据导致死循环
            if not pending:
                break
            task = pending[0]
            title = (task.get("text") or "未命名任务").strip()
            print(f"\n>>> [小号任务 {completed + 1}] 点击: {title}")

            verified = False
            for attempt in range(1, 3):
                try:
                    click_react_daily_task(task)
                    time.sleep(6)
                    verified = verify_task_completed(task)
                except Exception as e:
                    print(f"    [错误] 任务第 {attempt} 次异常: {e}")
                if verified:
                    break
                print(f"    [校验] 第 {attempt} 次未确认完成，准备重试...")

            if not verified:
                print(f"    [失败] 任务“{title}”未通过 Rewards 完成校验，跳过并继续后面的任务")
                pending = pending[1:]
                continue

            completed += 1
            stats["completed"] = completed
            print("    [状态] 任务已确认完成")
            fresh = load_dashboard_state()
            pending = fresh["pending_tasks"] if fresh is not None else pending[1:]

        return completed, load_dashboard_state()

    def run_dom_mode():
        """旧版侧边栏模式：仪表盘数据读不到时的后备路径。

        返回 (已确认完成数, 剩余任务数或 None)。
        """
        completed = 0
        failed_snapshots = []
        for task_num in range(3):
            print(f"\n>>> [小号任务 {task_num + 1}] 打开侧边栏...")
            driver.switch_to.default_content()
            driver.get("https://www.bing.com")
            time.sleep(3)
            try:
                open_sidebar()
                daily_links = find_daily_links()
            except Exception as e:
                print(f"    [错误] 打开侧边栏失败: {e}")
                daily_links = []
            # 校验失败过的任务本轮不再重复点击，只处理其余任务
            candidates = [
                link for link in daily_links
                if not any(tasks_match(f, task_snapshot(link)) for f in failed_snapshots)
            ]
            print(f"    找到 {len(candidates)} 个待完成的 Daily Set 任务")

            stats["expected"] = max(stats["expected"], discovery.get("total", 0))
            stats["detected"] = max(stats["detected"], discovery.get("total", 0))

            if not candidates:
                if discovery.get("parsed"):
                    print(f"    当前没有待完成任务，已验证完成 {completed} 个")
                    break
                stats.update({"status": "not_detected", "success": False})
                print("    [失败] 未能可靠读取 Daily Set 状态，不能判定为成功")
                return completed, None

            task = candidates[0]
            snapshot = task_snapshot(task)
            title = snapshot.get("text") or "未命名任务"
            print(f"    点击: {title}")

            verified = False
            for attempt in range(1, 3):
                try:
                    if attempt > 1:
                        # 第一次点击后原页面已跳转，旧元素引用已失效，必须重新查找
                        rediscovered = rediscover_dom_task(snapshot)
                        if rediscovered is None:
                            raise RuntimeError("重试时未能在侧边栏中重新找到该任务")
                        task = rediscovered
                    # 用当前标签页的 JS 点击绕过元素遮挡和 target=_blank
                    driver.execute_script(
                        "arguments[0].target='_self'; arguments[0].click();", task
                    )
                    time.sleep(6)
                    driver.switch_to.default_content()
                    print(f"    [状态] 跳转成功: {driver.current_url[:60]}...")
                    driver.execute_script("window.scrollTo(0, 200);")
                    time.sleep(random.uniform(3, 5))
                    verified = verify_task_completed(snapshot)
                except Exception as e:
                    print(f"    [错误] 任务 {task_num + 1} 第 {attempt} 次异常: {e}")
                    try:
                        driver.switch_to.default_content()
                        driver.get("https://www.bing.com")
                        time.sleep(3)
                    except Exception:
                        pass
                if verified:
                    break
                print(f"    [校验] 第 {attempt} 次未确认完成，准备重试...")

            if not verified:
                failed_snapshots.append(snapshot)
                print(f"    [失败] 任务“{title}”未通过 Rewards 完成校验，跳过并继续后面的任务")
                continue

            completed += 1
            stats["completed"] = completed
            print(f"    [状态] 任务 {task_num + 1} 已确认完成")

        # 最后再读一次待办列表，防止还有遗漏的任务。
        driver.switch_to.default_content()
        driver.get("https://www.bing.com")
        time.sleep(3)
        try:
            open_sidebar()
            remaining = find_daily_links()
        except Exception as e:
            print(f"[错误] 最终校验读取侧边栏失败: {e}")
            return completed, None
        if not discovery.get("parsed"):
            return completed, None
        return completed, len(remaining)

    try:
        print("正在读取 Rewards 仪表盘数据...")
        state = load_dashboard_state()
        if state is not None:
            stats["date"] = state["date"]
            stats["expected"] = state["total"]
            stats["detected"] = state["total"]
            print(
                f"    仪表盘数据：共 {state['total']} 个 Daily Set 任务，"
                f"已完成 {state['completed']} 个，待完成 {state['pending']} 个，"
                f"结算日 {state['date']}"
            )
            completed, final = run_react_mode(state)
            stats["completed"] = completed
            if final is None:
                stats.update({"status": "verification_failed", "success": False})
                print("[失败] 无法读取最终 Daily Set 状态")
                return stats
            stats["pending"] = final["pending"]
            stats["date"] = final["date"]
            stats["expected"] = max(stats["expected"], final["total"])
            stats["detected"] = max(stats["detected"], final["total"])
            if stats["pending"] == 0:
                stats.update({
                    "status": "already_completed" if completed == 0 else "completed",
                    "success": True,
                })
                print(
                    f"\n>>> [小号] Daily Set 已验证完成：本次确认 {completed} 个，"
                    f"当前剩余 {stats['pending']} 个"
                )
                return stats
            stats.update({"status": "verification_failed", "success": False})
            print(f"[失败] 仍有 {stats['pending']} 个 Daily Set 任务未完成")
            return stats

        print("    [debug] 仪表盘数据不可用，回退到旧版侧边栏模式")
        completed, remaining = run_dom_mode()
        stats["completed"] = completed
        if remaining is None:
            stats.update({"status": "not_detected", "success": False})
            print("[失败] 最终校验无法读取 Daily Set 状态")
            return stats
        stats["pending"] = remaining
        stats["expected"] = max(stats["expected"], completed + remaining)
        stats["detected"] = max(stats["detected"], stats["expected"])
        if remaining == 0:
            stats.update({
                "status": "already_completed" if completed == 0 else "completed",
                "success": True,
            })
            print(
                f"\n>>> [小号] Daily Set 已验证完成：本次确认 {completed} 个，"
                f"当前剩余 {stats['pending']} 个"
            )
            return stats
        stats.update({"status": "pending", "success": False})
        print(f"[失败] 仍有 {remaining} 个 Daily Set 任务未完成")
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
            print("[结果] 小号任务未全部通过校验，不允许报告成功")
    except Exception as e:
        print(f"脚本出错: {e}")
        errors.append(str(e))
    finally:
        if driver:
            print("\n小号浏览器将在 10 秒后退出...")
            time.sleep(10)
            try:
                driver.quit()
            except:
                pass

        result = {
            "schema": 1,
            "account": ACCOUNT_LABEL,
            "profile": {
                "source_user_data_dir": os.path.abspath(YOUR_USER_DATA_PATH),
                "source_profile": SOURCE_PROFILE_NAME,
                "user_data_dir": os.path.abspath(CLONED_PROFILE_PATH),
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
