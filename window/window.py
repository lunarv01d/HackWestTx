import sys
import subprocess
import importlib.util
from pathlib import Path


# ---------------------------------------------------------
# Dependency bootstrap
# ---------------------------------------------------------

def install_dependencies():
    required_packages = {
        "PySide6": "PySide6",
        "psutil": "psutil",
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

    # Make sure pip exists
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


install_dependencies()


# ---------------------------------------------------------
# Project path
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------
# Normal imports
# ---------------------------------------------------------

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

import Taskagotchi.Taskagotchi.Taskagotchi as task


# ---------------------------------------------------------
# Taskagotchi Window
# ---------------------------------------------------------

class TaskagotchiWindow(QWidget):

    def __init__(self):
        super().__init__()

        # Frameless and always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # Transparent window background
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )

        # -------------------------------------------------
        # Load images
        # -------------------------------------------------

        assets_path = Path(__file__).resolve().parent / "assets"

        image_path = assets_path / "Pot.png"
        sun_path = assets_path / "Sun.png"

        self.pet_image = QPixmap(str(image_path))
        self.sun_image = QPixmap(str(sun_path))

        if self.pet_image.isNull():
            raise FileNotFoundError(
                f"Could not load Taskagotchi image: {image_path}"
            )

        if self.sun_image.isNull():
            raise FileNotFoundError(
                f"Could not load sun image: {sun_path}"
            )

        # -------------------------------------------------
        # System state
        # -------------------------------------------------

        self.plugged_in = False
        self.cpu_percent = 0
        self.LeafPercent = 0
        self.TreePercent = 0

        self.system_timer = QTimer(self)
        self.system_timer.timeout.connect(self.update_system_state)

        # Update every 2 seconds
        self.system_timer.start(2000)

        # Get values immediately on startup
        self.update_system_state()

        # -------------------------------------------------
        # Window setup
        # -------------------------------------------------

        self.setFixedSize(self.pet_image.size())

        # Used for dragging
        self.drag_offset = None

        # Start near bottom-right corner
        screen = QApplication.primaryScreen().availableGeometry()

        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 20

        self.move(x, y)

    # -----------------------------------------------------
    # Update system state
    # -----------------------------------------------------

    def update_system_state(self):
        self.plugged_in = task.check_PluggedIn()
        self.cpu_percent = task.check_CPUusage(task.CPUCheckLength)
        self.LeafPercent = task.check_MemoryRatio()
        self.TreePercent = task.check_DiskRatio()

        # Repaint window with new values
        self.update()

    # -----------------------------------------------------
    # Draw images and text
    # -----------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)

        # Always draw pet
        painter.drawPixmap(
            -50,  # x
            0,    # y
            self.pet_image,
        )

        # Draw sun when plugged in
        if self.plugged_in:
            painter.drawPixmap(
                45,  # x
                10,  # y
                self.sun_image,
            )

        # -------------------------------------------------
        # Tree / Leaf Logic
        # -------------------------------------------------

        if self.TreePercent > 95:

            if self.LeafPercent > 95:
                print("LeafF")

            elif self.LeafPercent > 70:
                print("LeafF")

            elif self.LeafPercent > 35:
                print("LeafH")

            else:
                print("LeafN")

        elif self.TreePercent > 80:

            if self.LeafPercent > 95:
                print("LeafF")

            elif self.LeafPercent > 70:
                print("LeafF")

            elif self.LeafPercent > 35:
                print("LeafH")

            else:
                print("LeafN")

        elif self.TreePercent > 60:

            if self.LeafPercent > 95:
                print("LeafF")

            elif self.LeafPercent > 70:
                print("LeafF")

            elif self.LeafPercent > 35:
                print("LeafH")

            else:
                print("LeafN")

        elif self.TreePercent > 40:

            if self.LeafPercent > 95:
                print("LeafF")

            elif self.LeafPercent > 70:
                print("LeafF")

            elif self.LeafPercent > 35:
                print("LeafH")

            else:
                print("LeafN")

        elif self.TreePercent > 20:

            if self.LeafPercent > 95:
                print("LeafF")

            elif self.LeafPercent > 70:
                print("LeafF")

            elif self.LeafPercent > 35:
                print("LeafH")

            else:
                print("LeafN")

        else:

            if self.LeafPercent > 95:
                print("LeafF")

            elif self.LeafPercent > 70:
                print("LeafF")

            elif self.LeafPercent > 35:
                print("LeafH")

            else:
                print("LeafN")

        # -------------------------------------------------
        # Add text
        # -------------------------------------------------

        painter.setPen(Qt.GlobalColor.white)

        painter.drawText(
            70,
            75,
            f"CPU: {round(self.cpu_percent, 2)}%",
        )

        painter.drawText(
            70,
            90,
            f"RAM: {round(self.LeafPercent, 2)}%",
        )

        painter.drawText(
            70,
            105,
            f"Disk: {round(self.TreePercent, 2)}%",
        )

    # -----------------------------------------------------
    # Dragging
    # -----------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self.drag_offset is not None
        ):
            self.move(
                event.globalPosition().toPoint()
                - self.drag_offset
            )

            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = None
            event.accept()

    # -----------------------------------------------------
    # Keyboard
    # -----------------------------------------------------

    def keyPressEvent(self, event):
        # Escape closes Taskagotchi while developing
        if event.key() == Qt.Key.Key_Escape:
            self.close()

        else:
            super().keyPressEvent(event)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Taskagotchi")

    window = TaskagotchiWindow()

    window.show()
    window.raise_()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()