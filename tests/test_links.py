import unittest

from dlforge.links import extract_first_url


class LinkExtractionTests(unittest.TestCase):
    def test_plain_url_is_preserved(self):
        self.assertEqual(
            extract_first_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )

    def test_bilibili_share_copy_ignores_description(self):
        text = "【开学大三的疯了？！】 https://b23.tv/QnVw3PQ 复制本条消息，打开哔哩哔哩"
        self.assertEqual(extract_first_url(text), "https://b23.tv/QnVw3PQ")

    def test_douyin_style_copy_ignores_leading_and_trailing_text(self):
        text = "8.88 复制打开抖音，看看这个视频 https://v.douyin.com/AbC123/ 10/12 X@x.ab"
        self.assertEqual(extract_first_url(text), "https://v.douyin.com/AbC123/")

    def test_chinese_punctuation_and_zero_width_characters_are_removed(self):
        text = "推荐：https://example.com/video?id=7&part=2。\u200b请查收"
        self.assertEqual(extract_first_url(text), "https://example.com/video?id=7&part=2")

    def test_first_http_url_wins_when_text_contains_multiple_links(self):
        text = "视频：https://example.com/video/1 主页：https://example.com/u/2"
        self.assertEqual(extract_first_url(text), "https://example.com/video/1")

    def test_non_web_text_is_rejected(self):
        self.assertIsNone(extract_first_url("复制这段文字打开应用，没有网址"))
        self.assertIsNone(extract_first_url("ftp://example.com/video.mp4"))


if __name__ == "__main__":
    unittest.main()

