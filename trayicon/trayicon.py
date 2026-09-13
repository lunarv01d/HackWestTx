import importlib.util
import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

TRAY_DIR = Path(__file__).resolve().parent
ROOT = TRAY_DIR.parent
ICON_PATH = TRAY_DIR / "TrayIcon.png"


# ---------------------------------------------------------
# Dependency bootstrap
# ---------------------------------------------------------

def install_dependencies():
    """
    Install only the packages required for tray mode itself.

    Gemini has its own dependency check in main.py, so google-genai
    is intentionally not installed here.
    """

    required_packages = {
        "pystray": "pystray",
        "PIL": "pillow",
        "psutil": "psutil",
    }

    missing_packages = []

    for import_name, pip_name in required_packages.items():
        try:
            available = (
                importlib.util.find_spec(import_name)
                is not None
            )
        except (
            ModuleNotFoundError,
            ValueError,
        ):
            available = False

        if not available:
            missing_packages.append(pip_name)

    if not missing_packages:
        return

    print(
        "Taskagotchi tray is missing required packages:"
    )

    for package in missing_packages:
        print(f"  - {package}")

    print("\nInstalling required packages...")

    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                *missing_packages,
            ],
            cwd=str(ROOT),
        )

    except subprocess.CalledProcessError as exc:
        print(
            "\nCould not install Taskagotchi tray dependencies."
        )
        print("Install them manually with:")
        print(
            f"{sys.executable} -m pip install "
            + " ".join(missing_packages)
        )
        raise SystemExit(exc.returncode)

    print("\nTray dependencies installed successfully.\n")


install_dependencies()

import psutil
import pystray
from PIL import Image


# ---------------------------------------------------------
# Tray icon image
# ---------------------------------------------------------

def load_tray_icon():
    """
    Load and normalize the Taskagotchi tray image.

    The source TrayIcon.png is intentionally tiny pixel art. That works
    on macOS, but pystray's Windows backend serializes the PIL image to
    ICO before passing it to Win32 LoadImage.

    Pillow cannot create a valid ICO from an 8x8 image, so Windows gets
    an invalid temporary icon and LoadImage fails with WinError 0.

    Upscaling to 64x64 with nearest-neighbor preserves the pixel-art look
    and gives Pillow enough size to generate valid Windows ICO frames.
    """

    if not ICON_PATH.exists():
        raise FileNotFoundError(
            f"Could not find tray icon: {ICON_PATH}"
        )

    with Image.open(ICON_PATH) as source:
        image = source.convert("RGBA")

    # 64x64 is also the size used by pystray's own usage example.
    # NEAREST keeps an 8-bit / pixel-art icon crisp instead of blurry.
    if image.size != (64, 64):
        image = image.resize(
            (64, 64),
            Image.Resampling.NEAREST,
        )

    return image


# ---------------------------------------------------------
# Launch helpers
# ---------------------------------------------------------

def launch_window(icon=None, item=None):
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "window.window",
        ],
        cwd=str(ROOT),
    )


def launch_cli(icon=None, item=None):
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "pet.cli",
        ],
        cwd=str(ROOT),
    )


def launch_launcher(icon=None, item=None):
    subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "main.py"),
        ],
        cwd=str(ROOT),
    )


def ask_gemini(icon=None, item=None):
    """
    Route Gemini through main.py so the launcher performs the
    google-genai and GEMINI_API_KEY checks in one place.
    """

    subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "main.py"),
            "--gemini",
        ],
        cwd=str(ROOT),
    )


def open_settings(icon=None, item=None):
    print("Settings are not implemented yet.")


# ---------------------------------------------------------
# Taskagotchi process detection
# ---------------------------------------------------------

def is_taskagotchi_process(process):
    """
    Returns True only for Python processes that appear to be one
    of Taskagotchi's own entry points.

    This deliberately does NOT kill everything running from the
    repository folder, so your terminal/editor are left alone.
    """

    try:
        cmdline = process.cmdline()

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
    ):
        return False

    if not cmdline:
        return False

    command = " ".join(
        str(part)
        for part in cmdline
    )

    normalized = (
        command
        .replace("\\", "/")
        .lower()
    )

    root_text = (
        str(ROOT)
        .replace("\\", "/")
        .lower()
    )

    markers = (
        "-m window.window",
        "-m pet.cli",
        "-m trayicon.trayicon",
        "-m gemini.gemini_window",
        f"{root_text}/main.py",
        f"{root_text}/window/window.py",
        f"{root_text}/pet/cli.py",
        f"{root_text}/trayicon/trayicon.py",
        f"{root_text}/gemini/gemini_window.py",
    )

    return any(
        marker in normalized
        for marker in markers
    )


def find_taskagotchi_processes():
    """
    Finds all Taskagotchi launcher/window/CLI/Gemini/tray processes
    except this tray process itself.
    """

    current_pid = os.getpid()
    found = {}

    for process in psutil.process_iter():

        if process.pid == current_pid:
            continue

        if not is_taskagotchi_process(process):
            continue

        found[process.pid] = process

        try:
            for child in process.children(
                recursive=True
            ):
                if child.pid != current_pid:
                    found[child.pid] = child

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            pass

    return list(found.values())


# ---------------------------------------------------------
# Quit everything
# ---------------------------------------------------------

def quit_taskagotchi(icon, item=None):
    """
    Stops every Taskagotchi-related process we can identify.

    This includes:
      - desktop window(s)
      - CLI instance(s)
      - Gemini window(s)
      - launcher instance(s)
      - other tray instance(s)
      - child/helper processes
    """

    try:
        icon.visible = False
    except Exception:
        pass

    processes = find_taskagotchi_processes()

    for process in processes:
        try:
            process.terminate()

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            pass

    if processes:
        _, alive = psutil.wait_procs(
            processes,
            timeout=2.0,
        )

        for process in alive:
            try:
                process.kill()

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):
                pass

    icon.stop()


# ---------------------------------------------------------
# Main tray icon
# ---------------------------------------------------------

def main():
    icon_image = load_tray_icon()

    menu = pystray.Menu(
        pystray.MenuItem(
            "Open Taskagotchi",
            launch_window,
            default=True,
        ),
        pystray.MenuItem(
            "Ask Gemini",
            ask_gemini,
        ),
        pystray.MenuItem(
            "Open CLI",
            launch_cli,
        ),
        pystray.MenuItem(
            "Open Launcher",
            launch_launcher,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Settings",
            open_settings,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Quit Everything",
            quit_taskagotchi,
        ),
    )

    icon = pystray.Icon(
        "Taskagotchi",
        icon_image,
        "Taskagotchi",
        menu,
    )

    icon.run()


if __name__ == "__main__":
    main()
