from pathlib import Path
import py_compile
import zipfile

out_dir = Path("/mnt/data/taskagotchi_quit_all")
(out_dir / "trayicon").mkdir(parents=True, exist_ok=True)

main_code = r'''import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------
# Paths / launch targets
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parent

MODES = {
    "Window": {
        "module": "window.window",
        "path": ROOT / "window" / "window.py",
        "description": "Run the desktop Taskagotchi window.",
    },
    "CLI": {
        "module": "pet.cli",
        "path": ROOT / "pet" / "cli.py",
        "description": "Run Taskagotchi in the command line.",
    },
    "Tray": {
        "module": "trayicon.trayicon",
        "path": ROOT / "trayicon" / "trayicon.py",
        "description": "Run Taskagotchi from the system tray/menu bar.",
    },
}


# ---------------------------------------------------------
# Dependency bootstrap
# ---------------------------------------------------------

def install_dependencies():
    required_packages = {
        "PySide6": "PySide6",
        "psutil": "psutil",
        "pynput": "pynput",
        "pystray": "pystray",
        "PIL": "pillow",
    }

    missing_packages = []

    for import_name, pip_name in required_packages.items():
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(pip_name)

    if not missing_packages:
        return

    print("Taskagotchi is missing required components:")

    for package in missing_packages:
        print(f"  - {package}")

    print("\nInstalling required components...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
        )

    except subprocess.CalledProcessError:
        print("pip was not found. Attempting to install pip...")

        subprocess.check_call(
            [sys.executable, "-m", "ensurepip", "--upgrade"]
        )

    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                *missing_packages,
            ]
        )

    except subprocess.CalledProcessError:
        print("\nCould not install Taskagotchi dependencies.")
        print("Check your internet connection and Python permissions.")
        sys.exit(1)

    print("\nDependencies installed successfully!\n")


# ---------------------------------------------------------
# Process launching
# ---------------------------------------------------------

def mode_available(mode_name):
    return MODES[mode_name]["path"].exists()


def launch_mode(mode_name):
    if mode_name not in MODES:
        raise ValueError(f"Unknown Taskagotchi mode: {mode_name}")

    mode = MODES[mode_name]

    if not mode["path"].exists():
        raise FileNotFoundError(
            f"{mode_name} mode is not available.\n"
            f"Expected: {mode['path']}"
        )

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            mode["module"],
        ],
        cwd=ROOT,
    )


# ---------------------------------------------------------
# GUI launcher
# ---------------------------------------------------------

def run_gui():
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    class TaskagotchiLauncher(QMainWindow):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("Taskagotchi")
            self.setMinimumWidth(380)

            central_widget = QWidget()
            layout = QVBoxLayout(central_widget)

            title = QLabel("Taskagotchi")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)

            title_font = title.font()
            title_font.setPointSize(22)
            title_font.setBold(True)
            title.setFont(title_font)

            subtitle = QLabel(
                "How would you like to run Taskagotchi?"
            )
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setWordWrap(True)

            self.status_label = QLabel("Ready")
            self.status_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.status_label.setWordWrap(True)

            self.close_after_launch = QCheckBox(
                "Close launcher after starting"
            )

            layout.addWidget(title)
            layout.addWidget(subtitle)
            layout.addSpacing(12)

            self.mode_buttons = {}

            for mode_name, mode in MODES.items():
                button = QPushButton(mode_name)

                if mode_available(mode_name):
                    button.setToolTip(mode["description"])
                    button.clicked.connect(
                        lambda checked=False, name=mode_name:
                        self.start_mode(name)
                    )
                else:
                    button.setText(f"{mode_name} — Unavailable")
                    button.setEnabled(False)
                    button.setToolTip(
                        f"Missing: "
                        f"{mode['path'].relative_to(ROOT)}"
                    )

                self.mode_buttons[mode_name] = button
                layout.addWidget(button)

            layout.addSpacing(8)
            layout.addWidget(self.close_after_launch)
            layout.addWidget(self.status_label)

            quit_button = QPushButton("Quit Launcher")
            quit_button.clicked.connect(self.close)
            layout.addWidget(quit_button)

            self.setCentralWidget(central_widget)

        def start_mode(self, mode_name):
            try:
                process = launch_mode(mode_name)

            except Exception as exc:
                QMessageBox.critical(
                    self,
                    "Taskagotchi",
                    str(exc),
                )
                return

            self.status_label.setText(
                f"{mode_name} started "
                f"(PID {process.pid})"
            )

            if mode_name == "CLI":
                self.status_label.setText(
                    f"CLI started (PID {process.pid}). "
                    "Input/output is in the terminal "
                    "that launched this selector."
                )

            if self.close_after_launch.isChecked():
                self.close()

    app = QApplication(sys.argv)
    app.setApplicationName("Taskagotchi Launcher")

    launcher = TaskagotchiLauncher()
    launcher.show()
    launcher.raise_()

    sys.exit(app.exec())


# ---------------------------------------------------------
# Command-line selection
# ---------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Taskagotchi launcher"
    )

    mode_group = parser.add_mutually_exclusive_group()

    mode_group.add_argument(
        "--window",
        action="store_true",
        help="Launch the desktop window directly.",
    )

    mode_group.add_argument(
        "--cli",
        action="store_true",
        help="Launch the command-line interface directly.",
    )

    mode_group.add_argument(
        "--tray",
        action="store_true",
        help="Launch the tray application directly.",
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    install_dependencies()

    args = parse_args()

    if args.window:
        launch_mode("Window")
        return

    if args.cli:
        process = launch_mode("CLI")
        process.wait()
        return

    if args.tray:
        launch_mode("Tray")
        return

    run_gui()


if __name__ == "__main__":
    main()
'''

tray_code = r'''import importlib.util
import os
import subprocess
import sys
import time
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
    required_packages = {
        "pystray": "pystray",
        "PIL": "pillow",
        "psutil": "psutil",
    }

    missing_packages = []

    for import_name, pip_name in required_packages.items():
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(pip_name)

    if not missing_packages:
        return

    print("Taskagotchi tray is missing required components:")

    for package in missing_packages:
        print(f"  - {package}")

    print("\nInstalling required components...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
        )

    except subprocess.CalledProcessError:
        print("pip was not found. Attempting to install pip...")

        subprocess.check_call(
            [sys.executable, "-m", "ensurepip", "--upgrade"]
        )

    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                *missing_packages,
            ]
        )

    except subprocess.CalledProcessError:
        print("\nCould not install tray dependencies.")
        print("Check your internet connection and Python permissions.")
        sys.exit(1)

    print("\nTray dependencies installed successfully!\n")


install_dependencies()

import psutil
import pystray
from PIL import Image


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
    Return True only for Python processes that appear to be one of
    Taskagotchi's own entry points.

    We intentionally do NOT kill every process whose working directory
    is the repo, because that could kill the user's shell, editor, etc.
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

    return any(marker in normalized for marker in markers)


def find_taskagotchi_processes():
    """
    Find every currently-running Taskagotchi launcher/window/CLI/tray
    process, regardless of which Taskagotchi process launched it.
    """

    current_pid = os.getpid()
    found = {}

    for process in psutil.process_iter():
        if process.pid == current_pid:
            continue

        if not is_taskagotchi_process(process):
            continue

        found[process.pid] = process

        # Also include children such as temporary helper processes.
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
    Quit ALL Taskagotchi-related processes:
      - desktop window(s)
      - CLI instance(s)
      - launcher window(s)
      - other tray instances
      - child helper processes

    The current tray process is stopped last.
    """

    # Remove the icon immediately so the user gets visual feedback.
    try:
        icon.visible = False
    except Exception:
        pass

    processes = find_taskagotchi_processes()

    # Ask all matching processes to exit cleanly first.
    for process in processes:
        try:
            process.terminate()
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            pass

    # Give them a moment to close cleanly.
    gone, alive = psutil.wait_procs(
        processes,
        timeout=2.0,
    )

    # Force-close anything that ignored terminate().
    for process in alive:
        try:
            process.kill()
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            pass

    # Stop this pystray instance last.
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
'''

init_code = '"""Taskagotchi tray icon package."""\n'

main_path = out_dir / "main.py"
tray_path = out_dir / "trayicon" / "trayicon.py"
init_path = out_dir / "trayicon" / "__init__.py"

main_path.write_text(main_code, encoding="utf-8")
tray_path.write_text(tray_code, encoding="utf-8")
init_path.write_text(init_code, encoding="utf-8")

py_compile.compile(str(main_path), doraise=True)
py_compile.compile(str(tray_path), doraise=True)
py_compile.compile(str(init_path), doraise=True)

zip_path = Path("/mnt/data/taskagotchi_quit_everything.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(main_path, "main.py")
    z.write(tray_path, "trayicon/trayicon.py")
    z.write(init_path, "trayicon/__init__.py")

print("Created and syntax-checked:")
print(main_path)
print(tray_path)
print(init_path)
print(zip_path)
