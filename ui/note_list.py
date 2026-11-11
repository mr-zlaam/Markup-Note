"""Note list widget displaying note cards with title, timestamp, and snippet."""

from typing import List, Optional

from PyQt6.QtCore import QModelIndex, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScroller,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from core.note import Note
from utils.icons import (
    create_notes_toggle_icon,
    create_plus_icon,
    create_search_icon,
    create_sidebar_toggle_icon,
)


class NoteCardDelegate(QStyledItemDelegate):
    """Custom item delegate for painting Apple Notes-style cards."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), 64)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Retrieve note data
        note: Optional[Note] = index.data(Qt.ItemDataRole.UserRole)
        if note is None:
            painter.restore()
            return

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hover = bool(option.state & QStyle.StateFlag.State_MouseOver)

        rect = option.rect.adjusted(4, 2, -4, -2)

        # Draw card background
        if is_selected:
            painter.setBrush(QColor("#2c2c2e"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
        elif is_hover:
            painter.setBrush(QColor("#252528"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)

        # 1. Draw Title
        title_font = QFont(option.font)
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#ffffff" if is_selected else "#ececec"))

        metrics = QFontMetrics(title_font)
        elided_title = metrics.elidedText(note.title, Qt.TextElideMode.ElideRight, rect.width() - 20)
        title_rect = QRect(rect.left() + 10, rect.top() + 8, rect.width() - 20, 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)

        # 2. Draw Timestamp & Snippet line
        meta_font = QFont(option.font)
        meta_font.setPointSize(9)
        painter.setFont(meta_font)

        # Relative time (e.g., "10:45 AM" or "Yesterday")
        time_text = note.formatted_time
        time_metrics = QFontMetrics(meta_font)
        time_width = time_metrics.horizontalAdvance(time_text)

        painter.setPen(QColor("#9e9e9e"))
        time_rect = QRect(rect.left() + 10, rect.top() + 32, time_width, 18)
        painter.drawText(time_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, time_text)

        # Preview Snippet
        snippet_x = time_rect.right() + 8
        snippet_width = max(0, rect.right() - snippet_x - 10)
        snippet_rect = QRect(snippet_x, rect.top() + 32, snippet_width, 18)

        painter.setPen(QColor("#757575"))
        elided_snippet = time_metrics.elidedText(note.preview_snippet, Qt.TextElideMode.ElideRight, snippet_width)
        painter.drawText(snippet_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_snippet)

        painter.restore()


class NoteListPanel(QWidget):
    """Middle panel displaying search bar, new note button, and note cards."""

    note_selected = pyqtSignal(object)  # Emits Note instance
    create_note_requested = pyqtSignal()
    search_query_changed = pyqtSignal(str)
    toggle_folders_requested = pyqtSignal()
    collapse_notes_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._notes: List[Note] = []
        self._init_ui()

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        # Top Bar: Toggle Folders, Search Bar, New Note, Collapse Notes
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 0)
        top_bar.setSpacing(6)

        # Toggle Folders button (shown when folders is collapsed or to toggle folders)
        self.toggle_folders_btn = QPushButton(parent=self)
        self.toggle_folders_btn.setObjectName("IconButton")
        self.toggle_folders_btn.setIcon(create_sidebar_toggle_icon("#8e8e93", size=15))
        self.toggle_folders_btn.setToolTip("Toggle Folders (Ctrl+\\)")
        self.toggle_folders_btn.setFixedSize(26, 26)
        self.toggle_folders_btn.clicked.connect(self.toggle_folders_requested.emit)
        top_bar.addWidget(self.toggle_folders_btn)

        # Search Bar with embedded vector magnifying glass icon
        self.search_bar = QLineEdit(parent=self)
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("Search notes...")
        self.search_bar.addAction(
            create_search_icon("#7a7a80", size=14),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_bar.textChanged.connect(self._on_search_text_changed)
        top_bar.addWidget(self.search_bar)

        # New Note Button with vector plus icon
        self.new_note_btn = QPushButton(" Note", parent=self)
        self.new_note_btn.setObjectName("ActionBtn")
        self.new_note_btn.setIcon(create_plus_icon("#ffffff", size=12))
        self.new_note_btn.setToolTip("Create new note (Ctrl+N)")
        self.new_note_btn.clicked.connect(self.create_note_requested.emit)
        top_bar.addWidget(self.new_note_btn)

        # Collapse Notes list button
        self.collapse_notes_btn = QPushButton(parent=self)
        self.collapse_notes_btn.setObjectName("IconButton")
        self.collapse_notes_btn.setIcon(create_notes_toggle_icon("#8e8e93", size=15))
        self.collapse_notes_btn.setToolTip("Collapse Notes List")
        self.collapse_notes_btn.setFixedSize(26, 26)
        self.collapse_notes_btn.clicked.connect(self.collapse_notes_requested.emit)
        top_bar.addWidget(self.collapse_notes_btn)

        layout.addLayout(top_bar)

        # Note Cards List
        self.list_widget = QListWidget(parent=self)
        self.list_widget.setObjectName("NoteCardsList")
        self.list_widget.setItemDelegate(NoteCardDelegate(self.list_widget))
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        QScroller.grabGesture(self.list_widget.viewport(), QScroller.ScrollerGestureType.TouchGesture)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

    def set_notes(
        self,
        notes: List[Note],
        preserve_selection_path: Optional[str] = None,
        emit_selection: bool = True,
    ) -> None:
        """Update the list with note items."""
        self._notes = notes
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        selected_item: Optional[QListWidgetItem] = None

        for note in notes:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, note)
            self.list_widget.addItem(item)
            if preserve_selection_path and str(note.path) == preserve_selection_path:
                selected_item = item

        if selected_item is not None:
            self.list_widget.setCurrentItem(selected_item)
        elif self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

        self.list_widget.blockSignals(False)

        # Trigger selection for currently selected row if requested
        if emit_selection and self.list_widget.currentItem() is not None:
            self._on_selection_changed()

    def update_note_card(self, old_path_str: str, updated_note: Note) -> None:
        """Update an existing note card in-place without emitting selection signals."""
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            if item is not None:
                existing: Optional[Note] = item.data(Qt.ItemDataRole.UserRole)
                if existing is not None and str(existing.path) in (old_path_str, str(updated_note.path)):
                    item.setData(Qt.ItemDataRole.UserRole, updated_note)
                    break
        self.list_widget.viewport().update()

    def get_selected_note(self) -> Optional[Note]:
        """Return the currently selected Note, if any."""
        current = self.list_widget.currentItem()
        if current is not None:
            return current.data(Qt.ItemDataRole.UserRole)
        return None

    def _on_selection_changed(self) -> None:
        note = self.get_selected_note()
        if note is not None:
            self.note_selected.emit(note)

    def _on_search_text_changed(self, text: str) -> None:
        self.search_query_changed.emit(text.strip().lower())
