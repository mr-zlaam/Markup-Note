"""Visual styling and QSS theme for Apple Notes aesthetic on Linux."""

from __future__ import annotations

DARK_THEME_QSS = """
/* Global Window & Fonts */
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, "Cantarell", "Inter", "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}

/* Splitter Styling */
QSplitter::handle {
    background-color: #2b2b2b;
}

QSplitter::handle:horizontal {
    width: 1px;
}

/* Sidebar List (flat fallback) */
QListWidget#SidebarList {
    background-color: #181818;
    border: none;
    padding: 8px 4px;
    outline: none;
}

QListWidget#SidebarList::item {
    padding: 6px 8px;
    border-radius: 4px;
    margin: 1px 2px;
    color: #b0b0b0;
    font-weight: 500;
}

QListWidget#SidebarList::item:selected {
    background-color: #2a2a2a;
    color: #f3f3f3;
}

QListWidget#SidebarList::item:hover:!selected {
    background-color: #222222;
    color: #e0e0e0;
}

/* Sidebar Tree (hierarchical folder structure) */
QTreeWidget#SidebarTree {
    background-color: #181818;
    border: none;
    padding: 6px 4px;
    outline: none;
    show-decoration-selected: 1;
}

QTreeWidget#SidebarTree::item {
    padding: 6px 4px;
    border-radius: 0px;
    margin: 0px;
    color: #b0b0b0;
    font-weight: 500;
}

QTreeWidget#SidebarTree::item:selected,
QTreeWidget#SidebarTree::branch:selected {
    background-color: #2a2a2a;
    color: #f3f3f3;
}

QTreeWidget#SidebarTree::item:hover:!selected,
QTreeWidget#SidebarTree::branch:hover:!selected {
    background-color: #222222;
    color: #e0e0e0;
}

QTreeWidget#SidebarTree::branch {
    background: transparent;
}

QTreeWidget#SidebarTree::branch:has-children:closed {
    image: url("CHEVRON_RIGHT_URL");
}

QTreeWidget#SidebarTree::branch:has-children:open {
    image: url("CHEVRON_DOWN_URL");
}

/* Note Cards List */
QListWidget#NoteCardsList {
    background-color: #202020;
    border: none;
    border-right: 1px solid #2b2b2b;
    outline: none;
    padding: 4px;
}

QListWidget#NoteCardsList::item {
    background-color: transparent;
    border-bottom: 1px solid #282828;
    padding: 10px 14px;
    border-radius: 6px;
    margin: 2px 4px;
}

QListWidget#NoteCardsList::item:selected {
    background-color: #2c2c2e;
}

QListWidget#NoteCardsList::item:hover:!selected {
    background-color: #252528;
}

/* Search Input */
QLineEdit#SearchBar {
    background-color: #282828;
    color: #f0f0f0;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 10px 6px 4px;
    margin: 0px;
    font-size: 12px;
}

QLineEdit#SearchBar:focus {
    border: 1px solid #0a84ff;
    background-color: #2e2e2e;
}

/* Editor Styling */
QTextEdit#MarkdownEditor, QPlainTextEdit#MarkdownEditor {
    background-color: #1e1e1e;
    color: #e6e6e6;
    border: none;
    padding: 6px 36px 24px 36px;
    font-size: 16px;
    selection-background-color: #0a84ff;
    selection-color: #ffffff;
}

/* Toolbar Buttons */
QPushButton#ActionBtn {
    background-color: transparent;
    color: #a0a0a0;
    border: none;
    border-radius: 4px;
    padding: 5px 8px;
    font-weight: 500;
}

QPushButton#ActionBtn:hover {
    background-color: #2e2e2e;
    color: #ffffff;
}

QPushButton#ActionBtn:pressed {
    background-color: #383838;
}

/* Icon Buttons */
QPushButton#IconButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 3px;
}

QPushButton#IconButton:hover {
    background-color: #2c2c30;
}

QPushButton#IconButton:pressed {
    background-color: #38383e;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #3e3e3e;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Context Menus */
QMenu {
    background-color: #242428;
    color: #f2f2f6;
    border: 1px solid #3c3c44;
    border-radius: 8px;
    padding: 5px;
}

QMenu::item {
    background-color: transparent;
    padding: 7px 22px 7px 10px;
    border-radius: 5px;
    margin: 1px;
    font-size: 13px;
    font-weight: 500;
}

QMenu::item:selected {
    background-color: #0a84ff;
    color: #ffffff;
}

QMenu::item:disabled {
    color: #6c6c74;
}

QMenu::separator {
    height: 1px;
    background-color: #383840;
    margin: 4px 6px;
}

/* Modern Dark Tooltips */
QToolTip {
    background-color: #202024;
    color: #e2e2e6;
    border: 1px solid #36363c;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 11px;
    font-weight: 500;
}

/* Modern Dark File Dialog */
QFileDialog {
    background-color: #202024;
    color: #e0e0e0;
}
QFileDialog QListView, QFileDialog QTreeView {
    background-color: #1a1a1d;
    color: #e0e0e4;
    border: 1px solid #36363c;
    border-radius: 6px;
    selection-background-color: #0a84ff;
    selection-color: #ffffff;
}
QFileDialog QHeaderView::section {
    background-color: #242428;
    color: #9c9ca4;
    padding: 4px;
    border: none;
    border-bottom: 1px solid #36363c;
}
QFileDialog QLineEdit {
    background-color: #161619;
    border: 1px solid #383840;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
}
QFileDialog QPushButton {
    background-color: #2c2c32;
    color: #e0e0e0;
    border: 1px solid #3c3c44;
    border-radius: 6px;
    padding: 6px 14px;
}
QFileDialog QPushButton:hover {
    background-color: #383840;
    color: #ffffff;
}
"""


def apply_theme(app) -> None:
    """Apply the application-wide dark styling and ensure assets."""
    from utils.icons import ensure_chevron_assets
    themed_qss = DARK_THEME_QSS
    try:
        right_path, down_path = ensure_chevron_assets()
        r_url = right_path.resolve().as_posix()
        d_url = down_path.resolve().as_posix()
        themed_qss = themed_qss.replace("CHEVRON_RIGHT_URL", r_url).replace("CHEVRON_DOWN_URL", d_url)
    except Exception:
        # Fallback to relative assets path if dynamic resolution fails
        themed_qss = themed_qss.replace("CHEVRON_RIGHT_URL", "assets/chevron_right.png").replace(
            "CHEVRON_DOWN_URL", "assets/chevron_down.png"
        )
    app.setStyleSheet(themed_qss)
