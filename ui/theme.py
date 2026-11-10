"""Visual styling and QSS theme for Apple Notes aesthetic on Linux."""

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

/* Sidebar List */
QListWidget#SidebarList {
    background-color: #181818;
    border: none;
    padding: 8px 4px;
    outline: none;
}

QListWidget#SidebarList::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 6px;
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
    padding: 6px 12px;
    margin: 8px;
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
    padding: 24px 36px;
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
    padding: 6px 10px;
    font-weight: 500;
}

QPushButton#ActionBtn:hover {
    background-color: #2e2e2e;
    color: #ffffff;
}

QPushButton#ActionBtn:pressed {
    background-color: #383838;
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
"""


def apply_theme(app) -> None:
    """Apply the application-wide dark styling."""
    app.setStyleSheet(DARK_THEME_QSS)
