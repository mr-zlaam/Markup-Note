"""Editor canvas panel with Obsidian-style cursor-aware Live Preview and debounced auto-save."""

import re
from typing import Optional

from PyQt6.QtCore import QRect, QRectF, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QTextBlock,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.note import Note
from ui.highlighter import MarkdownHighlighter
from utils.markdown import (
    CHECKBOX_PATTERN,
    get_auto_continue_prefix,
    get_checkbox_info,
    is_checkbox_line,
)


class MarkdownEditor(QTextEdit):
    """Pure plain-text Markdown editor with cursor-aware Obsidian Live Preview."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("MarkdownEditor")
        self.setPlaceholderText("Write your note in Markdown...")
        self.setAcceptRichText(False)

        # Guarantee strict Left-to-Right layout
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        opt = self.document().defaultTextOption()
        opt.setTextDirection(Qt.LayoutDirection.LeftToRight)
        opt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.document().setDefaultTextOption(opt)

        # Set base editor font in Python so QSyntaxHighlighter can freely scale headings
        base_font = QFont("Cantarell", 12)
        self.setFont(base_font)
        self.document().setDefaultFont(base_font)

        # Attach cursor-aware Obsidian syntax highlighter
        self.highlighter = MarkdownHighlighter(self.document())
        self.cursorPositionChanged.connect(self._on_cursor_position_changed)

    def _on_cursor_position_changed(self) -> None:
        """Rehighlight the previous and current lines when the cursor moves between lines."""
        new_block = self.textCursor().block()
        new_block_num = new_block.blockNumber()
        old_block_num = self.highlighter.active_block_number

        if new_block_num != old_block_num:
            self.highlighter.active_block_number = new_block_num
            old_block = self.document().findBlockByNumber(old_block_num)
            if old_block.isValid():
                self.highlighter.rehighlightBlock(old_block)
            if new_block.isValid():
                self.highlighter.rehighlightBlock(new_block)
        self.viewport().update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the editor text and overlay crisp graphical checkboxes on checklist lines."""
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        block = self.document().firstBlock()
        viewport_height = self.viewport().height()

        while block.isValid():
            if block.isVisible():
                text = block.text()
                match = CHECKBOX_PATTERN.match(text)
                if match:
                    indent, _, status, _ = match.groups()
                    c = QTextCursor(block)
                    c.setPosition(block.position() + len(indent))
                    rect = self.cursorRect(c)

                    if rect.top() > viewport_height:
                        break
                    if rect.bottom() >= 0:
                        self._draw_checkbox(painter, rect, status.lower() == "x")
            block = block.next()

        painter.end()

    def _draw_checkbox(self, painter: QPainter, cursor_rect: QRect, is_checked: bool) -> None:
        """Draw a rounded 14x14 checkbox and vector tick mark at the given cursor rect."""
        box_size = 14.0
        box_x = float(cursor_rect.left() + 3)
        box_y = float(cursor_rect.top()) + (cursor_rect.height() - box_size) / 2.0
        box_rect = QRectF(box_x, box_y, box_size, box_size)

        if is_checked:
            painter.setPen(QPen(QColor("#0a84ff"), 1.5))
            painter.setBrush(QBrush(QColor("#0a84ff")))
            painter.drawRoundedRect(box_rect, 3.5, 3.5)

            check_pen = QPen(QColor("#ffffff"), 1.9)
            check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(check_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            path = QPainterPath()
            path.moveTo(box_x + 3.2, box_y + 7.2)
            path.lineTo(box_x + 5.9, box_y + 9.9)
            path.lineTo(box_x + 10.8, box_y + 4.3)
            painter.drawPath(path)
        else:
            painter.setPen(QPen(QColor("#787880"), 1.5))
            painter.setBrush(QBrush(QColor("#262629")))
            painter.drawRoundedRect(box_rect, 3.5, 3.5)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle clicking directly on graphical checkboxes to toggle their state."""
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            block = cursor.block()
            text = block.text()
            match = CHECKBOX_PATTERN.match(text)

            if match:
                indent, prefix, _, _ = match.groups()
                prefix_end = len(indent) + len(prefix)
                c = QTextCursor(block)
                c.setPosition(block.position() + len(indent))
                rect = self.cursorRect(c)
                box_x = float(rect.left() + 2)
                box_y = float(rect.top()) + (rect.height() - 16.0) / 2.0
                hit_rect = QRectF(box_x - 4.0, box_y - 4.0, 24.0, 24.0)

                char_idx = cursor.positionInBlock()
                if hit_rect.contains(event.position()) or (len(indent) <= char_idx < prefix_end):
                    self._toggle_checkbox_at_block(block)
                    return

        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle Ctrl+Enter checkbox toggling, smart list continuation, and Tab indentation."""
        cursor = self.textCursor()
        block = cursor.block()
        line_text = block.text()
        pos_in_block = cursor.positionInBlock()

        # 0. Auto-expand "- []" into "- [ ]" when the user types closing bracket "]"
        if event.text() == "]" and re.match(r"^\s*[-*+]\s*\[$", line_text[:pos_in_block]):
            cursor.beginEditBlock()
            cursor.insertText(" ]")
            cursor.endEditBlock()
            self.viewport().update()
            return

        # 1. Backspace right after a checkbox removes the entire checkbox prefix cleanly
        if (
            event.key() == Qt.Key.Key_Backspace
            and not cursor.hasSelection()
        ):
            cb_info = get_checkbox_info(line_text)
            if cb_info is not None:
                _, _, prefix_end, _ = cb_info
                if pos_in_block == prefix_end:
                    indent_len = len(line_text) - len(line_text.lstrip())
                    cursor.beginEditBlock()
                    cursor.setPosition(block.position() + indent_len)
                    cursor.setPosition(
                        block.position() + prefix_end,
                        QTextCursor.MoveMode.KeepAnchor,
                    )
                    cursor.removeSelectedText()
                    cursor.endEditBlock()
                    self.viewport().update()
                    return

        # 2. Ctrl+Enter: Toggle checkbox on current line or convert line into a checkbox
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            if is_checkbox_line(line_text):
                self._toggle_checkbox_at_block(block)
            else:
                cursor.beginEditBlock()
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                cursor.insertText("- [ ] ")
                cursor.endEditBlock()
                self.viewport().update()
            return

        # 3. Enter key: Auto-continue checklists and bulleted/numbered lists
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            event.modifiers() & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier)
        ):
            continuation = get_auto_continue_prefix(line_text)
            if continuation is not None:
                if continuation == "":
                    # Empty list/checkbox item -> remove marker and exit list
                    cursor.beginEditBlock()
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    cursor.movePosition(
                        QTextCursor.MoveOperation.EndOfBlock,
                        QTextCursor.MoveMode.KeepAnchor,
                    )
                    cursor.removeSelectedText()
                    cursor.endEditBlock()
                    self.viewport().update()
                    return
                else:
                    cursor.beginEditBlock()
                    # Normalize "- []" on the current line to "- [ ]" if needed
                    cb_info = get_checkbox_info(line_text)
                    if cb_info is not None:
                        b_start, b_end, _, is_chk = cb_info
                        if (b_end - b_start) == 2:
                            fix_cursor = QTextCursor(block)
                            fix_cursor.setPosition(block.position() + b_start)
                            fix_cursor.setPosition(
                                block.position() + b_end,
                                QTextCursor.MoveMode.KeepAnchor,
                            )
                            fix_cursor.insertText("[x]" if is_chk else "[ ]")
                    cursor.insertText("\n" + continuation)
                    cursor.endEditBlock()
                    self.ensureCursorVisible()
                    self.viewport().update()
                    return

        # 4. Tab & Shift+Tab: Indent / unindent by 2 spaces
        if event.key() == Qt.Key.Key_Tab:
            cursor.beginEditBlock()
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                spaces_to_remove = 2 if line_text.startswith("  ") else (1 if line_text.startswith(" ") else 0)
                if spaces_to_remove > 0:
                    c = QTextCursor(block)
                    c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    for _ in range(spaces_to_remove):
                        c.deleteChar()
            else:
                cursor.insertText("  ")
            cursor.endEditBlock()
            self.viewport().update()
            return

        super().keyPressEvent(event)

    def _toggle_checkbox_at_block(self, block: QTextBlock) -> None:
        """Atomically toggle '[ ]' / '[]' <-> '[x]' in the given text block."""
        text = block.text()
        info = get_checkbox_info(text)
        if info is None:
            return

        bracket_start, bracket_end, prefix_end, is_checked = info
        replacement = "[ ] " if is_checked else "[x] "

        edit_cursor = QTextCursor(self.document())
        edit_cursor.beginEditBlock()
        edit_cursor.setPosition(block.position() + bracket_start)
        edit_cursor.setPosition(
            block.position() + max(bracket_end, prefix_end),
            QTextCursor.MoveMode.KeepAnchor,
        )
        edit_cursor.insertText(replacement)
        edit_cursor.endEditBlock()
        self.viewport().update()


class EditorPanel(QWidget):
    """Right pane editor containing metadata header and the editor canvas."""

    content_saved = pyqtSignal(str)  # Emits new content when debounced auto-save fires
    create_note_with_content = pyqtSignal(str)  # Emitted when user types on empty canvas
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
        self.word_count_label.setStyleSheet("color: #7a7a7a; font-size: 11px; padding-right: 6px;")
        header.addWidget(self.word_count_label)

        self.delete_btn = QPushButton("Delete", parent=self)
        self.delete_btn.setObjectName("ActionBtn")
        self.delete_btn.setToolTip("Delete note (Ctrl+D)")
        self.delete_btn.clicked.connect(self.delete_requested.emit)
        header.addWidget(self.delete_btn)

        layout.addLayout(header)

        # Editor canvas
        self.editor = MarkdownEditor(parent=self)
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor)

    def load_note(self, note: Optional[Note]) -> None:
        """Load note markdown into the editor as pure plain text with live highlighting."""
        self._current_note = note
        self._save_timer.stop()

        if note is None:
            self.editor.blockSignals(True)
            self.editor.setPlainText("")
            self.meta_label.setText("No note selected")
            self.word_count_label.setText("0 words")
            self.editor.blockSignals(False)
            return

        # Clean any accidental escaped headings (\# ) and normalize "- []" to "- [ ]"
        cleaned_content = re.sub(r"^\\(#+\s)", r"\1", note.content, flags=re.MULTILINE)
        cleaned_content = re.sub(
            r"^(\s*[-*+]\s*)\[\](?=\s|$)", r"\1[ ]", cleaned_content, flags=re.MULTILINE
        )

        self.editor.blockSignals(True)
        self.editor.setPlainText(cleaned_content)
        self.editor.highlighter.active_block_number = self.editor.textCursor().block().blockNumber()
        self.editor.highlighter.rehighlight()
        self.editor.viewport().update()
        self.editor.blockSignals(False)

        self.update_meta(note)
        self._update_word_count()

    def update_meta(self, note: Note) -> None:
        """Update only the metadata header without reloading the editor document."""
        self._current_note = note
        folder_name = note.path.parent.name
        self.meta_label.setText(f"{folder_name}  •  Edited {note.formatted_time}")

    def get_content(self) -> str:
        """Return the pure plain-text Markdown content."""
        return self.editor.toPlainText()

    def _on_text_changed(self) -> None:
        self._update_word_count()
        self._save_timer.start()

    def _update_word_count(self) -> None:
        words = len(self.editor.toPlainText().split())
        self.word_count_label.setText(f"{words} words")

    def _trigger_auto_save(self) -> None:
        """Emit save signal with latest Markdown text."""
        content = self.editor.toPlainText()
        if self._current_note is None:
            if content.strip():
                self.create_note_with_content.emit(content)
        else:
            self.content_saved.emit(content)
