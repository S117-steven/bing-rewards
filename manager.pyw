# -*- coding: utf-8 -*-
"""Bing 双号刷积分 - WebUI 管理器"""
from __future__ import annotations

import os
os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = "--no-proxy-server"

import json
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import webview

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000 if os.name == "nt" else 0)
REPO_DIR = Path(__file__).resolve().parent
LOG_DIR = REPO_DIR / "logs"

def _load_config():
    cfg_path = REPO_DIR / "config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    return {}

_config = _load_config()
PYTHON_EXE = Path(_config.get("python_exe", str(REPO_DIR / ".venv" / "Scripts" / "python.exe")))
if not PYTHON_EXE.is_absolute():
    PYTHON_EXE = REPO_DIR / PYTHON_EXE
MAIN_SCRIPT = REPO_DIR / "scripts" / "bing_daily_main.py"
SMALL_SCRIPT = REPO_DIR / "scripts" / "bing_daily_small.py"


class Api:
    def __init__(self):
        self._processes = []
        self._stop_flag = False
        self._countdown_thread = None
        LOG_DIR.mkdir(exist_ok=True)

    def _js(self, code):
        try:
            webview.windows[0].evaluate_js(code)
        except Exception:
            pass

    def _log(self, msg):
        self._js(f"window.addLog({json.dumps(msg)})")

    def _update_card(self, which, state, detail=""):
        self._js(f"window.updateCard({json.dumps(which)}, {json.dumps(state)}, {json.dumps(detail)})")

    def _set_card_class(self, which, cls):
        self._js(f"window.setCardClass({json.dumps(which)}, {json.dumps(cls)})")

    def _update_progress(self, pct, text):
        self._js(f"window.updateProgress({pct}, {json.dumps(text)})")

    def _set_buttons(self, running):
        self._js(f"window.setButtons({'true' if running else 'false'})")

    def _run_script(self, label, script_path, log_file):
        self._log(f"[{label}] 启动: {script_path.name}")
        self._update_card(label, "运行中", "搜索 + Daily Set")
        self._set_card_class(label, "state-running")

        log_path = LOG_DIR / log_file
        with open(log_path, "w", encoding="utf-8") as lf:
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                proc = subprocess.Popen(
                    [str(PYTHON_EXE), "-u", str(script_path)],
                    cwd=str(REPO_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW,
                    env=env,
                )
                self._processes.append(proc)

                for raw_line in iter(proc.stdout.readline, b""):
                    if self._stop_flag:
                        proc.terminate()
                        self._log(f"[{label}] 已停止")
                        break
                    line = raw_line.decode("utf-8", errors="replace").rstrip()
                    if line:
                        lf.write(line + "\n")
                        lf.flush()
                        self._log(f"  [{label}] {line}")

                proc.wait()
                rc = proc.returncode

                if self._stop_flag:
                    self._update_card(label, "已停止", f"exit={rc}")
                    self._set_card_class(label, "state-error")
                elif rc == 0:
                    self._update_card(label, "完成", "任务全部完成")
                    self._set_card_class(label, "state-done")
                    self._log(f"[{label}] 完成 (exit={rc})")
                else:
                    self._update_card(label, "异常", f"exit={rc}")
                    self._set_card_class(label, "state-error")
                    self._log(f"[{label}] 异常退出 (exit={rc})")

                return rc

            except Exception as e:
                self._update_card(label, "错误", str(e)[:40])
                self._set_card_class(label, "state-error")
                self._log(f"[{label}] 启动失败: {e}")
                return -1

    def _do_shutdown(self):
        self._log("[系统] 执行关机...")
        try:
            subprocess.run(
                ["shutdown", "/s", "/t", "60", "/c", "Bing Rewards 双号刷积分完成，60 秒后关机"],
                creationflags=CREATE_NO_WINDOW,
            )
            self._log("[系统] 关机命令已发送（60 秒后），如需取消请在终端运行 shutdown /a")
        except Exception as e:
            self._log(f"[系统] 关机失败: {e}")

    def _worker(self, config):
        self._stop_flag = False
        self._processes = []
        self._log("=" * 40)
        self._log("开始双号刷积分任务（并行模式）")

        self._set_buttons(True)
        self._update_progress(0, "双号并行运行中...")
        start_time = time.time()

        results = {}
        def run(label, script, log):
            results[label] = self._run_script(label, script, log)

        t_main = threading.Thread(target=run, args=("main", MAIN_SCRIPT, "bing-main.log"))
        t_small = threading.Thread(target=run, args=("small", SMALL_SCRIPT, "bing-small.log"))
        t_main.start()
        t_small.start()
        t_main.join()
        t_small.join()

        self._processes = []
        stopped = self._stop_flag
        has_error = results.get("main", -1) != 0 or results.get("small", -1) != 0
        self._finalize(start_time, stopped=stopped, has_error=has_error, shutdown=config.get("shutdown"))

    def _finalize(self, start_time, stopped, has_error=False, shutdown=False):
        elapsed = round((time.time() - start_time) / 60, 1)
        if stopped:
            self._update_card("overall", "已停止", f"耗时 {elapsed} 分钟")
            self._set_card_class("overall", "state-error")
            self._update_progress(None, "")
        elif has_error:
            self._update_card("overall", "部分异常", f"耗时 {elapsed} 分钟")
            self._set_card_class("overall", "state-error")
            self._update_progress(1.0, f"完成（有异常）耗时 {elapsed} 分钟")
        else:
            self._update_card("overall", "全部完成", f"耗时 {elapsed} 分钟")
            self._set_card_class("overall", "state-done")
            self._update_progress(1.0, f"完成! 总耗时 {elapsed} 分钟")
        self._set_buttons(False)
        self._log("=" * 40)
        self._log(f"任务结束，总耗时 {elapsed} 分钟")

        if shutdown and not stopped and not has_error:
            self._do_shutdown()

    def _countdown_and_run(self, config):
        """等待延迟/定时时间到达后执行任务"""
        mode = config.get("mode", "now")

        if mode == "delay":
            minutes = config.get("delay_minutes", 30)
            target = datetime.now() + timedelta(minutes=minutes)
            self._log(f"[倒计时] 将在 {target.strftime('%H:%M')} 执行（{minutes} 分钟后）")
            self._update_card("overall", "等待中", f"{minutes} 分钟后执行")
            self._set_card_class("overall", "state-idle")

            end_time = time.time() + minutes * 60
            while time.time() < end_time:
                if self._stop_flag:
                    self._log("[倒计时] 已取消")
                    self._update_card("overall", "已取消", "")
                    self._set_card_class("overall", "state-error")
                    self._set_buttons(False)
                    return
                remaining = int(end_time - time.time())
                mm, ss = divmod(remaining, 60)
                self._update_progress(0, f"等待中: {mm:02d}:{ss:02d}")
                self._update_card("overall", "等待中", f"剩余 {mm:02d}:{ss:02d}")
                time.sleep(1)

        elif mode == "schedule":
            time_str = config.get("schedule_time", "03:30")
            now = datetime.now()
            h, m = map(int, time_str.split(":"))
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            delta = (target - now).total_seconds()
            self._log(f"[定时] 将在 {target.strftime('%Y-%m-%d %H:%M')} 执行")
            self._update_card("overall", "定时中", target.strftime("%H:%M"))
            self._set_card_class("overall", "state-idle")

            end_time = time.time() + delta
            while time.time() < end_time:
                if self._stop_flag:
                    self._log("[定时] 已取消")
                    self._update_card("overall", "已取消", "")
                    self._set_card_class("overall", "state-error")
                    self._set_buttons(False)
                    return
                remaining = int(end_time - time.time())
                hh, rem = divmod(remaining, 3600)
                mm, ss = divmod(rem, 60)
                self._update_progress(0, f"等待中: {hh:02d}:{mm:02d}:{ss:02d}")
                self._update_card("overall", "定时中", f"剩余 {hh:02d}:{mm:02d}:{ss:02d}")
                time.sleep(1)

        # 时间到达，开始执行
        self._log("[系统] 时间到达，开始执行!")
        self._worker(config)

    def start_tasks(self, config_json="{}"):
        if self._processes:
            self._log("[提示] 任务已在运行中")
            return "already_running"
        if self._countdown_thread and self._countdown_thread.is_alive():
            self._log("[提示] 已有等待中的任务")
            return "already_running"

        try:
            config = json.loads(config_json)
        except Exception:
            config = {"mode": "now"}

        self._stop_flag = False
        self._countdown_thread = threading.Thread(
            target=self._countdown_and_run, args=(config,), daemon=True
        )
        self._countdown_thread.start()
        return "started"

    def stop_tasks(self):
        self._stop_flag = True

        # 取消待执行的关机
        try:
            subprocess.run(["shutdown", "/a"], creationflags=CREATE_NO_WINDOW,
                           capture_output=True, timeout=5)
        except Exception:
            pass

        # 终止所有运行中的脚本
        for proc in self._processes:
            try:
                proc.terminate()
            except Exception:
                pass
        self._processes = []

        self._log("[操作] 已取消：关机已撤销、脚本已终止、等待已中断")

        # 重置 UI
        self._update_card("main", "待命", "-")
        self._set_card_class("main", "state-idle")
        self._update_card("small", "待命", "-")
        self._set_card_class("small", "state-idle")
        self._update_card("overall", "-", "就绪")
        self._set_card_class("overall", "state-idle")
        self._update_progress(None, "")
        self._set_buttons(False)

        return "cancelled"


if __name__ == "__main__":
    api = Api()
    html_file = REPO_DIR / "web" / "index.html"
    window = webview.create_window(
        title="Bing 双号刷积分",
        url=html_file.as_uri(),
        js_api=api,
        width=580,
        height=720,
        min_size=(500, 620),
    )
    webview.start()
    os._exit(0)
