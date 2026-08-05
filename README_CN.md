<p align="center">
  <img src="assets/dlforge-icon.png" alt="DLForge" width="128" height="128">
</p>

<h1 align="center">DLForge</h1>

<p align="center">
  <strong>现代化 Windows 视频下载器，基于 yt-dlp 与 FFmpeg</strong><br>
  支持 YouTube、Bilibili 等 1900+ 网站 — 播放列表、字幕下载、深色卡片界面
</p>

<p align="center">
  <a href="https://github.com/0higgs/DLForge/releases"><img src="https://img.shields.io/github/v/release/0higgs/DLForge?color=7C5CFC&label=Latest" alt="Latest Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-Windows%2010%2B-7C5CFC" alt="Platform: Windows"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-无需安装-brightgreen" alt="No Python needed"></a>
</p>

<br>

<p align="center">
  <img src="screenshots/screenshoot1.jpg" alt="DLForge 主界面" width="800">
</p>

<p align="center">
  <img src="screenshots/screenshoot2.jpg" alt="DLForge 下载进度" width="800">
</p>

---

## 为什么选 DLForge？

大多数 yt-dlp GUI 是网页套壳或 Electron 应用。DLForge 是一个**原生 Windows 应用**，基于 CustomTkinter 构建 — 轻量、无浏览器引擎，目标电脑**无需预装任何依赖**（无需 Python、无需 yt-dlp、无需 FFmpeg）。

| | 其他 GUI | DLForge |
|---|---|---|
| 💾 安装体积 | 150 MB+ (Electron) | ~80 MB |
| 🐍 需要 Python？ | 通常需要 | **不需要** — 开箱即用 |
| 🌙 深色模式 | 通常是 CSS 模拟 | **原生 Windows 深色主题** |
| 📋 播放列表体验 | 单一扁平列表 | **逐集勾选 + 失败重试** |
| 🎬 Bilibili | 通用标题 | **BV API → 准确分P名称** |
| 📦 离线安装器 | 少见 | **支持 (Inno Setup)** |

---

## 功能特性

- 🔗 **粘贴即解析** — 支持单视频、合集、播放列表
- ✅ **逐集选择** — 可下载当前、已选分集或全部列表
- 🎬 **Bilibili 增强** — 通过 B站 API 获取准确分P信息
- 📺 **画质预设** — 最佳 MP4、1080p、720p、MP3 音频
- 🇨🇳🇬🇧 **字幕下载** — 简体中文、繁体中文、英文（人工 + 自动字幕）
- 📊 **双进度条** — 当前分集进度 + 总任务进度
- 🔄 **失败重试** — 部分失败时自动选中失败分集，一键重试
- 📝 **实时日志** — 可滚动 yt-dlp 输出查看器
- ⚡ **进程树终止** — `taskkill /T /F` 彻底终止 yt-dlp 与 FFmpeg
- 📂 **一键打开目录** — 快速定位已下载文件
- 🎨 **深色卡片 UI** — #080C17 色板、18px 圆角卡片、流畅动画

---

## 快速开始

### 方式一：离线安装器（推荐）

从 [Releases](https://github.com/0higgs/DLForge/releases) 下载 `DLForge-*-Setup-offline.exe`，双击运行即可。安装包内置所有组件，安装过程无需联网。

安装器会将 yt-dlp、FFmpeg、ffprobe 安装到 DLForge 私有目录，不修改系统 `PATH`。

### 方式二：便携版 ZIP

从 [Releases](https://github.com/0higgs/DLForge/releases) 下载 `DLForge-*-win64.zip`，解压后运行 `DLForge\DLForge.exe`。

> ⚠️ 请勿直接运行 PyInstaller `build` 目录中的 EXE。始终使用 `dist\DLForge\` 目录下的文件。

### 方式三：从源码运行

```powershell
# 1. 安装依赖
python -m pip install -r requirements.txt

# 2. 下载固定版本的 yt-dlp、ffmpeg、ffprobe（带 SHA-256 校验）
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_tools.ps1

# 3. 启动
python .\app.py
```

需要 Python 3.12+ 和 Windows 10+。

---

## 构建

```powershell
# 构建 PyInstaller 发布目录 → dist\DLForge\DLForge.exe
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1

# 打包 ZIP + SHA-256 校验文件
powershell -ExecutionPolicy Bypass -File .\scripts\package.ps1

# 构建离线安装器（需要 Inno Setup 6.7+）
powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

构建后运行 `python app.py --self-test` 可验证 yt-dlp、ffmpeg、ffprobe 在发布包中是否正常工作。

---

## 架构

```
┌──────────────┐     ┌────────────────┐     ┌─────────────────┐
│  dlforge/app │────▶│ queue.Queue()  │────▶│  dlforge/engine │
│  (GUI/CTk)   │◀────│  80ms 轮询     │◀────│  (yt-dlp 子进程) │
└──────────────┘     └────────────────┘     └─────────────────┘
                                                  │
                    DLFORGE_PROGRESS:             │
                    DLFORGE_FILE:     ◀───────────┘
```

`dlforge/` 包内只有三层：
- **`engine.py`** — 下载引擎：启动 yt-dlp 子进程，解析 stdout，emit 事件
- **`app.py`** — GUI：CustomTkinter 深色卡片界面，通过 `queue.Queue` 事件驱动
- **`__init__.py`** — 版本号 `__version__`

所有工具（yt-dlp、ffmpeg、ffprobe）均通过 SHA-256 校验固定版本，frozen 模式下绝不回退到系统 PATH。

---

## 仓库说明

本仓库仅保存源码、测试和构建脚本。`yt-dlp.exe`、`ffmpeg.exe`、`ffprobe.exe` 及安装包不进入 Git 历史，通过 [GitHub Releases](https://github.com/0higgs/DLForge/releases) 发布。

当前 FFmpeg 来源为 Gyan.dev 的 release essentials 8.1.2 静态构建（GPLv3）。仓库保留 GPLv3 全文、Gyan 原包构建配置与外部库版本清单；每个 Release 均附带精确提交的 FFmpeg 源码包。详见 [FFmpeg 来源与再分发资料](docs/FFMPEG_SOURCE.md)。

---

## 常见问题

### 免费吗？
是的。DLForge 自有源码采用 [MIT License](LICENSE)。第三方组件（FFmpeg、yt-dlp 等）保留各自许可证，详见 [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt)。

### 支持 Mac / Linux 吗？
目前不支持。GUI 使用了 Windows 特化的 Tcl/Tk 打包方案。跨平台版本需要不同的 UI 框架（Android 移植版正在开发中）。

### 二进制文件在哪？
本仓库只含源码。预构建的发布包（含 yt-dlp + FFmpeg）在 [Releases](https://github.com/0higgs/DLForge/releases) 页面。本地开发运行 `scripts/prepare_tools.ps1` 即可下载固定版本的依赖工具。

### 使用合法吗？
DLForge 本身是下载工具。请只下载你有权保存的内容，并遵守目标网站的服务条款及所在地法律。

---

## Star 历史

如果你觉得 DLForge 有用，点个 ⭐ 能让更多人发现它！

[![Star History Chart](https://api.star-history.com/svg?repos=0higgs/DLForge&type=Date)](https://star-history.com/#0higgs/DLForge&Date)

---

<p align="center">
  <sub>English readers see <a href="README.md">README.md</a></sub>
</p>
