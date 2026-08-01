import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dlforge.engine import DownloadEngine, DownloadOptions, tool_path


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


if __name__ == "__main__":
    unittest.main()
