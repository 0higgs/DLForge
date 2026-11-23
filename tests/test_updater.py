import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dlforge.updater import (
    YtDlpRelease,
    fetch_latest_release,
    install_release,
    is_newer_version,
    parse_executable_checksum,
    version_key,
)


class _Response(io.BytesIO):
    def __init__(self, data: bytes):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def _queued_opener(*payloads: bytes):
    responses = iter(payloads)

    def open_request(_request, timeout=0):
        assert timeout > 0
        return _Response(next(responses))

    return open_request


class UpdaterTests(unittest.TestCase):
    def test_version_comparison_uses_release_date_components(self):
        self.assertEqual(version_key("stable@2026.07.04"), (2026, 7, 4))
        self.assertTrue(is_newer_version("2026.10.26", "2026.07.04"))
        self.assertFalse(is_newer_version("2026.07.04", "2026.07.04"))

    def test_latest_release_must_use_official_assets(self):
        payload = {
            "tag_name": "2026.10.26",
            "draft": False,
            "prerelease": False,
            "assets": [
                {
                    "name": "yt-dlp.exe",
                    "browser_download_url": "https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/yt-dlp.exe",
                },
                {
                    "name": "SHA2-256SUMS",
                    "browser_download_url": "https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/SHA2-256SUMS",
                },
            ],
        }
        release = fetch_latest_release(_queued_opener(json.dumps(payload).encode("utf-8")))
        self.assertEqual(release.version, "2026.10.26")

        payload["assets"][0]["browser_download_url"] = "https://example.com/yt-dlp.exe"
        with self.assertRaises(RuntimeError):
            fetch_latest_release(_queued_opener(json.dumps(payload).encode("utf-8")))

    def test_checksum_parser_selects_windows_executable(self):
        wanted = "a" * 64
        text = f"{'b' * 64}  yt-dlp\n{wanted}  yt-dlp.exe\n"
        self.assertEqual(parse_executable_checksum(text), wanted)

    def test_install_verifies_and_atomically_replaces_core(self):
        payload = b"MZ" + (b"x" * (1024 * 1024))
        checksum = hashlib.sha256(payload).hexdigest()
        release = YtDlpRelease(
            "2026.10.26",
            "https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/yt-dlp.exe",
            "https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/SHA2-256SUMS",
        )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "yt-dlp.exe"
            target.write_bytes(b"old-core")
            version = install_release(
                release,
                target,
                opener=_queued_opener(f"{checksum}  yt-dlp.exe\n".encode(), payload),
                version_reader=lambda _path: "2026.10.26",
            )
            self.assertEqual(version, "2026.10.26")
            self.assertEqual(target.read_bytes(), payload)
            self.assertFalse(list(target.parent.glob(".yt-dlp-update-*.exe")))

    def test_checksum_failure_keeps_existing_core(self):
        payload = b"MZ" + (b"x" * (1024 * 1024))
        release = YtDlpRelease(
            "2026.10.26",
            "https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/yt-dlp.exe",
            "https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/SHA2-256SUMS",
        )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "yt-dlp.exe"
            target.write_bytes(b"old-core")
            with self.assertRaises(RuntimeError):
                install_release(
                    release,
                    target,
                    opener=_queued_opener(f"{'0' * 64}  yt-dlp.exe\n".encode(), payload),
                    version_reader=lambda _path: "2026.10.26",
                )
            self.assertEqual(target.read_bytes(), b"old-core")


if __name__ == "__main__":
    unittest.main()

