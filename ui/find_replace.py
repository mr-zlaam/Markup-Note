"""In-note Find and Replace floating bar widget (Notion / VS Code aesthetic)."""

from typing import Optional, Tuple
from PyQt6.QtCore import QEvent, QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QKeyEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.icons import (
    create_chevron_icon,
    create_close_icon,
    create_search_icon,
)


class CustomKeyLineEdit(QLineEdit):
    """QLineEdit with dedicated KeyPress signals for navigation (Enter, Shift+Enter, Esc, Up, Down)."""

    enter_pressed = pyqtSignal(bool)  # is_shift
    escape_pressed = pyqtSignal()
    up_pressed = pyqtSignal()
    down_pressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            is_shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self.enter_pressed.emit(is_shift)
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
            return
        elif event.key() == Qt.Key.Key_Up:
            self.up_pressed.emit()
            return
        elif event.key() == Qt.Key.Key_Down:
            self.down_pressed.emit()
            return
        super().keyPressEvent(event)


class FindReplaceBar(QFrame):
    """Sleek dark floating/docked Find & Replace widget for the active Markdown editor."""

    find_changed = pyqtSignal(str, bool, bool)  # (query, match_case, whole_word)
    find_next_requested = pyqtSignal()
    find_prev_requested = pyqtSignal()
    replace_current_requested = pyqtSignal(str)  # (replacement)
    replace_all_requested = pyqtSignal(str, str, bool, bool)  # (query, replacement, match_case, whole_word)
    closed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("FindReplaceBar")
        self._replace_visible: bool = False

        self.setStyleSheet("""
            QFrame#FindReplaceBar {
                background-color: #202024;
                border: 1px solid #36363c;
                border-radius: 8px;
            }
            QLineEdit#SearchLineEdit {
                background-color: #161618;
                color: #f0f0f4;
                border: 1px solid #323238;
                border-radius: 5px;
                padding: 4px 7px;
                font-size: 12px;
            }
            QLineEdit#SearchLineEdit:focus {
                border: 1px solid #0a84ff;
                background-color: #1a1a1e;
            }
            QPushButton#SearchIconBtn {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 2px;
                min-width: 22px;
                min-height: 22px;
            }
            QPushButton#SearchIconBtn:hover {
                background-color: #2c2c32;
            }
            QPushButton#SearchIconBtn:pressed {
                background-color: #383842;
            }
            QPushButton#SearchToggleBtn {
                background-color: transparent;
                color: #8e8e94;
                border: 1px solid transparent;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                min-width: 24px;
                min-height: 22px;
                padding: 0px 4px;
            }
            QPushButton#SearchToggleBtn:hover {
                background-color: #2c2c32;
                color: #e0e0e4;
            }
            QPushButton#SearchToggleBtn:checked {
                background-color: #0a84ff;
                color: #ffffff;
                border: 1px solid #0a84ff;
            }
            QPushButton#SearchActionBtn {
                background-color: #28282e;
                color: #e2e2e6;
                border: 1px solid #383840;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
                padding: 3px 10px;
                min-height: 22px;
            }
            QPushButton#SearchActionBtn:hover {
                background-color: #36363e;
                color: #ffffff;
            }
            QPushButton#SearchActionBtn:pressed {
                background-color: #0a84ff;
                color: #ffffff;
            }
            QPushButton#SearchActionBtn:disabled {
                color: #55555c;
                border-color: #26262a;
                background-color: #1c1c20;
            }
            QLabel#MatchCountLabel {
                color: #8e8e94;
                font-size: 11px;
                min-width: 48px;
                padding: 0 4px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # -----------------------------------------------------------------
        # Row 1: Find Row
        # -----------------------------------------------------------------
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(4)

        # Toggle Expand/Collapse Replace Row Button
        self.toggle_replace_btn = QPushButton(parent=self)
        self.toggle_replace_btn.setObjectName("SearchIconBtn")
        self.toggle_replace_btn.setToolTip("Toggle Replace Mode (Ctrl+H)")
        self.toggle_replace_btn.setIcon(create_chevron_icon("right", color="#8e8e94", size=14))
        self.toggle_replace_btn.setFixedSize(22, 22)
        self.toggle_replace_btn.clicked.connect(self.toggle_replace_row)
        row1.addWidget(self.toggle_replace_btn)

        # Find Input
        self.find_input = CustomKeyLineEdit(parent=self)
        self.find_input.setObjectName("SearchLineEdit")
        self.find_input.setPlaceholderText("Find in note...")
        self.find_input.setMinimumWidth(150)
        self.find_input.textChanged.connect(self._on_search_text_changed)
        self.find_input.enter_pressed.connect(self._on_find_enter)
        self.find_input.escape_pressed.connect(self.closed.emit)
        self.find_input.down_pressed.connect(self._on_find_down)
        row1.addWidget(self.find_input)

        # Match Count Label
        self.match_label = QLabel("No results", parent=self)
        self.match_label.setObjectName("MatchCountLabel")
        self.match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row1.addWidget(self.match_label)

        # Match Case Button ("Aa")
        self.case_btn = QPushButton("Aa", parent=self)
        self.case_btn.setObjectName("SearchToggleBtn")
        self.case_btn.setCheckable(True)
        self.case_btn.setToolTip("Match Case (Alt+C)")
        self.case_btn.setFixedSize(26, 22)
        self.case_btn.toggled.connect(self._on_search_text_changed)
        row1.addWidget(self.case_btn)

        # Match Whole Word Button ("\b")
        self.word_btn = QPushButton(r"\b", parent=self)
        self.word_btn.setObjectName("SearchToggleBtn")
        self.word_btn.setCheckable(True)
        self.word_btn.setToolTip("Match Whole Word (Alt+W)")
        self.word_btn.setFixedSize(26, 22)
        self.word_btn.toggled.connect(self._on_search_text_changed)
        row1.addWidget(self.word_btn)

        # Previous Match Button (Chevron Up)
        self.prev_btn = QPushButton(parent=self)
        self.prev_btn.setObjectName("SearchIconBtn")
        self.prev_btn.setToolTip("Previous Match (Shift+Enter)")
        self.prev_btn.setIcon(create_chevron_icon("up", color="#8e8e94", size=14))
        self.prev_btn.setFixedSize(22, 22)
        self.prev_btn.clicked.connect(self.find_prev_requested.emit)
        row1.addWidget(self.prev_btn)

        # Next Match Button (Chevron Down)
        self.next_btn = QPushButton(parent=self)
        self.next_btn.setObjectName("SearchIconBtn")
        self.next_btn.setToolTip("Next Match (Enter)")
        self.next_btn.setIcon(create_chevron_icon("down", color="#8e8e94", size=14))
        self.next_btn.setFixedSize(22, 22)
        self.next_btn.clicked.connect(self.find_next_requested.emit)
        row1.addWidget(self.next_btn)

        # Close Button
        self.close_btn = QPushButton(parent=self)
        self.close_btn.setObjectName("SearchIconBtn")
        self.close_btn.setToolTip("Close (Escape)")
        self.close_btn.setIcon(create_close_icon(color="#8e8e94", size=14))
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.clicked.connect(self.closed.emit)
        row1.addWidget(self.close_btn)

        main_layout.addLayout(row1)

        # -----------------------------------------------------------------
        # Row 2: Replace Row (Expandable)
        # -----------------------------------------------------------------
        self.replace_widget = QWidget(parent=self)
        row2 = QHBoxLayout(self.replace_widget)
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(4)

        # Indent spacer matching toggle_replace_btn width
        indent_label = QLabel(parent=self.replace_widget)
        indent_label.setFixedWidth(22)
        row2.addWidget(indent_label)

        # Replace Input
        self.replace_input = CustomKeyLineEdit(parent=self.replace_widget)
        self.replace_input.setObjectName("SearchLineEdit")
        self.replace_input.setPlaceholderText("Replace with...")
        self.replace_input.setMinimumWidth(150)
        self.replace_input.enter_pressed.connect(self._on_replace_enter)
        self.replace_input.escape_pressed.connect(self.closed.emit)
        self.replace_input.up_pressed.connect(self.focus_find)
        row2.addWidget(self.replace_input)

        # Replace Button
        self.replace_btn = QPushButton("Replace", parent=self.replace_widget)
        self.replace_btn.setObjectName("SearchActionBtn")
        self.replace_btn.setToolTip("Replace Current Match (Enter)")
        self.replace_btn.clicked.connect(self._emit_replace_current)
        row2.addWidget(self.replace_btn)

        # Replace All Button
        self.replace_all_btn = QPushButton("Replace All", parent=self.replace_widget)
        self.replace_all_btn.setObjectName("SearchActionBtn")
        self.replace_all_btn.setToolTip("Replace All Occurrences")
        self.replace_all_btn.clicked.connect(self._emit_replace_all)
        row2.addWidget(self.replace_all_btn)

        self.replace_widget.setVisible(False)
        main_layout.addWidget(self.replace_widget)

    # ---------------------------------------------------------------------
    # Public Methods & Slot Handlers
    # ---------------------------------------------------------------------

    def toggle_replace_row(self) -> None:
        """Toggle the visibility of the Replace row."""
        self.set_replace_visible(not self._replace_visible)

    def set_replace_visible(self, visible: bool) -> None:
        """Expand or collapse the Replace row."""
        self._replace_visible = visible
        self.replace_widget.setVisible(visible)
        icon_dir = "down" if visible else "right"
        self.toggle_replace_btn.setIcon(create_chevron_icon(icon_dir, color="#8e8e94", size=14))
        self.adjustSize()

    def set_match_status(self, current: int, total: int) -> None:
        """Update match status count label (e.g. '3 / 14' or 'No results')."""
        if total <= 0:
            query = self.find_input.text().strip()
            self.match_label.setText("No results" if query else "")
            self.replace_btn.setEnabled(False)
            self.replace_all_btn.setEnabled(False)
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
        else:
            self.match_label.setText(f"{current} / {total}")
            self.replace_btn.setEnabled(True)
            self.replace_all_btn.setEnabled(True)
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)

    def focus_find(self) -> None:
        """Focus the search query input and highlight its text."""
        self.find_input.setFocus()
        self.find_input.selectAll()

    def focus_replace(self) -> None:
        """Focus the replacement input and highlight its text."""
        if not self._replace_visible:
            self.set_replace_visible(True)
        self.replace_input.setFocus()
        self.replace_input.selectAll()

    def retrigger_search(self) -> None:
        """Re-emit search query to update matches when note text changes."""
        self._on_search_text_changed()

    # ---------------------------------------------------------------------
    # Internal Signals
    # ---------------------------------------------------------------------

    def _on_search_text_changed(self) -> None:
        query = self.find_input.text()
        match_case = self.case_btn.isChecked()
        whole_word = self.word_btn.isChecked()
        self.find_changed.emit(query, match_case, whole_word)

    def _on_find_enter(self, is_shift: bool) -> None:
        if is_shift:
            self.find_prev_requested.emit()
        else:
            self.find_next_requested.emit()

    def _on_find_down(self) -> None:
        if self._replace_visible:
            self.focus_replace()

    def _on_replace_enter(self, is_shift: bool) -> None:
        if is_shift:
            self._emit_replace_all()
        else:
            self._emit_replace_current()

    def _emit_replace_current(self) -> None:
        replacement = self.replace_input.text()
        self.replace_current_requested.emit(replacement)

    def _emit_replace_all(self) -> None:
        query = self.find_input.text()
        replacement = self.replace_input.text()
        match_case = self.case_btn.isChecked()
        whole_word = self.word_btn.isChecked()
        self.replace_all_requested.emit(query, replacement, match_case, whole_word)
