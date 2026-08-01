$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$releaseDir = Join-Path $projectRoot "release"
$revision = "38b88335f99e76ed89ff3c93f877fdefce736c13"
$revisionShort = $revision.Substring(0, 10)
$sourceUrl = "https://github.com/FFmpeg/FFmpeg/archive/$revision.zip"
$sourceArchiveSha256 = "c3453fbfc7ca25423f4984a83ceda01949d458a8bc04f9d68fab7c392f75b3ab"
$assetName = "DLForge-0.5.0-FFmpeg-source-$revisionShort.zip"
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("dlforge-ffmpeg-source-" + [guid]::NewGuid().ToString("N"))

New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

try {
    $download = Join-Path $tempRoot "ffmpeg-source.zip"
    & curl.exe -fL --retry 3 --connect-timeout 20 $sourceUrl -o $download
    if ($LASTEXITCODE -ne 0) { throw "Failed to download FFmpeg source revision $revision." }
    $actualHash = (Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $sourceArchiveSha256) {
        throw "FFmpeg source SHA-256 mismatch. Expected $sourceArchiveSha256, got $actualHash."
    }

    $expanded = Join-Path $tempRoot "expanded"
    Expand-Archive -LiteralPath $download -DestinationPath $expanded -Force
    $sourceRoot = Get-ChildItem -LiteralPath $expanded -Directory | Select-Object -First 1
    if (-not $sourceRoot) { throw "Downloaded FFmpeg source archive is empty." }

    $packageRoot = Join-Path $tempRoot "DLForge-0.5.0-FFmpeg-source-$revisionShort"
    Move-Item -LiteralPath $sourceRoot.FullName -Destination $packageRoot
    $distributionInfo = Join-Path $packageRoot "DLForge-distribution-info"
    New-Item -ItemType Directory -Force -Path $distributionInfo | Out-Null
    Copy-Item -LiteralPath (Join-Path $projectRoot "licenses\FFmpeg-GPL-3.0.txt") -Destination $distributionInfo
    Copy-Item -LiteralPath (Join-Path $projectRoot "licenses\FFmpeg-Gyan-8.1.2-README.txt") -Destination $distributionInfo
    Copy-Item -LiteralPath (Join-Path $projectRoot "docs\FFMPEG_SOURCE.md") -Destination $distributionInfo

    $asset = Join-Path $releaseDir $assetName
    if (Test-Path -LiteralPath $asset) { Remove-Item -LiteralPath $asset -Force }
    Compress-Archive -LiteralPath $packageRoot -DestinationPath $asset -CompressionLevel Optimal
    $assetHash = (Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath ($asset + ".sha256") -Value "$assetHash  $assetName" -Encoding ascii
    Write-Host "FFmpeg source asset ready: $asset"
    Write-Host "SHA256: $assetHash"
}
finally {
    $resolvedTemp = [System.IO.Path]::GetFullPath($tempRoot)
    $resolvedSystemTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
    if ($resolvedTemp.StartsWith($resolvedSystemTemp + '\', [System.StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $resolvedTemp)) {
        Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
    }
}
