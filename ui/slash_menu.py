"""Floating slash ('/') command palette for instant markdown block insertion."""

from dataclasses import dataclass
from typing import List, Optional

from PyQt6.QtCore import QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class SlashCommand:
    """Represents a selectable markdown command in the slash menu."""

    id: str
    title: str
    description: str
    icon: str
    prefix: str


COMMANDS: List[SlashCommand] = [
    SlashCommand("h1", "Heading 1", "Large document title", "H1", "# "),
    SlashCommand("h2", "Heading 2", "Section heading", "H2", "## "),
    SlashCommand("h3", "Heading 3", "Sub-section heading", "H3", "### "),
    SlashCommand("todo", "To-do Checkbox", "Track tasks with a clickable checkbox", "[ ]", "- [ ] "),
    SlashCommand("bullet", "Bulleted List", "Simple bullet list", "•", "- "),
    SlashCommand("number", "Numbered List", "Ordered list with numbers", "1.", "1. "),
    SlashCommand("code", "Code Block", "Code snippet with syntax highlight", "{ }", "```\n\n```"),
    SlashCommand("quote", "Quote", "Indented blockquote", ">", "> "),
    SlashCommand("divider", "Divider", "Horizontal separation line", "---", "---\n"),
]


class SlashItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering slash menu items with icon, title, and description."""

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(option.rect.width(), 44)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cmd: Optional[SlashCommand] = index.data(Qt.ItemDataRole.UserRole)
        if cmd is None:
            painter.restore()
            return

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        rect = option.rect.adjusted(4, 2, -4, -2)

        if is_selected:
            painter.setBrush(QColor("#0a84ff"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)

        # Icon box
        icon_font = QFont(option.font)
        icon_font.setPointSize(10)
        icon_font.setBold(True)
        painter.setFont(icon_font)
        painter.setPen(QColor("#ffffff" if is_selected else "#0a84ff"))
        icon_rect = QRect(rect.left() + 8, rect.top() + 8, 28, 28)
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, cmd.icon)

        # Title
        title_font = QFont(option.font)
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#ffffff" if is_selected else "#f0f0f0"))
        title_rect = QRect(rect.left() + 42, rect.top() + 4, rect.width() - 50, 18)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, cmd.title)

        # Description
        desc_font = QFont(option.font)
        desc_font.setPointSize(8)
        painter.setFont(desc_font)
        painter.setPen(QColor("#e0e0e0" if is_selected else "#888888"))
        desc_rect = QRect(rect.left() + 42, rect.top() + 22, rect.width() - 50, 16)
        painter.drawText(desc_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, cmd.description)

        painter.restore()


class SlashCommandPalette(QFrame):
    """Floating popup menu triggered by typing '/' at the start of a line."""

    command_selected = pyqtSignal(object)  # Emits selected SlashCommand

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("SlashCommandPalette")
        self.setFixedSize(280, 280)
        self.setStyleSheet("""
            QFrame#SlashCommandPalette {
                background-color: #242426;
                border: 1px solid #38383a;
                border-radius: 8px;
            }
            QLabel#FilterHeader {
                color: #98989d;
                font-size: 11px;
                padding: 4px 10px;
                border-bottom: 1px solid #323234;
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.filter_label = QLabel("Type to filter commands...", parent=self)
        self.filter_label.setObjectName("FilterHeader")
        layout.addWidget(self.filter_label)

        self.list_widget = QListWidget(parent=self)
        self.list_widget.setItemDelegate(SlashItemDelegate(self.list_widget))
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        self._filter_text = ""
        self.populate()

    @property
    def filter_text(self) -> str:
        """Return current active filter query."""
        return self._filter_text

    def populate(self, query: str = "") -> None:
        """Filter and populate command items."""
        self._filter_text = query.lower().strip()
        if self._filter_text:
            self.filter_label.setText(f"Filter: {self._filter_text}")
            self.filter_label.setStyleSheet("color: #0a84ff; font-size: 11px; font-weight: 600; padding: 4px 10px; border-bottom: 1px solid #323234;")
        else:
            self.filter_label.setText("Type to filter commands...")
            self.filter_label.setStyleSheet("color: #98989d; font-size: 11px; padding: 4px 10px; border-bottom: 1px solid #323234;")

        self.list_widget.clear()

        for cmd in COMMANDS:
            if not self._filter_text or (
                self._filter_text in cmd.title.lower()
                or self._filter_text in cmd.id
                or self._filter_text in cmd.description.lower()
            ):
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, cmd)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def append_filter_char(self, ch: str) -> None:
        """Append a character to the filter query and refresh list."""
        self.populate(self._filter_text + ch)

    def backspace_filter(self) -> bool:
        """Remove last character from filter. Returns False if filter was already empty."""
        if not self._filter_text:
            return False
        self.populate(self._filter_text[:-1])
        return True

    def select_next(self) -> None:
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(row + 1)

    def select_previous(self) -> None:
        row = self.list_widget.currentRow()
        if row > 0:
            self.list_widget.setCurrentRow(row - 1)

    def execute_current(self) -> None:
        current_item = self.list_widget.currentItem()
        if current_item is not None:
            cmd = current_item.data(Qt.ItemDataRole.UserRole)
            self.hide()
            self.command_selected.emit(cmd)
        else:
            self.hide()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        self.hide()
        self.command_selected.emit(cmd)
