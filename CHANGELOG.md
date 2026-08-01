# Changelog

## v0.5.0 - 2026-08-02

- Added a guided Windows installer with Start menu and optional desktop shortcuts.
- Added a fully offline installer containing yt-dlp, FFmpeg, and ffprobe.
- Kept all media tools private to DLForge, without requiring Python or changing PATH.
- Added complete uninstall cleanup for installer-managed tools.

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
