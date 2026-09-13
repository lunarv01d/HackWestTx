import argparse
import importlib.util
import os
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
        "dependencies": {
            "PySide6": "PySide6",
            "psutil": "psutil",
            "pynput": "pynput",
        },
    },
    "CLI": {
        "module": "pet.cli",
        "path": ROOT / "pet" / "cli.py",
        "description": "Run Taskagotchi in the command line.",
        "dependencies": {
            "psutil": "psutil",
        },
    },
    "Gemini": {
        "module": "gemini.gemini_window",
        "path": ROOT / "gemini" / "gemini_window.py",
        "description": "Open the Taskagotchi Gemini assistant.",
        "dependencies": {
            "PySide6": "PySide6",
            "certifi": "certifi",
        },
    },
    "Tray": {
        "module": "trayicon.trayicon",
        "path": ROOT / "trayicon" / "trayicon.py",
        "description": "Run Taskagotchi from the system tray/menu bar.",
        "dependencies": {
            "pystray": "pystray",
            "PIL": "pillow",
            "psutil": "psutil",
        },
    },
}


# ---------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------

def module_available(import_name):
    try:
        return importlib.util.find_spec(import_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def missing_dependencies(mode_name=None):
    if mode_name is None:
        # The launcher itself now uses psutil for Quit Everything.
        required = {
            "PySide6": "PySide6",
            "psutil": "psutil",
        }
    else:
        required = MODES[mode_name].get(
            "dependencies",
            {},
        )

    missing = []

    for import_name, pip_name in required.items():
        if not module_available(import_name):
            missing.append(pip_name)

    return sorted(set(missing))


def install_packages(packages):
    if not packages:
        return

    print("Taskagotchi is missing required packages:")

    for package in packages:
        print(f"  - {package}")

    print("\nInstalling required packages...\n")

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        *packages,
    ]

    try:
        subprocess.check_call(
            command,
            cwd=str(ROOT),
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Taskagotchi could not install the required packages.\n\n"
            "Try running this manually:\n\n"
            + " ".join(command)
        ) from exc

    importlib.invalidate_caches()

    print("\nDependencies installed successfully.\n")


def ensure_dependencies(mode_name=None):
    missing = missing_dependencies(mode_name)

    if not missing:
        return

    install_packages(missing)

    still_missing = missing_dependencies(mode_name)

    if still_missing:
        raise RuntimeError(
            "The following packages were installed, but Python still "
            "cannot import them:\n\n"
            + ", ".join(still_missing)
            + "\n\nPython executable:\n"
            + sys.executable
        )


# ---------------------------------------------------------
# Process launching
# ---------------------------------------------------------

def mode_available(mode_name):
    return MODES[mode_name]["path"].exists()


def launch_mode(mode_name):
    if mode_name not in MODES:
        raise ValueError(
            f"Unknown Taskagotchi mode: {mode_name}"
        )

    mode = MODES[mode_name]

    if not mode["path"].exists():
        raise FileNotFoundError(
            f"{mode_name} mode is not available.\n"
            f"Expected: {mode['path']}"
        )

    ensure_dependencies(mode_name)

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            mode["module"],
        ],
        cwd=str(ROOT),
    )


# ---------------------------------------------------------
# Taskagotchi process detection / shutdown
# ---------------------------------------------------------

def is_taskagotchi_process(process):
    """
    Return True only for Python processes that appear to belong
    to Taskagotchi.

    This deliberately does not kill a terminal, IDE, or other process
    simply because its working directory happens to be the repo.
    """

    import psutil

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
        "-m gemini.gemini_window",
        "-m trayicon.trayicon",
        f"{root_text}/main.py",
        f"{root_text}/window/window.py",
        f"{root_text}/pet/cli.py",
        f"{root_text}/gemini/gemini_window.py",
        f"{root_text}/trayicon/trayicon.py",
    )

    return any(
        marker in normalized
        for marker in markers
    )


def find_taskagotchi_processes():
    """
    Find every Taskagotchi process except the launcher process
    currently executing this function.
    """

    import psutil

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


def quit_everything():
    """
    Stop all other Taskagotchi processes, then allow the current
    launcher to close itself normally.
    """

    import psutil

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


# ---------------------------------------------------------
# GUI launcher
# ---------------------------------------------------------

def run_gui():
    ensure_dependencies()

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
            title.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            title_font = title.font()
            title_font.setPointSize(22)
            title_font.setBold(True)
            title.setFont(title_font)

            subtitle = QLabel(
                "How would you like to run Taskagotchi?"
            )
            subtitle.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
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
                    button.setToolTip(
                        mode["description"]
                    )
                    button.clicked.connect(
                        lambda checked=False,
                        name=mode_name:
                        self.start_mode(name)
                    )
                else:
                    button.setText(
                        f"{mode_name} — Unavailable"
                    )
                    button.setEnabled(False)
                    button.setToolTip(
                        "Missing: "
                        f"{mode['path'].relative_to(ROOT)}"
                    )

                self.mode_buttons[mode_name] = button
                layout.addWidget(button)

            layout.addSpacing(8)
            layout.addWidget(
                self.close_after_launch
            )
            layout.addWidget(
                self.status_label
            )

            quit_launcher_button = QPushButton(
                "Quit Launcher"
            )
            quit_launcher_button.clicked.connect(
                self.close
            )
            layout.addWidget(
                quit_launcher_button
            )

            quit_everything_button = QPushButton(
                "Quit Everything"
            )
            quit_everything_button.setToolTip(
                "Close all Taskagotchi windows, CLI sessions, "
                "Gemini windows, tray instances, and this launcher."
            )
            quit_everything_button.clicked.connect(
                self.quit_all
            )
            layout.addWidget(
                quit_everything_button
            )

            self.setCentralWidget(
                central_widget
            )

        def start_mode(self, mode_name):
            self.status_label.setText(
                f"Preparing {mode_name}..."
            )

            QApplication.processEvents()

            try:
                process = launch_mode(
                    mode_name
                )

            except Exception as exc:
                self.status_label.setText(
                    "Ready"
                )

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
                    f"CLI started "
                    f"(PID {process.pid}). "
                    "Input/output is in the terminal "
                    "that launched this selector."
                )

            if (
                self.close_after_launch
                .isChecked()
            ):
                self.close()

        def quit_all(self):
            self.status_label.setText(
                "Closing Taskagotchi..."
            )
            QApplication.processEvents()

            try:
                quit_everything()

            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "Taskagotchi",
                    "Some Taskagotchi processes may not "
                    f"have closed cleanly.\n\n{exc}",
                )

            QApplication.quit()

    app = QApplication(sys.argv)
    app.setApplicationName(
        "Taskagotchi Launcher"
    )

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

    mode_group = (
        parser.add_mutually_exclusive_group()
    )

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
        "--gemini",
        action="store_true",
        help="Launch the Gemini assistant directly.",
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
    args = parse_args()

    if args.window:
        launch_mode("Window")
        return

    if args.cli:
        process = launch_mode("CLI")
        process.wait()
        return

    if args.gemini:
        launch_mode("Gemini")
        return

    if args.tray:
        launch_mode("Tray")
        return

    run_gui()


if __name__ == "__main__":
    main()
