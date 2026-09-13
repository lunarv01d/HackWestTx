# Native Taskagotchi Installers

This packaging kit produces:

- **Windows:** `Taskagotchi-Setup-Windows-x64.exe`
- **macOS:** `Taskagotchi.app` and `Taskagotchi-macOS.dmg`

The end user does **not** need Python installed. PyInstaller bundles the Python
runtime and Taskagotchi's dependencies into the application.

## Recommended: GitHub Actions

Copy the `packaging/` directory and `.github/workflows/build-installers.yml`
into the Taskagotchi repository.

Then open:

**GitHub -> Actions -> Build Taskagotchi Installers -> Run workflow**

The Windows and macOS installers will be downloadable as workflow artifacts.

The workflow also runs automatically for tags matching `v*`.

## Local Windows build

From PowerShell at the repository root:

```powershell
.\packaging\build_windows.ps1
```

Result:

```text
dist\installer\Taskagotchi-Setup-Windows-x64.exe
```

## Local macOS build

From Terminal at the repository root:

```bash
chmod +x packaging/build_macos.sh
./packaging/build_macos.sh
```

Results:

```text
dist/Taskagotchi.app
dist/Taskagotchi-macOS.dmg
```

## Why there is a separate packaged entry point

The development launcher starts child modes with `python -m ...`. A frozen
application no longer has a standalone Python interpreter at `sys.executable`;
`sys.executable` is Taskagotchi itself.

`packaging/app_entry.py` therefore launches the same packaged executable with
`--window`, `--gemini`, or `--tray`, then imports that mode inside the child
process. This keeps the development workflow unchanged while making a frozen
app work correctly.

The packaged entry point also fixes the current hard-coded `/Users/...` disk
path at runtime so the system monitor works on Windows without needing a
source-code fork.

## Signing warning

These builds are **unsigned developer/hackathon builds**.

- macOS uses ad-hoc signing. Gatekeeper may require right-click -> Open the
  first time, and Accessibility/Input Monitoring permission may need to be
  granted for global scroll tracking.
- Windows SmartScreen may warn about an unknown publisher.

Removing those warnings for public distribution requires an Apple Developer ID
certificate/notarization and a Windows Authenticode code-signing certificate.

## Packaged features

The packaged launcher includes:

- Taskagotchi desktop pet
- Gemini
- System tray/menu bar mode
- Quit Launcher
- Quit Everything

The interactive developer CLI is intentionally not exposed in the GUI build
because Windows GUI executables do not have an interactive console attached.
The source CLI remains available when running the repository normally.
