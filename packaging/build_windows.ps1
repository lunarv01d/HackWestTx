$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== Taskagotchi Windows Builder ==="

if (-not (Get-Command py -ErrorAction SilentlyContinue) -and
    -not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.13 is required on the build machine."
}

$Python = "python"

if (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = "py"
}

if ($Python -eq "py") {
    & py -3.13 -m venv .build-venv
    $BuildPython = Join-Path $Root ".build-venv\Scripts\python.exe"
}
else {
    & python -m venv .build-venv
    $BuildPython = Join-Path $Root ".build-venv\Scripts\python.exe"
}

& $BuildPython -m pip install --upgrade pip
& $BuildPython -m pip install -r packaging\requirements-build.txt

& $BuildPython packaging\make_icons.py

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

& $BuildPython -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name Taskagotchi `
    --icon packaging\Taskagotchi.ico `
    --add-data "window\assets;window\assets" `
    --add-data "trayicon\TrayIcon.png;trayicon" `
    --hidden-import pystray._win32 `
    --hidden-import pynput.keyboard._win32 `
    --hidden-import pynput.mouse._win32 `
    packaging\app_entry.py

$ISCC = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"

if (-not (Test-Path $ISCC)) {
    Write-Host "Inno Setup not found. Installing with winget..."

    winget install `
        --id JRSoftware.InnoSetup `
        --exact `
        --silent `
        --accept-package-agreements `
        --accept-source-agreements

    $ISCC = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $ISCC)) {
    throw "Inno Setup 6 could not be found."
}

& $ISCC packaging\Taskagotchi.iss

Write-Host ""
Write-Host "Built installer:"
Write-Host "dist\installer\Taskagotchi-Setup-Windows-x64.exe"
