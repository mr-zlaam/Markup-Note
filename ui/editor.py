"""Editor canvas panel with debounced auto-save and title extraction."""

from typing import Optional

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.note import Note


class MarkdownEditor(QPlainTextEdit):
    """Custom plain text editor prepared for markdown styling and live events."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("MarkdownEditor")
        self.setPlaceholderText("Write your note here... Type / for markdown commands")


class EditorPanel(QWidget):
    """Right pane editor containing metadata header and the editor canvas."""

    content_saved = pyqtSignal(str)  # Emits new content when debounced auto-save fires
    delete_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._current_note: Optional[Note] = None

        # Debounce timer for smooth non-blocking auto-save
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._trigger_auto_save)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 12)
        layout.setSpacing(8)

        # Header bar (Folder name, word count, delete button)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        self.meta_label = QLabel("", parent=self)
        self.meta_label.setStyleSheet("color: #7a7a7a; font-size: 11px;")
        header.addWidget(self.meta_label)

        header.addStretch()

        self.word_count_label = QLabel("0 words", parent=self)
        self.word_count_label.setStyleSheet("color: #7a7a7a; font-size: 11px;")
        header.addWidget(self.word_count_label)

        self.delete_btn = QPushButton("🗑️", parent=self)
        self.delete_btn.setObjectName("ActionBtn")
        self.delete_btn.setToolTip("Delete note")
        self.delete_btn.setFixedSize(26, 26)
        self.delete_btn.clicked.connect(self.delete_requested.emit)
        header.addWidget(self.delete_btn)

        layout.addLayout(header)

        # Editor canvas
        self.editor = MarkdownEditor(parent=self)
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor)

    def load_note(self, note: Optional[Note]) -> None:
        """Load note content into the editor and reset timers."""
        self._current_note = note
        self._save_timer.stop()

        if note is None:
            self.editor.blockSignals(True)
            self.editor.setPlainText("")
            self.editor.setEnabled(False)
            self.meta_label.setText("")
            self.word_count_label.setText("0 words")
            self.editor.blockSignals(False)
            return

        self.editor.setEnabled(True)
        self.editor.blockSignals(True)
        self.editor.setPlainText(note.content)
        self.editor.blockSignals(False)

        folder_name = note.path.parent.name
        self.meta_label.setText(f"📁 {folder_name}  •  Edited {note.formatted_time}")
        self._update_word_count(note.content)

    def get_content(self) -> str:
        """Return the current text inside the editor."""
        return self.editor.toPlainText()

    def _on_text_changed(self) -> None:
        content = self.editor.toPlainText()
        self._update_word_count(content)
        # Restart debounce timer
        self._save_timer.start()

    def _update_word_count(self, content: str) -> None:
        words = len(content.split())
        self.word_count_label.setText(f"{words} words")

    def _trigger_auto_save(self) -> None:
        """Emit save signal with latest text."""
        content = self.editor.toPlainText()
        self.content_saved.emit(content)
