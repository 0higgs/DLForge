from __future__ import annotations

import re
from urllib.parse import urlsplit


# Platform share text commonly wraps links in Chinese copywriting and punctuation.
# Stop before whitespace, quotes, CJK text, or common full-width separators, then
# defensively trim ASCII punctuation that may close a sentence or Markdown link.
_HTTP_URL = re.compile(
    r"https?://[^\s<>\"'“”‘’\u3000-\u303f\u3400-\u9fff\uff01-\uff65]+",
    re.IGNORECASE,
)
_TRAILING_PUNCTUATION = ".,;:!?)]}"


def extract_first_url(text: str | None) -> str | None:
    """Return the first valid HTTP(S) URL embedded in arbitrary share text."""
    if not text:
        return None

    normalized = text.replace("\u200b", "").replace("\ufeff", "")
    for match in _HTTP_URL.finditer(normalized):
        candidate = match.group(0).rstrip(_TRAILING_PUNCTUATION)
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            continue
        if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
            return candidate
    return None

