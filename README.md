# Bing Rewards 双号自动刷积分

自动完成 Microsoft Rewards 每日搜索和 Daily Set 任务，支持双号并行。打开一个漂亮的 WebUI 控制台，点击一下就能开始刷。

## 它能做什么

- **自动搜索**：每个号自动进行 23 次 Bing 随机搜索，赚取搜索积分
- **自动完成每日任务**：自动打开 Rewards 侧边栏，点击完成 Daily Set 的 3 个活动任务
- **双号并行**：主号和小号同时运行，总耗时约 10-15 分钟
- **WebUI 控制台**：漂亮的桌面窗口，实时显示运行状态和日志
- **灵活调度**：立即执行、延迟执行、定时执行，三种模式可选
- **完成后关机**：可选执行完毕自动关机

## 你需要什么

在开始之前，确保你的电脑有以下东西：

| 需要 | 说明 | 如何检查 |
|------|------|----------|
| Windows 10/11 | 操作系统 | 一般都有 |
| Python 3.10+ | 脚本运行环境 | 打开终端输入 `python --version` |
| Edge 浏览器 | 脚本操控的浏览器 | 一般系统自带 |
| Git | 下载代码（可选） | 打开终端输入 `git --version` |

### 如何安装 Python

1. 打开 https://www.python.org/downloads/
2. 点击下载最新的 Python 3.x
3. 运行安装程序，**务必勾选** `Add Python to PATH`
4. 点击 `Install Now`

### 如何安装 Git（可选）

1. 打开 https://git-scm.com/download/win
2. 下载并安装，全部默认选项即可

## 第一步：下载代码

打开终端（按 `Win+R`，输入 `cmd` 回车），执行以下命令：

```bash
# 方式 A：用 Git 下载（推荐）
git clone https://github.com/S117-steven/bing-rewards.git
cd bing-rewards

# 方式 B：不用 Git，直接下载 ZIP
# 到 https://github.com/S117-steven/bing-rewards 点 "Code" → "Download ZIP"
# 解压后进入 bing-rewards 文件夹
```

## 第二步：运行安装脚本

在 `bing-rewards` 文件夹里，双击 `setup.bat`。

它会自动做 4 件事：
1. 创建 Python 虚拟环境（一个独立的 Python 环境，不影响系统）
2. 安装需要的依赖包（selenium、pywebview、psutil）
3. 生成配置文件 `config.json`
4. 在桌面创建快捷方式

安装过程大约需要 1-2 分钟，看到 `Setup complete!` 就说明成功了。

## 第三步：编辑配置文件

用记事本打开 `config.json`（在 `bing-rewards` 文件夹里），修改以下内容：

```json
{
  "python_exe": ".venv\\Scripts\\python.exe",
  "edge_user_data_path": "C:\\Users\\你的Windows用户名\\AppData\\Local\\Microsoft\\Edge\\User Data",
  "edge_source_profile": "Profile 1",
  "search_count": 23
}
```

**只需要改两个地方：**

### 1. `edge_user_data_path`（Edge 数据目录）

把你 Windows 用户名填进去。例如你的用户名是 `zhangsan`：

```
C:\\Users\\zhangsan\\AppData\\Local\\Microsoft\\Edge\\User Data
```

**不知道自己的用户名？** 打开文件管理器，看左边的「快速访问」上方显示的名字，或者在终端输入 `whoami`。

**不确定路径对不对？** 在文件管理器的地址栏输入 `%LOCALAPPDATA%\Microsoft\Edge\User Data`，如果能打开就说明路径是对的。

### 2. `edge_source_profile`（Edge 配置名）

1. 打开 Edge 浏览器
2. 在地址栏输入 `edge://version` 回车
3. 找到「个人资料路径」这一行
4. 路径末尾的 `Profile 1` 或 `Profile 2` 就是你要填的值

例如路径是 `C:\Users\zhangsan\AppData\Local\Microsoft\Edge\User Data\Profile 2`，那就填 `Profile 2`。

## 第四步：首次运行

双击桌面的 **Bing双号刷积分** 快捷方式（或者直接运行 `launcher.bat`）。

**首次运行会发生什么：**

1. 弹出一个漂亮的 WebUI 控制台窗口
2. 脚本会自动打开两个 Edge 浏览器窗口
3. **小号的浏览器会弹出来**，需要你手动登录一次微软账号
4. 登录后关闭那个浏览器窗口，回到控制台点「开始刷积分」

**之后再运行就不需要登录了**，脚本会记住登录状态。

## 第五步：开始刷积分

在 WebUI 控制台上：

1. **执行模式**：选择「立即执行」
2. **完成后关机**：按需开关
3. 点击 **「开始刷积分」** 按钮

你会看到：
- 两个状态卡片实时显示主号/小号的运行状态
- 下方日志面板流式输出每一步操作
- 进度条显示整体进度

大约 10-15 分钟后，两个号的搜索和每日任务都会完成。

## 常见问题

### Q: 启动时报错 "找不到 Python"

说明 Python 没有安装，或者安装时没有勾选 `Add to PATH`。重新安装 Python 并勾选该选项。

### Q: 启动时报错 "找不到 Edge 浏览器"

说明你的电脑没有安装 Edge。去 https://www.microsoft.com/edge 下载安装。

### Q: 小号登录后还是没有积分

确认 `config.json` 里的 `edge_source_profile` 填对了。去 `edge://version` 查看。

### Q: Daily Set 任务没有完成

Bing Rewards 页面会偶尔改版。如果脚本无法找到任务，可能是页面结构变了。到 GitHub 提 issue 反馈。

### Q: 如何更新到最新版本

```bash
cd bing-rewards
git pull
```

如果你是下载 ZIP 的，重新下载解压覆盖即可。

## 仓库里有什么

```
bing-rewards/
├── launcher.bat           ← 启动器（双击运行）
├── manager.pyw            ← WebUI 主程序
├── config.json            ← 你的配置（不上传到 git）
├── config.example.json    ← 配置模板
├── setup.bat              ← 一键安装
├── requirements.txt       ← Python 依赖列表
├── web/                   ← WebUI 界面文件
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── scripts/               ← 核心脚本
    ├── bing_daily_main.py    ← 主号自动刷积分
    ├── bing_daily_small.py   ← 小号自动刷积分
    └── remote_runner.py      ← 手机远程触发（可选）
```

## 手机远程触发（可选高级功能）

如果你想用手机远程启动刷积分：

1. 先运行一次 `scripts/remote_runner.py`
2. 确保电脑和手机在同一局域网
3. 手机浏览器访问 `http://电脑IP:5000/run`

查看电脑 IP：终端输入 `ipconfig`，找 `无线局域网适配器 WLAN` 下的 `IPv4 地址`。

## License

MIT
