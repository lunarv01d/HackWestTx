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
from PySide6.QtGui import QMovie, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

import Taskagotchi.Taskagotchi.Taskagotchi as task


# ---------------------------------------------------------
# Taskagotchi Window
# ---------------------------------------------------------

class TaskagotchiWindow(QWidget):

    def __init__(self):
        super().__init__()

        # -------------------------------------------------
        # Easy-to-adjust drawing positions
        # -------------------------------------------------

        self.pet_x = -50
        self.pet_y = 0

        self.tree_x = -50
        self.tree_y = 0

        self.sun_x = 45
        self.sun_y = 10

        self.fire_x = -50
        self.fire_y = 0

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
        fire_path = assets_path / "Fire.gif"

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
        # Load tree images
        # -------------------------------------------------

        self.tree_images = {}

        for stage in range(1, 6):
            for condition in ("Good", "Mid", "Bad"):
                tree_path = (
                    assets_path
                    / f"TreeStg{stage}{condition}.png"
                )

                tree_image = QPixmap(str(tree_path))

                if tree_image.isNull():
                    raise FileNotFoundError(
                        f"Could not load tree image: {tree_path}"
                    )

                self.tree_images[(stage, condition)] = tree_image

        # -------------------------------------------------
        # Load animated fire GIF
        # -------------------------------------------------

        self.fire_movie = QMovie(str(fire_path))

        if not self.fire_movie.isValid():
            raise FileNotFoundError(
                f"Could not load fire animation: {fire_path}"
            )

        # Repaint whenever the GIF moves to another frame.
        self.fire_movie.frameChanged.connect(self.update)
        self.fire_movie.start()

        # -------------------------------------------------
        # System state
        # -------------------------------------------------

        self.plugged_in = False
        self.cpu_percent = 0
        self.LeafPercent = 0
        self.TreePercent = 0

        self.system_timer = QTimer(self)
        self.system_timer.timeout.connect(self.update_system_state)

        # Update every 2 seconds.
        self.system_timer.start(2000)

        # Get values immediately on startup.
        self.update_system_state()

        # -------------------------------------------------
        # Window setup
        # -------------------------------------------------

        self.setFixedSize(self.pet_image.size())

        # Used for dragging.
        self.drag_offset = None

        # Start near bottom-right corner.
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
        if sys.platform == ('darwin'):
            self.LeafPercent = 100 - task.check_MemoryRatio()
        elif sys.platform == ('win32'):
            self.LeafPercent = task.check_MemoryRatio()
        self.TreePercent = task.check_DiskRatio()

        # Repaint the window with the new values.
        self.update()

    # -----------------------------------------------------
    # Tree / leaf selection
    # -----------------------------------------------------

    def get_tree_stage(self):
        """
        Disk usage controls the tree growth stage.
        """
        if self.TreePercent > 80:
            return 5
        elif self.TreePercent > 60:
            return 4
        elif self.TreePercent > 40:
            return 3
        elif self.TreePercent > 20:
            return 2
        else:
            return 1

    def get_leaf_condition(self):
        """
        RAM usage controls the leaf condition.

        Current behavior:
            > 70% RAM  -> Good
            35-70% RAM -> Mid
            <= 35% RAM -> Bad

        Reverse these if high RAM usage is supposed to hurt the tree.
        """
        if self.LeafPercent > 70:
            return "Good"
        elif self.LeafPercent > 35:
            return "Mid"
        else:
            return "Bad"

    def get_tree_image(self):
        stage = self.get_tree_stage()
        condition = self.get_leaf_condition()

        return self.tree_images[(stage, condition)]

    def is_on_fire(self):
        """
        Show Fire.gif whenever RAM or disk use exceeds 95%.
        """
        return (
            self.LeafPercent > 95
            or self.TreePercent > 95
        )

    # -----------------------------------------------------
    # Draw images and text
    # -----------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw the selected tree.
        tree_image = self.get_tree_image()

        painter.drawPixmap(
            self.tree_x,
            self.tree_y,
            tree_image,
        )

        # Draw the pot.
        painter.drawPixmap(
            self.pet_x,
            self.pet_y,
            self.pet_image,
        )

        # Draw the sun only while plugged in.
        if self.plugged_in:
            painter.drawPixmap(
                self.sun_x,
                self.sun_y,
                self.sun_image,
            )

        # Draw animated fire if RAM or disk is above 95%.
        if self.is_on_fire():
            fire_frame = self.fire_movie.currentPixmap()

            if not fire_frame.isNull():
                painter.drawPixmap(
                    self.fire_x,
                    self.fire_y,
                    fire_frame,
                )

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
        # Escape closes Taskagotchi while developing.
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
