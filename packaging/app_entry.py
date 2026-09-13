import argparse
import multiprocessing
import os
import subprocess
import sys
from pathlib import Path


FROZEN = bool(getattr(sys, "frozen", False))

if FROZEN:
    BUNDLE_ROOT = Path(sys._MEIPASS)
    APP_DIR = Path(sys.executable).resolve().parent
else:
    BUNDLE_ROOT = Path(__file__).resolve().parents[1]
    APP_DIR = BUNDLE_ROOT


# ---------------------------------------------------------
# Process launching
# ---------------------------------------------------------

def self_command(*args):
    if FROZEN:
        return [sys.executable, *args]

    return [
        sys.executable,
        str(Path(__file__).resolve()),
        *args,
    ]


def spawn_mode(flag=None):
    args = []

    if flag:
        args.append(flag)

    return subprocess.Popen(
        self_command(*args),
        cwd=str(APP_DIR),
    )


# ---------------------------------------------------------
# Cross-platform runtime fixes
# ---------------------------------------------------------

def patch_system_helpers():
    """
    Patch the original system-monitor helpers for packaged Windows/macOS
    builds without changing the development CLI behavior.
    """

    import psutil
    import Taskagotchi.Taskagotchi.Taskagotchi as task

    def check_disk_ratio():
        home = Path.home()

        try:
            return psutil.disk_usage(str(home)).percent
        except OSError:
            anchor = home.anchor

            if not anchor:
                anchor = "/"

            return psutil.disk_usage(anchor).percent

    def check_battery_percent():
        battery = psutil.sensors_battery()

        if battery is None:
            return 100.0

        return battery.percent

    task.check_DiskRatio = check_disk_ratio
    task.check_BatteryPercent = check_battery_percent


# ---------------------------------------------------------
# Taskagotchi process detection / shutdown
# ---------------------------------------------------------

def is_taskagotchi_process(process):
    import psutil

    try:
        if process.pid == os.getpid():
            return False

        if FROZEN:
            process_exe = Path(process.exe()).resolve()
            our_exe = Path(sys.executable).resolve()

            return process_exe == our_exe

        cmdline = process.cmdline()

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess,
        OSError,
    ):
        return False

    if not cmdline:
        return False

    command = (
        " ".join(str(part) for part in cmdline)
        .replace("\\", "/")
        .lower()
    )

    entry = (
        str(Path(__file__).resolve())
        .replace("\\", "/")
        .lower()
    )

    return entry in command


def find_taskagotchi_processes():
    import psutil

    found = {}

    for process in psutil.process_iter():

        if not is_taskagotchi_process(process):
            continue

        found[process.pid] = process

        try:
            for child in process.children(recursive=True):
                if child.pid != os.getpid():
                    found[child.pid] = child

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            pass

    return list(found.values())


def quit_everything():
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
# Direct mode runners
# ---------------------------------------------------------

def run_window():
    patch_system_helpers()

    from window.window import main as window_main

    window_main()


def run_gemini():
    from gemini.gemini_window import main as gemini_main

    gemini_main()


def load_tray_image():
    from PIL import Image

    icon_path = (
        BUNDLE_ROOT
        / "trayicon"
        / "TrayIcon.png"
    )

    if not icon_path.exists():
        raise FileNotFoundError(
            f"Could not find tray icon: {icon_path}"
        )

    with Image.open(icon_path) as source:
        image = source.convert("RGBA")

    if image.size != (64, 64):
        image = image.resize(
            (64, 64),
            Image.Resampling.NEAREST,
        )

    return image


def run_tray():
    import pystray

    def open_taskagotchi(icon=None, item=None):
        spawn_mode("--window")

    def ask_gemini(icon=None, item=None):
        spawn_mode("--gemini")

    def open_launcher(icon=None, item=None):
        spawn_mode()

    def quit_all(icon=None, item=None):
        try:
            icon.visible = False
        except Exception:
            pass

        quit_everything()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(
            "Open Taskagotchi",
            open_taskagotchi,
            default=True,
        ),
        pystray.MenuItem(
            "Ask Gemini",
            ask_gemini,
        ),
        pystray.MenuItem(
            "Open Launcher",
            open_launcher,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Quit Everything",
            quit_all,
        ),
    )

    icon = pystray.Icon(
        "Taskagotchi",
        load_tray_image(),
        "Taskagotchi",
        menu,
    )

    icon.run()


# ---------------------------------------------------------
# Launcher GUI
# ---------------------------------------------------------

def run_launcher():
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QApplication,
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

            icon_path = (
                BUNDLE_ROOT
                / "trayicon"
                / "TrayIcon.png"
            )

            if icon_path.exists():
                self.setWindowIcon(
                    QIcon(str(icon_path))
                )

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

            window_button = QPushButton(
                "Open Taskagotchi"
            )
            window_button.clicked.connect(
                lambda: self.start_mode(
                    "--window",
                    "Taskagotchi",
                )
            )

            gemini_button = QPushButton(
                "Ask Gemini"
            )
            gemini_button.clicked.connect(
                lambda: self.start_mode(
                    "--gemini",
                    "Gemini",
                )
            )

            tray_button = QPushButton(
                "Start Tray / Menu Bar"
            )
            tray_button.clicked.connect(
                lambda: self.start_mode(
                    "--tray",
                    "Tray",
                )
            )

            quit_launcher_button = QPushButton(
                "Quit Launcher"
            )
            quit_launcher_button.clicked.connect(
                self.close
            )

            quit_all_button = QPushButton(
                "Quit Everything"
            )
            quit_all_button.clicked.connect(
                self.quit_all
            )

            layout.addWidget(title)
            layout.addWidget(subtitle)
            layout.addSpacing(12)
            layout.addWidget(window_button)
            layout.addWidget(gemini_button)
            layout.addWidget(tray_button)
            layout.addSpacing(8)
            layout.addWidget(self.status_label)
            layout.addWidget(quit_launcher_button)
            layout.addWidget(quit_all_button)

            self.setCentralWidget(
                central_widget
            )

        def start_mode(self, flag, label):
            try:
                process = spawn_mode(flag)

            except Exception as exc:
                QMessageBox.critical(
                    self,
                    "Taskagotchi",
                    str(exc),
                )
                return

            self.status_label.setText(
                f"{label} started "
                f"(PID {process.pid})"
            )

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
        "Taskagotchi"
    )

    icon_path = (
        BUNDLE_ROOT
        / "trayicon"
        / "TrayIcon.png"
    )

    if icon_path.exists():
        app.setWindowIcon(
            QIcon(str(icon_path))
        )

    launcher = TaskagotchiLauncher()
    launcher.show()
    launcher.raise_()

    sys.exit(app.exec())


# ---------------------------------------------------------
# Arguments
# ---------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Taskagotchi"
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--window",
        action="store_true",
    )

    group.add_argument(
        "--gemini",
        action="store_true",
    )

    group.add_argument(
        "--tray",
        action="store_true",
    )

    return parser.parse_args()


def main():
    multiprocessing.freeze_support()

    args = parse_args()

    if args.window:
        run_window()
        return

    if args.gemini:
        run_gemini()
        return

    if args.tray:
        run_tray()
        return

    run_launcher()


if __name__ == "__main__":
    main()
