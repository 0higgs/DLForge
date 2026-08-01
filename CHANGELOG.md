# Changelog

## v0.5.0 - 2026-08-02

- Added a distinctive purple-blue download/anvil/media icon across the app,
  executable, installer UI, shortcuts, and uninstall entry.
- Added a guided Windows installer with Start menu and optional desktop shortcuts.
- Added a fully offline installer containing yt-dlp, FFmpeg, and ffprobe.
- Kept all media tools private to DLForge, without requiring Python or changing PATH.
- Added complete uninstall cleanup for installer-managed tools.
- Pinned yt-dlp and FFmpeg downloads with SHA-256 verification.
- Added the GPLv3 text, the original Gyan build manifest, exact binary hashes,
  and an exact-revision FFmpeg source bundle for the binary Release.

## v0.4.0 - 2026-08-02

- Reworked the interface so the primary download controls remain visible.
- Added explicit single-video and playlist download scopes.
- Improved playlist parsing, item selection, and mouse-wheel scrolling.
- Made cancellation terminate the complete yt-dlp/FFmpeg process tree.
- Added frozen-app dependency discovery without requiring Python on end-user systems.
- Added reproducible Windows build and packaging scripts.

The v0.5.0 GitHub Release publishes the offline Windows installer, its SHA-256
file, and the exact-revision FFmpeg source bundle together.
