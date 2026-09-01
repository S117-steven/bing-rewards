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

它会自动做 5 件事：
1. 创建 Python 虚拟环境
2. 安装需要的依赖包
3. **自动检测你的 Windows 用户名和 Edge 配置**，生成 `config.json`
4. 在桌面创建快捷方式

安装过程大约需要 1-2 分钟，看到 `Setup complete!` 就说明成功了。

**大部分情况下你不需要手动编辑 config.json**，setup.bat 会自动检测正确的路径。

## 第三步：检查配置（一般不需要改）

用记事本打开 `config.json`（在 `bing-rewards` 文件夹里），确认里面的路径是对的：

```json
{
  "python_exe": ".venv\\Scripts\\python.exe",
  "edge_user_data_path": "C:\\Users\\zhangsan\\AppData\\Local\\Microsoft\\Edge\\User Data",
  "edge_source_profile": "Profile 1",
  "search_count": 23
}
```

**只有以下情况需要手动改：**

1. **`edge_source_profile` 不对**：去 Edge 浏览器地址栏输入 `edge://version`，找到「个人资料路径」末尾的 `Profile 1` 或 `Profile 2`，改成对应的值
2. **`edge_user_data_path` 不对**：一般不需要改，除非你把 Edge 装在了非默认位置

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

每次运行的完整结果会保存在 `logs/runs/<运行时间>/`，其中 `summary.json` 会记录两个账号的搜索数量、Daily Set 发现/确认/剩余数量，以及关机命令是否发送。只有两个账号都通过页面完成校验时才会自动关机；如果任务状态无法读取、仍有待办或脚本返回失败，系统会跳过关机。

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
