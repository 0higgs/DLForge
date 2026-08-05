# GitHub Topics & Promotion Guide

> How to get DLForge discovered — actions you can take right now.

## 1. GitHub Topics (add at repo page → ⚙️ → Topics)

```
yt-dlp
yt-dlp-gui
video-downloader
ffmpeg
youtube-downloader
bilibili
windows
python
customtkinter
dark-theme
media-downloader
playlist-downloader
offline-installer
desktop-app
```

## 2. Community Promotion Checklist

### Reddit
- [ ] Post to **r/youtubedl** — "I built a native Windows GUI for yt-dlp (no Python required)"
- [ ] Post to **r/software** — weekend showcase
- [ ] Post to **r/Python** — show & tell (mention the architecture)
- [ ] Post to **r/foss** — free & open-source Windows app

### GitHub
- [ ] PR to **awesome-yt-dlp** lists
- [ ] PR to **awesome-video** lists
- [ ] Comment on yt-dlp Discussions → "Show & Tell" thread

### Chinese Community
- [ ] V2EX → 创造分享节点
- [ ] 少数派 → 投稿
- [ ] 小众软件 → 自荐
- [ ] B站 → 演示视频

### Other
- [ ] Hacker News → "Show HN" (must lead with English content)
- [ ] Twitter/X → short demo clip
- [ ] AlternativeTo → list DLForge as a yt-dlp GUI alternative

## 3. Screenshot Specs

Place screenshots in `screenshots/`:

```
screenshots/
├── main.png          # Full app window (1180×800)
├── parsing.png       # After URL inspection with playlist loaded
├── downloading.png   # Mid-download with progress bars
└── demo.gif          # 10-15 sec: paste → parse → download → complete
```

Replace the placeholder in `README.md`:
```markdown
<p align="center">
  <img src="screenshots/main.png" alt="DLForge Main Screen" width="800">
</p>
```

## 4. Release Notes Template

Every GitHub Release should include:
- What's new in this version (from `CHANGELOG.md`)
- SHA-256 hashes for all downloadable files
- Installer + Portable ZIP download links
- FFmpeg source bundle link (GPL compliance)
- `THIRD_PARTY_NOTICES.txt` link

## 5. SEO Keywords (for README and repo description)

Make sure these appear naturally in your README:
- "yt-dlp GUI Windows"
- "video downloader Windows 10 11"
- "Bilibili playlist downloader"
- "yt-dlp frontend native Windows"
- "ffmpeg video converter GUI"
- "YouTube playlist download app"
- "offline video downloader Windows"
