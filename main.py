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
# Dependency checks
# ---------------------------------------------------------

def missing_dependencies(mode_name=None):
    """
    Check dependencies without trying to install anything.

    This avoids pip/temp-directory problems and keeps main.py from
    writing anywhere outside the project.
    """

    required = {
        "PySide6": "PySide6",
    }

    if mode_name is not None:
        required.update(
            MODES[mode_name].get("dependencies", {})
        )
    else:
        for mode in MODES.values():
            required.update(
                mode.get("dependencies", {})
            )

    missing = []

    for import_name, pip_name in required.items():
        if importlib.util.find_spec(import_name) is None:
            missing.append(pip_name)

    return sorted(set(missing))


def dependency_error_text(packages):
    package_list = " ".join(packages)

    return (
        "Taskagotchi is missing required Python packages:\n\n"
        f"{', '.join(packages)}\n\n"
        "Install them with:\n\n"
        f"{sys.executable} -m pip install {package_list}"
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

    missing = missing_dependencies(mode_name)

    if missing:
        raise RuntimeError(
            dependency_error_text(missing)
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
    gui_missing = missing_dependencies()

    if "PySide6" in gui_missing:
        print(
            dependency_error_text(["PySide6"]),
            file=sys.stderr,
        )
        sys.exit(1)

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
            layout.addWidget(self.status_label)

            quit_button = QPushButton(
                "Quit Launcher"
            )
            quit_button.clicked.connect(
                self.close
            )
            layout.addWidget(quit_button)

            self.setCentralWidget(
                central_widget
            )

        def start_mode(self, mode_name):
            try:
                process = launch_mode(
                    mode_name
                )

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
                    f"CLI started "
                    f"(PID {process.pid}). "
                    "Input/output is in the "
                    "terminal that launched "
                    "this selector."
                )

            if (
                self.close_after_launch
                .isChecked()
            ):
                self.close()

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

    if args.tray:
        launch_mode("Tray")
        return

    run_gui()


if __name__ == "__main__":
    main()
