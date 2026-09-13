import argparse
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
        "module": "tray.tray",
        "path": ROOT / "tray" / "tray.py",
        "description": "Run Taskagotchi from the system tray.",
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
    """
    A mode is considered available when its entry-point file exists.

    This makes Tray automatically become available later when
    tray/tray.py is added to the project.
    """

    return MODES[mode_name]["path"].exists()


def launch_mode(mode_name):
    """
    Launch the selected mode as a separate Python process.

    Separate processes are intentional:
    - The selector can keep running.
    - The window can own its QApplication cleanly.
    - The CLI can keep using input().
    - A future tray mode can run independently.
    """

    if mode_name not in MODES:
        raise ValueError(f"Unknown Taskagotchi mode: {mode_name}")

    mode = MODES[mode_name]

    if not mode["path"].exists():
        raise FileNotFoundError(
            f"{mode_name} mode is not available yet.\n"
            f"Expected: {mode['path']}"
        )

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            mode["module"],
        ],
        cwd=ROOT,
    )

    return process


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

                available = mode_available(mode_name)

                if available:
                    button.setToolTip(mode["description"])
                    button.clicked.connect(
                        lambda checked=False, name=mode_name:
                        self.start_mode(name)
                    )
                else:
                    button.setText(f"{mode_name} — Coming Soon")
                    button.setEnabled(False)
                    button.setToolTip(
                        f"Waiting for {mode['path'].relative_to(ROOT)}"
                    )

                self.mode_buttons[mode_name] = button
                layout.addWidget(button)

            layout.addSpacing(8)
            layout.addWidget(self.close_after_launch)
            layout.addWidget(self.status_label)

            quit_button = QPushButton("Quit")
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

            # The existing CLI uses input(), so when launching CLI
            # from this selector during development, run main.py
            # from a terminal so the CLI has a console to use.
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

    # No mode argument = show graphical selector.
    run_gui()


if __name__ == "__main__":
    main()