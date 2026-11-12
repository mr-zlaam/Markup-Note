"""Note list widget displaying note cards with title, timestamp, and snippet."""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from PyQt6.QtCore import QModelIndex, QPoint, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScroller,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from core.note import Note
from ui.dialogs import ModernColorDialog
from utils.icons import (
    PRESET_COLORS,
    create_check_icon,
    create_close_icon,
    create_color_circle_icon,
    create_markdown_icon,
    create_notes_toggle_icon,
    create_plus_icon,
    create_search_icon,
    create_sidebar_toggle_icon,
    create_trash_icon,
    create_uncheck_icon,
)


class NoteCardDelegate(QStyledItemDelegate):
    """Custom item delegate for painting Apple Notes-style cards with batch selection support."""

    def __init__(self, panel: "NoteListPanel") -> None:
        super().__init__(panel)
        self.panel = panel

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

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected) and not self.panel.is_selection_mode
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

        # Text left margin (indented when selection circle is visible)
        text_left_offset = 10

        # Draw Selection Checkbox Circle when in selection mode
        if self.panel.is_selection_mode:
            text_left_offset = 36
            is_checked = str(note.path) in self.panel.selected_paths
            circle_y = rect.top() + (rect.height() - 18) // 2
            circle_rect = QRectF(float(rect.left() + 8), float(circle_y), 18.0, 18.0)

            if is_checked:
                # Filled circle with checkmark
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#0a84ff"))
                painter.drawEllipse(circle_rect)

                check_pen = QPen(QColor("#ffffff"), 1.8)
                check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(check_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)

                check_path = QPainterPath()
                cx = circle_rect.left()
                cy = circle_rect.top()
                check_path.moveTo(cx + 4.5, cy + 9.5)
                check_path.lineTo(cx + 7.5, cy + 13.0)
                check_path.lineTo(cx + 13.5, cy + 5.5)
                painter.drawPath(check_path)
            else:
                # Unchecked empty circle
                uncheck_pen = QPen(QColor("#5c5c64"), 1.6)
                painter.setPen(uncheck_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(circle_rect)

        # 1. Draw Title with vector Markdown icon
        title_font = QFont(option.font)
        title_font.setPointSize(10)
        title_font.setBold(False)
        painter.setFont(title_font)
        painter.setPen(QColor("#ffffff" if is_selected else "#ececec"))

        # Vector Markdown emblem
        md_color = self.panel.get_note_color(str(note.path)) or "#8e8e93"
        md_icon = create_markdown_icon(color=md_color, size=14)
        md_x = rect.left() + text_left_offset
        md_y = rect.top() + 11
        md_icon.paint(painter, md_x, md_y, 16, 14)

        title_left = md_x + 20
        metrics = QFontMetrics(title_font)
        avail_title_w = rect.width() - (title_left - rect.left()) - 10
        elided_title = metrics.elidedText(note.title, Qt.TextElideMode.ElideRight, avail_title_w)
        title_rect = QRect(title_left, rect.top() + 8, avail_title_w, 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)

        # 2. Draw Timestamp & Snippet line
        meta_font = QFont(option.font)
        meta_font.setPointSize(9)
        painter.setFont(meta_font)

        time_text = note.formatted_time
        time_metrics = QFontMetrics(meta_font)
        time_width = time_metrics.horizontalAdvance(time_text)

        painter.setPen(QColor("#9e9e9e"))
        time_rect = QRect(rect.left() + text_left_offset, rect.top() + 32, time_width, 18)
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
    """Middle panel displaying search bar, note cards, batch selection, and right-click actions."""

    note_selected = pyqtSignal(object)  # Emits Note instance
    create_note_requested = pyqtSignal()
    search_query_changed = pyqtSignal(str)
    toggle_folders_requested = pyqtSignal()
    collapse_notes_requested = pyqtSignal()
    rename_note_requested = pyqtSignal(object)  # Emits Note instance
    delete_note_requested = pyqtSignal(object)  # Emits Note instance
    delete_notes_batch_requested = pyqtSignal(list)  # Emits List[Note]
    selection_mode_changed = pyqtSignal(bool)
    note_color_changed = pyqtSignal(object, object)  # Emits (Note, hex_color_or_None)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._notes: List[Note] = []
        self._is_selection_mode: bool = False
        self._selected_paths: Set[str] = set()
        self._note_colors: Dict[str, str] = {}
        self._init_ui()

    def set_note_colors(self, colors: Dict[str, str]) -> None:
        """Update cached note colors and repaint note cards."""
        self._note_colors = dict(colors)
        self.list_widget.viewport().update()

    def get_note_color(self, note_path_str: str) -> Optional[str]:
        """Get custom color for note path, or None if default."""
        return self._note_colors.get(note_path_str)

    @property
    def is_selection_mode(self) -> bool:
        return self._is_selection_mode

    @property
    def selected_paths(self) -> Set[str]:
        return self._selected_paths

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        # Header Stack: switches between normal top bar and batch selection bar
        self.header_stack = QStackedWidget(parent=self)
        self.header_stack.setFixedHeight(36)

        # 1. Normal Top Bar: Toggle Folders, Search Bar, New Note, Collapse Notes
        normal_bar_widget = QWidget(parent=self.header_stack)
        top_bar = QHBoxLayout(normal_bar_widget)
        top_bar.setContentsMargins(4, 0, 4, 0)
        top_bar.setSpacing(6)

        # Toggle Folders button (shown when folders is collapsed or to toggle folders)
        self.toggle_folders_btn = QPushButton(parent=normal_bar_widget)
        self.toggle_folders_btn.setObjectName("IconButton")
        self.toggle_folders_btn.setIcon(create_sidebar_toggle_icon("#8e8e93", size=15))
        self.toggle_folders_btn.setToolTip("Toggle Folders (Ctrl+\\)")
        self.toggle_folders_btn.setFixedSize(26, 26)
        self.toggle_folders_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_folders_btn.clicked.connect(self.toggle_folders_requested.emit)
        top_bar.addWidget(self.toggle_folders_btn)

        # Search Bar with embedded vector magnifying glass icon
        self.search_bar = QLineEdit(parent=normal_bar_widget)
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("Search notes...")
        self.search_bar.addAction(
            create_search_icon("#7a7a80", size=14),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_bar.textChanged.connect(self._on_search_text_changed)
        top_bar.addWidget(self.search_bar)

        # New Note Button with vector plus icon
        self.new_note_btn = QPushButton(" Note", parent=normal_bar_widget)
        self.new_note_btn.setObjectName("ActionBtn")
        self.new_note_btn.setIcon(create_plus_icon("#ffffff", size=12))
        self.new_note_btn.setToolTip("Create new note (Ctrl+N)")
        self.new_note_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_note_btn.clicked.connect(self.create_note_requested.emit)
        top_bar.addWidget(self.new_note_btn)

        # Collapse Notes list button
        self.collapse_notes_btn = QPushButton(parent=normal_bar_widget)
        self.collapse_notes_btn.setObjectName("IconButton")
        self.collapse_notes_btn.setIcon(create_notes_toggle_icon("#8e8e93", size=15))
        self.collapse_notes_btn.setToolTip("Collapse Notes List")
        self.collapse_notes_btn.setFixedSize(26, 26)
        self.collapse_notes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_notes_btn.clicked.connect(self.collapse_notes_requested.emit)
        top_bar.addWidget(self.collapse_notes_btn)

        self.header_stack.addWidget(normal_bar_widget)

        # 2. Batch Selection Bar
        batch_bar_widget = QWidget(parent=self.header_stack)
        batch_layout = QHBoxLayout(batch_bar_widget)
        batch_layout.setContentsMargins(6, 2, 6, 2)
        batch_layout.setSpacing(8)

        self.select_count_label = QLabel("0 selected", parent=batch_bar_widget)
        self.select_count_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #a8a8b0;")
        batch_layout.addWidget(self.select_count_label)

        self.select_all_btn = QPushButton("Select All", parent=batch_bar_widget)
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c30;
                color: #e0e0e0;
                font-size: 12px;
                font-weight: 500;
                border: 1px solid #3c3c44;
                border-radius: 5px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #383840;
                color: #ffffff;
            }
        """)
        self.select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_all_btn.clicked.connect(self._on_toggle_select_all)
        batch_layout.addWidget(self.select_all_btn)

        batch_layout.addStretch()

        # Vector trash icon button for batch delete (no text)
        self.batch_delete_btn = QPushButton(parent=batch_bar_widget)
        self.batch_delete_btn.setObjectName("IconButton")
        self.batch_delete_btn.setIcon(create_trash_icon("#e03e3e", size=16))
        self.batch_delete_btn.setFixedSize(28, 28)
        self.batch_delete_btn.setToolTip("Delete selected notes")
        self.batch_delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_delete_btn.setEnabled(False)
        self.batch_delete_btn.clicked.connect(self._on_batch_delete_clicked)
        batch_layout.addWidget(self.batch_delete_btn)

        # Vector cross icon button for cancel (no text)
        self.cancel_btn = QPushButton(parent=batch_bar_widget)
        self.cancel_btn.setObjectName("IconButton")
        self.cancel_btn.setIcon(create_close_icon("#8e8e93", size=15))
        self.cancel_btn.setFixedSize(28, 28)
        self.cancel_btn.setToolTip("Cancel selection (Esc)")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.exit_selection_mode)
        batch_layout.addWidget(self.cancel_btn)

        self.header_stack.addWidget(batch_bar_widget)
        layout.addWidget(self.header_stack, 0)

        # 3. Note Cards List
        self.list_widget = QListWidget(parent=self)
        self.list_widget.setObjectName("NoteCardsList")
        self.list_widget.setItemDelegate(NoteCardDelegate(self))
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        QScroller.grabGesture(self.list_widget.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self.list_widget, 1)

    def enter_selection_mode(self, initial_note_path: Optional[str] = None) -> None:
        """Enter multi-note selection mode."""
        self._is_selection_mode = True
        self._selected_paths = {initial_note_path} if initial_note_path else set()
        self.header_stack.setCurrentIndex(1)
        self._update_batch_bar()
        self.list_widget.viewport().update()
        self.selection_mode_changed.emit(True)

    def exit_selection_mode(self) -> None:
        """Exit multi-note selection mode and return to normal view."""
        self._is_selection_mode = False
        self._selected_paths.clear()
        self.header_stack.setCurrentIndex(0)
        self.list_widget.viewport().update()
        self.selection_mode_changed.emit(False)

    def toggle_note_selection(self, note_path_str: str) -> None:
        """Toggle a single note's checked status in selection mode."""
        if note_path_str in self._selected_paths:
            self._selected_paths.remove(note_path_str)
        else:
            self._selected_paths.add(note_path_str)
        self._update_batch_bar()
        self.list_widget.viewport().update()

    def _on_toggle_select_all(self) -> None:
        """Select all or deselect all notes in current list."""
        if len(self._selected_paths) == len(self._notes) and len(self._notes) > 0:
            self._selected_paths.clear()
        else:
            self._selected_paths = {str(n.path) for n in self._notes}
        self._update_batch_bar()
        self.list_widget.viewport().update()

    def _update_batch_bar(self) -> None:
        """Update counter and button states in batch selection header."""
        count = len(self._selected_paths)
        self.select_count_label.setText(f"{count} selected")
        self.batch_delete_btn.setEnabled(count > 0)
        self.batch_delete_btn.setToolTip(f"Delete {count} selected notes" if count > 0 else "Delete selected notes")
        if count > 0 and count == len(self._notes):
            self.select_all_btn.setText("Deselect All")
        else:
            self.select_all_btn.setText("Select All")

    def _on_batch_delete_clicked(self) -> None:
        """Emit batch delete signal for all checked notes."""
        selected_notes = [n for n in self._notes if str(n.path) in self._selected_paths]
        if selected_notes:
            self.delete_notes_batch_requested.emit(selected_notes)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle clicks on note cards."""
        if self._is_selection_mode:
            note = item.data(Qt.ItemDataRole.UserRole)
            if note is not None:
                self.toggle_note_selection(str(note.path))

    def keyPressEvent(self, event) -> None:
        """Handle Escape key to cancel selection mode."""
        if self._is_selection_mode and event.key() == Qt.Key.Key_Escape:
            self.exit_selection_mode()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_context_menu(self, pos: QPoint) -> None:
        """Display sleek context menu for note card."""
        item = self.list_widget.itemAt(pos)
        if item is None:
            return

        note: Optional[Note] = item.data(Qt.ItemDataRole.UserRole)
        if note is None:
            return

        menu = QMenu(self)

        if not self._is_selection_mode:
            rename_act = menu.addAction("Rename Note...")
            select_act = menu.addAction("Select...")

            # Color options submenu
            color_menu = menu.addMenu("Color")
            self._populate_color_menu(color_menu, note)

            menu.addSeparator()
            delete_act = menu.addAction("Delete Note")

            action = menu.exec(self.list_widget.viewport().mapToGlobal(pos))
            if action == rename_act:
                self.rename_note_requested.emit(note)
            elif action == select_act:
                self.enter_selection_mode(initial_note_path=str(note.path))
            elif action == delete_act:
                self.delete_note_requested.emit(note)
        else:
            select_all_act = menu.addAction("Select All")
            deselect_all_act = menu.addAction("Clear Selection")
            menu.addSeparator()
            delete_batch_act = menu.addAction(f"Delete Selected ({len(self._selected_paths)})")
            done_act = menu.addAction("Done")

            action = menu.exec(self.list_widget.viewport().mapToGlobal(pos))
            if action == select_all_act:
                self._selected_paths = {str(n.path) for n in self._notes}
                self._update_batch_bar()
                self.list_widget.viewport().update()
            elif action == deselect_all_act:
                self._selected_paths.clear()
                self._update_batch_bar()
                self.list_widget.viewport().update()
            elif action == delete_batch_act and self._selected_paths:
                self._on_batch_delete_clicked()
            elif action == done_act:
                self.exit_selection_mode()

    def _populate_color_menu(self, color_menu: QMenu, note: Note) -> None:
        """Populate the color submenu for a note."""
        for name, hex_code in PRESET_COLORS:
            icon = create_color_circle_icon(hex_code, size=12)
            act = color_menu.addAction(icon, name)
            act.triggered.connect(
                lambda checked=False, n=note, col=hex_code: self._apply_note_color(n, col)
            )

        color_menu.addSeparator()
        custom_act = color_menu.addAction("Custom Color...")
        custom_act.triggered.connect(
            lambda checked=False, n=note: self._pick_custom_note_color(n)
        )

    def _apply_note_color(self, note: Note, color: Optional[str]) -> None:
        """Apply color to note and emit signal."""
        path_str = str(note.path)
        if color:
            self._note_colors[path_str] = color
        else:
            self._note_colors.pop(path_str, None)
        self.list_widget.viewport().update()
        self.note_color_changed.emit(note, color)

    def _pick_custom_note_color(self, note: Note) -> None:
        """Open modern color dialog for custom note color."""
        path_str = str(note.path)
        initial = QColor(self._note_colors.get(path_str, "#8e8e93"))
        color = ModernColorDialog.get_color(initial, self, f"Choose Color for '{note.title}'")
        if color.isValid():
            self._apply_note_color(note, color.name())

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
        elif self.list_widget.count() > 0 and not self._is_selection_mode:
            self.list_widget.setCurrentRow(0)

        self.list_widget.blockSignals(False)

        if self._is_selection_mode:
            # Prune deleted notes from selection
            existing_paths = {str(n.path) for n in self._notes}
            self._selected_paths = self._selected_paths.intersection(existing_paths)
            self._update_batch_bar()

        # Trigger selection for currently selected row if requested
        if emit_selection and not self._is_selection_mode and self.list_widget.currentItem() is not None:
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
        if self._is_selection_mode:
            return
        note = self.get_selected_note()
        if note is not None:
            self.note_selected.emit(note)

    def _on_search_text_changed(self, text: str) -> None:
        self.search_query_changed.emit(text.strip().lower())
