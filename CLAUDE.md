# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

DLForge 是面向 Windows 的 yt-dlp 图形界面视频下载器，使用 CustomTkinter 构建深色卡片 UI。发布包自带 Python 运行时、yt-dlp、ffmpeg 和 ffprobe，目标电脑无需预装任何依赖。

## 常用命令

```powershell
# 安装依赖
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

# 下载固定版本的 yt-dlp/ffmpeg/ffprobe（带 SHA-256 校验）
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_tools.ps1

# 运行
python .\app.py

# 运行测试
python -m unittest discover -s tests -v

# 运行单个测试
python -m unittest tests.test_engine.EngineTests.test_windows_gbk_output_preserves_chinese_filename -v

# 编译检查（CI 会执行）
python -m compileall -q app.py dlforge tests

# 构建发布目录（产物：dist\DLForge\DLForge.exe）
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1

# 打包 ZIP + SHA-256（产物：release/ 目录）
powershell -ExecutionPolicy Bypass -File .\scripts\package.ps1

# 构建 Inno Setup 离线安装器（需 Inno Setup 6.7+）
powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1

# 界面自检（无需网络）
python app.py --ui-self-test

# 发布包依赖自检
python app.py --self-test
```

## 架构

代码只有三层，全部在 `dlforge/` 包内：

- **engine.py** — 下载引擎，纯后端逻辑。`DownloadEngine` 接收 `emit` 回调，所有事件（metadata/progress/file/finished/error/cancelled/partial）通过字典 emit 给 UI。引擎在后台线程中运行 yt-dlp 子进程，通过 `--progress-template` 和 `--print after_move:` 两个自定义前缀（`DLFORGE_PROGRESS:` / `DLFORGE_FILE:`）解析 stdout 输出。`decode_subprocess_output` 处理 Windows 下 GBK/UTF-8 编码混合问题。
- **app.py** — `DLForgeApp(ctk.CTk)` 是完整的 GUI，通过 `queue.Queue` 接收引擎事件，`_drain_events` 以 80ms 轮询主线程消费。UI 由 `_build_*` 方法构建，颜色常量定义在文件顶部。
- **\_\_init\_\_.py** — 版本号 `__version__`。

入口文件是根目录的 **app.py**，它处理 `--self-test` / `--ui-self-test` 命令行参数，否则调用 `dlforge.app.main()`。

## 关键设计约束

- **工具路径**：`tool_path()` 在 frozen 模式（PyInstaller）下只从包内查找 yt-dlp/ffmpeg/ffprobe，绝不回退到系统 PATH；开发模式下可回退。
- **Bilibili 增强**：引擎对 bilibili.com 链接会额外调用 B站 API 获取更准确的分P信息（`_bilibili_metadata`）。
- **进程树终止**：Windows 下取消任务时使用 `taskkill /T /F` 终止 yt-dlp 和 FFmpeg 整个进程树。
- **发布包不含工具二进制**：yt-dlp/ffmpeg/ffprobe 通过 `scripts/prepare_tools.ps1` 下载固定版本到 `tools/`，不进入 git 历史。

## 版本号更新

版本号出现在以下位置，发版时需同步修改：
- `dlforge/__init__.py` 的 `__version__`
- `.github/workflows/release.yml` 中的产物路径
- `CHANGELOG.md`
