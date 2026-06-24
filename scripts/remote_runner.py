import http.server
import socketserver
import os
import socket
import subprocess
from datetime import datetime

PORT = 5000
MAIN_SCRIPT = "bing每日任务双号大号.py"
SMALL_SCRIPT = "bing每日任务双号小号.py"
LOG_FILE = "remote_runner.log"
LOG_DIR_NAME = "logs"


def log(message):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(current_dir, LOG_FILE)
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "请手动查询 (cmd -> ipconfig)"


def check_selenium(venv_python):
    if not os.path.exists(venv_python):
        return False, f"找不到 Python: {venv_python}"

    try:
        result = subprocess.run(
            [venv_python, "-c", "import selenium"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception as e:
        return False, f"依赖预检失败: {e}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "import selenium 失败").strip()
        return False, f"当前 .venv 缺少 selenium 或导入失败: {detail}"

    return True, "OK"


def spawn_task(venv_python, script_path, log_path, cwd):
    log_file = open(log_path, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [venv_python, "-u", script_path],
        cwd=cwd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
    )
    return proc


class TaskHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def respond_html(self, status_code, html):
        self.send_response(status_code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_GET(self):
        if self.path != '/run':
            self.respond_html(404, "<h1>404 Not Found</h1>")
            return

        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(current_dir, LOG_DIR_NAME)
        os.makedirs(log_dir, exist_ok=True)

        venv_python = os.path.join(current_dir, ".venv", "Scripts", "python.exe")
        main_script_path = os.path.join(current_dir, MAIN_SCRIPT)
        small_script_path = os.path.join(current_dir, SMALL_SCRIPT)
        launcher_log = os.path.join(log_dir, "launcher.log")
        main_log = os.path.join(log_dir, "bing-main.log")
        small_log = os.path.join(log_dir, "bing-small.log")

        log("[收到指令] 准备直接启动双号 Bing 任务")

        missing = [p for p in [main_script_path, small_script_path] if not os.path.exists(p)]
        if missing:
            message = "找不到脚本: " + " | ".join(missing)
            log(f"[错误] {message}")
            self.respond_html(500, f"<h1>启动失败</h1><p>{message}</p>")
            return

        ok, detail = check_selenium(venv_python)
        if not ok:
            log(f"[错误] {detail}")
            self.respond_html(500, f"<h1>启动失败</h1><p>{detail}</p>")
            return

        try:
            with open(launcher_log, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 收到远程触发\n")

            main_proc = spawn_task(venv_python, main_script_path, main_log, current_dir)
            small_proc = spawn_task(venv_python, small_script_path, small_log, current_dir)

            with open(launcher_log, "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已启动主号 PID={main_proc.pid} 小号 PID={small_proc.pid}\n"
                )

            log(f"[状态] 已直接启动双号任务，主号 PID={main_proc.pid}，小号 PID={small_proc.pid}")
            self.respond_html(
                200,
                f"<h1>Success</h1><p>Main PID={main_proc.pid}, Small PID={small_proc.pid}</p>",
            )
        except Exception as e:
            log(f"[错误] 启动失败: {e}")
            self.respond_html(500, f"<h1>启动失败</h1><p>{e}</p>")


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("0.0.0.0", PORT), TaskHandler) as httpd:
        local_ip = get_local_ip()
        log("=" * 40)
        log("【双开版】远程监听服务已启动！")
        log(f"主号脚本: {MAIN_SCRIPT}")
        log(f"小号脚本: {SMALL_SCRIPT}")
        log(f"手机访问地址: http://{local_ip}:{PORT}/run")
        log("=" * 40)
        log("正在等待手机指令...")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            log("服务已停止。")
