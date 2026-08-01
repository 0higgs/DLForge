# Changelog

## v0.4.0 - 2026-08-02

- Reworked the interface so the primary download controls remain visible.
- Added explicit single-video and playlist download scopes.
- Improved playlist parsing, item selection, and mouse-wheel scrolling.
- Made cancellation terminate the complete yt-dlp/FFmpeg process tree.
- Added frozen-app dependency discovery without requiring Python on end-user systems.
- Added reproducible Windows build and packaging scripts.

This GitHub release is source-only. Windows packages that redistribute FFmpeg
must also satisfy the license and corresponding-source obligations documented in
`THIRD_PARTY_NOTICES.txt`.
