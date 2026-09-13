import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gemini.gemini_client import (
    DEFAULT_MODEL,
    GeminiAssistant,
)


class AskWorker(QThread):
    response_ready = Signal(str)
    request_failed = Signal(str)

    def __init__(self, assistant, prompt):
        super().__init__()
        self.assistant = assistant
        self.prompt = prompt

    def run(self):
        try:
            response = self.assistant.ask(
                self.prompt
            )
            self.response_ready.emit(response)

        except Exception as exc:
            self.request_failed.emit(str(exc))


class GeminiWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ask Gemini — Taskagotchi")
        self.resize(620, 520)

        self.worker = None

        try:
            self.assistant = GeminiAssistant()

        except Exception as exc:
            self.assistant = None

            QMessageBox.critical(
                self,
                "Gemini Setup",
                str(exc),
            )

        central = QWidget()
        layout = QVBoxLayout(central)

        title = QLabel("Ask Gemini")
        title_font = title.font()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)

        model_label = QLabel(
            f"Model: {DEFAULT_MODEL}"
        )

        self.transcript = QPlainTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText(
            "Ask Gemini for help breaking a "
            "scrolling loop, planning your next task, "
            "or anything else."
        )

        input_row = QHBoxLayout()

        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText(
            "Ask Gemini..."
        )
        self.prompt_input.returnPressed.connect(
            self.send_message
        )

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(
            self.send_message
        )

        input_row.addWidget(self.prompt_input)
        input_row.addWidget(self.send_button)

        bottom_row = QHBoxLayout()

        self.new_chat_button = QPushButton(
            "New Chat"
        )
        self.new_chat_button.clicked.connect(
            self.new_chat
        )

        self.status_label = QLabel("Ready")

        bottom_row.addWidget(
            self.new_chat_button
        )
        bottom_row.addStretch()
        bottom_row.addWidget(
            self.status_label
        )

        layout.addWidget(title)
        layout.addWidget(model_label)
        layout.addWidget(self.transcript)
        layout.addLayout(input_row)
        layout.addLayout(bottom_row)

        self.setCentralWidget(central)

        if self.assistant is None:
            self.set_input_enabled(False)

    def set_input_enabled(self, enabled):
        self.prompt_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        self.new_chat_button.setEnabled(enabled)

    def append_message(self, speaker, text):
        if self.transcript.toPlainText():
            self.transcript.appendPlainText("")

        self.transcript.appendPlainText(
            f"{speaker}:\n{text}"
        )

        scrollbar = (
            self.transcript.verticalScrollBar()
        )
        scrollbar.setValue(
            scrollbar.maximum()
        )

    def send_message(self):
        if self.assistant is None:
            return

        if self.worker is not None:
            return

        prompt = self.prompt_input.text().strip()

        if not prompt:
            return

        self.prompt_input.clear()

        self.append_message(
            "You",
            prompt,
        )

        self.status_label.setText(
            "Gemini is thinking..."
        )
        self.set_input_enabled(False)

        self.worker = AskWorker(
            self.assistant,
            prompt,
        )

        self.worker.response_ready.connect(
            self.handle_response
        )

        self.worker.request_failed.connect(
            self.handle_error
        )

        self.worker.finished.connect(
            self.worker_finished
        )

        self.worker.start()

    def handle_response(self, response):
        self.append_message(
            "Gemini",
            response,
        )

        self.status_label.setText("Ready")

    def handle_error(self, error):
        self.append_message(
            "Error",
            error,
        )

        self.status_label.setText(
            "Request failed"
        )

    def worker_finished(self):
        self.worker = None

        if self.assistant is not None:
            self.set_input_enabled(True)
            self.prompt_input.setFocus()

    def new_chat(self):
        if self.assistant is None:
            return

        self.assistant.new_chat()
        self.transcript.clear()
        self.status_label.setText(
            "New chat started"
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(
        "Taskagotchi Gemini"
    )

    window = GeminiWindow()
    window.show()
    window.raise_()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
