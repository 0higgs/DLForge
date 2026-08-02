import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dlforge.engine import DownloadEngine, DownloadOptions, decode_subprocess_output, tool_path


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.engine = DownloadEngine(self.events.append)

    def test_selected_playlist_items_are_passed_to_ytdlp(self):
        with mock.patch("dlforge.engine.tool_path", side_effect=lambda name: f"C:/tools/{name}.exe"):
            command = self.engine._build_command(
                DownloadOptions("https://example.com/list", Path("out"), "720", True, False, (2, 5, 9))
            )
        position = command.index("--playlist-items")
        self.assertEqual(command[position + 1], "2,5,9")

    def test_frozen_app_never_falls_back_to_system_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch.object(sys, "frozen", True, create=True),
                mock.patch("dlforge.engine.app_root", return_value=Path(directory)),
                mock.patch("dlforge.engine.shutil.which", return_value="C:/Python/Scripts/yt-dlp.exe"),
            ):
                with self.assertRaises(FileNotFoundError):
                    tool_path("yt-dlp")

    def test_frozen_app_finds_installer_managed_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            install_root = Path(directory)
            tools = install_root / "tools"
            tools.mkdir()
            executable = tools / "yt-dlp.exe"
            executable.touch()
            with (
                mock.patch.object(sys, "frozen", True, create=True),
                mock.patch.object(sys, "executable", str(install_root / "DLForge.exe")),
                mock.patch("dlforge.engine.app_root", return_value=install_root / "_internal"),
            ):
                self.assertTrue(os.path.samefile(tool_path("yt-dlp"), executable))

    @unittest.skipUnless(sys.platform == "win32", "Windows process-tree behavior")
    def test_cancel_terminates_the_whole_process_tree(self):
        process = mock.Mock(pid=43210)
        process.poll.return_value = None
        self.engine._process = process
        with mock.patch("dlforge.engine.subprocess.run") as run:
            self.engine.cancel()
        args = run.call_args.args[0]
        self.assertEqual(args, ["taskkill.exe", "/PID", "43210", "/T", "/F"])
        self.assertTrue(self.engine._cancel_requested)

    def test_bilibili_api_enriches_playlist_metadata(self):
        response = {
            "code": 0,
            "data": {
                "title": "课程",
                "duration": 180,
                "pic": "https://example.com/cover.jpg",
                "owner": {"name": "作者"},
                "pages": [
                    {"page": 1, "part": "第一讲", "duration": 80},
                    {"page": 2, "part": "第二讲", "duration": 100},
                ],
            },
        }
        context = mock.MagicMock()
        context.__enter__.return_value = mock.Mock()
        context.__enter__.return_value.read.return_value = json.dumps(response).encode("utf-8")
        with mock.patch("dlforge.engine.urllib.request.urlopen", return_value=context):
            metadata = self.engine._bilibili_metadata("https://www.bilibili.com/video/BV1AB411C7DE")
        self.assertEqual(metadata["uploader"], "作者")
        self.assertEqual(metadata["entries"][1]["title"], "第二讲")

    def test_windows_gbk_output_preserves_chinese_filename(self):
        message = "已保存：26年9月计算机三级网络技术.mp4"
        self.assertEqual(decode_subprocess_output(message.encode("gb18030")), message)

    def test_file_event_tracks_playlist_index(self):
        self.engine._parse_line("DLFORGE_FILE:21|D:/视频/第二十一集.mp4")
        self.assertEqual(self.events[-1]["item_index"], 21)
        self.assertEqual(self.events[-1]["path"], "D:/视频/第二十一集.mp4")
        self.assertEqual(self.engine._completed_items, {21})

    def test_command_prints_playlist_index_with_saved_file(self):
        with mock.patch("dlforge.engine.tool_path", side_effect=lambda name: f"C:/tools/{name}.exe"):
            command = self.engine._build_command(
                DownloadOptions("https://example.com/list", Path("out"), "best", True)
            )
        print_template = command[command.index("--print") + 1]
        self.assertIn("%(playlist_index|)s", print_template)

    def test_progress_reports_current_item_and_overall_playlist_progress(self):
        self.engine._expected_items = (2, 5, 9)
        self.engine._completed_items = {2}
        self.engine._parse_line("DLFORGE_PROGRESS:5| 50.0%|2.0MiB/s|00:12")
        event = self.events[-1]
        self.assertEqual(event["item_index"], 5)
        self.assertEqual(event["item_percent"], 50.0)
        self.assertAlmostEqual(event["percent"], 50.0)
        self.assertEqual(event["completed"], 1)
        self.assertEqual(event["total"], 3)


if __name__ == "__main__":
    unittest.main()
