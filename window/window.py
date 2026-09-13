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

        self.shadow_x = -50
        self.shadow_y = 0

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
        sun_path = assets_path / "Sun.gif"
        fire_path = assets_path / "Fire.gif"
        shadow_path = assets_path / "DropShadow.png"

        self.shadow_image = QPixmap(str(shadow_path))
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

        if self.shadow_image.isNull():
            raise FileNotFoundError(
                f"Could not load shadow image: {shadow_path}"
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

        self.fire_movie.frameChanged.connect(self.update)
        self.fire_movie.start()

        # -------------------------------------------------
        # System state
        # -------------------------------------------------

        self.plugged_in = False
        self.cpu_percent = 0

        # RAM
        self.ram_used_percent = 0
        self.LeafPercent = 0

        # Disk
        self.disk_used_percent = 0
        self.TreePercent = 0

        # Network
        self.net_upload = 0
        self.net_download = 0

        self.system_timer = QTimer(self)
        self.system_timer.timeout.connect(
            self.update_system_state
        )

        self.system_timer.start(2000)
        self.update_system_state()

        # -------------------------------------------------
        # Window setup
        # -------------------------------------------------

        self.setFixedSize(
            self.pet_image.width() + 120,
            self.pet_image.height() + 60,
        )

        self.drag_offset = None

        screen = QApplication.primaryScreen().availableGeometry()

        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 20

        self.move(x, y)

    # -----------------------------------------------------
    # Update system state
    # -----------------------------------------------------

    def update_system_state(self):
        self.plugged_in = task.check_PluggedIn()

        self.cpu_percent = task.check_CPUusage(
            task.CPUCheckLength
        )

        # Actual RAM usage for text display
        self.ram_used_percent = task.check_MemoryRatio()

        # Available RAM controls leaf condition
        self.LeafPercent = 100 - self.ram_used_percent

        # Actual disk usage for text display
        self.disk_used_percent = task.check_DiskRatio()

        # Free disk percentage controls tree stage
        self.TreePercent = 100 - self.disk_used_percent

        self.net_upload, self.net_download = task.check_netUsage()

        self.update()

    # -----------------------------------------------------
    # Tree / leaf selection
    # -----------------------------------------------------

    def get_tree_stage(self):
        """
        Free disk space controls tree fullness.

        81-100% free -> Stage 5
        61-80% free  -> Stage 4
        41-60% free  -> Stage 3
        21-40% free  -> Stage 2
        6-20% free   -> Stage 1
        0-5% free    -> Fire, no tree
        """

        free_disk = self.TreePercent

        if free_disk > 80:
            return 5
        elif free_disk > 60:
            return 4
        elif free_disk > 40:
            return 3
        elif free_disk > 20:
            return 2
        else:
            return 1

    def get_leaf_condition(self):
        """
        Available RAM controls leaf condition.
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
        5% or less free disk space means:
        hide the tree and show fire instead.
        """

        return self.TreePercent <= 5

    # -----------------------------------------------------
    # Draw images and text
    # -----------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw shadow
        painter.drawPixmap(
            self.shadow_x,
            self.shadow_y,
            self.shadow_image,
        )

        # Draw one of the five tree stages unless disk is critical
        if not self.is_on_fire():
            tree_image = self.get_tree_image()

            painter.drawPixmap(
                self.tree_x,
                self.tree_y,
                tree_image,
            )

        # Draw pot
        painter.drawPixmap(
            self.pet_x,
            self.pet_y,
            self.pet_image,
        )

        # Draw sun when plugged in
        if self.plugged_in:
            painter.drawPixmap(
                self.sun_x,
                self.sun_y,
                self.sun_image,
            )

        # Draw fire instead of a tree when <= 5% disk is free
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
            f"RAM: {round(self.ram_used_percent, 2)}%",
        )

        painter.drawText(
            70,
            105,
            f"Disk: {round(self.disk_used_percent, 2)}%",
        )

        painter.drawText(
            70,
            120,
            f"Up: {round(self.net_upload, 2)} Mb/s",
        )

        painter.drawText(
            70,
            135,
            f"Down: {round(self.net_download, 2)} Mb/s",
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
