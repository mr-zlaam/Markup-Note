"""Modern dark-themed keyboard shortcuts cheatsheet modal dialog."""

from __future__ import annotations

from typing import List, Optional, Tuple

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from utils.icons import create_badge_pixmap, create_close_icon, create_keyboard_icon, create_search_icon


SHORTCUT_GROUPS: List[Tuple[str, List[Tuple[str, str, List[str]]]]] = [
    (
        "Markdown & Text Formatting",
        [
            ("Bold", "Toggle bold text formatting around selection", ["Ctrl", "B"]),
            ("Italic", "Toggle italic text formatting around selection", ["Ctrl", "I"]),
            ("Underline", "Toggle underline HTML tags around selection", ["Ctrl", "U"]),
            ("Strikethrough", "Toggle strikethrough syntax around selection", ["Ctrl", "Shift", "X"]),
            ("Inline Code", "Wrap selection in code backticks", ["Ctrl", "Shift", "C"]),
            ("Code Block", "Insert multiline fenced code block", ["Ctrl", "Shift", "K"]),
            ("Insert Link", "Insert or edit markdown link with URL", ["Ctrl", "K"]),
            ("Bulleted List", "Toggle bullet list on current block", ["Ctrl", "Shift", "U"]),
            ("Numbered List", "Toggle ordered numbered list on current block", ["Ctrl", "Shift", "O"]),
            ("Task Checkbox", "Toggle interactive to-do checkbox list", ["Ctrl", "Shift", "T"]),
            ("Heading 1", "Format current line as Heading 1 (#)", ["Ctrl", "1"]),
            ("Heading 2", "Format current line as Heading 2 (##)", ["Ctrl", "2"]),
            ("Heading 3", "Format current line as Heading 3 (###)", ["Ctrl", "3"]),
            ("Blockquote", "Toggle quote block formatting (>)", ["Ctrl", "Shift", "Q"]),
            ("Toggle Checkbox", "Check or uncheck task under cursor", ["Ctrl", "Enter"]),
            ("Indent List Item", "Indent bullet or task by 2 spaces", ["Tab"]),
            ("Outdent List Item", "Outdent bullet or task item", ["Shift", "Tab"]),
            ("Slash Command Palette", "Open Notion-style block insert palette", ["/"]),
        ],
    ),
    (
        "Notes & Folders",
        [
            ("New Note", "Create a new note in the active folder", ["Ctrl", "N"]),
            ("New Folder", "Create a new folder or subfolder", ["Ctrl", "Shift", "N"]),
            ("Delete Folder", "Prompt confirmation to delete focused folder", ["Delete"]),
            ("Delete Note", "Prompt confirmation to delete focused note card", ["Delete"]),
            ("Toggle Folder", "Single-click row to open or close subfolders", ["Click"]),
            ("Multi-Selection Mode", "Right-click item and choose Select", ["Right-Click"]),
            ("Exit Selection Mode", "Cancel multi-note or multi-folder selection", ["Esc"]),
        ],
    ),
    (
        "Navigation & Search",
        [
            ("Search Notes", "Focus the global note filter search bar", ["Ctrl", "Shift", "F"]),
            ("In-Note Find", "Open document search bar overlay", ["Ctrl", "F"]),
            ("In-Note Replace", "Open document find and replace bar", ["Ctrl", "H"]),
            ("Next Search Match", "Jump to the next search occurrence", ["Enter"]),
            ("Previous Match", "Jump to the previous search occurrence", ["Shift", "Enter"]),
            ("Jump to Note Title", "From top line of note, jump up to title", ["Up Arrow"]),
            ("Dismiss Overlay / Palette", "Close find bar, slash menu, or dialog", ["Esc"]),
        ],
    ),
    (
        "Panels, Sync & Export",
        [
            ("Toggle Folders Sidebar", "Expand or collapse the folder tree sidebar", ["Ctrl", "\\"]),
            ("Toggle Notes List Pane", "Expand or collapse the note cards list", ["Ctrl", "Shift", "\\"]),
            ("Cloud Backup & History", "Open Git sync & version history panel", ["Ctrl", "Shift", "B"]),
            ("Open Markdown File", "Open external .md document into notes", ["Ctrl", "O"]),
            ("Export Note", "Export note to PDF, HTML, or Markdown", ["Ctrl", "E"]),
            ("Keyboard Shortcuts", "Display this keyboard shortcuts cheatsheet", ["Ctrl", "/"]),
        ],
    ),
]


class KeyBadge(QLabel):
    """Sleek keyboard key cap badge component."""

    def __init__(self, key_name: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(key_name, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #26262b;
                color: #e5e5ea;
                font-family: monospace, "DejaVu Sans Mono", monospace;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid #3c3c46;
                border-bottom: 2px solid #202026;
                border-radius: 4px;
                padding: 2px 7px;
            }
        """)


class ShortcutRow(QWidget):
    """A single shortcut item displaying title, description, and key cap badges."""

    def __init__(
        self, title: str, description: str, keys: List[str], parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.title_text = title
        self.description_text = description
        self.keys_text = " ".join(keys)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(12)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self.lbl_title = QLabel(title, parent=self)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #f2f2f6;")
        info_layout.addWidget(self.lbl_title)

        self.lbl_desc = QLabel(description, parent=self)
        self.lbl_desc.setStyleSheet("font-size: 11px; color: #8e8e93;")
        info_layout.addWidget(self.lbl_desc)

        layout.addLayout(info_layout, 1)

        keys_layout = QHBoxLayout()
        keys_layout.setContentsMargins(0, 0, 0, 0)
        keys_layout.setSpacing(4)
        for idx, k in enumerate(keys):
            if idx > 0:
                plus_lbl = QLabel("+", parent=self)
                plus_lbl.setStyleSheet("color: #636366; font-size: 11px; font-weight: 600;")
                keys_layout.addWidget(plus_lbl)
            keys_layout.addWidget(KeyBadge(k, parent=self))

        layout.addLayout(keys_layout, 0)

        self.setStyleSheet("""
            ShortcutRow {
                background-color: transparent;
                border-radius: 6px;
            }
            ShortcutRow:hover {
                background-color: #28282e;
            }
        """)

    def matches(self, query: str) -> bool:
        """Check if this shortcut matches the search query string."""
        if not query:
            return True
        q = query.lower()
        return (
            q in self.title_text.lower()
            or q in self.description_text.lower()
            or q in self.keys_text.lower()
        )


class ModernShortcutsDialog(QDialog):
    """Categorized keyboard shortcuts reference modal dialog."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setFixedSize(680, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._shortcut_rows: List[Tuple[ShortcutRow, QWidget]] = []
        self._group_widgets: List[Tuple[QWidget, List[ShortcutRow]]] = []

        self._init_ui()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        card = QFrame(parent=self)
        card.setObjectName("ShortcutsCard")
        card.setStyleSheet("""
            QFrame#ShortcutsCard {
                background-color: #1c1c20;
                border: 1px solid #383840;
                border-radius: 12px;
            }
        """)
        outer_layout.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(14)

        # 1. Header with Badge Icon and Close Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        kb_icon = create_keyboard_icon(color="#0a84ff", size=20)
        badge_pm = create_badge_pixmap(kb_icon, bg_color="#182232", border_color="#233b5d", badge_size=38, icon_size=20)
        icon_label = QLabel(parent=card)
        icon_label.setPixmap(badge_pm)
        header_layout.addWidget(icon_label)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)

        title_lbl = QLabel("Keyboard Shortcuts", parent=card)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f2f2f6;")
        title_col.addWidget(title_lbl)

        sub_lbl = QLabel("Master Markup Notes with quick keyboard actions", parent=card)
        sub_lbl.setStyleSheet("font-size: 12px; color: #8e8e93;")
        title_col.addWidget(sub_lbl)

        header_layout.addLayout(title_col, 1)

        close_btn = QPushButton(parent=card)
        close_btn.setObjectName("IconButton")
        close_btn.setIcon(create_close_icon(color="#8e8e93", size=14))
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Close (Esc)")
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #242428;
                border: 1px solid #383840;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #303038;
                color: #ffffff;
            }
        """)
        header_layout.addWidget(close_btn)

        card_layout.addLayout(header_layout)

        # 2. Search & Filter Bar
        self.search_edit = QLineEdit(parent=card)
        self.search_edit.setPlaceholderText("Search shortcuts (e.g. bold, link, delete, folder)...")
        self.search_edit.addAction(create_search_icon(color="#7a7a82", size=14), QLineEdit.ActionPosition.LeadingPosition)
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #24242a;
                color: #f2f2f6;
                font-size: 13px;
                border: 1px solid #3c3c46;
                border-radius: 8px;
                padding: 7px 12px 7px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #0a84ff;
                background-color: #282830;
            }
        """)
        card_layout.addWidget(self.search_edit)

        # 3. Scrollable Categories Area
        scroll = QScrollArea(parent=card)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3c3c44;
                min-height: 24px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555560;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setContentsMargins(0, 4, 4, 4)
        self.container_layout.setSpacing(14)

        for group_title, items in SHORTCUT_GROUPS:
            group_widget = QWidget(parent=container)
            group_layout = QVBoxLayout(group_widget)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(4)

            # Group Header
            group_header = QLabel(group_title.upper(), parent=group_widget)
            group_header.setStyleSheet("""
                QLabel {
                    color: #0a84ff;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 0.8px;
                    padding-bottom: 2px;
                }
            """)
            group_layout.addWidget(group_header)

            group_rows: List[ShortcutRow] = []
            for title, desc, keys in items:
                row = ShortcutRow(title, desc, keys, parent=group_widget)
                group_layout.addWidget(row)
                group_rows.append(row)
                self._shortcut_rows.append((row, group_widget))

            self.container_layout.addWidget(group_widget)
            self._group_widgets.append((group_widget, group_rows))

        self.container_layout.addStretch()
        scroll.setWidget(container)
        card_layout.addWidget(scroll, 1)

        # 4. Footer hint
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        tip_lbl = QLabel("Tip: Press Ctrl+/ or F1 anywhere to view shortcuts.", parent=card)
        tip_lbl.setStyleSheet("font-size: 11px; color: #636366;")
        footer_layout.addWidget(tip_lbl)
        footer_layout.addStretch()

        ok_btn = QPushButton("Done", parent=card)
        ok_btn.setFixedSize(70, 28)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c32;
                color: #e5e5ea;
                font-size: 12px;
                font-weight: 600;
                border: 1px solid #44444c;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #383840;
                color: #ffffff;
            }
        """)
        footer_layout.addWidget(ok_btn)

        card_layout.addLayout(footer_layout)

    def _on_search_changed(self, query: str) -> None:
        """Filter shortcuts and group headers dynamically based on query."""
        clean_query = query.strip()
        for group_widget, rows in self._group_widgets:
            any_visible = False
            for row in rows:
                is_match = row.matches(clean_query)
                row.setVisible(is_match)
                if is_match:
                    any_visible = True
            group_widget.setVisible(any_visible)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Close on Escape or Enter."""
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept()
            event.accept()
            return
        super().keyPressEvent(event)

    @staticmethod
    def show_shortcuts(parent: Optional[QWidget] = None) -> None:
        """Convenience method to instantiate and execute the shortcuts modal."""
        dialog = ModernShortcutsDialog(parent=parent)
        dialog.exec()
