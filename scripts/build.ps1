$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsDir = Join-Path $projectRoot "tools"
$required = @("yt-dlp.exe", "ffmpeg.exe", "ffprobe.exe")
foreach ($name in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $toolsDir $name))) {
        throw "Missing tools/$name. Run scripts/prepare_tools.ps1 first."
    }
}

$pythonHome = Split-Path -Parent (Get-Command python -ErrorAction Stop).Source
$tkinterPackage = Join-Path $pythonHome "Lib\tkinter"
$tclLibrary = Join-Path $pythonHome "tcl\tcl8.6"
$tkLibrary = Join-Path $pythonHome "tcl\tk8.6"
$tclPackages = Join-Path $pythonHome "tcl\tcl8"
$tkinterBinary = Join-Path $pythonHome "DLLs\_tkinter.pyd"
$tclBinary = Join-Path $pythonHome "DLLs\tcl86t.dll"
$tkBinary = Join-Path $pythonHome "DLLs\tk86t.dll"
$tkRequired = @($tkinterPackage, $tclLibrary, $tkLibrary, $tclPackages, $tkinterBinary, $tclBinary, $tkBinary)
foreach ($path in $tkRequired) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Python build environment is missing Tcl/Tk component: $path" }
}

python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    python -m pip install -r (Join-Path $projectRoot "requirements-dev.txt")
    if ($LASTEXITCODE -ne 0) { throw "Failed to install PyInstaller." }
}
python -c "import customtkinter, PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    python -m pip install -r (Join-Path $projectRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "Failed to install GUI dependencies." }
}
$customTkRoot = python -c "import customtkinter, pathlib; print(pathlib.Path(customtkinter.__file__).resolve().parent)"
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $customTkRoot)) {
    throw "Cannot locate CustomTkinter package data."
}

Push-Location $projectRoot
try {
    python -m PyInstaller --noconfirm --clean --windowed --onedir --name DLForge `
        --hidden-import tkinter `
        --runtime-hook "scripts\pyi_rth_tkinter.py" `
        --add-data "tools;tools" `
        --add-data "$customTkRoot;customtkinter" `
        --add-data "$tkinterPackage;tkinter" `
        --add-data "$tclLibrary;_tcl_data" `
        --add-data "$tkLibrary;_tk_data" `
        --add-data "$tclPackages;tcl8" `
        --add-binary "$tkinterBinary;." `
        --add-binary "$tclBinary;." `
        --add-binary "$tkBinary;." `
        app.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }
    Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination (Join-Path $projectRoot "dist\DLForge") -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot "THIRD_PARTY_NOTICES.txt") -Destination (Join-Path $projectRoot "dist\DLForge") -Force
    $workDir = Join-Path $projectRoot "build"
    if (Test-Path -LiteralPath $workDir) {
        $resolvedRoot = [System.IO.Path]::GetFullPath($projectRoot).TrimEnd('\')
        $resolvedWork = [System.IO.Path]::GetFullPath($workDir)
        if (-not $resolvedWork.StartsWith($resolvedRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean unexpected PyInstaller work path: $resolvedWork"
        }
        Remove-Item -LiteralPath $resolvedWork -Recurse -Force
    }
    $specFile = Join-Path $projectRoot "DLForge.spec"
    if (Test-Path -LiteralPath $specFile) { Remove-Item -LiteralPath $specFile -Force }
    Write-Host "Build ready: $projectRoot\dist\DLForge\DLForge.exe"
}
finally {
    Pop-Location
}
