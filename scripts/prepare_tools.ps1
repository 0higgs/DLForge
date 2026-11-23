$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsDir = Join-Path $projectRoot "tools"
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("dlforge-tools-" + [guid]::NewGuid().ToString("N"))
$ytDlpVersion = "2026.10.26"
$ytDlpSha256 = "f5389d3698ecde4ef06f4e6b1ce0294fe9ac1396228c8990b8d3416d6d177a7d"
$denoVersion = "v2.9.8"
$denoArchiveSha256 = "cba84b26e0df5ae7f74fc66b86a95b866872a86292ebd84fa1e959927edd93bf"
$ffmpegVersion = "8.1.2"
$ffmpegArchiveSha256 = "db580001caa24ac104c8cb856cd113a87b0a443f7bdf47d8c12b1d740584a2ec"
$ffmpegExeSha256 = "1326dde4c84ff1f96fe6b8916c5bed29e163e9b5dccf995f6f3db069d143ec5e"
$ffprobeExeSha256 = "b49ccc7c6547b141ad5a2f6ec69cc04323d7133d7704d70b331b904c63eecb07"
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

function Assert-Sha256([string]$Path, [string]$Expected) {
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected) {
        throw "SHA-256 mismatch for $Path. Expected $Expected, got $actual."
    }
}

try {
    $ytDlpTarget = Join-Path $toolsDir "yt-dlp.exe"
    & curl.exe -fL --retry 3 --connect-timeout 20 "https://github.com/yt-dlp/yt-dlp/releases/download/$ytDlpVersion/yt-dlp.exe" -o $ytDlpTarget
    if ($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $ytDlpTarget).Length -lt 1MB) {
        throw "Failed to download the standalone yt-dlp executable."
    }
    Assert-Sha256 $ytDlpTarget $ytDlpSha256
    $denoArchive = Join-Path $tempDir "deno.zip"
    & curl.exe -fL --retry 3 --connect-timeout 20 "https://github.com/denoland/deno/releases/download/$denoVersion/deno-x86_64-pc-windows-msvc.zip" -o $denoArchive
    if ($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $denoArchive).Length -lt 1MB) {
        throw "Failed to download the Deno archive."
    }
    Assert-Sha256 $denoArchive $denoArchiveSha256
    $denoExtract = Join-Path $tempDir "deno"
    Expand-Archive -LiteralPath $denoArchive -DestinationPath $denoExtract -Force
    $deno = Join-Path $denoExtract "deno.exe"
    if (-not (Test-Path -LiteralPath $deno)) { throw "Deno archive does not contain deno.exe." }
    Copy-Item -LiteralPath $deno -Destination (Join-Path $toolsDir "deno.exe") -Force
    $archive = Join-Path $tempDir "ffmpeg.zip"
    & curl.exe -fL --retry 3 --connect-timeout 20 "https://github.com/GyanD/codexffmpeg/releases/download/$ffmpegVersion/ffmpeg-$ffmpegVersion-essentials_build.zip" -o $archive
    if ($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $archive).Length -lt 1MB) {
        throw "Failed to download the FFmpeg archive."
    }
    Assert-Sha256 $archive $ffmpegArchiveSha256
    Expand-Archive -LiteralPath $archive -DestinationPath $tempDir -Force
    $ffmpeg = Get-ChildItem -Path $tempDir -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
    $ffprobe = Get-ChildItem -Path $tempDir -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
    if (-not $ffmpeg -or -not $ffprobe) { throw "FFmpeg archive does not contain ffmpeg.exe and ffprobe.exe." }
    Copy-Item -LiteralPath $ffmpeg.FullName -Destination (Join-Path $toolsDir "ffmpeg.exe") -Force
    Copy-Item -LiteralPath $ffprobe.FullName -Destination (Join-Path $toolsDir "ffprobe.exe") -Force
    Assert-Sha256 (Join-Path $toolsDir "ffmpeg.exe") $ffmpegExeSha256
    Assert-Sha256 (Join-Path $toolsDir "ffprobe.exe") $ffprobeExeSha256
    Write-Host "Prepared yt-dlp, Deno, ffmpeg and ffprobe in $toolsDir"
}
finally {
    if (Test-Path -LiteralPath $tempDir) { Remove-Item -LiteralPath $tempDir -Recurse -Force }
}
