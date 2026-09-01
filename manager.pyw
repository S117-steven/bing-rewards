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
RUNS_DIR = LOG_DIR / "runs"
RESULT_PREFIX = "__BING_REWARDS_RESULT__ "

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
        self._log_lock = threading.Lock()
        self._active_run_dir = None
        self._active_run_id = None
        LOG_DIR.mkdir(exist_ok=True)
        RUNS_DIR.mkdir(exist_ok=True)

    def _js(self, code):
        try:
            webview.windows[0].evaluate_js(code)
        except Exception:
            pass

    def _log(self, msg):
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        with self._log_lock:
            for path in (LOG_DIR / "manager.log", self._active_run_dir and self._active_run_dir / "manager.log"):
                if path is None:
                    continue
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("a", encoding="utf-8") as log_file:
                        log_file.write(line + "\n")
                except Exception:
                    pass
        self._js(f"window.addLog({json.dumps(msg)})")

    @staticmethod
    def _parse_worker_result(line):
        if not line.startswith(RESULT_PREFIX):
            return None
        try:
            value = json.loads(line[len(RESULT_PREFIX):])
        except (TypeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _result_detail(result):
        if not isinstance(result, dict):
            return "缺少结构化结果"
        search = result.get("search") or {}
        daily = result.get("daily_set") or {}
        return (
            f"搜索 {search.get('completed', 0)}/{search.get('requested', 0)}，"
            f"Daily Set 已确认 {daily.get('completed', 0)} 个，"
            f"剩余 {daily.get('pending', 0)} 个"
        )

    @staticmethod
    def _write_json(path, value):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(value, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _update_card(self, which, state, detail=""):
        self._js(f"window.updateCard({json.dumps(which)}, {json.dumps(state)}, {json.dumps(detail)})")

    def _set_card_class(self, which, cls):
        self._js(f"window.setCardClass({json.dumps(which)}, {json.dumps(cls)})")

    def _update_progress(self, pct, text):
        self._js(f"window.updateProgress({pct}, {json.dumps(text)})")

    def _set_buttons(self, running):
        self._js(f"window.setButtons({'true' if running else 'false'})")

    def _run_script(self, label, script_path, log_file, run_dir):
        self._log(f"[{label}] 启动: {script_path.name}")
        self._update_card(label, "运行中", "搜索 + Daily Set")
        self._set_card_class(label, "state-running")

        # Keep the old filenames as a convenient "latest run" view, while
        # also writing an immutable copy inside the timestamped run folder.
        latest_log_path = LOG_DIR / log_file
        history_log_path = run_dir / log_file
        child_result = None
        with latest_log_path.open("w", encoding="utf-8") as latest_log, \
                history_log_path.open("w", encoding="utf-8") as history_log:
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
                        latest_log.write(line + "\n")
                        latest_log.flush()
                        history_log.write(line + "\n")
                        history_log.flush()
                        parsed = self._parse_worker_result(line)
                        if parsed is not None:
                            child_result = parsed
                        self._log(f"  [{label}] {line}")

                proc.wait()
                rc = proc.returncode
                structured_success = (
                    rc == 0
                    and isinstance(child_result, dict)
                    and child_result.get("success") is True
                )
                detail = self._result_detail(child_result)

                if self._stop_flag:
                    self._update_card(label, "已停止", f"exit={rc} | {detail}")
                    self._set_card_class(label, "state-error")
                elif structured_success:
                    self._update_card(label, "完成", detail)
                    self._set_card_class(label, "state-done")
                    self._log(f"[{label}] 已验证完成 (exit={rc}) | {detail}")
                else:
                    reason = "结构化结果未确认成功" if rc == 0 else f"exit={rc}"
                    self._update_card(label, "异常", f"{reason} | {detail}")
                    self._set_card_class(label, "state-error")
                    self._log(f"[{label}] 未通过完成校验 ({reason}) | {detail}")

                return {
                    "returncode": rc,
                    "success": structured_success,
                    "result": child_result,
                }

            except Exception as e:
                self._update_card(label, "错误", str(e)[:40])
                self._set_card_class(label, "state-error")
                self._log(f"[{label}] 启动失败: {e}")
                return {"returncode": -1, "success": False, "result": child_result, "error": str(e)}

    def _do_shutdown(self):
        self._log("[系统] 执行关机...")
        try:
            completed = subprocess.run(
                ["shutdown", "/s", "/t", "60", "/c", "Bing Rewards 双号刷积分完成，60 秒后关机"],
                creationflags=CREATE_NO_WINDOW,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if completed.returncode == 0:
                self._log("[系统] 关机命令已发送（60 秒后），如需取消请在终端运行 shutdown /a")
                return True
            detail = (completed.stderr or completed.stdout or "无返回信息").strip()
            self._log(f"[系统] 关机命令失败 (exit={completed.returncode}): {detail}")
            return False
        except Exception as e:
            self._log(f"[系统] 关机失败: {e}")
            return False

    def _worker(self, config):
        self._stop_flag = False
        self._processes = []
        started_at = datetime.now()
        run_id = started_at.strftime("%Y%m%d_%H%M%S_%f")
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        self._active_run_id = run_id
        self._active_run_dir = run_dir
        self._write_json(run_dir / "run.json", {
            "schema": 1,
            "run_id": run_id,
            "started_at": started_at.isoformat(timespec="seconds"),
            "shutdown_requested": bool(config.get("shutdown")),
        })
        self._log("=" * 40)
        self._log(f"开始双号刷积分任务（并行模式，run_id={run_id}）")

        self._set_buttons(True)
        self._update_progress(0, "双号并行运行中...")
        start_time = time.time()

        results = {}
        def run(label, script, log):
            results[label] = self._run_script(label, script, log, run_dir)

        t_main = threading.Thread(target=run, args=("main", MAIN_SCRIPT, "bing-main.log"), daemon=True)
        t_small = threading.Thread(target=run, args=("small", SMALL_SCRIPT, "bing-small.log"), daemon=True)
        t_main.start()
        t_small.start()
        t_main.join()
        t_small.join()

        self._processes = []
        stopped = self._stop_flag
        has_error = any(
            not isinstance(results.get(label), dict) or not results[label].get("success")
            for label in ("main", "small")
        )
        self._finalize(
            start_time,
            stopped=stopped,
            has_error=has_error,
            shutdown=config.get("shutdown"),
            results=results,
            run_dir=run_dir,
            run_id=run_id,
            started_at=started_at,
        )

    def _finalize(
        self,
        start_time,
        stopped,
        has_error=False,
        shutdown=False,
        results=None,
        run_dir=None,
        run_id=None,
        started_at=None,
    ):
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

        shutdown_sent = False
        if shutdown and not stopped and not has_error:
            shutdown_sent = self._do_shutdown()
        elif shutdown:
            self._log("[系统] 检测到任务异常，跳过自动关机")

        if run_dir is not None:
            summary = {
                "schema": 1,
                "run_id": run_id,
                "started_at": started_at.isoformat(timespec="seconds") if started_at else None,
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "elapsed_minutes": elapsed,
                "success": bool(not stopped and not has_error),
                "stopped": bool(stopped),
                "shutdown_requested": bool(shutdown),
                "shutdown_sent": bool(shutdown_sent),
                "results": results or {},
            }
            self._write_json(run_dir / "summary.json", summary)
        self._active_run_dir = None
        self._active_run_id = None

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
