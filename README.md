# DLForge

> 现代化 Windows 视频下载器，基于 yt-dlp 与 FFmpeg。

DLForge 是一个面向 Windows 的 yt-dlp 图形界面。发布包会携带 Python 运行时、`yt-dlp`、`ffmpeg` 和 `ffprobe`，目标电脑无需预装 Python 或任何媒体工具。发布版只使用包内组件，不会回退调用用户环境里的 Python 或 yt-dlp。

## 本地运行

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_tools.ps1
python .\app.py
```

## 构建发布目录

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

产物位于 `dist\DLForge\DLForge.exe`。建议发布整个 `dist\DLForge` 目录；下一阶段可再用 Inno Setup 将它制作成带卸载程序和开始菜单快捷方式的安装包。

> 请勿运行 PyInstaller 临时 `build` 目录中的 EXE。构建脚本会在成功后自动清理该目录，用户应解压发布 ZIP 并运行其中 `DLForge\DLForge.exe`。

生成单个 ZIP 发布文件和 SHA-256 校验文件：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package.ps1
```

发布文件位于 `release` 目录。公开分发前，请同时满足 `THIRD_PARTY_NOTICES.txt` 中列出的第三方许可证要求。

## 当前功能

- 链接元数据解析
- 单视频、合集和分集列表展示，可多选列表项目下载
- 现代深色卡片界面、视频封面、平滑进度和状态提示动效
- 固定下载操作栏与左右工作台布局，核心功能始终可见
- 明确的“仅当前 / 已选分集 / 全部列表”下载范围
- 针对 Windows 鼠标与触控板优化的分区高速滚动
- 最佳画质、1080p、720p 与 MP3 预设
- “仅当前 / 已选分集 / 全部列表”下载范围
- 中英文字幕下载
- 进度、速度、剩余时间和任务日志
- 取消任务、打开保存目录
- Windows 下取消时终止 yt-dlp 与 FFmpeg 整个进程树

请只下载你有权保存的内容，并遵守目标网站服务条款及所在地法律。

## 仓库与二进制说明

本仓库只保存 DLForge 源码、测试和构建脚本，不提交 `yt-dlp.exe`、`ffmpeg.exe`、`ffprobe.exe` 或构建产物。运行 `scripts/prepare_tools.ps1` 会从各项目的公开发布地址准备本地构建所需工具。

当前 FFmpeg 来源为 Gyan.dev 的 release essentials 静态构建，该构建启用了 GPLv3。公开分发包含该构建的 Windows 压缩包时，发布者必须同时满足 GPLv3 对许可文本和对应源码的要求。DLForge 仓库的 MIT 许可不会取代任何第三方许可证。

## License

DLForge 自有源码采用 [MIT License](LICENSE)。第三方组件保留各自许可证，详见 [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt)。
