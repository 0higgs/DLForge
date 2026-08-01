$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsDir = Join-Path $projectRoot "tools"
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("dlforge-tools-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

try {
    $ytDlpTarget = Join-Path $toolsDir "yt-dlp.exe"
    & curl.exe -fL --retry 3 --connect-timeout 20 "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" -o $ytDlpTarget
    if ($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $ytDlpTarget).Length -lt 1MB) {
        throw "Failed to download the standalone yt-dlp executable."
    }
    $archive = Join-Path $tempDir "ffmpeg.zip"
    & curl.exe -fL --retry 3 --connect-timeout 20 "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -o $archive
    if ($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $archive).Length -lt 1MB) {
        throw "Failed to download the FFmpeg archive."
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $tempDir -Force
    $ffmpeg = Get-ChildItem -Path $tempDir -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
    $ffprobe = Get-ChildItem -Path $tempDir -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
    if (-not $ffmpeg -or -not $ffprobe) { throw "FFmpeg archive does not contain ffmpeg.exe and ffprobe.exe." }
    Copy-Item -LiteralPath $ffmpeg.FullName -Destination (Join-Path $toolsDir "ffmpeg.exe") -Force
    Copy-Item -LiteralPath $ffprobe.FullName -Destination (Join-Path $toolsDir "ffprobe.exe") -Force
    Write-Host "Prepared yt-dlp, ffmpeg and ffprobe in $toolsDir"
}
finally {
    if (Test-Path -LiteralPath $tempDir) { Remove-Item -LiteralPath $tempDir -Recurse -Force }
}
