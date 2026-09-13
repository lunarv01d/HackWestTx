import sys
import subprocess
import importlib.util
import time
from collections import deque
from pathlib import Path
from threading import Lock


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

from pynput import mouse
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QMovie, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

import Taskagotchi.Taskagotchi.Taskagotchi as task


# ---------------------------------------------------------
# Doom-scroll tracker
# ---------------------------------------------------------

class DoomTracker:
    """
    Tracks recent global scroll-wheel / trackpad scroll activity.

    Tree health falls while the user is actively scrolling.
    Tree health recovers while the user takes a break.

    Duration controls tree stage.
    Recent scroll intensity controls Good / Mid / Bad leaves.
    """

    def __init__(
        self,
        fire_seconds=1200,
        recovery_multiplier=2.0,
        activity_window=10,
        min_scrolls=3,
        mid_scrolls=8,
        bad_scrolls=16,
    ):
        # 1200 seconds = 20 minutes of sustained scrolling
        # before the tree reaches 0% health.
        self.fire_seconds = fire_seconds

        # 2.0 means the tree recovers twice as fast
        # as it deteriorates.
        self.recovery_multiplier = recovery_multiplier

        # Number of recent seconds used to judge
        # whether scrolling is active/intense.
        self.activity_window = activity_window

        # Thresholds for active scrolling and leaf quality.
        self.min_scrolls = min_scrolls
        self.mid_scrolls = mid_scrolls
        self.bad_scrolls = bad_scrolls

        self.doom_seconds = 0.0
        self.scroll_events = deque()
        self.last_update = time.monotonic()
        self.lock = Lock()

        # Global scroll listener.
        # This listens only for scrolling, not keyboard input.
        self.listener = mouse.Listener(
            on_scroll=self._on_scroll
        )

        self.listener.start()

    def _on_scroll(self, x, y, dx, dy):
        now = time.monotonic()

        with self.lock:
            self.scroll_events.append(now)

    def update(self):
        now = time.monotonic()

        with self.lock:
            elapsed = now - self.last_update
            self.last_update = now

            cutoff = now - self.activity_window

            # Forget old scroll events.
            while (
                self.scroll_events
                and self.scroll_events[0] < cutoff
            ):
                self.scroll_events.popleft()

            recent_scrolls = len(self.scroll_events)

            is_scrolling = (
                recent_scrolls >= self.min_scrolls
            )

            if is_scrolling:
                # Doomscrolling makes the tree deteriorate.
                self.doom_seconds += elapsed

                self.doom_seconds = min(
                    self.doom_seconds,
                    self.fire_seconds,
                )

            else:
                # Taking a break lets the tree recover.
                self.doom_seconds -= (
                    elapsed
                    * self.recovery_multiplier
                )

                self.doom_seconds = max(
                    0.0,
                    self.doom_seconds,
                )

            # 100 = fully healthy
            # 0   = completely cooked
            tree_health = (
                1.0
                - (
                    self.doom_seconds
                    / self.fire_seconds
                )
            ) * 100.0

            tree_health = max(
                0.0,
                min(100.0, tree_health),
            )

            # Scroll intensity drives leaf condition.
            if recent_scrolls >= self.bad_scrolls:
                leaf_condition = "Bad"

            elif recent_scrolls >= self.mid_scrolls:
                leaf_condition = "Mid"

            else:
                leaf_condition = "Good"

            return (
                tree_health,
                self.doom_seconds,
                is_scrolling,
                recent_scrolls,
                leaf_condition,
            )

    def stop(self):
        self.listener.stop()


# ---------------------------------------------------------
# Taskagotchi Window
# ---------------------------------------------------------

class TaskagotchiWindow(QWidget):

    def __init__(self):
        super().__init__()

        # -------------------------------------------------
        # Doom-scroll tuning
        # -------------------------------------------------

        # Production / demo default:
        # 20 minutes of sustained scrolling = fire.
        #
        # For quick testing, temporarily change this to 60.
        self.doom_tracker = DoomTracker(
            fire_seconds=1200,
            recovery_multiplier=2.0,
            activity_window=10,
            min_scrolls=3,
            mid_scrolls=8,
            bad_scrolls=16,
        )

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

        # Disk
        self.disk_used_percent = 0

        # Network
        self.net_upload = 0
        self.net_download = 0

        # Doom-scroll state
        self.tree_health = 100.0
        self.doom_seconds = 0.0
        self.is_scrolling = False
        self.recent_scrolls = 0
        self.leaf_condition = "Good"

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
    # Update state
    # -----------------------------------------------------

    def update_system_state(self):
        # Computer stats remain informational.
        self.plugged_in = task.check_PluggedIn()

        self.cpu_percent = task.check_CPUusage(
            task.CPUCheckLength
        )

        self.ram_used_percent = task.check_MemoryRatio()
        self.disk_used_percent = task.check_DiskRatio()

        self.net_upload, self.net_download = (
            task.check_netUsage()
        )

        # Doom scrolling now drives the actual pet/tree.
        (
            self.tree_health,
            self.doom_seconds,
            self.is_scrolling,
            self.recent_scrolls,
            self.leaf_condition,
        ) = self.doom_tracker.update()

        self.update()

    # -----------------------------------------------------
    # Tree / leaf selection
    # -----------------------------------------------------

    def get_tree_stage(self):
        """
        Doom-scroll tree health controls tree size.

        81-100% health -> Stage 5
        61-80% health  -> Stage 4
        41-60% health  -> Stage 3
        21-40% health  -> Stage 2
        1-20% health   -> Stage 1
        0% health      -> Fire, no tree
        """

        if self.tree_health > 80:
            return 5

        elif self.tree_health > 60:
            return 4

        elif self.tree_health > 40:
            return 3

        elif self.tree_health > 20:
            return 2

        else:
            return 1

    def get_leaf_condition(self):
        """
        Recent scroll intensity controls leaf condition.
        """

        return self.leaf_condition

    def get_tree_image(self):
        stage = self.get_tree_stage()
        condition = self.get_leaf_condition()

        return self.tree_images[(stage, condition)]

    def is_on_fire(self):
        """
        Tree reaches fire state after the configured
        sustained doom-scroll duration.
        """

        return self.tree_health <= 0

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

        # Draw tree unless it has completely burned out.
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

        # Keep existing plugged-in sun behavior.
        if self.plugged_in:
            painter.drawPixmap(
                self.sun_x,
                self.sun_y,
                self.sun_image,
            )

        # Fire replaces the tree at 0 health.
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

        # Doom-scroll status
        doom_minutes = self.doom_seconds / 60.0

        if self.is_scrolling:
            scroll_status = "Scrolling"
        else:
            scroll_status = "Recovering"

        painter.drawText(
            70,
            150,
            f"Tree: {round(self.tree_health, 1)}%",
        )

        painter.drawText(
            70,
            165,
            f"{scroll_status}: {doom_minutes:.1f} min",
        )

        painter.drawText(
            70,
            180,
            f"Scrolls/10s: {self.recent_scrolls}",
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
    # Cleanup / Keyboard
    # -----------------------------------------------------

    def closeEvent(self, event):
        self.doom_tracker.stop()
        event.accept()

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
