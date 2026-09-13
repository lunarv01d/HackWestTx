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
        "environment": [],
    },
    "CLI": {
        "module": "pet.cli",
        "path": ROOT / "pet" / "cli.py",
        "description": "Run Taskagotchi in the command line.",
        "dependencies": {
            "psutil": "psutil",
        },
        "environment": [],
    },
    "Gemini": {
        "module": "gemini.gemini_window",
        "path": ROOT / "gemini" / "gemini_window.py",
        "description": "Open the Taskagotchi Gemini assistant.",
        "dependencies": {
            "PySide6": "PySide6",
            "google.genai": "google-genai",
        },
        "environment": [
            "GEMINI_API_KEY",
        ],
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
        "environment": [],
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
        required = {
            "PySide6": "PySide6",
        }
    else:
        required = MODES[mode_name].get("dependencies", {})

    missing = []

    for import_name, pip_name in required.items():
        if not module_available(import_name):
            missing.append(pip_name)

    return sorted(set(missing))


def install_packages(packages):
    """
    Install packages into the same Python interpreter running Taskagotchi.
    """

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
    """
    Install missing dependencies, then verify that Python can import them.
    """

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
# Environment checks
# ---------------------------------------------------------

def missing_environment(mode_name):
    missing = []

    for variable in MODES[mode_name].get("environment", []):
        if not os.getenv(variable):
            missing.append(variable)

    return missing


def environment_error_text(variables):
    message = (
        "Taskagotchi is missing required environment variables:\n\n"
        f"{', '.join(variables)}"
    )

    if "GEMINI_API_KEY" in variables:
        message += (
            "\n\nSet your Gemini API key before launching Gemini.\n\n"
            "macOS/Linux:\n"
            'export GEMINI_API_KEY="your-key-here"\n\n'
            "Windows PowerShell:\n"
            '$env:GEMINI_API_KEY="your-key-here"'
        )

    return message


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

    # IMPORTANT:
    # Install the selected mode's dependencies BEFORE starting it.
    # Previously main.py stopped here when Tray packages were missing,
    # so trayicon.py never got a chance to install them.
    ensure_dependencies(mode_name)

    missing_env = missing_environment(mode_name)

    if missing_env:
        raise RuntimeError(
            environment_error_text(missing_env)
        )

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            mode["module"],
        ],
        cwd=str(ROOT),
    )


# ---------------------------------------------------------
# GUI launcher
# ---------------------------------------------------------

def run_gui():
    # The launcher itself needs PySide6. Install it first if necessary.
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
            layout.addWidget(self.close_after_launch)
            layout.addWidget(self.status_label)

            quit_button = QPushButton("Quit Launcher")
            quit_button.clicked.connect(self.close)
            layout.addWidget(quit_button)

            self.setCentralWidget(central_widget)

        def start_mode(self, mode_name):
            self.status_label.setText(
                f"Preparing {mode_name}..."
            )

            QApplication.processEvents()

            try:
                process = launch_mode(mode_name)

            except Exception as exc:
                self.status_label.setText("Ready")

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
