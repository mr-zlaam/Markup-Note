"""Floating slash ('/') command palette for instant markdown block insertion (Notion aesthetic)."""

from dataclasses import dataclass, field
from typing import List, Optional

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
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

from utils.icons import draw_checkbox_badge


@dataclass
class SlashCommand:
    """Represents a selectable markdown command in the slash menu."""

    id: str
    title: str
    description: str
    icon: str
    prefix: str
    keywords: tuple[str, ...] = field(default_factory=tuple)


COMMANDS: List[SlashCommand] = [
    SlashCommand(
        id="checkbox",
        title="Checkbox",
        description="Track tasks with a clickable checkbox",
        icon="[ ]",
        prefix="- [ ] ",
        keywords=("checkbox", "check", "todo", "task", "box"),
    ),
    SlashCommand(
        id="bullet",
        title="Bulleted list",
        description="Create a simple bulleted list",
        icon="•",
        prefix="- ",
        keywords=("bullet", "bulleted", "list", "ul", "point"),
    ),
    SlashCommand(
        id="number",
        title="Numbered list",
        description="Create a list with numbering",
        icon="1.",
        prefix="1. ",
        keywords=("number", "numbered", "ordered", "ol", "count"),
    ),
    SlashCommand(
        id="h1",
        title="Heading 1",
        description="Big section heading",
        icon="H1",
        prefix="# ",
        keywords=("h1", "heading1", "heading", "title", "large"),
    ),
    SlashCommand(
        id="h2",
        title="Heading 2",
        description="Medium section heading",
        icon="H2",
        prefix="## ",
        keywords=("h2", "heading2", "subheading", "subtitle", "medium"),
    ),
    SlashCommand(
        id="h3",
        title="Heading 3",
        description="Small section heading",
        icon="H3",
        prefix="### ",
        keywords=("h3", "heading3", "small"),
    ),
    SlashCommand(
        id="quote",
        title="Quote",
        description="Capture a quote or callout",
        icon="”",
        prefix="> ",
        keywords=("quote", "blockquote", "callout", "cite"),
    ),
    SlashCommand(
        id="divider",
        title="Divider",
        description="Visually divide blocks with a horizontal line",
        icon="—",
        prefix="---\n",
        keywords=("divider", "line", "rule", "hr", "separator"),
    ),
]


class SlashItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering slash menu items with icon badge, title, and description."""

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(option.rect.width(), 46)

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
            painter.setBrush(QColor("#2c2c32"))
            painter.setPen(QPen(QColor("#3a3a40"), 1))
            painter.drawRoundedRect(rect, 6, 6)

        # Icon badge box on left
        badge_rect = QRect(rect.left() + 8, rect.top() + (rect.height() - 28) // 2, 28, 28)
        painter.setBrush(QColor("#28282c" if not is_selected else "#36363c"))
        painter.setPen(QPen(QColor("#38383e"), 1))
        painter.drawRoundedRect(badge_rect, 6, 6)

        # Icon text / symbol
        if cmd.id == "checkbox":
            draw_checkbox_badge(
                painter,
                badge_rect,
                color="#0a84ff" if is_selected else "#0a84ff",
                box_color="#0a84ff" if is_selected else "#8e8e93",
            )
        else:
            icon_font = QFont(option.font)
            icon_font.setPointSize(10)
            icon_font.setBold(False)
            painter.setFont(icon_font)
            painter.setPen(QColor("#0a84ff" if is_selected else "#c8c8cc"))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, cmd.icon)

        # Title
        title_font = QFont(option.font)
        title_font.setPointSize(10)
        title_font.setBold(False)
        painter.setFont(title_font)
        painter.setPen(QColor("#ffffff" if is_selected else "#f0f0f2"))
        title_rect = QRect(rect.left() + 44, rect.top() + 6, rect.width() - 52, 18)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, cmd.title)

        # Description
        desc_font = QFont(option.font)
        desc_font.setPointSize(8)
        painter.setFont(desc_font)
        painter.setPen(QColor("#a0a0a5" if is_selected else "#7a7a7e"))
        desc_rect = QRect(rect.left() + 44, rect.top() + 24, rect.width() - 52, 16)
        painter.drawText(desc_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, cmd.description)

        painter.restore()


class SlashCommandPalette(QFrame):
    """Floating popup menu triggered by typing '/' at cursor position."""

    command_selected = pyqtSignal(object)  # Emits selected SlashCommand

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setObjectName("SlashCommandPalette")
        self.setFixedSize(300, 290)
        self.setStyleSheet("""
            QFrame#SlashCommandPalette {
                background-color: #202022;
                border: 1px solid #333336;
                border-radius: 10px;
            }
            QLabel#FilterHeader {
                color: #8e8e93;
                font-size: 11px;
                font-weight: 500;
                padding: 6px 12px 4px 12px;
                border-bottom: 1px solid #2c2c2e;
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 4px 2px 4px 0px;
            }
            QScrollBar::handle:vertical {
                background: #48484a;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #636366;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                height: 0px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.filter_label = QLabel("Basic blocks", parent=self)
        self.filter_label.setObjectName("FilterHeader")
        layout.addWidget(self.filter_label)

        self.list_widget = QListWidget(parent=self)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setItemDelegate(SlashItemDelegate(self.list_widget))
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        self._filter_text = ""
        self.populate()

    @property
    def filter_text(self) -> str:
        """Return current active filter query."""
        return self._filter_text

    def count(self) -> int:
        """Return the number of visible matching commands."""
        return self.list_widget.count()

    def populate(self, query: str = "") -> None:
        """Filter and populate command items."""
        self._filter_text = query.lower().strip()
        if self._filter_text:
            self.filter_label.setText(f"Filter: {self._filter_text}")
            self.filter_label.setStyleSheet("color: #0a84ff; font-size: 11px; font-weight: 500; padding: 6px 12px 4px 12px; border-bottom: 1px solid #2c2c2e;")
        else:
            self.filter_label.setText("Basic blocks")
            self.filter_label.setStyleSheet("color: #8e8e93; font-size: 11px; font-weight: 500; padding: 6px 12px 4px 12px; border-bottom: 1px solid #2c2c2e;")

        self.list_widget.clear()

        for cmd in COMMANDS:
            if not self._filter_text:
                matches = True
            else:
                matches = (
                    self._filter_text in cmd.title.lower()
                    or self._filter_text in cmd.id
                    or self._filter_text in cmd.description.lower()
                    or any(self._filter_text in kw for kw in cmd.keywords)
                )
            if matches:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, cmd)
                item.setSizeHint(QSize(270, 46))
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def select_next(self) -> None:
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(row + 1)
        elif self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def select_previous(self) -> None:
        row = self.list_widget.currentRow()
        if row > 0:
            self.list_widget.setCurrentRow(row - 1)
        elif self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)

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
