# Bing Rewards 双号自动刷积分

自动完成 Microsoft Rewards 每日搜索和 Daily Set 任务，支持双号并行。

## 功能

- 双号并行执行（主号 + 小号同时跑）
- 每号 33 次随机 Bing 搜索
- 自动完成 Daily Set 每日任务
- WebUI 控制台（实时日志、状态卡片）
- 三种执行模式：立即 / 延迟 / 定时
- 完成后可选自动关机
- 手机远程触发（HTTP 接口）

## 快速开始

### 1. 安装

```bash
git clone <repo-url> bing-rewards
cd bing-rewards
setup.bat
```

### 2. 配置

编辑 `config.json`：

```json
{
  "python_exe": ".venv\\Scripts\\python.exe",
  "edge_user_data_path": "C:\\Users\\你的用户名\\AppData\\Local\\Microsoft\\Edge\\User Data",
  "edge_source_profile": "Profile 1",
  "search_count": 33
}
```

- `edge_user_data_path`：Edge 浏览器的 User Data 目录
- `edge_source_profile`：要克隆的 Edge 配置名（在 `edge://version` 查看）

### 3. 运行

双击桌面快捷方式 `Bing双号刷积分`，或运行 `launcher.bat`。

## 仓库结构

```
bing-rewards/
├── launcher.bat           # 启动器
├── manager.pyw            # WebUI 主程序
├── config.json            # 用户配置（不入 git）
├── config.example.json    # 配置模板
├── requirements.txt       # Python 依赖
├── setup.bat              # 一键安装
├── web/                   # WebUI 前端
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── scripts/
    ├── bing_daily_main.py    # 主号脚本
    ├── bing_daily_small.py   # 小号脚本
    └── remote_runner.py      # 手机远程触发
```

## 运行时生成（不入 git）

- `logs/` — 运行日志
- `.venv/` — Python 虚拟环境
- `Edge_Cloned_Profile/` — 小号的 Edge 浏览器配置
- `Edge_User_Data_Bot_Profile/` — 主号的 Edge 浏览器配置

## 手机远程触发

运行 `scripts/remote_runner.py`，监听 5000 端口：

```bash
cd scripts
python remote_runner.py
```

然后访问 `http://<电脑IP>:5000/run` 触发。

## 依赖

- Python 3.10+
- Edge 浏览器（Chromium 版）
- selenium、pywebview、psutil
