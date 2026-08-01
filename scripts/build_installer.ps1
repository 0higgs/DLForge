param(
    [switch]$SkipAppBuild,
    [switch]$UseDefaultSetupIcon
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$installerScript = Join-Path $projectRoot "installer\DLForge.iss"
$isccCandidates = @(
    "D:\ProgramFiles\Inno Setup 7\ISCC.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 7\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 7\ISCC.exe",
    "C:\Program Files\Inno Setup 7\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup 6.7+ is required. Install it with: winget install --id JRSoftware.InnoSetup -e -s winget"
}

$publishDir = Join-Path $projectRoot "dist\DLForge"
if (-not $SkipAppBuild) {
    & (Join-Path $PSScriptRoot "build.ps1")
    if ($LASTEXITCODE -ne 0) { throw "DLForge application build failed." }
}
if (-not (Test-Path -LiteralPath (Join-Path $publishDir "DLForge.exe"))) {
    throw "Missing dist/DLForge/DLForge.exe. Build the application first."
}
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination $publishDir -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination $publishDir -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "THIRD_PARTY_NOTICES.txt") -Destination $publishDir -Force

$compilerArgs = @()
if ($UseDefaultSetupIcon) { $compilerArgs += "/DUseDefaultSetupIcon" }
& $iscc @compilerArgs $installerScript
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed." }

$setup = Join-Path $projectRoot "release\DLForge-0.5.0-Setup-offline.exe"
$compiledSetup = Join-Path $projectRoot "tmp\installer-output\DLForge-0.5.0-Setup-offline.exe"
if (-not (Test-Path -LiteralPath $compiledSetup)) { throw "Installer output was not created: $compiledSetup" }
New-Item -ItemType Directory -Path (Split-Path -Parent $setup) -Force | Out-Null
Copy-Item -LiteralPath $compiledSetup -Destination $setup -Force
$hash = Get-FileHash -LiteralPath $setup -Algorithm SHA256
$hashLine = "$($hash.Hash.ToLowerInvariant())  $([System.IO.Path]::GetFileName($setup))"
Set-Content -LiteralPath ($setup + ".sha256") -Value $hashLine -Encoding ascii
Write-Host "Installer ready: $setup"
Write-Host "SHA256: $($hash.Hash.ToLowerInvariant())"
