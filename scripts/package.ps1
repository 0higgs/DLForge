$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$publishDir = Join-Path $projectRoot "dist\DLForge"
$releaseDir = Join-Path $projectRoot "release"
$archive = Join-Path $releaseDir "DLForge-0.5.0-win64.zip"

if (-not (Test-Path -LiteralPath (Join-Path $publishDir "DLForge.exe"))) {
    throw "Missing dist/DLForge/DLForge.exe. Run scripts/build.ps1 first."
}

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination $publishDir -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "THIRD_PARTY_NOTICES.txt") -Destination $publishDir -Force
if (Test-Path -LiteralPath $archive) { Remove-Item -LiteralPath $archive -Force }
Compress-Archive -LiteralPath $publishDir -DestinationPath $archive -CompressionLevel Optimal
$hash = Get-FileHash -LiteralPath $archive -Algorithm SHA256
$hashLine = "$($hash.Hash.ToLowerInvariant())  $([System.IO.Path]::GetFileName($archive))"
Set-Content -LiteralPath ($archive + ".sha256") -Value $hashLine -Encoding ascii
Write-Host "Release archive: $archive"
Write-Host "SHA256: $($hash.Hash.ToLowerInvariant())"
