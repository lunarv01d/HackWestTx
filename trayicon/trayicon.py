import os
import subprocess
import sys
from pathlib import Path

import psutil
import pystray
from PIL import Image


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

TRAY_DIR = Path(__file__).resolve().parent
ROOT = TRAY_DIR.parent
ICON_PATH = TRAY_DIR / "TrayIcon.png"


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
        cwd=ROOT,
    )


def launch_cli(icon=None, item=None):
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "pet.cli",
        ],
        cwd=ROOT,
    )


def launch_launcher(icon=None, item=None):
    subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "main.py"),
        ],
        cwd=ROOT,
    )


# ---------------------------------------------------------
# Placeholder actions
# ---------------------------------------------------------

def ask_gemini(icon=None, item=None):
    print("Ask Gemini is not implemented yet.")


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

    command = " ".join(str(part) for part in cmdline)

    # Normalize Windows backslashes so the same checks work on
    # macOS, Linux, and Windows.
    normalized = command.replace("\\", "/").lower()
    root_text = str(ROOT).replace("\\", "/").lower()

    markers = (
        "-m window.window",
        "-m pet.cli",
        "-m trayicon.trayicon",
        f"{root_text}/main.py",
        f"{root_text}/window/window.py",
        f"{root_text}/pet/cli.py",
        f"{root_text}/trayicon/trayicon.py",
    )

    return any(
        marker in normalized
        for marker in markers
    )


def find_taskagotchi_processes():
    """
    Finds all Taskagotchi launcher/window/CLI/tray processes except
    this tray process itself.
    """

    current_pid = os.getpid()
    found = {}

    for process in psutil.process_iter():

        if process.pid == current_pid:
            continue

        if not is_taskagotchi_process(process):
            continue

        found[process.pid] = process

        # Include helper/child processes spawned by Taskagotchi.
        try:
            for child in process.children(recursive=True):
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
    Stops every Taskagotchi-related process we can identify:

      - Taskagotchi window(s)
      - CLI instance(s)
      - launcher instance(s)
      - other tray instance(s)
      - helper child processes

    It first asks them to terminate cleanly. Anything still alive
    after two seconds is force-killed.
    """

    # Hide the tray icon immediately so clicking Quit gives
    # visible feedback before process cleanup begins.
    try:
        icon.visible = False
    except Exception:
        pass

    processes = find_taskagotchi_processes()

    # Graceful termination first.
    for process in processes:
        try:
            process.terminate()

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            pass

    # Wait briefly for clean shutdown.
    if processes:
        _, alive = psutil.wait_procs(
            processes,
            timeout=2.0,
        )

        # Force-close anything that did not terminate.
        for process in alive:
            try:
                process.kill()

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):
                pass

    # Stop this tray process last.
    icon.stop()


# ---------------------------------------------------------
# Main tray icon
# ---------------------------------------------------------

def main():
    if not ICON_PATH.exists():
        raise FileNotFoundError(
            f"Could not find tray icon: {ICON_PATH}"
        )

    icon_image = Image.open(ICON_PATH)

    menu = pystray.Menu(
        pystray.MenuItem(
            "Open Taskagotchi",
            launch_window,
            default=True,
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
            "Ask Gemini",
            ask_gemini,
        ),
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
