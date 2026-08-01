from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


PROGRESS_PREFIX = "DLFORGE_PROGRESS:"
FILE_PREFIX = "DLFORGE_FILE:"


@dataclass(frozen=True)
class DownloadOptions:
    url: str
    output_dir: Path
    preset: str
    playlist: bool = False
    subtitles: bool = False
    playlist_items: tuple[int, ...] = ()


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[1]


def tool_path(name: str) -> str:
    suffix = ".exe" if os.name == "nt" else ""
    candidates = [app_root() / "tools" / f"{name}{suffix}"]
    if getattr(sys, "frozen", False):
        # The online installer keeps downloaded tools beside DLForge.exe instead
        # of embedding them in PyInstaller's private runtime directory.
        candidates.insert(0, Path(sys.executable).resolve().parent / "tools" / f"{name}{suffix}")
    for bundled in candidates:
        if bundled.exists():
            return str(bundled)
    if getattr(sys, "frozen", False):
        raise FileNotFoundError(f"发布包不完整：缺少内置组件 {name}{suffix}。请重新安装 DLForge。")
    found = shutil.which(name)
    if found:
        return found
    raise FileNotFoundError(f"找不到 {name}。请先运行 scripts/prepare_tools.ps1。")


def _startupinfo() -> subprocess.STARTUPINFO | None:
    if os.name != "nt":
        return None
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return info


class DownloadEngine:
    def __init__(self, emit: Callable[[dict], None]):
        self.emit = emit
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._cancel_requested = False

    def inspect(self, url: str) -> None:
        threading.Thread(target=self._inspect_worker, args=(url,), daemon=True).start()

    def _inspect_worker(self, url: str) -> None:
        self.emit({"type": "inspect_started"})
        try:
            command = [
                tool_path("yt-dlp"),
                "--dump-single-json",
                "--no-warnings",
                "--flat-playlist",
                url,
            ]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=_startupinfo(),
                timeout=45,
            )
            if result.returncode != 0:
                raise RuntimeError(self._last_error(result.stderr))
            data = json.loads(result.stdout)
            self.emit(self._metadata_event(data, url))
        except Exception as exc:
            self.emit({"type": "inspect_error", "message": f"链接解析失败：{exc}"})

    def download(self, options: DownloadOptions) -> None:
        with self._lock:
            self._cancel_requested = False
        threading.Thread(target=self._download_worker, args=(options,), daemon=True).start()

    def _download_worker(self, options: DownloadOptions) -> None:
        try:
            options.output_dir.mkdir(parents=True, exist_ok=True)
            command = self._build_command(options)
            self.emit({"type": "started", "command": command})
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                startupinfo=_startupinfo(),
                creationflags=creationflags,
            )
            with self._lock:
                self._process = process
                cancel_immediately = self._cancel_requested
            if cancel_immediately:
                self._terminate_process_tree(process)
            assert process.stdout is not None
            for raw_line in process.stdout:
                self._parse_line(raw_line.rstrip())
            return_code = process.wait()
            with self._lock:
                self._process = None
                cancelled = self._cancel_requested
            if cancelled:
                self.emit({"type": "cancelled"})
            elif return_code == 0:
                self.emit({"type": "finished"})
            else:
                self.emit({"type": "error", "message": f"下载失败（退出码 {return_code}），请查看任务日志。"})
        except Exception as exc:
            with self._lock:
                self._process = None
            self.emit({"type": "error", "message": str(exc)})

    def _build_command(self, options: DownloadOptions) -> list[str]:
        ffmpeg = tool_path("ffmpeg")
        command = [
            tool_path("yt-dlp"),
            "--newline",
            "--windows-filenames",
            "--no-color",
            "--progress",
            "--ffmpeg-location",
            str(Path(ffmpeg).parent),
            "--progress-template",
            f"download:{PROGRESS_PREFIX}%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s",
            "--print",
            f"after_move:{FILE_PREFIX}%(filepath)s",
            "--output",
            str(options.output_dir / "%(title).180B [%(id)s].%(ext)s"),
        ]
        presets = {
            "best": ["-f", "bv*+ba/b", "--merge-output-format", "mp4"],
            "1080": ["-f", "bv*[height<=1080]+ba/b[height<=1080]", "--merge-output-format", "mp4"],
            "720": ["-f", "bv*[height<=720]+ba/b[height<=720]", "--merge-output-format", "mp4"],
            "audio": ["-f", "ba/b", "-x", "--audio-format", "mp3", "--audio-quality", "0"],
        }
        command.extend(presets[options.preset])
        command.append("--yes-playlist" if options.playlist else "--no-playlist")
        if options.playlist and options.playlist_items:
            command.extend(["--playlist-items", ",".join(str(item) for item in options.playlist_items)])
        if options.subtitles:
            command.extend(["--write-subs", "--write-auto-subs", "--sub-langs", "zh.*,en.*", "--convert-subs", "srt"])
        command.append(options.url)
        return command

    def cancel(self) -> None:
        with self._lock:
            process = self._process
            self._cancel_requested = True
        if process and process.poll() is None:
            self.emit({"type": "cancelling"})
            self._terminate_process_tree(process)

    @staticmethod
    def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=_startupinfo(),
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
        else:
            process.terminate()

    def _metadata_event(self, data: dict, url: str) -> dict:
        entries = data.get("entries") or []
        is_playlist = data.get("_type") in {"playlist", "multi_video"} or bool(entries)
        event = {
            "type": "metadata",
            "title": data.get("title") or "未命名视频",
            "uploader": data.get("uploader") or data.get("channel") or "未知作者",
            "duration": data.get("duration"),
            "thumbnail": data.get("thumbnail"),
            "entries": [],
        }
        if not is_playlist:
            return event

        event["entries"] = [
            {
                "index": index,
                "title": entry.get("title") or f"第 {index} 项",
                "duration": entry.get("duration"),
                "url": entry.get("url") or entry.get("webpage_url"),
            }
            for index, entry in enumerate(entries, 1)
        ]
        bili = self._bilibili_metadata(url)
        if bili:
            event.update({key: value for key, value in bili.items() if key != "entries" and value is not None})
            if bili.get("entries"):
                event["entries"] = bili["entries"]
        elif entries:
            first = entries[0]
            event["uploader"] = event["uploader"] if event["uploader"] != "未知作者" else (first.get("uploader") or first.get("channel") or "未知作者")
        return event

    @staticmethod
    def _bilibili_metadata(url: str) -> dict | None:
        host = urllib.parse.urlparse(url).hostname or ""
        if host.lower() not in {"bilibili.com", "www.bilibili.com", "m.bilibili.com"}:
            return None
        match = re.search(r"/(BV[0-9A-Za-z]+)", url, re.IGNORECASE)
        if not match:
            return None
        endpoint = "https://api.bilibili.com/x/web-interface/view?" + urllib.parse.urlencode({"bvid": match.group(1)})
        request = urllib.request.Request(endpoint, headers={"User-Agent": "Mozilla/5.0 DLForge/0.2"})
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                payload = json.load(response)
            info = payload.get("data") if payload.get("code") == 0 else None
            if not info:
                return None
            pages = info.get("pages") or []
            return {
                "title": info.get("title"),
                "uploader": (info.get("owner") or {}).get("name"),
                "duration": info.get("duration"),
                "thumbnail": info.get("pic"),
                "entries": [
                    {
                        "index": page.get("page") or index,
                        "title": page.get("part") or f"第 {index} 集",
                        "duration": page.get("duration"),
                        "url": f"https://www.bilibili.com/video/{match.group(1)}?p={page.get('page') or index}",
                    }
                    for index, page in enumerate(pages, 1)
                ],
            }
        except (OSError, ValueError, json.JSONDecodeError):
            return None

    def _parse_line(self, line: str) -> None:
        if line.startswith(PROGRESS_PREFIX):
            fields = line[len(PROGRESS_PREFIX) :].split("|", 2)
            match = re.search(r"([\d.]+)%", fields[0])
            self.emit(
                {
                    "type": "progress",
                    "percent": float(match.group(1)) if match else 0.0,
                    "speed": fields[1].strip() if len(fields) > 1 else "",
                    "eta": fields[2].strip() if len(fields) > 2 else "",
                }
            )
        elif line.startswith(FILE_PREFIX):
            self.emit({"type": "file", "path": line[len(FILE_PREFIX) :]})
        elif line:
            self.emit({"type": "log", "message": line})

    @staticmethod
    def _last_error(stderr: str) -> str:
        lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        return lines[-1] if lines else "未知错误"
