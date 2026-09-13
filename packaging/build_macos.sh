#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Taskagotchi macOS Builder ==="

PYTHON="${PYTHON:-python3}"

"$PYTHON" -m venv .build-venv

BUILD_PYTHON="$ROOT/.build-venv/bin/python"

"$BUILD_PYTHON" -m pip install --upgrade pip
"$BUILD_PYTHON" -m pip install -r packaging/requirements-build.txt

"$BUILD_PYTHON" packaging/make_icons.py

rm -rf build dist

"$BUILD_PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --name Taskagotchi \
  --icon packaging/Taskagotchi.icns \
  --osx-bundle-identifier com.taskagotchi.app \
  --add-data "window/assets:window/assets" \
  --add-data "trayicon/TrayIcon.png:trayicon" \
  --hidden-import pystray._darwin \
  --hidden-import pynput.keyboard._darwin \
  --hidden-import pynput.mouse._darwin \
  packaging/app_entry.py

# Ad-hoc sign for hackathon/internal distribution.
codesign \
  --force \
  --deep \
  --sign - \
  dist/Taskagotchi.app

DMG_ROOT="$ROOT/dist/dmg-root"
rm -rf "$DMG_ROOT"
mkdir -p "$DMG_ROOT"

cp -R \
  dist/Taskagotchi.app \
  "$DMG_ROOT/Taskagotchi.app"

ln -s /Applications \
  "$DMG_ROOT/Applications"

hdiutil create \
  -volname "Taskagotchi" \
  -srcfolder "$DMG_ROOT" \
  -ov \
  -format UDZO \
  "$ROOT/dist/Taskagotchi-macOS.dmg"

rm -rf "$DMG_ROOT"

echo
echo "Built:"
echo "dist/Taskagotchi.app"
echo "dist/Taskagotchi-macOS.dmg"
