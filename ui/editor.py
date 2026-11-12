"""Editor canvas panel with Obsidian-style cursor-aware Live Preview and debounced auto-save."""

from __future__ import annotations

import math
from pathlib import Path
import re
import time
from typing import Dict, List, Optional, Set, Tuple

from PyQt6.QtCore import QEvent, QMimeData, QPoint, QPointF, QRect, QRectF, QTimer, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QDesktopServices,
    QFont,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QTextBlock,
    QTextBlockFormat,
    QTextCursor,
    QTextOption,
    QTouchEvent,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from core.note import Note
from ui.dialogs import ModernLinkDialog
from ui.find_replace import FindReplaceBar
from ui.highlighter import HR_RE, HTML_KBD_RE, LIST_RE, QUOTE_RE, MarkdownHighlighter
from ui.selection_toolbar import SelectionFormatToolbar
from ui.slash_menu import SlashCommand, SlashCommandPalette
from utils.exporter import export_note_to_html, export_note_to_pdf
from utils.touch import TouchScrollTracker, is_touch_event
from utils.icons import (
    create_backup_icon,
    create_export_icon,
    create_notes_toggle_icon,
    create_open_file_icon,
    create_sidebar_toggle_icon,
)
from utils.code_engine import (
    CodeRegion,
    get_code_content_width,
    get_code_copy_button_rect,
    get_code_edit_button_rect,
    get_code_scrollbar_geometry,
    render_code_card,
)
from utils.markdown import (
    CHECKBOX_PATTERN,
    find_link_at_offset,
    get_auto_continue_prefix,
    get_checkbox_info,
    is_checkbox_line,
)
from utils.math_engine import (
    INLINE_MATH_RE,
    render_math_to_pixmap,
)
from utils.mermaid_engine import (
    render_mermaid_to_pixmap,
)
from utils.table import (
    TableRegion,
    create_empty_table_row,
    find_next_cell_pos,
    find_prev_cell_pos,
    get_table_column_widths,
    get_table_scrollbar_geometry,
    is_empty_table_row,
    is_table_row,
    is_table_separator,
    render_table,
    split_table_cells,
)


class NoteTitleEdit(QLineEdit):
    """Frameless modern note title input with smooth keyboard navigation (Notion/Craft aesthetic)."""

    down_pressed = pyqtSignal()
    enter_pressed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("NoteTitleEdit")
        self.setPlaceholderText("Untitled")
        title_font = QFont("Cantarell", 22)
        title_font.setPointSize(22)
        title_font.setBold(True)
        self.setFont(title_font)
        self.setStyleSheet("""
            QLineEdit#NoteTitleEdit {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 26px;
                font-weight: 700;
                padding: 10px 36px 4px 36px;
                selection-background-color: #0a84ff;
            }
            QLineEdit#NoteTitleEdit:focus {
                border: none;
                background-color: transparent;
            }
            QLineEdit#NoteTitleEdit:disabled {
                color: #555555;
            }
        """)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.enter_pressed.emit()
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Down:
            self.down_pressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class MarkdownEditor(QTextEdit):
    """Pure plain-text Markdown editor with cursor-aware Obsidian Live Preview."""

    up_at_top_requested = pyqtSignal()
    find_requested = pyqtSignal(bool)  # is_replace_mode
    find_close_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("MarkdownEditor")
        self.setPlaceholderText("Type text or / for commands")
        self.setAcceptRichText(False)

        # Guarantee strict Left-to-Right layout and clean word wrapping
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        opt = self.document().defaultTextOption()
        opt.setTextDirection(Qt.LayoutDirection.LeftToRight)
        opt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        self.document().setDefaultTextOption(opt)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)

        # Set base editor font in Python so QSyntaxHighlighter can freely scale headings
        base_font = QFont("Cantarell", 16)
        base_font.setPointSize(16)
        self.setFont(base_font)
        self.document().setDefaultFont(base_font)

        # Apply comfortable 120% proportional line height across documents
        cur = self.textCursor()
        bf = cur.blockFormat()
        bf.setLineHeight(120.0, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        cur.setBlockFormat(bf)
        self.setTextCursor(cur)

        # Attach cursor-aware Obsidian syntax highlighter
        self.highlighter = MarkdownHighlighter(self.document())
        self.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self.document().contentsChanged.connect(self._on_contents_changed)
        self._rendered_block_rects: list[tuple[int, int, QRectF]] = []

        # Horizontal scrolling & interaction states for tables and code blocks
        self._table_scroll_x: dict[int, float] = {}
        self._code_scroll_x: dict[int, float] = {}
        self._scrollbar_drag: Optional[tuple[str, int, float, float, float, float, float]] = None
        self._hovered_copy_btn: Optional[int] = None
        self._hovered_edit_btn: Optional[int] = None
        self._copied_code_block: Optional[int] = None
        self._copied_timer = QTimer(self)
        self._copied_timer.setSingleShot(True)
        self._copied_timer.setInterval(2000)
        self._copied_timer.timeout.connect(self._reset_copied_state)

        # Enable mouse and touch tracking
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        # Touchscreen gesture tracking & kinetic momentum
        self._touch_tracker = TouchScrollTracker()
        self._last_tap_time: float = 0.0
        self._last_tap_pos: QPointF = QPointF()

        self._kinetic_timer = QTimer(self)
        self._kinetic_timer.setInterval(16)  # ~60 FPS
        self._kinetic_timer.timeout.connect(self._on_kinetic_tick)
        self._kinetic_vx: float = 0.0
        self._kinetic_vy: float = 0.0
        self._kinetic_target: Optional[tuple[str, int, float]] = None

        # Debounced blockquote margin updates & atomic batch edit guard
        self._updating_margins: bool = False
        self._margin_timer = QTimer(self)
        self._margin_timer.setSingleShot(True)
        self._margin_timer.setInterval(50)
        self._margin_timer.timeout.connect(self._update_blockquote_margins)

        # Slash command palette (Notion-style block creation)
        self.slash_palette = SlashCommandPalette(self)
        self.slash_palette.command_selected.connect(self._on_slash_command_selected)
        self._slash_start_pos: Optional[int] = None

        # Floating text format bubble toolbar (Notion-style inline formatting)
        self.format_toolbar = SelectionFormatToolbar(self)
        self.format_toolbar.format_requested.connect(self._apply_text_format)
        self.selectionChanged.connect(self._on_selection_changed)

        # In-note search & replace state
        self._search_matches: list[tuple[int, int]] = []
        self._current_search_idx: int = -1
        self._search_query: str = ""
        self._search_case: bool = False
        self._search_word: bool = False

    def focusOutEvent(self, event) -> None:
        if self.slash_palette.isVisible() and not self.slash_palette.hasFocus():
            self.slash_palette.hide()
        if hasattr(self, "format_toolbar") and self.format_toolbar.isVisible() and not self.format_toolbar.hasFocus():
            self.format_toolbar.hide()
        super().focusOutEvent(event)

    def _on_selection_changed(self) -> None:
        """Show or hide the floating format toolbar based on current text selection."""
        cursor = self.textCursor()
        if not cursor.hasSelection() or not cursor.selectedText().strip():
            if hasattr(self, "format_toolbar") and self.format_toolbar.isVisible():
                self.format_toolbar.hide()
            return

        if self.slash_palette.isVisible():
            return

        self._show_format_toolbar()

    def _show_format_toolbar(self) -> None:
        """Compute the bounding rectangle of selected text and anchor the toolbar above it."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return

        start_c = QTextCursor(cursor)
        start_c.setPosition(cursor.selectionStart())
        end_c = QTextCursor(cursor)
        end_c.setPosition(cursor.selectionEnd())

        r_start = self.cursorRect(start_c)
        r_end = self.cursorRect(end_c)

        sel_left = min(r_start.left(), r_end.left())
        sel_right = max(r_start.right(), r_end.right())
        sel_top = min(r_start.top(), r_end.top())
        sel_bottom = max(r_start.bottom(), r_end.bottom())

        sel_rect = QRect(sel_left, sel_top, max(24, sel_right - sel_left), max(16, sel_bottom - sel_top))
        global_top_left = self.viewport().mapToGlobal(sel_rect.topLeft())
        global_rect = QRect(global_top_left.x(), global_top_left.y(), sel_rect.width(), sel_rect.height())

        self.format_toolbar.show_above_rect(global_rect)

    def _apply_text_format(self, format_type: str) -> None:
        """Apply or toggle inline markdown formatting on selected text."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return

        text = cursor.selectedText()
        if not text:
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        if format_type == "bold":
            prefix, suffix = "**", "**"
        elif format_type == "italic":
            prefix, suffix = "*", "*"
        elif format_type == "strike":
            prefix, suffix = "~~", "~~"
        elif format_type == "underline":
            prefix, suffix = "<u>", "</u>"
        elif format_type == "code":
            prefix, suffix = "`", "`"
        elif format_type == "link":
            struct_match = re.match(
                r"^(\s*(?:>+\s*)*(?:[-*+]\s*\[[ xX]?\]\s*|[-*+]\s+|\d+\.\s+|#{1,6}\s+))(.*)$",
                text,
            )
            lead_prefix = struct_match.group(1) if struct_match else ""
            core_text = struct_match.group(2) if struct_match else text

            # Check if selection is already a markdown link [Text](URL)
            existing_match = re.match(r"^\[(.*?)\]\((.*?)\)$", core_text.strip())
            if existing_match:
                init_text = existing_match.group(1)
                init_url = existing_match.group(2)
            else:
                init_text = core_text
                init_url = ""
                cb = QApplication.clipboard().text().strip()
                if cb.startswith(("http://", "https://", "mailto:")) and "\n" not in cb:
                    init_url = cb

            # Temporarily hide floating toolbar while modal dialog is open
            if hasattr(self, "format_toolbar") and self.format_toolbar.isVisible():
                self.format_toolbar.hide()

            link_text, link_url, accepted = ModernLinkDialog.get_link_data(
                self, initial_text=init_text, initial_url=init_url
            )
            if not accepted:
                return

            if not link_text and not link_url:
                return

            if not link_text:
                link_text = link_url

            if link_url:
                if not link_url.startswith(("http://", "https://", "mailto:", "file:", "#", "/", "./", "../")):
                    link_url = "https://" + link_url
                formatted = f"{lead_prefix}[{link_text}]({link_url})"
            else:
                formatted = f"{lead_prefix}{link_text}"

            cursor.beginEditBlock()
            cursor.insertText(formatted)
            new_cursor = self.textCursor()
            new_cursor.setPosition(start)
            new_cursor.setPosition(start + len(formatted), QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(new_cursor)
            cursor.endEditBlock()
            self.viewport().update()
            self._show_format_toolbar()
            return
        elif format_type in ("bullet", "number", "todo", "checkbox"):
            cursor.beginEditBlock()
            b_start = self.document().findBlock(start)
            b_end = self.document().findBlock(end)
            if b_end.position() == end and b_end.blockNumber() > b_start.blockNumber():
                b_end = b_end.previous()

            blocks = []
            curr = b_start
            while curr.isValid() and curr.blockNumber() <= b_end.blockNumber():
                blocks.append(curr)
                if curr == b_end:
                    break
                curr = curr.next()

            non_empty_blocks = [b for b in blocks if b.text().strip()]
            if format_type in ("todo", "checkbox"):
                all_formatted = bool(non_empty_blocks) and all(
                    re.match(r"^\s*[-*+]\s*\[[ xX]?\]\s*", b.text()) for b in non_empty_blocks
                )
            elif format_type == "bullet":
                all_formatted = bool(non_empty_blocks) and all(
                    re.match(r"^\s*[-*+]\s+(?!\[[ xX]?\])", b.text()) for b in non_empty_blocks
                )
            else:
                all_formatted = bool(non_empty_blocks) and all(
                    re.match(r"^\s*\d+\.\s+", b.text()) for b in non_empty_blocks
                )

            for b in reversed(blocks):
                b_text = b.text()
                if not b_text.strip():
                    continue
                indent = b_text[: len(b_text) - len(b_text.lstrip())]
                content = b_text[len(indent) :]
                content_clean = re.sub(
                    r"^(\s*[-*+]\s*\[[ xX]?\]\s*|\s*[-*+]\s*|\s*\d+\.\s*)", "", content
                )

                if all_formatted:
                    new_line = indent + content_clean
                else:
                    if format_type in ("todo", "checkbox"):
                        new_line = indent + "- [ ] " + content_clean
                    elif format_type == "bullet":
                        new_line = indent + "- " + content_clean
                    else:
                        fwd_idx = non_empty_blocks.index(b) + 1
                        new_line = indent + f"{fwd_idx}. " + content_clean

                c = QTextCursor(b)
                c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                c.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                c.insertText(new_line)

            # Re-select affected blocks
            sel_cursor = QTextCursor(self.document())
            sel_cursor.setPosition(b_start.position())
            sel_cursor.setPosition(b_end.position() + len(b_end.text()), QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(sel_cursor)

            cursor.endEditBlock()
            self.viewport().update()
            self._show_format_toolbar()
            return
        else:
            return

        cursor.beginEditBlock()

        # Intelligently protect structural prefixes (- [ ] , - [x] , - , 1. , > , # )
        struct_match = re.match(
            r"^(\s*(?:>+\s*)*(?:[-*+]\s*\[[ xX]?\]\s*|[-*+]\s+|\d+\.\s+|#{1,6}\s+))(.*)$",
            text,
        )
        lead_prefix = struct_match.group(1) if struct_match else ""
        core_text = struct_match.group(2) if struct_match else text

        p_len = len(prefix)
        s_len = len(suffix)

        # 1. Check if core_text itself is already wrapped in prefix/suffix
        if core_text.startswith(prefix) and core_text.endswith(suffix) and len(core_text) >= p_len + s_len:
            unwrapped = core_text[p_len:-s_len]
            formatted = f"{lead_prefix}{unwrapped}"
            cursor.insertText(formatted)
            new_cursor = self.textCursor()
            new_cursor.setPosition(start)
            new_cursor.setPosition(start + len(formatted), QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(new_cursor)
        else:
            # 2. Check if surrounding characters in document are already prefix/suffix
            doc_text = self.document().toPlainText()
            has_surrounding = False
            core_start = start + len(lead_prefix)
            core_end = end
            if core_start >= p_len and core_end + s_len <= len(doc_text):
                if doc_text[core_start - p_len:core_start] == prefix and doc_text[core_end:core_end + s_len] == suffix:
                    has_surrounding = True

            if has_surrounding:
                del_cursor = QTextCursor(self.document())
                del_cursor.setPosition(core_end)
                del_cursor.setPosition(core_end + s_len, QTextCursor.MoveMode.KeepAnchor)
                del_cursor.removeSelectedText()
                del_cursor.setPosition(core_start - p_len)
                del_cursor.setPosition(core_start, QTextCursor.MoveMode.KeepAnchor)
                del_cursor.removeSelectedText()

                new_cursor = self.textCursor()
                new_cursor.setPosition(core_start - p_len)
                new_cursor.setPosition(core_end - p_len, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(new_cursor)
            else:
                formatted = f"{lead_prefix}{prefix}{core_text}{suffix}"
                cursor.insertText(formatted)
                new_cursor = self.textCursor()
                new_cursor.setPosition(start)
                new_cursor.setPosition(start + len(formatted), QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(new_cursor)

        cursor.endEditBlock()
        self.viewport().update()
        self._show_format_toolbar()

    def find_matches(
        self, query: str, match_case: bool = False, whole_word: bool = False
    ) -> Tuple[int, int]:
        """Scan document for occurrences, highlight with ExtraSelection, and return (current_1_based, total)."""
        self._search_query = query
        self._search_case = match_case
        self._search_word = whole_word

        if not query:
            self.clear_search()
            return (0, 0)

        text = self.document().toPlainText()
        pattern = re.escape(query)
        if whole_word:
            pattern = r"\b" + pattern + r"\b"

        re_flags = 0 if match_case else re.IGNORECASE
        try:
            compiled = re.compile(pattern, re_flags)
        except re.error:
            self.clear_search()
            return (0, 0)

        matches = [(m.start(), m.end()) for m in compiled.finditer(text)]
        if not matches:
            self._search_matches = []
            self._current_search_idx = -1
            self.setExtraSelections([])
            self.viewport().update()
            return (0, 0)

        self._search_matches = matches

        # Select match nearest to current cursor position
        cursor_pos = self.textCursor().selectionStart()
        nearest_idx = 0
        for i, (start, end) in enumerate(matches):
            if start <= cursor_pos <= end or start >= cursor_pos:
                nearest_idx = i
                break

        self._current_search_idx = nearest_idx
        self._apply_search_highlights(scroll_to_active=True)
        return (self._current_search_idx + 1, len(matches))

    def find_next(self) -> Tuple[int, int]:
        """Jump to the next search occurrence and scroll it into view."""
        if not self._search_matches:
            return (0, 0)
        self._current_search_idx = (self._current_search_idx + 1) % len(self._search_matches)
        self._apply_search_highlights(scroll_to_active=True)
        return (self._current_search_idx + 1, len(self._search_matches))

    def find_prev(self) -> Tuple[int, int]:
        """Jump to the previous search occurrence and scroll it into view."""
        if not self._search_matches:
            return (0, 0)
        self._current_search_idx = (self._current_search_idx - 1) % len(self._search_matches)
        self._apply_search_highlights(scroll_to_active=True)
        return (self._current_search_idx + 1, len(self._search_matches))

    def replace_current(self, replacement: str) -> Tuple[int, int]:
        """Replace the active match and advance to the next match."""
        if not self._search_matches or self._current_search_idx < 0:
            return (0, 0)

        start, end = self._search_matches[self._current_search_idx]
        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(replacement)
        cursor.endEditBlock()

        # Place cursor right after the newly inserted replacement
        new_c = self.textCursor()
        new_c.setPosition(start + len(replacement))
        self.setTextCursor(new_c)

        return self.find_matches(self._search_query, self._search_case, self._search_word)

    def replace_all(
        self, query: str, replacement: str, match_case: bool = False, whole_word: bool = False
    ) -> int:
        """Atomically replace all matches in the document in a single undo block."""
        if not query:
            return 0

        text = self.document().toPlainText()
        pattern = re.escape(query)
        if whole_word:
            pattern = r"\b" + pattern + r"\b"

        re_flags = 0 if match_case else re.IGNORECASE
        try:
            compiled = re.compile(pattern, re_flags)
        except re.error:
            return 0

        matches = [(m.start(), m.end()) for m in compiled.finditer(text)]
        if not matches:
            return 0

        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        for start, end in reversed(matches):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(replacement)
        cursor.endEditBlock()

        self.clear_search()
        self.viewport().update()
        return len(matches)

    def clear_search(self) -> None:
        """Clear all search highlights, matches, and state."""
        self._search_matches = []
        self._current_search_idx = -1
        self._search_query = ""
        self.setExtraSelections([])
        self.viewport().update()

    def _apply_search_highlights(self, scroll_to_active: bool = True) -> None:
        """Apply visual highlights for all search matches via QTextEdit.ExtraSelection."""
        if not self._search_matches:
            self.setExtraSelections([])
            return

        selections = []
        doc = self.document()

        for i, (start, end) in enumerate(self._search_matches):
            sel = QTextEdit.ExtraSelection()
            c = QTextCursor(doc)
            c.setPosition(start)
            c.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            sel.cursor = c

            if i == self._current_search_idx:
                sel.format.setBackground(QColor("#0a84ff"))
                sel.format.setForeground(QColor("#ffffff"))
                if scroll_to_active:
                    self.setTextCursor(c)
                    self.ensureCursorVisible()
            else:
                sel.format.setBackground(QColor(235, 175, 40, 95))
                sel.format.setForeground(QColor("#ffffff"))

            selections.append(sel)

        self.setExtraSelections(selections)
        self.viewport().update()

    def _show_slash_palette(self) -> None:
        """Position and display the floating slash palette directly beneath the cursor."""
        cursor_rect = self.cursorRect()
        global_pos = self.viewport().mapToGlobal(cursor_rect.bottomLeft())
        palette_w = self.slash_palette.width()
        palette_h = self.slash_palette.height()

        x = global_pos.x()
        y = global_pos.y() + 4

        # Keep on screen if near edges
        screen = self.screen()
        if screen:
            screen_geom = screen.availableGeometry()
            if y + palette_h > screen_geom.bottom():
                top_pos = self.viewport().mapToGlobal(cursor_rect.topLeft())
                y = top_pos.y() - palette_h - 4
            if x + palette_w > screen_geom.right():
                x = screen_geom.right() - palette_w - 8

        self.slash_palette.move(x, y)
        self.slash_palette.populate("")
        self.slash_palette.show()
        self.slash_palette.raise_()

    def _on_slash_command_selected(self, cmd: SlashCommand) -> None:
        """Replace the typed slash query with the selected Markdown block syntax."""
        self.slash_palette.hide()
        cursor = self.textCursor()
        block = cursor.block()

        # Determine the slash position
        slash_pos = self._slash_start_pos - 1 if self._slash_start_pos is not None else None
        if slash_pos is None or slash_pos < block.position() or slash_pos > cursor.position():
            b_text = block.text()
            b_offset = cursor.positionInBlock()
            last_slash = b_text.rfind("/", 0, b_offset)
            if last_slash != -1:
                slash_pos = block.position() + last_slash
            else:
                slash_pos = cursor.position()

        cursor.beginEditBlock()
        replace_cursor = QTextCursor(self.document())
        replace_cursor.setPosition(slash_pos)
        replace_cursor.setPosition(cursor.position(), QTextCursor.MoveMode.KeepAnchor)

        if cmd.id == "code":
            replace_cursor.insertText("```\n\n```")
            target_pos = slash_pos + 4
            c = QTextCursor(self.document())
            c.setPosition(target_pos)
            self.setTextCursor(c)
        else:
            replace_cursor.insertText(cmd.prefix)
            self.setTextCursor(replace_cursor)

        cursor.endEditBlock()
        self._slash_start_pos = None
        self.setFocus()
        self.ensureCursorVisible()
        self.viewport().update()

    def _reset_copied_state(self) -> None:
        """Reset the copy button feedback to default."""
        self._copied_code_block = None
        self.viewport().update()

    def _get_table_rect(self, tr: TableRegion) -> Optional[QRectF]:
        """Compute the geometry QRectF of an inactive rendered table card."""
        b_top = self.document().findBlockByNumber(tr.start_block)
        b_bot = self.document().findBlockByNumber(tr.end_block)
        if not (b_top.isValid() and b_bot.isValid()):
            return None
        r_top = self.cursorRect(QTextCursor(b_top))
        r_bot = self.cursorRect(QTextCursor(b_bot))
        avail_w = max(100.0, float(self.viewport().width() - r_top.left() - 28))
        return QRectF(float(r_top.left()), float(r_top.top()), avail_w, float(r_bot.bottom() - r_top.top()))

    def _get_code_card_rect(self, cr: CodeRegion) -> Optional[QRectF]:
        """Compute the tightly bounded geometry QRectF of an inactive rendered code card."""
        b_top = self.document().findBlockByNumber(cr.start_block)
        b_bot = self.document().findBlockByNumber(cr.end_block)
        if not (b_top.isValid() and b_bot.isValid()):
            return None
        r_top = self.cursorRect(QTextCursor(b_top))

        avail_w = max(100.0, float(self.viewport().width() - r_top.left() - 28.0))
        header_h = 28.0
        line_h = 22.0
        # Exact height: header (28px) + top padding (8px) + code lines + bottom padding (16px)
        card_h = header_h + 8.0 + len(cr.lines) * line_h + 16.0
        return QRectF(float(r_top.left()), float(r_top.top()), avail_w, card_h)

    def _update_blockquote_margins(self) -> None:
        """Ensure all blockquotes have leftMargin proportional to their quote nesting depth and uniform line height."""
        if self._updating_margins:
            return
        self._updating_margins = True
        try:
            doc = self.document()
            b = doc.firstBlock()
            cur = QTextCursor(doc)
            cur.beginEditBlock()
            try:
                while b.isValid():
                    text = b.text()
                    target_margin = 0.0
                    if ">" in text and b.userState() != 1:
                        qm = QUOTE_RE.match(text)
                        if qm:
                            level = qm.group(1).count(">")
                            if level > 0:
                                target_margin = level * 18.0 + 8.0

                    c = QTextCursor(b)
                    bf = c.blockFormat()
                    changed = False
                    if abs(bf.leftMargin() - target_margin) > 0.5:
                        bf.setLeftMargin(target_margin)
                        changed = True
                    if abs(bf.lineHeight() - 120.0) > 0.5:
                        bf.setLineHeight(120.0, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
                        changed = True
                    if changed:
                        c.setBlockFormat(bf)
                    b = b.next()
            finally:
                cur.endEditBlock()
        finally:
            self._updating_margins = False

    def setPlainText(self, text: str) -> None:
        """Set editor plain text and synchronously apply line height and block margins."""
        super().setPlainText(text)
        self._update_blockquote_margins()

    def insertFromMimeData(self, source: QMimeData) -> None:
        """Ensure pasted content is always inserted as clean Markdown / plain text in a single edit block."""
        if source.hasText():
            text = source.text()
            cursor = self.textCursor()
            cursor.beginEditBlock()
            try:
                cursor.insertText(text)
            finally:
                cursor.endEditBlock()
        else:
            super().insertFromMimeData(source)

    def _on_contents_changed(self) -> None:
        """Recompute table, math, and mermaid regions on text content modification."""
        if not self._updating_margins:
            self._margin_timer.start()
        cursor = self.textCursor()
        self.highlighter.active_block_number = cursor.block().blockNumber()
        self.highlighter.cursor_pos_in_block = cursor.positionInBlock()
        changed = self.highlighter.refresh_regions()
        for b_num in changed:
            b = self.document().findBlockByNumber(b_num)
            if b.isValid():
                self.highlighter.rehighlightBlock(b)
        self.viewport().update()

    def _on_cursor_position_changed(self) -> None:
        """Rehighlight lines and regions when the cursor moves between lines or across syntax boundaries."""
        cursor = self.textCursor()
        new_block = cursor.block()
        new_block_num = new_block.blockNumber()
        new_pos_in_block = cursor.positionInBlock()

        old_block_num = self.highlighter.active_block_number
        old_pos_in_block = getattr(self.highlighter, "cursor_pos_in_block", -1)

        block_changed = new_block_num != old_block_num
        self.highlighter.active_block_number = new_block_num
        self.highlighter.cursor_pos_in_block = new_pos_in_block

        if block_changed:
            changed = self.highlighter.refresh_regions()
            changed.add(old_block_num)
            changed.add(new_block_num)
            for b_num in changed:
                b = self.document().findBlockByNumber(b_num)
                if b.isValid():
                    self.highlighter.rehighlightBlock(b)
        else:
            if new_pos_in_block != old_pos_in_block:
                self.highlighter.rehighlightBlock(new_block)

        self.viewport().update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint editor text, vector checkboxes, styled tables, math equations, and mermaid diagrams."""
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        active_bn = self.highlighter.active_block_number
        vp_height = self.viewport().height()
        vp_width = self.viewport().width()

        self._rendered_block_rects.clear()

        # 1. Render Inactive Tables
        for tr in self.highlighter.table_regions:
            if tr.start_block <= active_bn <= tr.end_block:
                continue  # Active editing mode for this table
            b_top = self.document().findBlockByNumber(tr.start_block)
            b_bot = self.document().findBlockByNumber(tr.end_block)
            if not (b_top.isValid() and b_bot.isValid()):
                continue

            r_top = self.cursorRect(QTextCursor(b_top))
            r_bot = self.cursorRect(QTextCursor(b_bot))
            if r_top.top() > vp_height or r_bot.bottom() < 0:
                continue

            avail_w = max(100.0, float(vp_width - r_top.left() - 28))
            table_rect = QRectF(float(r_top.left()), float(r_top.top()), avail_w, float(r_bot.bottom() - r_top.top()))
            self._rendered_block_rects.append((tr.start_block, tr.end_block, table_rect))
            scroll_x = self._table_scroll_x.get(tr.start_block, 0.0)
            render_table(painter, table_rect, tr, self.font(), scroll_x=scroll_x)

        # 2. Render Inactive Display Math ($$ ... $$)
        for mr in self.highlighter.math_regions:
            if mr.start_block <= active_bn <= mr.end_block:
                continue
            b_top = self.document().findBlockByNumber(mr.start_block)
            b_bot = self.document().findBlockByNumber(mr.end_block)
            if not (b_top.isValid() and b_bot.isValid()):
                continue

            r_top = self.cursorRect(QTextCursor(b_top))
            r_bot = self.cursorRect(QTextCursor(b_bot))
            if r_top.top() > vp_height or r_bot.bottom() < 0:
                continue

            math_rect = QRectF(float(r_top.left()), float(r_top.top()), float(vp_width - r_top.left() - 28), float(r_bot.bottom() - r_top.top()))
            self._rendered_block_rects.append((mr.start_block, mr.end_block, math_rect))

            pix = render_math_to_pixmap(mr.latex, font_size=19.0, display_mode=True)
            log_w = pix.width() / pix.devicePixelRatio()
            log_h = pix.height() / pix.devicePixelRatio()
            px = math_rect.left() + max(0.0, (math_rect.width() - log_w) / 2.0)
            py = math_rect.top() + max(0.0, (math_rect.height() - log_h) / 2.0)
            painter.drawPixmap(QPointF(px, py), pix)

        # 3. Render Inactive Mermaid Diagrams (```mermaid ... ```)
        for mmd in self.highlighter.mermaid_regions:
            if mmd.start_block <= active_bn <= mmd.end_block:
                continue
            b_top = self.document().findBlockByNumber(mmd.start_block)
            b_bot = self.document().findBlockByNumber(mmd.end_block)
            if not (b_top.isValid() and b_bot.isValid()):
                continue

            r_top = self.cursorRect(QTextCursor(b_top))
            r_bot = self.cursorRect(QTextCursor(b_bot))
            if r_top.top() > vp_height or r_bot.bottom() < 0:
                continue

            mmd_rect = QRectF(float(r_top.left()), float(r_top.top()), float(vp_width - r_top.left() - 28), float(r_bot.bottom() - r_top.top()))
            self._rendered_block_rects.append((mmd.start_block, mmd.end_block, mmd_rect))

            pix = render_mermaid_to_pixmap(mmd.source)
            log_w = pix.width() / pix.devicePixelRatio()
            log_h = pix.height() / pix.devicePixelRatio()
            px = mmd_rect.left() + max(0.0, (mmd_rect.width() - log_w) / 2.0)
            py = mmd_rect.top() + max(0.0, (mmd_rect.height() - log_h) / 2.0)
            painter.drawPixmap(QPointF(px, py), pix)

        # 4. Render Inactive Code Cards (```lang ... ```)
        for cr in self.highlighter.code_regions:
            if cr.start_block <= active_bn <= cr.end_block:
                continue

            card_rect = self._get_code_card_rect(cr)
            if card_rect is None:
                continue

            if card_rect.top() > vp_height or card_rect.bottom() < 0:
                continue

            self._rendered_block_rects.append((cr.start_block, cr.end_block, card_rect))
            scroll_x = self._code_scroll_x.get(cr.start_block, 0.0)
            is_copied = self._copied_code_block == cr.start_block
            is_copy_hovered = self._hovered_copy_btn == cr.start_block
            is_edit_hovered = self._hovered_edit_btn == cr.start_block
            render_code_card(
                painter,
                card_rect,
                cr,
                scroll_x=scroll_x,
                is_copied=is_copied,
                is_copy_hovered=is_copy_hovered,
                is_edit_hovered=is_edit_hovered,
            )

        # 5. Render Checkboxes, Inactive Bullets & Inactive Inline Math ($...$)
        # Start strictly from the first visible block in the viewport for O(viewport) performance
        first_cursor = self.cursorForPosition(QPoint(0, 0))
        block = first_cursor.block()
        while block.isValid():
            b_num = block.blockNumber()
            c = QTextCursor(block)
            b_rect = self.cursorRect(c)
            if b_rect.top() > vp_height:
                break

            text = block.text()

            # Horizontal rule (draw clean vector divider line)
            if HR_RE.match(text):
                if b_rect.bottom() >= 0:
                    line_y = float(b_rect.top()) + float(b_rect.height()) / 2.0
                    painter.setPen(QPen(QColor("#48484a"), 1.2))
                    painter.drawLine(QPointF(float(b_rect.left()), line_y), QPointF(float(vp_width - 24.0), line_y))

            # Blockquote vertical accent bars (for all quote lines, outside code blocks)
            if block.userState() != 1 and ">" in text:
                qm_bar = QUOTE_RE.match(text)
                if qm_bar:
                    prefix_bar = qm_bar.group(1)
                    level_bar = prefix_bar.count(">")
                    if level_bar > 0:
                        c_s_b = QTextCursor(block)
                        c_e_b = QTextCursor(block)
                        c_e_b.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                        r_s_b = self.cursorRect(c_s_b)
                        r_e_b = self.cursorRect(c_e_b)
                        top_y = float(r_s_b.top())
                        bot_y = float(r_e_b.bottom())

                        if bot_y >= 0 and top_y <= vp_height:
                            painter.save()
                            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                            target_m = level_bar * 18.0 + 8.0
                            base_x = float(r_s_b.left()) - target_m + 4.0
                            for lvl in range(level_bar):
                                bx = base_x + lvl * 18.0
                                next_b = block.next()
                                connects_next = False
                                if next_b.isValid():
                                    next_qm = QUOTE_RE.match(next_b.text())
                                    if next_qm and next_qm.group(1).count(">") > lvl:
                                        connects_next = True

                                pen = QPen(QColor("#545462"), 2.6)
                                if not connects_next:
                                    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                                painter.setPen(pen)
                                y2 = bot_y + 1.0 if connects_next else bot_y - 1.0
                                painter.drawLine(QPointF(bx, top_y + 1.0), QPointF(bx, y2))
                            painter.restore()

            # HTML <kbd> Keycaps (inactive lines, outside code blocks)
            if "<kbd>" in text.lower() and b_num != active_bn and block.userState() != 1:
                for km in HTML_KBD_RE.finditer(text):
                    c_s = QTextCursor(block)
                    c_s.setPosition(block.position() + km.start(2))
                    c_e = QTextCursor(block)
                    c_e.setPosition(block.position() + km.end(2))
                    r_s = self.cursorRect(c_s)
                    r_e = self.cursorRect(c_e)
                    if r_s.bottom() >= 0 and r_s.top() <= vp_height:
                        kw = float(r_e.left() - r_s.left())
                        if kw > 0:
                            k_rect = QRectF(float(r_s.left()) - 4.0, float(r_s.top()) + 1.5, kw + 8.0, float(r_s.height()) - 3.0)
                            painter.save()
                            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                            # 3D Bottom shadow edge
                            painter.setPen(QPen(QColor("#18181e"), 1.2))
                            painter.setBrush(QBrush(QColor("#222228")))
                            painter.drawRoundedRect(k_rect, 4.0, 4.0)
                            # Top keycap face
                            top_rect = QRectF(k_rect.left(), k_rect.top(), k_rect.width(), k_rect.height() - 1.8)
                            painter.setPen(QPen(QColor("#545464"), 1.0))
                            painter.setBrush(QBrush(QColor("#2e2e38")))
                            painter.drawRoundedRect(top_rect, 3.5, 3.5)
                            # Key text
                            kf = QFont("Cantarell", -1)
                            kf.setPixelSize(12)
                            kf.setWeight(QFont.Weight.Bold)
                            painter.setFont(kf)
                            painter.setPen(QColor("#f5f5f7"))
                            painter.drawText(top_rect, int(Qt.AlignmentFlag.AlignCenter), km.group(2))
                            painter.restore()

            # Checkbox (never paint inside a code block)
            if block.userState() != 1:
                match = CHECKBOX_PATTERN.match(text)
                if match:
                    indent, _, status, _ = match.groups()
                    c_cb = QTextCursor(block)
                    c_cb.setPosition(block.position() + len(indent))
                    rect = self.cursorRect(c_cb)
                    if rect.bottom() >= 0:
                        self._draw_checkbox(painter, rect, status.lower() == "x")
                else:
                    qm = QUOTE_RE.match(text)
                    if qm:
                        prefix = qm.group(1)
                        inner_cb = CHECKBOX_PATTERN.match(text[len(prefix):])
                        if inner_cb:
                            indent, _, status, _ = inner_cb.groups()
                            c_cb = QTextCursor(block)
                            c_cb.setPosition(block.position() + len(prefix) + len(indent))
                            rect = self.cursorRect(c_cb)
                            if rect.bottom() >= 0:
                                self._draw_checkbox(painter, rect, status.lower() == "x")

            # Bullet list item vector rendering (renders when block is inactive OR caret is in content)
            if (
                block.userState() != 1
                and b_num not in self.highlighter._block_modes
            ):
                if not CHECKBOX_PATTERN.match(text):
                    lm = LIST_RE.match(text)
                    if lm:
                        indent, marker, space, _ = lm.groups()
                        if marker in ("-", "*", "+"):
                            prefix_len = len(indent) + len(marker) + len(space)
                            should_draw_bullet = (
                                b_num != active_bn
                                or getattr(self.highlighter, "cursor_pos_in_block", -1) > prefix_len
                            )
                            if should_draw_bullet:
                                c_bl = QTextCursor(block)
                                c_bl.setPosition(block.position() + len(indent))
                                rect = self.cursorRect(c_bl)
                                if rect.bottom() >= 0:
                                    self._draw_bullet(painter, rect, len(indent))
                    else:
                        qm = QUOTE_RE.match(text)
                        if qm:
                            prefix = qm.group(1)
                            inner_text = text[len(prefix):]
                            if not CHECKBOX_PATTERN.match(inner_text):
                                ilm = LIST_RE.match(inner_text)
                                if ilm:
                                    l_indent, l_marker, l_sp, _ = ilm.groups()
                                    if l_marker in ("-", "*", "+"):
                                        prefix_len = len(prefix) + len(l_indent) + len(l_marker) + len(l_sp)
                                        should_draw_bullet = (
                                            b_num != active_bn
                                            or getattr(self.highlighter, "cursor_pos_in_block", -1) > prefix_len
                                        )
                                        if should_draw_bullet:
                                            c_bl = QTextCursor(block)
                                            c_bl.setPosition(block.position() + len(prefix) + len(l_indent))
                                            rect = self.cursorRect(c_bl)
                                            if rect.bottom() >= 0:
                                                self._draw_bullet(painter, rect, len(l_indent))

            # Inline Math on inactive regular blocks (never inside tables or code blocks)
            if (
                b_num != active_bn
                and block.userState() != 1
                and b_num not in self.highlighter._block_modes
                and ("$" in text or "\\(" in text)
            ):
                for m in INLINE_MATH_RE.finditer(text):
                    expr = m.group(1) if m.group(1) is not None else m.group(2)
                    c_m = QTextCursor(block)
                    c_m.setPosition(block.position() + m.start())
                    rect = self.cursorRect(c_m)
                    if rect.bottom() >= 0:
                        pix = render_math_to_pixmap(expr, font_size=15.0, display_mode=False)
                        log_h = pix.height() / pix.devicePixelRatio()
                        py = float(rect.top()) + (rect.height() - log_h) / 2.0
                        painter.drawPixmap(QPointF(float(rect.left()), py), pix)

            block = block.next()

        painter.end()

    def _draw_bullet(self, painter: QPainter, cursor_rect: QRect, indent_len: int) -> None:
        """Draw an Apple Notes-style vector bullet glyph (dot, ring, or square) at cursor_rect."""
        level = max(0, indent_len // 2)
        cx = float(cursor_rect.left()) + 10.0
        cy = float(cursor_rect.top()) + float(cursor_rect.height()) / 2.0

        if level == 0:
            # Level 0: Solid circular bullet
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#0a84ff")))
            painter.drawEllipse(QPointF(cx, cy), 3.0, 3.0)
        elif level == 1:
            # Level 1: Open ring bullet
            pen = QPen(QColor("#0a84ff"), 1.6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), 2.7, 2.7)
        else:
            # Level 2+: Solid square bullet
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#0a84ff")))
            sq = 4.8
            painter.drawRect(QRectF(cx - sq / 2.0, cy - sq / 2.0, sq, sq))

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

    def _checkbox_block_at_pos(self, pos: QPointF) -> Optional[QTextBlock]:
        """Return the QTextBlock if the viewport position is over a painted checkbox."""
        cursor = self.cursorForPosition(pos.toPoint())
        block = cursor.block()
        if not block.isValid():
            return None

        text = block.text()
        prefix_len = 0
        qm = QUOTE_RE.match(text)
        if qm:
            prefix_len = len(qm.group(1))
            text = text[prefix_len:]

        match = CHECKBOX_PATTERN.match(text)
        if not match:
            return None

        indent, _, _, _ = match.groups()
        c = QTextCursor(block)
        c.setPosition(block.position() + prefix_len + len(indent))
        rect = self.cursorRect(c)
        box_x = float(rect.left() + 3)
        box_y = float(rect.top()) + (rect.height() - 14.0) / 2.0
        min_x = max(0.0, box_x - 8.0)
        max_x = box_x + 22.0
        min_y = box_y - 6.0
        max_y = box_y + 20.0

        if min_x <= pos.x() <= max_x and min_y <= pos.y() <= max_y:
            return block
        return None

    def _region_at_pos(self, pos: QPointF) -> Optional[tuple[int, int, QRectF]]:
        """Return the rendered preview card (start_block, end_block, rect) if clicked/hovered."""
        for s_blk, e_blk, r in self._rendered_block_rects:
            if r.contains(pos):
                return s_blk, e_blk, r
        return None

    def _link_at_pos(self, pos: QPointF) -> Optional[tuple[int, int, str]]:
        """Return (start, end, url) if viewport position is over a Markdown link."""
        cursor = self.cursorForPosition(pos.toPoint())
        block = cursor.block()
        if not block.isValid():
            return None
        offset = cursor.positionInBlock()
        return find_link_at_offset(block.text(), offset)

    def _open_url(self, url: str) -> None:
        """Open a URL in the user's default web browser."""
        clean_url = url.strip()
        if not (
            clean_url.startswith("http://")
            or clean_url.startswith("https://")
            or clean_url.startswith("mailto:")
            or clean_url.startswith("file://")
        ):
            clean_url = "https://" + clean_url
        QDesktopServices.openUrl(QUrl(clean_url))

    def _find_hscroll_target(self, pos: QPointF) -> Optional[tuple[str, int, float]]:
        """Find if pos is within an inactive table or code card that has horizontal overflow."""
        active_bn = self.highlighter.active_block_number
        for tr in self.highlighter.table_regions:
            if not (tr.start_block <= active_bn <= tr.end_block):
                tbl_rect = self._get_table_rect(tr)
                if tbl_rect is not None and tbl_rect.contains(pos):
                    content_w, _ = get_table_column_widths(tr, self.font(), tbl_rect.width())
                    max_s = max(0.0, content_w - tbl_rect.width())
                    if max_s > 0:
                        return ("table", tr.start_block, max_s)
        for cr in self.highlighter.code_regions:
            if not (cr.start_block <= active_bn <= cr.end_block):
                card_rect = self._get_code_card_rect(cr)
                if card_rect is not None and card_rect.contains(pos):
                    content_w = get_code_content_width(cr)
                    max_s = max(0.0, content_w - (card_rect.width() - 28.0))
                    if max_s > 0:
                        return ("code", cr.start_block, max_s)
        return None

    def _on_touch_down(self, pos: QPointF) -> None:
        """Handle touchscreen press / contact begin."""
        self._kinetic_timer.stop()
        self._kinetic_vx = 0.0
        self._kinetic_vy = 0.0
        target = self._find_hscroll_target(pos)
        self._touch_tracker.start(pos, time.time(), target)

    def _on_touch_move(self, pos: QPointF) -> None:
        """Handle touchscreen drag / move."""
        dx, dy, is_scrolling = self._touch_tracker.update(pos, time.time())
        if is_scrolling:
            # Prevent text selection on touchscreen drag
            c = self.textCursor()
            if c.hasSelection():
                c.clearSelection()
                self.setTextCursor(c)

            # 1. Vertical scroll
            if dy != 0:
                vsb = self.verticalScrollBar()
                vsb.setValue(int(vsb.value() - dy))

            # 2. Horizontal scroll
            target = self._touch_tracker.target_region
            if target is not None:
                kind, blk_id, max_s = target
                if kind == "table":
                    cur_s = self._table_scroll_x.get(blk_id, 0.0)
                    new_s = max(0.0, min(max_s, cur_s - dx))
                    if new_s != cur_s:
                        self._table_scroll_x[blk_id] = new_s
                        self.viewport().update()
                elif kind == "code":
                    cur_s = self._code_scroll_x.get(blk_id, 0.0)
                    new_s = max(0.0, min(max_s, cur_s - dx))
                    if new_s != cur_s:
                        self._code_scroll_x[blk_id] = new_s
                        self.viewport().update()
            else:
                hsb = self.horizontalScrollBar()
                if hsb.maximum() > 0 and dx != 0:
                    hsb.setValue(int(hsb.value() - dx))

    def _on_touch_up(self, pos: QPointF) -> None:
        """Handle touchscreen release / contact end."""
        target = self._touch_tracker.target_region
        was_scrolling, vx, vy = self._touch_tracker.end(time.time())
        if was_scrolling:
            if abs(vy) > 0.8 or abs(vx) > 0.8:
                self._kinetic_vx = vx
                self._kinetic_vy = vy
                self._kinetic_target = target
                self._kinetic_timer.start(16)
        else:
            self._handle_touch_tap(pos)

    def _on_kinetic_tick(self) -> None:
        """Smooth momentum deceleration tick."""
        if abs(self._kinetic_vy) > 0.4:
            vsb = self.verticalScrollBar()
            vsb.setValue(int(vsb.value() - self._kinetic_vy))
            self._kinetic_vy *= 0.92
        else:
            self._kinetic_vy = 0.0

        if abs(self._kinetic_vx) > 0.4 and self._kinetic_target is not None:
            kind, blk_id, max_s = self._kinetic_target
            if kind == "table":
                cur_s = self._table_scroll_x.get(blk_id, 0.0)
                new_s = max(0.0, min(max_s, cur_s - self._kinetic_vx))
                self._table_scroll_x[blk_id] = new_s
                self.viewport().update()
            elif kind == "code":
                cur_s = self._code_scroll_x.get(blk_id, 0.0)
                new_s = max(0.0, min(max_s, cur_s - self._kinetic_vx))
                self._code_scroll_x[blk_id] = new_s
                self.viewport().update()
            self._kinetic_vx *= 0.92
        else:
            self._kinetic_vx = 0.0

        if abs(self._kinetic_vy) <= 0.4 and abs(self._kinetic_vx) <= 0.4:
            self._kinetic_timer.stop()

    def _handle_touch_tap(self, pos: QPointF) -> None:
        """Process a clean tap or double-tap on touchscreen without drag."""
        now = time.time()
        is_double_tap = (
            (now - self._last_tap_time <= 0.35)
            and (math.hypot(pos.x() - self._last_tap_pos.x(), pos.y() - self._last_tap_pos.y()) < 24.0)
        )
        self._last_tap_time = now
        self._last_tap_pos = pos

        if is_double_tap:
            reg = self._region_at_pos(pos)
            if reg is not None:
                s_blk, _, _ = reg
                target_block = self.document().findBlockByNumber(s_blk + 1)
                if not target_block.isValid():
                    target_block = self.document().findBlockByNumber(s_blk)
                if target_block.isValid():
                    c = QTextCursor(target_block)
                    c.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                    self.setTextCursor(c)
                    self.ensureCursorVisible()
                    self.viewport().update()
                    return
            else:
                c = self.cursorForPosition(pos.toPoint())
                c.select(QTextCursor.SelectionType.WordUnderCursor)
                self.setTextCursor(c)
                return

        # Single Tap Actions:
        active_bn = self.highlighter.active_block_number

        # 1. Check Copy button
        for cr in self.highlighter.code_regions:
            if not (cr.start_block <= active_bn <= cr.end_block):
                card_rect = self._get_code_card_rect(cr)
                if card_rect is not None and card_rect.contains(pos):
                    btn_rect = get_code_copy_button_rect(card_rect)
                    if btn_rect.contains(pos):
                        code_text = "\n".join(cr.lines)
                        QApplication.clipboard().setText(code_text)
                        self._copied_code_block = cr.start_block
                        self._copied_timer.start(2000)
                        self.viewport().update()
                        return

        # 2. Check Edit button
        for cr in self.highlighter.code_regions:
            if not (cr.start_block <= active_bn <= cr.end_block):
                card_rect = self._get_code_card_rect(cr)
                if card_rect is not None and card_rect.contains(pos):
                    edit_btn = get_code_edit_button_rect(card_rect)
                    if edit_btn.contains(pos):
                        target_block = self.document().findBlockByNumber(cr.start_block + 1)
                        if not target_block.isValid():
                            target_block = self.document().findBlockByNumber(cr.start_block)
                        if target_block.isValid():
                            c = QTextCursor(target_block)
                            c.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                            self.setTextCursor(c)
                            self.ensureCursorVisible()
                            self.viewport().update()
                            return

        # 3. Checkbox tap
        block = self._checkbox_block_at_pos(pos)
        if block is not None:
            self._toggle_checkbox_at_block(block)
            return

        # 4. Inactive preview card tap -> do nothing (keeps card intact)
        if self._region_at_pos(pos) is not None:
            return

        # 5. Normal text tap -> position cursor cleanly with no selection
        c = self.cursorForPosition(pos.toPoint())
        c.clearSelection()
        self.setTextCursor(c)
        self.ensureCursorVisible()

    def viewportEvent(self, event: QEvent) -> bool:
        """Handle touchscreen gestures natively without triggering text selection."""
        t = event.type()
        if t in (QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate, QEvent.Type.TouchEnd, QEvent.Type.TouchCancel):
            if isinstance(event, QTouchEvent) and event.points():
                pt = event.points()[0]
                pos = pt.position()
                if t == QEvent.Type.TouchBegin:
                    self._on_touch_down(pos)
                elif t == QEvent.Type.TouchUpdate:
                    self._on_touch_move(pos)
                elif t in (QEvent.Type.TouchEnd, QEvent.Type.TouchCancel):
                    self._on_touch_up(pos)
                event.accept()
                return True
        return super().viewportEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Show pointer cursor on interactive elements and handle scrollbar dragging."""
        if is_touch_event(event):
            if self._touch_tracker.is_active:
                self._on_touch_move(event.position())
            return
        elif self._touch_tracker.is_active:
            self._touch_tracker.reset()

        super().mouseMoveEvent(event)
        pos = event.position()
        active_bn = self.highlighter.active_block_number

        # Handle active scrollbar dragging
        if self._scrollbar_drag is not None:
            kind, block_id, start_x, start_s, max_s, track_w, thumb_w = self._scrollbar_drag
            scroll_range = max(1.0, track_w - thumb_w)
            dx = pos.x() - start_x
            new_s = max(0.0, min(max_s, start_s + (dx / scroll_range) * max_s))
            if kind == "table":
                self._table_scroll_x[block_id] = new_s
            else:
                self._code_scroll_x[block_id] = new_s
            self.viewport().update()
            return

        # Check if hovering over Code Copy button
        old_hovered_copy = self._hovered_copy_btn
        self._hovered_copy_btn = None
        for cr in self.highlighter.code_regions:
            if not (cr.start_block <= active_bn <= cr.end_block):
                card_rect = self._get_code_card_rect(cr)
                if card_rect is not None and card_rect.contains(pos):
                    btn_rect = get_code_copy_button_rect(card_rect)
                    if btn_rect.contains(pos):
                        self._hovered_copy_btn = cr.start_block
                        self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
                        tip = "Copied!" if self._copied_code_block == cr.start_block else "Copy code to clipboard"
                        QToolTip.showText(event.globalPosition().toPoint(), tip, self.viewport())
                        if old_hovered_copy != self._hovered_copy_btn:
                            self.viewport().update()
                        return

        if old_hovered_copy is not None:
            self.viewport().update()

        # Check if hovering over Code Edit button
        old_hovered_edit = self._hovered_edit_btn
        self._hovered_edit_btn = None
        for cr in self.highlighter.code_regions:
            if not (cr.start_block <= active_bn <= cr.end_block):
                card_rect = self._get_code_card_rect(cr)
                if card_rect is not None and card_rect.contains(pos):
                    edit_btn = get_code_edit_button_rect(card_rect)
                    if edit_btn.contains(pos):
                        self._hovered_edit_btn = cr.start_block
                        self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
                        QToolTip.showText(event.globalPosition().toPoint(), "Edit code block", self.viewport())
                        if old_hovered_edit != self._hovered_edit_btn:
                            self.viewport().update()
                        return

        if old_hovered_edit is not None:
            self.viewport().update()

        # Check if hovering over table scrollbar
        for tr in self.highlighter.table_regions:
            if not (tr.start_block <= active_bn <= tr.end_block):
                tbl_rect = self._get_table_rect(tr)
                if tbl_rect is not None and tbl_rect.contains(pos):
                    content_w, _ = get_table_column_widths(tr, self.font(), tbl_rect.width())
                    cur_s = self._table_scroll_x.get(tr.start_block, 0.0)
                    sb = get_table_scrollbar_geometry(tbl_rect, content_w, cur_s)
                    if sb is not None and sb[0].contains(pos):
                        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
                        QToolTip.hideText()
                        return

        # Check if hovering over code scrollbar
        for cr in self.highlighter.code_regions:
            if not (cr.start_block <= active_bn <= cr.end_block):
                card_rect = self._get_code_card_rect(cr)
                if card_rect is not None and card_rect.contains(pos):
                    content_w = get_code_content_width(cr)
                    cur_s = self._code_scroll_x.get(cr.start_block, 0.0)
                    sb = get_code_scrollbar_geometry(card_rect, content_w, cur_s)
                    if sb is not None and sb[0].contains(pos):
                        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
                        QToolTip.hideText()
                        return

        # Checkboxes
        if self._checkbox_block_at_pos(pos) is not None:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            QToolTip.hideText()
            return

        # Inactive preview card hover
        if self._region_at_pos(pos) is not None:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            QToolTip.hideText()
            return

        link_info = self._link_at_pos(pos)
        if link_info is not None:
            _, _, url = link_info
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            QToolTip.showText(
                event.globalPosition().toPoint(),
                f"Ctrl+Click or Ctrl+Enter to open {url}",
                self.viewport(),
            )
            return

        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        QToolTip.hideText()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle clicking directly on checkboxes, buttons, scrollbars, or Ctrl+Click on links."""
        if self.slash_palette.isVisible():
            self.slash_palette.hide()
        if hasattr(self, "format_toolbar") and self.format_toolbar.isVisible():
            self.format_toolbar.hide()

        if is_touch_event(event):
            self._on_touch_down(event.position())
            return
        elif self._touch_tracker.is_active:
            self._touch_tracker.reset()

        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            active_bn = self.highlighter.active_block_number

            # 0. Ctrl+Click on link -> open in browser
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                link_info = self._link_at_pos(pos)
                if link_info is not None:
                    _, _, url = link_info
                    self._open_url(url)
                    return

            # 1. Click on Code Card Copy button
            for cr in self.highlighter.code_regions:
                if not (cr.start_block <= active_bn <= cr.end_block):
                    card_rect = self._get_code_card_rect(cr)
                    if card_rect is not None and card_rect.contains(pos):
                        btn_rect = get_code_copy_button_rect(card_rect)
                        if btn_rect.contains(pos):
                            code_text = "\n".join(cr.lines)
                            QApplication.clipboard().setText(code_text)
                            self._copied_code_block = cr.start_block
                            self._copied_timer.start(2000)
                            self.viewport().update()
                            return

            # 2. Click on Code Card Edit button
            for cr in self.highlighter.code_regions:
                if not (cr.start_block <= active_bn <= cr.end_block):
                    card_rect = self._get_code_card_rect(cr)
                    if card_rect is not None and card_rect.contains(pos):
                        edit_btn = get_code_edit_button_rect(card_rect)
                        if edit_btn.contains(pos):
                            target_block = self.document().findBlockByNumber(cr.start_block + 1)
                            if not target_block.isValid():
                                target_block = self.document().findBlockByNumber(cr.start_block)
                            if target_block.isValid():
                                c = QTextCursor(target_block)
                                c.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                                self.setTextCursor(c)
                                self.ensureCursorVisible()
                                self.viewport().update()
                                return

            # 3. Click on Code Card Scrollbar
            for cr in self.highlighter.code_regions:
                if not (cr.start_block <= active_bn <= cr.end_block):
                    card_rect = self._get_code_card_rect(cr)
                    if card_rect is not None:
                        content_w = get_code_content_width(cr)
                        cur_s = self._code_scroll_x.get(cr.start_block, 0.0)
                        sb = get_code_scrollbar_geometry(card_rect, content_w, cur_s)
                        if sb is not None:
                            track_r, thumb_r, max_s = sb
                            if track_r.contains(pos):
                                if not thumb_r.contains(pos):
                                    ratio = (pos.x() - track_r.left()) / max(1.0, track_r.width())
                                    cur_s = max(0.0, min(max_s, ratio * max_s))
                                    self._code_scroll_x[cr.start_block] = cur_s
                                self._scrollbar_drag = ("code", cr.start_block, pos.x(), cur_s, max_s, track_r.width(), thumb_r.width())
                                self.viewport().update()
                                return
                            elif thumb_r.contains(pos):
                                self._scrollbar_drag = ("code", cr.start_block, pos.x(), cur_s, max_s, track_r.width(), thumb_r.width())
                                return

            # 4. Click on Table Scrollbar
            for tr in self.highlighter.table_regions:
                if not (tr.start_block <= active_bn <= tr.end_block):
                    tbl_rect = self._get_table_rect(tr)
                    if tbl_rect is not None:
                        content_w, _ = get_table_column_widths(tr, self.font(), tbl_rect.width())
                        cur_s = self._table_scroll_x.get(tr.start_block, 0.0)
                        sb = get_table_scrollbar_geometry(tbl_rect, content_w, cur_s)
                        if sb is not None:
                            track_r, thumb_r, max_s = sb
                            if track_r.contains(pos):
                                if not thumb_r.contains(pos):
                                    ratio = (pos.x() - track_r.left()) / max(1.0, track_r.width())
                                    cur_s = max(0.0, min(max_s, ratio * max_s))
                                    self._table_scroll_x[tr.start_block] = cur_s
                                self._scrollbar_drag = ("table", tr.start_block, pos.x(), cur_s, max_s, track_r.width(), thumb_r.width())
                                self.viewport().update()
                                return
                            elif thumb_r.contains(pos):
                                self._scrollbar_drag = ("table", tr.start_block, pos.x(), cur_s, max_s, track_r.width(), thumb_r.width())
                                return

            # 5. Checkbox click -> toggle
            block = self._checkbox_block_at_pos(pos)
            if block is not None:
                self._toggle_checkbox_at_block(block)
                return

            # Single click on rendered card does NOT blow up the card; double-click is required
            if self._region_at_pos(pos) is not None:
                return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Double-click on any rendered card to enter inline Markdown editing."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            reg = self._region_at_pos(pos)
            if reg is not None:
                s_blk, _, _ = reg
                target_block = self.document().findBlockByNumber(s_blk + 1)
                if not target_block.isValid():
                    target_block = self.document().findBlockByNumber(s_blk)
                if target_block.isValid():
                    c = QTextCursor(target_block)
                    c.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                    self.setTextCursor(c)
                    self.ensureCursorVisible()
                    self.viewport().update()
                    return

        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finish any active scrollbar dragging or touch scrolling."""
        if is_touch_event(event):
            self._on_touch_up(event.position())
            return
        elif self._touch_tracker.is_active:
            self._touch_tracker.reset()

        self._scrollbar_drag = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle horizontal scrolling on tables and code blocks with trackpad or Shift+Wheel."""
        if self.slash_palette.isVisible():
            self.slash_palette.hide()
        if hasattr(self, "format_toolbar") and self.format_toolbar.isVisible():
            self.format_toolbar.hide()

        pos = event.position()
        delta_x = event.angleDelta().x()
        if delta_x == 0 and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            delta_x = event.angleDelta().y()

        active_bn = self.highlighter.active_block_number

        if delta_x != 0:
            # 1. Check if hovering over an inactive table
            for tr in self.highlighter.table_regions:
                if tr.start_block <= active_bn <= tr.end_block:
                    continue
                tbl_rect = self._get_table_rect(tr)
                if tbl_rect is not None and tbl_rect.contains(pos):
                    content_w, _ = get_table_column_widths(tr, self.font(), tbl_rect.width())
                    max_s = max(0.0, content_w - tbl_rect.width())
                    if max_s > 0:
                        cur_s = self._table_scroll_x.get(tr.start_block, 0.0)
                        new_s = max(0.0, min(max_s, cur_s - delta_x * 0.8))
                        if new_s != cur_s:
                            self._table_scroll_x[tr.start_block] = new_s
                            self.viewport().update()
                        event.accept()
                        return

            # 2. Check if hovering over an inactive code card
            for cr in self.highlighter.code_regions:
                if cr.start_block <= active_bn <= cr.end_block:
                    continue
                card_rect = self._get_code_card_rect(cr)
                if card_rect is not None and card_rect.contains(pos):
                    content_w = get_code_content_width(cr)
                    max_s = max(0.0, content_w - card_rect.width())
                    if max_s > 0:
                        cur_s = self._code_scroll_x.get(cr.start_block, 0.0)
                        new_s = max(0.0, min(max_s, cur_s - delta_x * 0.8))
                        if new_s != cur_s:
                            self._code_scroll_x[cr.start_block] = new_s
                            self.viewport().update()
                        event.accept()
                        return

        super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle Escape exit, Ctrl+Enter toggling, smart list continuation, and Tab indentation."""
        # Dismiss format toolbar on keypress
        if hasattr(self, "format_toolbar") and self.format_toolbar.isVisible():
            if event.key() == Qt.Key.Key_Escape:
                self.format_toolbar.hide()
                event.accept()
                return
            self.format_toolbar.hide()

        # 0. Intercept Slash Command Palette navigation and execution when open
        if self.slash_palette.isVisible():
            if event.key() == Qt.Key.Key_Escape:
                self.slash_palette.hide()
                event.accept()
                return

            if event.key() == Qt.Key.Key_Down:
                self.slash_palette.select_next()
                event.accept()
                return

            if event.key() == Qt.Key.Key_Up:
                self.slash_palette.select_previous()
                event.accept()
                return

            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                self.slash_palette.execute_current()
                event.accept()
                return

            if event.key() == Qt.Key.Key_Backspace:
                super().keyPressEvent(event)
                cur_pos = self.textCursor().position()
                if self._slash_start_pos is None or cur_pos < self._slash_start_pos - 1:
                    self.slash_palette.hide()
                else:
                    if cur_pos < self._slash_start_pos:
                        self.slash_palette.populate("")
                    else:
                        query = self.document().toPlainText()[self._slash_start_pos:cur_pos]
                        self.slash_palette.populate(query)
                return

            if event.key() in (
                Qt.Key.Key_Left,
                Qt.Key.Key_Right,
                Qt.Key.Key_Home,
                Qt.Key.Key_End,
                Qt.Key.Key_PageUp,
                Qt.Key.Key_PageDown,
            ):
                self.slash_palette.hide()
                super().keyPressEvent(event)
                return

            if event.text() and event.text().isprintable():
                if event.text() == " ":
                    self.slash_palette.hide()
                    super().keyPressEvent(event)
                    return
                super().keyPressEvent(event)
                cur_pos = self.textCursor().position()
                if self._slash_start_pos is not None and cur_pos >= self._slash_start_pos:
                    query = self.document().toPlainText()[self._slash_start_pos:cur_pos]
                    if "\n" in query:
                        self.slash_palette.hide()
                    else:
                        self.slash_palette.populate(query)
                        if self.slash_palette.count() == 0:
                            self.slash_palette.hide()
                return

        cursor = self.textCursor()
        block = cursor.block()
        line_text = block.text()
        pos_in_block = cursor.positionInBlock()

        # In-note Find (Ctrl+F), Replace (Ctrl+H), and formatting shortcuts
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_F:
                self.find_requested.emit(False)
                return
            elif event.key() == Qt.Key.Key_H:
                self.find_requested.emit(True)
                return
            elif event.key() == Qt.Key.Key_K:
                self._apply_text_format("link")
                return
            elif event.key() == Qt.Key.Key_B:
                self._apply_text_format("bold")
                return
            elif event.key() == Qt.Key.Key_I:
                self._apply_text_format("italic")
                return
            elif event.key() == Qt.Key.Key_U:
                self._apply_text_format("underline")
                return

        # Up arrow at the very top of document: jump up to NoteTitleEdit
        if event.key() == Qt.Key.Key_Up:
            if block.blockNumber() == 0 and pos_in_block == 0 and not (event.modifiers() & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier)):
                self.up_at_top_requested.emit()
                event.accept()
                return

        # Open Slash Command Palette on typing '/' at start of line or after space
        if event.text() == "/" and not (
            event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
        ):
            is_valid_trigger = (
                pos_in_block == 0
                or line_text[:pos_in_block].isspace()
                or (pos_in_block > 0 and line_text[pos_in_block - 1] == " ")
            )
            if is_valid_trigger:
                super().keyPressEvent(event)
                self._slash_start_pos = self.textCursor().position()
                self._show_slash_palette()
                return

        # Escape key: dismiss active find bar, popups, or exit active card editing mode
        if event.key() == Qt.Key.Key_Escape:
            if self.format_toolbar.isVisible():
                self.format_toolbar.hide()
                return
            if self.slash_palette.isVisible():
                self.slash_palette.hide()
                return
            if self._search_matches:
                self.find_close_requested.emit()
                return
            b_num = block.blockNumber()
            for r_list in (
                self.highlighter.code_regions,
                self.highlighter.table_regions,
                self.highlighter.math_regions,
                self.highlighter.mermaid_regions,
            ):
                for r in r_list:
                    if r.start_block <= b_num <= r.end_block:
                        next_b = self.document().findBlockByNumber(r.end_block + 1)
                        if not next_b.isValid():
                            next_b = self.document().findBlockByNumber(r.start_block - 1)
                        if next_b.isValid():
                            c = QTextCursor(next_b)
                            c.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                            self.setTextCursor(c)
                            self.ensureCursorVisible()
                            self.viewport().update()
                            return

        # Check if inside a table row
        if is_table_row(line_text):
            # Tab inside table: advance to next cell (or create new row if at end)
            if event.key() == Qt.Key.Key_Tab and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                next_pos = find_next_cell_pos(line_text, pos_in_block)
                if next_pos is not None:
                    c = QTextCursor(block)
                    c.setPosition(block.position() + next_pos)
                    self.setTextCursor(c)
                else:
                    next_b = block.next()
                    if next_b.isValid() and is_table_row(next_b.text()):
                        if is_table_separator(next_b.text()):
                            next_b = next_b.next()
                        if next_b.isValid() and is_table_row(next_b.text()):
                            fp = find_next_cell_pos(next_b.text(), 0)
                            c = QTextCursor(next_b)
                            c.setPosition(next_b.position() + (fp or 2))
                            self.setTextCursor(c)
                    else:
                        num_cols = len(split_table_cells(line_text))
                        cursor.beginEditBlock()
                        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                        cursor.insertText("\n" + create_empty_table_row(num_cols))
                        cursor.endEditBlock()
                        new_b = self.textCursor().block()
                        fp = find_next_cell_pos(new_b.text(), 0)
                        c = QTextCursor(new_b)
                        c.setPosition(new_b.position() + (fp or 2))
                        self.setTextCursor(c)
                return

            # Shift+Tab inside table: go to previous cell
            if event.key() == Qt.Key.Key_Tab and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                prev_pos = find_prev_cell_pos(line_text, pos_in_block)
                if prev_pos is not None:
                    c = QTextCursor(block)
                    c.setPosition(block.position() + prev_pos)
                    self.setTextCursor(c)
                else:
                    prev_b = block.previous()
                    if prev_b.isValid() and is_table_separator(prev_b.text()):
                        prev_b = prev_b.previous()
                    if prev_b.isValid() and is_table_row(prev_b.text()):
                        pipes = [m.start() for m in re.finditer(r"\|", prev_b.text())]
                        if len(pipes) >= 2:
                            c = QTextCursor(prev_b)
                            c.setPosition(prev_b.position() + pipes[-2] + 2)
                            self.setTextCursor(c)
                return

            # Enter inside table: smart row continuation or exit
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
                event.modifiers() & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier)
            ):
                if is_empty_table_row(line_text):
                    # Exit table: remove current empty row
                    cursor.beginEditBlock()
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                    cursor.endEditBlock()
                    self.viewport().update()
                    return
                else:
                    num_cols = len(split_table_cells(line_text))
                    prev_b = block.previous()
                    is_first_header = not (prev_b.isValid() and is_table_row(prev_b.text()))
                    cursor.beginEditBlock()
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                    if is_first_header:
                        sep = "|" + "|".join("---" for _ in range(num_cols)) + "|"
                        cursor.insertText("\n" + sep + "\n" + create_empty_table_row(num_cols))
                    else:
                        cursor.insertText("\n" + create_empty_table_row(num_cols))
                    cursor.endEditBlock()
                    new_b = self.textCursor().block()
                    fp = find_next_cell_pos(new_b.text(), 0)
                    c = QTextCursor(new_b)
                    c.setPosition(new_b.position() + (fp or 2))
                    self.setTextCursor(c)
                    self.ensureCursorVisible()
                    self.viewport().update()
                    return

        # 0. Auto-expand "- []" into "- [ ]" when the user types closing bracket "]"
        if event.text() == "]" and re.match(r"^\s*[-*+]\s*\[$", line_text[:pos_in_block]):
            cursor.beginEditBlock()
            cursor.insertText(" ]")
            cursor.endEditBlock()
            self.viewport().update()
            return

        # 1. Backspace right after a checkbox or list marker removes prefix cleanly or unindents
        if event.key() == Qt.Key.Key_Backspace and not cursor.hasSelection():
            # Checkbox backspace
            cb_info = get_checkbox_info(line_text)
            if cb_info is not None:
                _, _, prefix_end, _ = cb_info
                if pos_in_block == prefix_end:
                    indent_len = len(line_text) - len(line_text.lstrip())
                    cursor.beginEditBlock()
                    if indent_len >= 2:
                        c = QTextCursor(block)
                        c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                        c.deleteChar()
                        c.deleteChar()
                    else:
                        cursor.setPosition(block.position() + indent_len)
                        cursor.setPosition(
                            block.position() + prefix_end,
                            QTextCursor.MoveMode.KeepAnchor,
                        )
                        cursor.removeSelectedText()
                    cursor.endEditBlock()
                    self.viewport().update()
                    return

            # Bullet / Ordered list backspace
            list_m = LIST_RE.match(line_text)
            if list_m:
                indent, marker, space, _ = list_m.groups()
                marker_end = len(indent) + len(marker) + len(space)
                if pos_in_block == marker_end:
                    cursor.beginEditBlock()
                    if len(indent) >= 2:
                        c = QTextCursor(block)
                        c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                        c.deleteChar()
                        c.deleteChar()
                    else:
                        c = QTextCursor(block)
                        c.setPosition(block.position() + len(indent))
                        c.setPosition(block.position() + marker_end, QTextCursor.MoveMode.KeepAnchor)
                        c.removeSelectedText()
                    cursor.endEditBlock()
                    self.viewport().update()
                    return

        # 2. Ctrl+Enter: If on a link, open in browser. Otherwise toggle or create checkbox.
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            link_info = find_link_at_offset(line_text, pos_in_block)
            if link_info is not None:
                _, _, url = link_info
                self._open_url(url)
                return

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
                    # Empty list/checkbox item -> unindent by 2 spaces or terminate list
                    indent_len = len(line_text) - len(line_text.lstrip())
                    cursor.beginEditBlock()
                    if indent_len >= 2:
                        c = QTextCursor(block)
                        c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                        c.deleteChar()
                        c.deleteChar()
                    else:
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
                    # If splitting text and remainder starts with space, remove that space
                    tail = line_text[pos_in_block:]
                    if tail.startswith(" "):
                        del_c = QTextCursor(cursor)
                        del_c.deleteChar()
                    cursor.insertText("\n" + continuation)
                    cursor.endEditBlock()
                    self.ensureCursorVisible()
                    self.viewport().update()
                    return

        # 4. Tab & Shift+Tab: Smart indentation for lists, checkboxes, selections, and text
        if event.key() == Qt.Key.Key_Tab:
            is_shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            if cursor.hasSelection():
                # Indent / unindent all blocks spanning the selection
                start_pos = cursor.selectionStart()
                end_pos = cursor.selectionEnd()
                b_curr = self.document().findBlock(start_pos)
                b_last = self.document().findBlock(end_pos)
                if b_last.position() == end_pos and b_last.blockNumber() > b_curr.blockNumber():
                    b_last = b_last.previous()

                cursor.beginEditBlock()
                while b_curr.isValid():
                    b_text = b_curr.text()
                    c = QTextCursor(b_curr)
                    c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    if is_shift:
                        rem = 2 if b_text.startswith("  ") else (1 if b_text.startswith(" ") else 0)
                        for _ in range(rem):
                            c.deleteChar()
                    else:
                        c.insertText("  ")
                    if b_curr.blockNumber() == b_last.blockNumber():
                        break
                    b_curr = b_curr.next()
                cursor.endEditBlock()
                self.viewport().update()
                return
            else:
                is_list_or_cb = (
                    LIST_RE.match(line_text) is not None
                    or CHECKBOX_PATTERN.match(line_text) is not None
                )
                if is_list_or_cb:
                    # Indent or unindent the entire list/checkbox line at start of block
                    cursor.beginEditBlock()
                    c = QTextCursor(block)
                    c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    if is_shift:
                        rem = 2 if line_text.startswith("  ") else (1 if line_text.startswith(" ") else 0)
                        for _ in range(rem):
                            c.deleteChar()
                    else:
                        c.insertText("  ")
                    cursor.endEditBlock()
                    self.viewport().update()
                    return
                else:
                    cursor.beginEditBlock()
                    if is_shift:
                        rem = 2 if line_text.startswith("  ") else (1 if line_text.startswith(" ") else 0)
                        if rem > 0:
                            c = QTextCursor(block)
                            c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                            for _ in range(rem):
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
        prefix_len = 0
        qm = QUOTE_RE.match(text)
        if qm:
            prefix_len = len(qm.group(1))
            text = text[prefix_len:]

        info = get_checkbox_info(text)
        if info is None:
            return

        bracket_start, bracket_end, prefix_end, is_checked = info
        replacement = "[ ] " if is_checked else "[x] "

        edit_cursor = QTextCursor(self.document())
        edit_cursor.beginEditBlock()
        edit_cursor.setPosition(block.position() + prefix_len + bracket_start)
        edit_cursor.setPosition(
            block.position() + prefix_len + max(bracket_end, prefix_end),
            QTextCursor.MoveMode.KeepAnchor,
        )
        edit_cursor.insertText(replacement)
        edit_cursor.endEditBlock()
        self.viewport().update()


class EditorPanel(QWidget):
    """Right pane editor containing metadata header, note title, and the editor canvas."""

    content_saved = pyqtSignal(str)  # Emits new content when debounced auto-save fires
    title_changed = pyqtSignal(str)  # Emits new title when debounced title editing fires
    create_note_with_content = pyqtSignal(str)  # Emitted when user types on empty canvas
    delete_requested = pyqtSignal()
    expand_notes_requested = pyqtSignal()
    open_file_requested = pyqtSignal()
    backup_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._current_note: Optional[Note] = None

        # Debounce timer for smooth non-blocking auto-save of body content
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._trigger_auto_save)

        # Debounce timer for note title editing / renaming
        self._title_timer = QTimer(self)
        self._title_timer.setSingleShot(True)
        self._title_timer.setInterval(350)
        self._title_timer.timeout.connect(self._flush_title_change)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 12)
        layout.setSpacing(6)

        # Header bar (Folder name, word count, delete button)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        # Button to expand notes list when collapsed
        self.expand_notes_btn = QPushButton(parent=self)
        self.expand_notes_btn.setObjectName("IconButton")
        self.expand_notes_btn.setIcon(create_notes_toggle_icon("#8e8e93", size=15))
        self.expand_notes_btn.setToolTip("Show Notes List")
        self.expand_notes_btn.setFixedSize(26, 26)
        self.expand_notes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_notes_btn.setVisible(False)
        self.expand_notes_btn.clicked.connect(self.expand_notes_requested.emit)
        header.addWidget(self.expand_notes_btn)

        self.meta_label = QLabel("", parent=self)
        self.meta_label.setStyleSheet("color: #7a7a7a; font-size: 11px;")
        header.addWidget(self.meta_label)

        header.addStretch()

        self.word_count_label = QLabel("0 words", parent=self)
        self.word_count_label.setStyleSheet("color: #7a7a7a; font-size: 11px; padding-right: 6px;")
        header.addWidget(self.word_count_label)

        # Cloud Backup & Sync Button
        self.backup_btn = QPushButton(parent=self)
        self.backup_btn.setObjectName("IconButton")
        self.backup_btn.setIcon(create_backup_icon("#8e8e93", size=15))
        self.backup_btn.setToolTip("Cloud Backup & Version History (Ctrl+Shift+B)")
        self.backup_btn.setFixedSize(26, 26)
        self.backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.backup_btn.clicked.connect(self.backup_requested.emit)
        header.addWidget(self.backup_btn)

        # Open Markdown File Button
        self.open_file_btn = QPushButton(parent=self)
        self.open_file_btn.setObjectName("IconButton")
        self.open_file_btn.setIcon(create_open_file_icon("#8e8e93", size=15))
        self.open_file_btn.setToolTip("Open Markdown File (Ctrl+O)")
        self.open_file_btn.setFixedSize(26, 26)
        self.open_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_file_btn.clicked.connect(self.open_file_requested.emit)
        header.addWidget(self.open_file_btn)

        # Export Note Button (PDF / HTML / Markdown)
        self.export_btn = QPushButton(parent=self)
        self.export_btn.setObjectName("IconButton")
        self.export_btn.setIcon(create_export_icon("#8e8e93", size=15))
        self.export_btn.setToolTip("Export Note (Ctrl+E)")
        self.export_btn.setFixedSize(26, 26)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._show_export_menu)
        header.addWidget(self.export_btn)

        layout.addLayout(header)

        # Frameless note title input (Notion/Craft aesthetic)
        self.title_edit = NoteTitleEdit(parent=self)
        self.title_edit.setEnabled(False)
        self.title_edit.enter_pressed.connect(self._on_title_enter_or_down)
        self.title_edit.down_pressed.connect(self._on_title_enter_or_down)
        self.title_edit.textEdited.connect(self._on_title_edited)
        self.title_edit.editingFinished.connect(self._flush_title_change)
        layout.addWidget(self.title_edit)

        # Editor canvas
        self.editor = MarkdownEditor(parent=self)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.up_at_top_requested.connect(self._on_up_at_top)

        # In-note Find & Replace Bar
        self.find_replace_bar = FindReplaceBar(parent=self)
        self.find_replace_bar.find_changed.connect(self._on_find_changed)
        self.find_replace_bar.find_next_requested.connect(self._on_find_next)
        self.find_replace_bar.find_prev_requested.connect(self._on_find_prev)
        self.find_replace_bar.replace_current_requested.connect(self._on_replace_current)
        self.find_replace_bar.replace_all_requested.connect(self._on_replace_all)
        self.find_replace_bar.closed.connect(self.close_find)

        self.editor.find_requested.connect(self.open_find)
        self.editor.find_close_requested.connect(self.close_find)

        find_container = QHBoxLayout()
        find_container.setContentsMargins(0, 0, 0, 2)
        find_container.addStretch()
        find_container.addWidget(self.find_replace_bar)
        self.find_replace_bar.setVisible(False)
        layout.addLayout(find_container)

        layout.addWidget(self.editor)

    def open_find(self, replace_mode: bool = False) -> None:
        """Display Find & Replace bar and prefill with current selection if any."""
        cursor = self.editor.textCursor()
        had_text_change = False
        if cursor.hasSelection():
            sel_text = cursor.selectedText()
            if sel_text and "\u2029" not in sel_text and "\n" not in sel_text:
                if self.find_replace_bar.find_input.text() != sel_text:
                    had_text_change = True
                    self.find_replace_bar.find_input.setText(sel_text)

        self.find_replace_bar.set_replace_visible(replace_mode)
        self.find_replace_bar.show()
        if replace_mode and self.find_replace_bar.find_input.text().strip():
            self.find_replace_bar.focus_replace()
        else:
            self.find_replace_bar.focus_find()

        if not had_text_change:
            self.find_replace_bar.retrigger_search()

    def close_find(self) -> None:
        """Hide Find & Replace bar, clear document highlights, and return focus to editor."""
        self.find_replace_bar.hide()
        self.editor.clear_search()
        self.editor.setFocus()

    def _on_find_changed(self, query: str, match_case: bool, whole_word: bool) -> None:
        curr, total = self.editor.find_matches(query, match_case, whole_word)
        self.find_replace_bar.set_match_status(curr, total)

    def _on_find_next(self) -> None:
        curr, total = self.editor.find_next()
        self.find_replace_bar.set_match_status(curr, total)

    def _on_find_prev(self) -> None:
        curr, total = self.editor.find_prev()
        self.find_replace_bar.set_match_status(curr, total)

    def _on_replace_current(self, replacement: str) -> None:
        curr, total = self.editor.replace_current(replacement)
        self.find_replace_bar.set_match_status(curr, total)

    def _on_replace_all(
        self, query: str, replacement: str, match_case: bool, whole_word: bool
    ) -> None:
        self.editor.replace_all(query, replacement, match_case, whole_word)
        self.find_replace_bar.set_match_status(0, 0)

    def _on_title_enter_or_down(self) -> None:
        """Move cursor from title edit into the start of the markdown editor body."""
        self._flush_title_change()
        self.editor.setFocus()
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)

    def _on_up_at_top(self) -> None:
        """Jump focus back into title edit when pressing Up arrow at position (0, 0)."""
        self.title_edit.setFocus()
        self.title_edit.setCursorPosition(len(self.title_edit.text()))

    def _on_title_edited(self, text: str) -> None:
        self._title_timer.start()

    def _flush_title_change(self) -> None:
        if self._title_timer.isActive():
            self._title_timer.stop()
        new_title = self.title_edit.text().strip()
        if not new_title:
            return
        if self._current_note is not None and new_title != self._current_note.title:
            self.title_changed.emit(new_title)

    def _show_export_menu(self) -> None:
        """Display export format menu and launch native desktop file chooser."""
        if self._current_note is None and not self.editor.toPlainText().strip():
            return

        menu = QMenu(self)
        pdf_action = menu.addAction("Export as PDF (.pdf)")
        html_dark_action = menu.addAction("Export as HTML (Dark)")
        html_light_action = menu.addAction("Export as HTML (Light)")
        md_action = menu.addAction("Export as Markdown (.md)")

        action = menu.exec(self.export_btn.mapToGlobal(QPoint(0, self.export_btn.height() + 2)))
        if not action:
            return

        title = self.get_title()
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip() or "Untitled"
        content = self.get_content()

        doc_dir = Path.home() / "Documents"
        if not doc_dir.exists():
            doc_dir = Path.home()

        if action == pdf_action:
            default_path = str(doc_dir / f"{safe_title}.pdf")
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Note as PDF",
                default_path,
                "PDF Documents (*.pdf);;All Files (*)",
            )
            if file_path:
                target = Path(file_path)
                if not target.suffix:
                    target = target.with_suffix(".pdf")
                from utils.exporter import export_note_to_pdf
                if export_note_to_pdf(title, content, target):
                    QToolTip.showText(
                        self.export_btn.mapToGlobal(QPoint(0, 0)),
                        f"Exported {target.name} successfully!",
                        self.export_btn,
                    )
        elif action in (html_dark_action, html_light_action):
            is_dark = (action == html_dark_action)
            default_path = str(doc_dir / f"{safe_title}.html")
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Note as HTML",
                default_path,
                "HTML Documents (*.html);;All Files (*)",
            )
            if file_path:
                target = Path(file_path)
                if not target.suffix:
                    target = target.with_suffix(".html")
                from utils.exporter import export_note_to_html
                if export_note_to_html(title, content, target, dark_theme=is_dark):
                    QToolTip.showText(
                        self.export_btn.mapToGlobal(QPoint(0, 0)),
                        f"Exported {target.name} successfully!",
                        self.export_btn,
                    )
        elif action == md_action:
            default_path = str(doc_dir / f"{safe_title}.md")
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Note as Markdown",
                default_path,
                "Markdown Documents (*.md);;All Files (*)",
            )
            if file_path:
                target = Path(file_path)
                if not target.suffix:
                    target = target.with_suffix(".md")
                try:
                    target.write_text(content, encoding="utf-8")
                    QToolTip.showText(
                        self.export_btn.mapToGlobal(QPoint(0, 0)),
                        f"Exported {target.name} successfully!",
                        self.export_btn,
                    )
                except Exception:
                    pass

    def export_current_note(self) -> None:
        """Trigger export menu from shortcut (Ctrl+E)."""
        self._show_export_menu()

    def load_note(self, note: Optional[Note]) -> None:
        """Load note markdown into the editor as pure plain text with live highlighting."""
        self._current_note = note
        self._save_timer.stop()
        self.editor.slash_palette.hide()
        if hasattr(self.editor, "format_toolbar"):
            self.editor.format_toolbar.hide()
        if self._title_timer.isActive():
            self._title_timer.stop()

        if note is None:
            self.export_btn.setEnabled(False)
            self.title_edit.blockSignals(True)
            self.title_edit.setText("")
            self.title_edit.setEnabled(False)
            self.title_edit.blockSignals(False)

            self.editor.blockSignals(True)
            self.editor.setPlainText("")
            self.meta_label.setText("No note selected")
            self.word_count_label.setText("0 words")
            self.editor.blockSignals(False)
            return

        self.export_btn.setEnabled(True)
        self.title_edit.setEnabled(True)
        self.title_edit.blockSignals(True)
        self.title_edit.setText(note.title)
        self.title_edit.blockSignals(False)

        # Clean any accidental escaped headings (\# ) and normalize "- []" to "- [ ]"
        cleaned_content = re.sub(r"^\\(#+\s)", r"\1", note.content, flags=re.MULTILINE)
        cleaned_content = re.sub(
            r"^(\s*[-*+]\s*)\[\](?=\s|$)", r"\1[ ]", cleaned_content, flags=re.MULTILINE
        )

        self.editor._table_scroll_x.clear()
        self.editor._code_scroll_x.clear()
        self.editor._copied_code_block = None
        self.editor._scrollbar_drag = None

        self.editor.blockSignals(True)
        self.editor.setPlainText(cleaned_content)
        self.editor._update_blockquote_margins()
        self.editor.highlighter.active_block_number = self.editor.textCursor().block().blockNumber()
        self.editor.highlighter.cursor_pos_in_block = self.editor.textCursor().positionInBlock()
        self.editor.highlighter.refresh_regions()
        self.editor.highlighter.rehighlight()
        self.editor.viewport().update()
        self.editor.blockSignals(False)

        self.update_meta(note)
        self._update_word_count()

        if hasattr(self, "find_replace_bar") and self.find_replace_bar.isVisible() and self.find_replace_bar.find_input.text():
            self.find_replace_bar.retrigger_search()
        else:
            self.editor.clear_search()

    def update_meta(self, note: Note) -> None:
        """Update only the metadata header without reloading the editor document."""
        self._current_note = note
        folder_name = note.path.parent.name
        self.meta_label.setText(f"{folder_name}  •  Edited {note.formatted_time}")
        if not self.title_edit.hasFocus() and self.title_edit.text() != note.title:
            self.title_edit.blockSignals(True)
            self.title_edit.setText(note.title)
            self.title_edit.blockSignals(False)

    def set_backup_changes_count(self, count: int) -> None:
        """Update the top-right cloud backup icon with a pending changes indicator."""
        has_changes = count > 0
        color = "#e5a93c" if has_changes else "#8e8e93"
        self.backup_btn.setIcon(create_backup_icon(color, size=15, has_dot=has_changes))
        tip = (
            f"Cloud Backup & Version History ({count} unsynced changes)"
            if has_changes
            else "Cloud Backup & Version History (Ctrl+Shift+B)"
        )
        self.backup_btn.setToolTip(tip)

    def get_title(self) -> str:
        """Return the current title edit text."""
        return self.title_edit.text().strip() or "Untitled"

    def get_content(self) -> str:
        """Return the pure plain-text Markdown content."""
        return self.editor.toPlainText()

    def _on_text_changed(self) -> None:
        self._update_word_count()
        self._save_timer.start()
        if hasattr(self, "find_replace_bar") and self.find_replace_bar.isVisible() and self.find_replace_bar.find_input.text():
            self.find_replace_bar.retrigger_search()

    def _update_word_count(self) -> None:
        words = len(self.editor.toPlainText().split())
        self.word_count_label.setText(f"{words} words")

    def flush_pending_save(self) -> None:
        """Immediately flush any pending debounced save before application exit or switch."""
        if self._title_timer.isActive():
            self._flush_title_change()
        if self._save_timer.isActive():
            self._save_timer.stop()
            self._trigger_auto_save()

    def _trigger_auto_save(self) -> None:
        """Emit save signal with latest Markdown text."""
        content = self.editor.toPlainText()
        if self._current_note is None:
            if content.strip():
                self.create_note_with_content.emit(content)
        else:
            self.content_saved.emit(content)
