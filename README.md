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

## 环境要求

- Windows 10/11
- [Python 3.10+](https://www.python.org/downloads/)（安装时勾选 **Add to PATH**）
- [Edge 浏览器](https://www.microsoft.com/edge)（Chromium 版，一般系统自带）
- Git（可选，用于 clone 仓库）

## 安装步骤

### 1. 下载仓库

**方式 A：Git clone（推荐）**

```bash
git clone https://github.com/S117-steven/bing-rewards.git
cd bing-rewards
```

**方式 B：直接下载**

到 [GitHub 仓库页面](https://github.com/S117-steven/bing-rewards) 点 **Code → Download ZIP**，解压到任意目录。

### 2. 运行安装脚本

双击 `setup.bat`，它会自动完成：

- 创建 Python 虚拟环境（`.venv`）
- 安装依赖（selenium、pywebview、psutil）
- 生成 `config.json` 配置文件
- 创建桌面快捷方式

### 3. 编辑配置

打开生成的 `config.json`，修改以下字段：

```json
{
  "python_exe": ".venv\\Scripts\\python.exe",
  "edge_user_data_path": "C:\\Users\\你的用户名\\AppData\\Local\\Microsoft\\Edge\\User Data",
  "edge_source_profile": "Profile 1",
  "search_count": 33
}
```

**如何找到你的 Edge 配置名：**

1. 打开 Edge 浏览器
2. 地址栏输入 `edge://version` 回车
3. 找到「个人资料路径」一行，末尾的 `Profile 1` 或 `Profile 2` 就是

**`edge_user_data_path` 怎么填：**

一般是 `C:\Users\<你的用户名>\AppData\Local\Microsoft\Edge\User Data`。不确定的话，在文件管理器地址栏输入 `%LOCALAPPDATA%\Microsoft\Edge\User Data` 看看是否存在。

### 4. 首次运行

双击桌面快捷方式 **Bing双号刷积分**，或运行仓库里的 `launcher.bat`。

首次运行时，小号脚本会自动克隆你的 Edge 配置文件。如果弹出浏览器窗口，需要手动登录一次微软账号（之后会记住登录状态）。

## 使用方法

### WebUI 控制台

双击桌面快捷方式后会弹出 WebUI 窗口，包含：

- **执行设置** — 选择立即执行、延迟执行（输入分钟数）、定时执行（选择时刻）
- **状态卡片** — 实时显示主号/小号运行状态
- **运行日志** — 流式输出脚本日志
- **完成后关机** — 开关选项，执行完毕自动关机

### 手机远程触发

运行 `scripts/remote_runner.py`，它会在 5000 端口监听 HTTP 请求：

```bash
cd scripts
python remote_runner.py
```

然后从手机或任意设备访问 `http://<电脑IP>:5000/run` 即可触发。

## 仓库结构

```
bing-rewards/
├── launcher.bat           # 启动器（桌面快捷方式指向这里）
├── manager.pyw            # WebUI 主程序
├── config.json            # 用户配置（不入 git，由 setup.bat 生成）
├── config.example.json    # 配置模板
├── requirements.txt       # Python 依赖
├── setup.bat              # 一键安装脚本
├── web/                   # WebUI 前端
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── scripts/
    ├── bing_daily_main.py    # 主号 Selenium 脚本
    ├── bing_daily_small.py   # 小号 Selenium 脚本
    └── remote_runner.py      # 手机远程触发服务
```

## 运行时生成（不入 git）

| 目录 | 说明 |
|------|------|
| `logs/` | 运行日志 |
| `.venv/` | Python 虚拟环境 |
| `Edge_Cloned_Profile/` | 小号的 Edge 浏览器配置（首次运行自动克隆） |
| `Edge_User_Data_Bot_Profile/` | 主号的 Edge 浏览器配置（首次运行自动创建） |

## 依赖

| 包 | 用途 |
|----|------|
| selenium | 浏览器自动化 |
| pywebview | WebUI 桌面窗口 |
| psutil | 进程管理 |

## 换电脑迁移

```bash
# 1. 在新电脑上 clone
git clone https://github.com/S117-steven/bing-rewards.git
cd bing-rewards

# 2. 运行安装
setup.bat

# 3. 编辑 config.json（修改用户名和 Edge 配置路径）

# 4. 运行
launcher.bat
```

## License

MIT
