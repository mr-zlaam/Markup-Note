"""Editor canvas panel with WYSIWYG Markdown Live Preview, hidden syntax, and debounced auto-save."""

import re
from typing import Optional

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QKeyEvent,
    QMouseEvent,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
    QTextOption,
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
from ui.slash_menu import SlashCommand, SlashCommandPalette


class MarkdownEditor(QTextEdit):
    """Rich Markdown editor where markdown syntax is hidden, rendered, and clean."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("MarkdownEditor")
        self.setPlaceholderText("Write your note here... Type / for markdown commands")

        # Guarantee strict Left-to-Right layout
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        opt = self.document().defaultTextOption()
        opt.setTextDirection(Qt.LayoutDirection.LeftToRight)
        opt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.document().setDefaultTextOption(opt)

        # Slash command palette
        self.slash_palette = SlashCommandPalette(self)
        self.slash_palette.command_selected.connect(self._on_slash_command_selected)
        self._slash_start_pos: Optional[int] = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle clicking directly on visual checkboxes."""
        if self.slash_palette.isVisible():
            self.slash_palette.hide()

        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            block = cursor.block()
            marker = block.blockFormat().marker()

            if marker in (
                QTextBlockFormat.MarkerType.Unchecked,
                QTextBlockFormat.MarkerType.Checked,
            ):
                # Click near margin or start of line toggles checkbox
                if cursor.positionInBlock() <= 2 or event.pos().x() < 60:
                    self._toggle_checkbox_at_block(block)
                    return

        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle slash menu, instant markdown symbol transformations, and shortcuts."""
        cursor = self.textCursor()

        # 1. Forward keys to active Slash Palette
        if self.slash_palette.isVisible():
            if event.key() == Qt.Key.Key_Down:
                self.slash_palette.select_next()
                return
            elif event.key() == Qt.Key.Key_Up:
                self.slash_palette.select_previous()
                return
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.slash_palette.execute_current()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.slash_palette.hide()
                return

        # 2. Ctrl+Enter: Toggle checkbox on current line or convert to checkbox
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            block = cursor.block()
            marker = block.blockFormat().marker()
            if marker in (
                QTextBlockFormat.MarkerType.Unchecked,
                QTextBlockFormat.MarkerType.Checked,
            ):
                self._toggle_checkbox_at_block(block)
            else:
                self._convert_block_to_checkbox()
            return

        # 3. Space key: Transform markdown shortcuts (# , ## , - , 1. , [] , > ) into rich elements
        if event.key() == Qt.Key.Key_Space:
            block = cursor.block()
            text = block.text()
            if text == "#":
                self._convert_block_to_heading(1)
                return
            elif text == "##":
                self._convert_block_to_heading(2)
                return
            elif text == "###":
                self._convert_block_to_heading(3)
                return
            elif text in ("-", "*"):
                self._convert_block_to_bullet()
                return
            elif text in ("1.", "1)"):
                self._convert_block_to_numbered()
                return
            elif text in ("[]", "[ ]"):
                self._convert_block_to_checkbox()
                return
            elif text == ">":
                self._convert_block_to_quote()
                return

        super().keyPressEvent(event)

        # 4. Check for Slash Menu trigger
        self._check_slash_trigger(event)

    def _check_slash_trigger(self, event: QKeyEvent) -> None:
        """Open or filter slash menu when '/' is typed."""
        cursor = self.textCursor()
        block = cursor.block()
        line_text = block.text()
        pos_in_line = cursor.positionInBlock()

        if event.text() == "/":
            prefix_before_slash = line_text[: pos_in_line - 1]
            if not prefix_before_slash.strip():
                self._slash_start_pos = cursor.position() - 1
                self._show_slash_palette()
                return

        if self.slash_palette.isVisible() and self._slash_start_pos is not None:
            if cursor.position() <= self._slash_start_pos:
                self.slash_palette.hide()
                self._slash_start_pos = None
                return

            query = self.toPlainText()[self._slash_start_pos + 1 : cursor.position()]
            if "\n" in query:
                self.slash_palette.hide()
                self._slash_start_pos = None
                return
            self.slash_palette.populate(query)

    def _show_slash_palette(self) -> None:
        """Position and show the slash menu."""
        cursor_rect = self.cursorRect()
        popup_pos = self.mapToGlobal(cursor_rect.bottomLeft())
        self.slash_palette.populate("")
        self.slash_palette.move(popup_pos.x(), popup_pos.y() + 4)
        self.slash_palette.show()

    def _on_slash_command_selected(self, cmd: SlashCommand) -> None:
        """Execute selected slash command directly in rich text format."""
        if self._slash_start_pos is not None:
            cursor = self.textCursor()
            cursor.beginEditBlock()
            cursor.setPosition(self._slash_start_pos)
            cursor.setPosition(self.textCursor().position(), QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self._slash_start_pos = None

        if cmd.id == "h1":
            self._convert_block_to_heading(1)
        elif cmd.id == "h2":
            self._convert_block_to_heading(2)
        elif cmd.id == "h3":
            self._convert_block_to_heading(3)
        elif cmd.id == "todo":
            self._convert_block_to_checkbox()
        elif cmd.id == "bullet":
            self._convert_block_to_bullet()
        elif cmd.id == "number":
            self._convert_block_to_numbered()
        elif cmd.id == "quote":
            self._convert_block_to_quote()
        elif cmd.id == "code":
            self.insertHtml("<pre style='background-color:#28282b; color:#f09a52; padding:8px; border-radius:4px;'><code> </code></pre>")
        elif cmd.id == "divider":
            self.insertHtml("<hr>")

        self.ensureCursorVisible()

    def _toggle_checkbox_at_block(self, block) -> None:
        """Toggle checked state on the visual ballot box and strike through text."""
        cursor = QTextCursor(block)
        cursor.beginEditBlock()
        bfmt = block.blockFormat()
        marker = bfmt.marker()

        cfmt = QTextCharFormat()
        if marker == QTextBlockFormat.MarkerType.Unchecked:
            bfmt.setMarker(QTextBlockFormat.MarkerType.Checked)
            cfmt.setFontStrikeOut(True)
            cfmt.setForeground(QColor("#686868"))
        else:
            bfmt.setMarker(QTextBlockFormat.MarkerType.Unchecked)
            cfmt.setFontStrikeOut(False)
            cfmt.setForeground(QColor("#e6e6e6"))

        cursor.setBlockFormat(bfmt)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.mergeCharFormat(cfmt)
        cursor.endEditBlock()

    def _convert_block_to_heading(self, level: int) -> None:
        """Convert current block to a clean Heading without raw '#' markers."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        raw = cursor.selectedText()
        clean = re.sub(r"^#+\s*", "", raw).strip()
        cursor.removeSelectedText()
        cursor.insertText(clean)

        bfmt = cursor.blockFormat()
        bfmt.setHeadingLevel(level)
        cursor.setBlockFormat(bfmt)

        cfmt = QTextCharFormat()
        sizes = {1: 20, 2: 17, 3: 15}
        cfmt.setFontPointSize(sizes.get(level, 14))
        cfmt.setFontWeight(QFont.Weight.Bold)
        cfmt.setForeground(QColor("#ffffff"))
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.mergeCharFormat(cfmt)
        cursor.endEditBlock()

    def _convert_block_to_checkbox(self) -> None:
        """Convert current block into a clean interactive checkbox."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        raw = cursor.selectedText()
        clean = re.sub(r"^(\[\]|[-*+]\s*\[[ xX]\]|[-*+])\s*", "", raw).strip()
        cursor.removeSelectedText()
        cursor.insertText(clean)

        lfmt = QTextListFormat()
        lfmt.setStyle(QTextListFormat.Style.ListDisc)
        cursor.createList(lfmt)

        bfmt = cursor.blockFormat()
        bfmt.setMarker(QTextBlockFormat.MarkerType.Unchecked)
        cursor.setBlockFormat(bfmt)
        cursor.endEditBlock()

    def _convert_block_to_bullet(self) -> None:
        """Convert current block into a bullet list item."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        raw = cursor.selectedText()
        clean = re.sub(r"^[-*+]\s*", "", raw).strip()
        cursor.removeSelectedText()
        cursor.insertText(clean)

        lfmt = QTextListFormat()
        lfmt.setStyle(QTextListFormat.Style.ListDisc)
        cursor.createList(lfmt)
        cursor.endEditBlock()

    def _convert_block_to_numbered(self) -> None:
        """Convert current block into a numbered list item."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        raw = cursor.selectedText()
        clean = re.sub(r"^\d+[\.\)]\s*", "", raw).strip()
        cursor.removeSelectedText()
        cursor.insertText(clean)

        lfmt = QTextListFormat()
        lfmt.setStyle(QTextListFormat.Style.ListDecimal)
        cursor.createList(lfmt)
        cursor.endEditBlock()

    def _convert_block_to_quote(self) -> None:
        """Convert current block into an indented blockquote."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        raw = cursor.selectedText()
        clean = re.sub(r"^>+\s*", "", raw).strip()
        cursor.removeSelectedText()
        cursor.insertText(clean)

        bfmt = cursor.blockFormat()
        bfmt.setIndent(bfmt.indent() + 1)
        cursor.setBlockFormat(bfmt)

        cfmt = QTextCharFormat()
        cfmt.setFontItalic(True)
        cfmt.setForeground(QColor("#98989d"))
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.mergeCharFormat(cfmt)
        cursor.endEditBlock()


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
        self.word_count_label.setStyleSheet("color: #7a7a7a; font-size: 11px;")
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
        """Load note markdown into the editor, rendering visual elements cleanly."""
        self._current_note = note
        self._save_timer.stop()

        if note is None:
            self.editor.blockSignals(True)
            self.editor.clear()
            self.meta_label.setText("No note selected")
            self.word_count_label.setText("0 words")
            self.editor.blockSignals(False)
            return

        self.editor.blockSignals(True)
        self.editor.setMarkdown(note.content)
        self.editor.blockSignals(False)

        folder_name = note.path.parent.name
        self.meta_label.setText(f"{folder_name}  •  Edited {note.formatted_time}")
        self._update_word_count()

    def get_content(self) -> str:
        """Return the clean Markdown representation."""
        return self.editor.toMarkdown()

    def _on_text_changed(self) -> None:
        self._update_word_count()
        self._save_timer.start()

    def _update_word_count(self) -> None:
        words = len(self.editor.toPlainText().split())
        self.word_count_label.setText(f"{words} words")

    def _trigger_auto_save(self) -> None:
        """Emit save signal with latest Markdown text."""
        content = self.editor.toMarkdown()
        if self._current_note is None:
            if content.strip():
                self.create_note_with_content.emit(content)
        else:
            self.content_saved.emit(content)
