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
        "psutil": "psutil"
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
            stdout=subprocess.DEVNULL
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
                *missing_packages
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
            True
        )

        # -------------------------------------------------
        # Load pet image
        # -------------------------------------------------

        image_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "Pot.png"
        )

        self.pet_image = QPixmap(str(image_path))

        if self.pet_image.isNull():
            raise FileNotFoundError(
                f"Could not load Taskagotchi image: {image_path}"
            )

        # -------------------------------------------------
        # Load sun image
        # -------------------------------------------------

        sun_path = (
            Path(__file__).resolve().parent
            / "assets"
            / "Sun.png"
        )

        self.sun_image = QPixmap(str(sun_path))

        if self.sun_image.isNull():
            raise FileNotFoundError(
                f"Could not load sun image: {sun_path}"
            )

        # -------------------------------------------------
        # Power state
        # -------------------------------------------------

        self.plugged_in = False

        self.power_timer = QTimer(self)
        self.power_timer.timeout.connect(self.update_power_state)

        # Check power every 2 seconds
        self.power_timer.start(2000)

        # Check immediately on startup
        self.update_power_state()

        # -------------------------------------------------
        # Window setup
        # -------------------------------------------------

        # Size window to pet image
        self.setFixedSize(self.pet_image.size())

        # Used for dragging
        self.drag_offset = None

        # Start near bottom-right corner
        screen = QApplication.primaryScreen().availableGeometry()

        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 20

        self.move(x, y)

    # -----------------------------------------------------
    # Update power state
    # -----------------------------------------------------

    def update_power_state(self):
        self.plugged_in = task.check_PluggedIn()

        # Repaint the window
        self.update()

    # -----------------------------------------------------
    # Draw images
    # -----------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)

        # Always draw the pet
        painter.drawPixmap(
            -50,  #x
            0,  #y
            self.pet_image
        )

        # Draw the sun only while plugged in
        if self.plugged_in:
            painter.drawPixmap(
                45,    #x
                10,     #y
                self.sun_image
            )



    # -----------------------------------------------------
    # Add Text
    # -----------------------------------------------------

        cpu_percent = task.check_CPUusage(task.CPUCheckLength)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(70, 75, f"CPU: {cpu_percent}%")
        
        
        ram_percent = task.MemPer()
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(70, 90, f"RAM: {ram_percent}%")




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