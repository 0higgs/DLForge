import unittest
from types import SimpleNamespace
from unittest import mock

from dlforge.app import DLForgeApp


class _Toggle:
    def __init__(self, value=True):
        self.value = value

    def get(self):
        return self.value


class ClipboardPollingTests(unittest.TestCase):
    def make_app(self, clipboard_text: str):
        return SimpleNamespace(
            clipboard_monitor_var=_Toggle(True),
            _clipboard_job="previous-job",
            _pending_clipboard_url=None,
            _parsing=False,
            _running=False,
            _last_clipboard_text=None,
            _last_auto_url=None,
            clipboard_get=mock.Mock(return_value=clipboard_text),
            _accept_clipboard_url=mock.Mock(),
            _poll_clipboard=mock.Mock(),
            after=mock.Mock(return_value="next-job"),
        )

    def test_new_share_text_is_automatically_accepted(self):
        app = self.make_app("标题和简介 https://b23.tv/QnVw3PQ 复制打开哔哩哔哩")

        DLForgeApp._poll_clipboard(app)

        app._accept_clipboard_url.assert_called_once_with("https://b23.tv/QnVw3PQ")
        self.assertEqual(app._last_clipboard_text, app.clipboard_get.return_value)
        self.assertEqual(app._clipboard_job, "next-job")
        app.after.assert_called_once_with(600, app._poll_clipboard)

    def test_link_is_queued_while_an_inspection_is_running(self):
        app = self.make_app("https://www.youtube.com/watch?v=123")
        app._parsing = True

        DLForgeApp._poll_clipboard(app)

        app._accept_clipboard_url.assert_not_called()
        self.assertEqual(app._pending_clipboard_url, "https://www.youtube.com/watch?v=123")

    def test_queued_link_is_processed_after_app_becomes_idle(self):
        app = self.make_app("")
        app._pending_clipboard_url = "https://v.douyin.com/AbC123/"

        DLForgeApp._poll_clipboard(app)

        app._accept_clipboard_url.assert_called_once_with("https://v.douyin.com/AbC123/")
        self.assertIsNone(app._pending_clipboard_url)


if __name__ == "__main__":
    unittest.main()

