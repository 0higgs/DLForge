# Changelog

## v0.5.1 - 2026-08-02

- Added separate live progress bars for the current episode and the complete task.
- Added current episode number, per-episode percentage, completed episode count,
  overall percentage, speed, and per-episode ETA to the task area.
- Fixed garbled Chinese titles and saved paths in logs by detecting UTF-8 and
  localized Windows subprocess output instead of forcing UTF-8 replacement.
- Changed playlist exit handling to report partial success accurately, such as
  `59/60 episodes completed`, instead of marking every saved file as failed.
- Added one-click retry for failed playlist episodes. Failed entries are selected
  automatically and the primary action changes to a retry button.
- Cleared the previous task log when a new download begins so cancelled and restarted
  jobs are no longer presented as one continuous task.
- Added regression tests for Windows Chinese output, playlist item tracking, saved
  file events, and combined episode/overall progress calculations.

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

The GitHub Release publishes the offline Windows installer, its SHA-256
file, and the exact-revision FFmpeg source bundle together.
