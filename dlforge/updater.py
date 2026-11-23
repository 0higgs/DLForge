from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from .engine import subprocess_environment, tool_path


RELEASE_API = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
OFFICIAL_DOWNLOAD_PREFIX = "https://github.com/yt-dlp/yt-dlp/releases/download/"
USER_AGENT = "DLForge yt-dlp updater (+https://github.com/0higgs/DLForge)"
MAX_CHECKSUM_BYTES = 256 * 1024
MAX_EXECUTABLE_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True)
class YtDlpRelease:
    version: str
    executable_url: str
    checksums_url: str


def version_key(version: str) -> tuple[int, ...]:
    """Return a comparable key for yt-dlp's date-based release versions."""
    normalized = version.strip().removeprefix("stable@").lstrip("v")
    parts = re.fullmatch(r"(\d{4})\.(\d{1,2})\.(\d{1,2})(?:\.(\d+))?", normalized)
    if not parts:
        raise ValueError(f"无法识别 yt-dlp 版本号：{version}")
    return tuple(int(part) for part in parts.groups() if part is not None)


def is_newer_version(latest: str, current: str) -> bool:
    return version_key(latest) > version_key(current)


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def _open(opener: Callable | None, request: urllib.request.Request, timeout: float):
    return (opener or urllib.request.urlopen)(request, timeout=timeout)


def _read_limited(response, limit: int) -> bytes:
    length = response.headers.get("Content-Length")
    if length and int(length) > limit:
        raise RuntimeError("更新服务器返回的文件大小异常。")
    data = response.read(limit + 1)
    if len(data) > limit:
        raise RuntimeError("更新服务器返回的文件超过安全大小限制。")
    return data


def fetch_latest_release(opener: Callable | None = None) -> YtDlpRelease:
    with _open(opener, _request(RELEASE_API), 12) as response:
        payload = json.loads(_read_limited(response, 2 * 1024 * 1024).decode("utf-8"))

    if payload.get("draft") or payload.get("prerelease"):
        raise RuntimeError("yt-dlp 最新版本不是稳定正式版。")
    version = str(payload.get("tag_name") or "").strip().lstrip("v")
    version_key(version)

    assets = {
        str(asset.get("name")): str(asset.get("browser_download_url") or "")
        for asset in payload.get("assets") or []
    }
    executable_url = assets.get("yt-dlp.exe", "")
    checksums_url = assets.get("SHA2-256SUMS", "")
    expected_prefix = f"{OFFICIAL_DOWNLOAD_PREFIX}{version}/"
    if not executable_url.startswith(expected_prefix) or not checksums_url.startswith(expected_prefix):
        raise RuntimeError("yt-dlp 官方 Release 缺少可信的 Windows 更新文件。")
    if urlparse(executable_url).scheme != "https" or urlparse(checksums_url).scheme != "https":
        raise RuntimeError("yt-dlp 更新地址不是安全的 HTTPS 地址。")
    return YtDlpRelease(version, executable_url, checksums_url)


def read_ytdlp_version(executable: str | Path) -> str:
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    result = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        creationflags=creationflags,
        env=subprocess_environment(),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("无法读取当前 yt-dlp 核心版本。")
    version = result.stdout.strip().splitlines()[0]
    version_key(version)
    return version


def parse_executable_checksum(text: str) -> str:
    for line in text.splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?yt-dlp\.exe", line.strip())
        if match:
            return match.group(1).lower()
    raise RuntimeError("官方校验文件中没有 yt-dlp.exe 的 SHA-256。")


def _download_to_file(url: str, destination: Path, opener: Callable | None = None) -> str:
    digest = hashlib.sha256()
    total = 0
    with _open(opener, _request(url), 45) as response, destination.open("wb") as output:
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_EXECUTABLE_BYTES:
            raise RuntimeError("yt-dlp 更新文件大小异常。")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_EXECUTABLE_BYTES:
                raise RuntimeError("yt-dlp 更新文件超过安全大小限制。")
            output.write(chunk)
            digest.update(chunk)
        output.flush()
        os.fsync(output.fileno())
    if total < 1024 * 1024:
        raise RuntimeError("下载的 yt-dlp 更新文件不完整。")
    return digest.hexdigest()


def install_release(
    release: YtDlpRelease,
    target: str | Path,
    opener: Callable | None = None,
    version_reader: Callable[[str | Path], str] = read_ytdlp_version,
) -> str:
    """Download, verify, self-test, and atomically replace yt-dlp.exe."""
    target_path = Path(target).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with _open(opener, _request(release.checksums_url), 20) as response:
        checksum_text = _read_limited(response, MAX_CHECKSUM_BYTES).decode("utf-8")
    expected_sha256 = parse_executable_checksum(checksum_text)

    handle, staged_name = tempfile.mkstemp(
        prefix=".yt-dlp-update-",
        suffix=".exe",
        dir=target_path.parent,
    )
    os.close(handle)
    staged = Path(staged_name)
    try:
        actual_sha256 = _download_to_file(release.executable_url, staged, opener)
        if actual_sha256 != expected_sha256:
            raise RuntimeError("yt-dlp 更新文件 SHA-256 校验失败，已保留原核心。")
        downloaded_version = version_reader(staged)
        if version_key(downloaded_version) != version_key(release.version):
            raise RuntimeError("下载的 yt-dlp 核心版本与官方 Release 不一致。")
        os.replace(staged, target_path)
        return downloaded_version
    finally:
        if staged.exists():
            staged.unlink()


class YtDlpUpdater:
    def __init__(self, emit: Callable[[dict], None]):
        self.emit = emit
        self._lock = threading.Lock()
        self._checking = False
        self._installing = False

    def check_async(self, manual: bool = False) -> bool:
        with self._lock:
            if self._checking or self._installing:
                return False
            self._checking = True
        threading.Thread(target=self._check_worker, args=(manual,), daemon=True).start()
        return True

    def _check_worker(self, manual: bool) -> None:
        try:
            executable = tool_path("yt-dlp")
            current = read_ytdlp_version(executable)
            release = fetch_latest_release()
            if is_newer_version(release.version, current):
                self.emit(
                    {
                        "type": "core_update_available",
                        "current": current,
                        "latest": release.version,
                        "release": release,
                    }
                )
            elif manual:
                self.emit({"type": "core_update_current", "version": current})
        except Exception as exc:
            if manual:
                self.emit({"type": "core_update_check_error", "message": str(exc)})
        finally:
            with self._lock:
                self._checking = False

    def install_async(self, release: YtDlpRelease) -> bool:
        with self._lock:
            if self._checking or self._installing:
                return False
            self._installing = True
        threading.Thread(target=self._install_worker, args=(release,), daemon=True).start()
        return True

    def _install_worker(self, release: YtDlpRelease) -> None:
        self.emit({"type": "core_update_started", "version": release.version})
        try:
            version = install_release(release, tool_path("yt-dlp"))
            self.emit({"type": "core_update_installed", "version": version})
        except Exception as exc:
            self.emit({"type": "core_update_error", "message": str(exc)})
        finally:
            with self._lock:
                self._installing = False

