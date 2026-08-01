# FFmpeg source and redistribution material

DLForge 0.5.0 invokes `ffmpeg.exe` and `ffprobe.exe` as separate programs. The
offline installer redistributes the unmodified 64-bit static **Gyan.dev release
essentials 8.1.2** build, which reports **GNU GPL version 3 or later**.

## Exact binary identification

- Gyan release: <https://github.com/GyanD/codexffmpeg/releases/tag/8.1.2>
- Upstream archive: `ffmpeg-8.1.2-essentials_build.zip`
- Archive SHA-256: `db580001caa24ac104c8cb856cd113a87b0a443f7bdf47d8c12b1d740584a2ec`
- `ffmpeg.exe` SHA-256: `1326dde4c84ff1f96fe6b8916c5bed29e163e9b5dccf995f6f3db069d143ec5e`
- `ffprobe.exe` SHA-256: `b49ccc7c6547b141ad5a2f6ec69cc04323d7133d7704d70b331b904c63eecb07`
- FFmpeg revision: `38b88335f99e76ed89ff3c93f877fdefce736c13`

The exact configure line, enabled components, external-library inventory and
external-library versions copied from the original binary package are retained
verbatim in [`licenses/FFmpeg-Gyan-8.1.2-README.txt`](../licenses/FFmpeg-Gyan-8.1.2-README.txt).
The applicable license is in [`licenses/FFmpeg-GPL-3.0.txt`](../licenses/FFmpeg-GPL-3.0.txt).

## Source release asset

The DLForge v0.5.0 Release publishes
`DLForge-0.5.0-FFmpeg-source-38b88335f9.zip` beside the Windows installer. It
contains the FFmpeg source tree at the exact revision above, the GPLv3 text,
the original Gyan build manifest, and this identification document.

Recreate that asset with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_ffmpeg_source.ps1
```

This material documents the binary shipped by DLForge; it does not change or
relicense FFmpeg or any external library. FFmpeg and every external component
retain their respective copyright and license terms. This document is a
distribution record, not legal advice.
