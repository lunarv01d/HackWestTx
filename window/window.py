import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget


class TaskagotchiWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Window settings:
        # - No title bar / border
        # - Stay above other windows
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # Allow actual per-pixel transparency
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )

        # Load image relative to THIS Python file
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

        # Make the window exactly the size of the PNG
        self.setFixedSize(self.pet_image.size())

        # Used while dragging the pet
        self.drag_offset = None

        # Start near the bottom-right of the usable screen
        screen = QApplication.primaryScreen().availableGeometry()

        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 20

        self.move(x, y)

    def paintEvent(self, event):
        """
        Draw the PNG directly onto the transparent window.
        Transparent pixels in the PNG remain transparent.
        """
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pet_image)

    def mousePressEvent(self, event):
        """
        Start dragging when the left mouse button is pressed.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(self, event):
        """
        Move the Taskagotchi while the left mouse button is held.
        """
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self.drag_offset is not None
        ):
            new_position = (
                event.globalPosition().toPoint()
                - self.drag_offset
            )

            self.move(new_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Stop dragging when the mouse button is released.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = None
            event.accept()

    def keyPressEvent(self, event):
        """
        Escape closes the window during development.
        """
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Taskagotchi")

    window = TaskagotchiWindow()
    window.show()
    window.raise_()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()