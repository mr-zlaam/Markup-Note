"""Sidebar widget displaying folders, navigation categories, and folder management."""

from pathlib import Path
from typing import List, Optional, Set

from PyQt6.QtCore import QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScroller,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs import ModernInputDialog
from utils.icons import (
    create_check_icon,
    create_done_icon,
    create_plus_icon,
    create_sidebar_toggle_icon,
    create_trash_icon,
    create_uncheck_icon,
)


class FolderSidebar(QWidget):
    """Left sidebar widget displaying folder hierarchy for notes with batch management."""

    # Signal emitted when a folder is selected. None represents 'All Notes'.
    folder_selected = pyqtSignal(object)
    # Signal emitted when user requests a new folder
    create_folder_requested = pyqtSignal(str)
    # Signal emitted when user clicks the sidebar collapse button
    collapse_requested = pyqtSignal()
    # Folder management signals
    rename_folder_requested = pyqtSignal(object)  # Emits Path
    delete_folder_requested = pyqtSignal(object)  # Emits Path
    delete_folders_batch_requested = pyqtSignal(list)  # Emits List[Path]
    select_all_notes_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._folders: List[Path] = []
        self._is_selection_mode: bool = False
        self._selected_folders: Set[Path] = set()
        self._init_ui()

    @property
    def is_selection_mode(self) -> bool:
        return self._is_selection_mode

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(6)

        # Header Stack: Normal header vs. Batch selection header
        self.header_stack = QStackedWidget(parent=self)
        self.header_stack.setFixedHeight(34)

        # 1. Normal Header with title, "New Folder" (+) button, and sidebar collapse button
        normal_header_widget = QWidget(parent=self.header_stack)
        header_layout = QHBoxLayout(normal_header_widget)
        header_layout.setContentsMargins(10, 4, 6, 4)
        header_layout.setSpacing(4)

        title_label = QLabel("Folders", parent=normal_header_widget)
        title_label.setStyleSheet("font-weight: 600; color: #888888; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Clean vector + icon for new folder
        self.add_folder_btn = QPushButton(parent=normal_header_widget)
        self.add_folder_btn.setObjectName("IconButton")
        self.add_folder_btn.setIcon(create_plus_icon("#8e8e93", size=14))
        self.add_folder_btn.setToolTip("New Folder (Ctrl+Shift+N)")
        self.add_folder_btn.setFixedSize(26, 26)
        self.add_folder_btn.clicked.connect(self._on_add_folder_clicked)
        header_layout.addWidget(self.add_folder_btn)

        # Domain-owned collapse button for Folders
        self.collapse_btn = QPushButton(parent=normal_header_widget)
        self.collapse_btn.setObjectName("IconButton")
        self.collapse_btn.setIcon(create_sidebar_toggle_icon("#8e8e93", size=15))
        self.collapse_btn.setToolTip("Collapse Folders (Ctrl+\\)")
        self.collapse_btn.setFixedSize(26, 26)
        self.collapse_btn.clicked.connect(self.collapse_requested.emit)
        header_layout.addWidget(self.collapse_btn)

        self.header_stack.addWidget(normal_header_widget)

        # 2. Batch Header for Folders
        batch_header_widget = QWidget(parent=self.header_stack)
        batch_layout = QHBoxLayout(batch_header_widget)
        batch_layout.setContentsMargins(10, 2, 6, 2)
        batch_layout.setSpacing(6)

        self.select_count_label = QLabel("0 selected", parent=batch_header_widget)
        self.select_count_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #a8a8b0;")
        batch_layout.addWidget(self.select_count_label)

        batch_layout.addStretch()

        # Vector trash icon button for batch delete
        self.batch_delete_btn = QPushButton(parent=batch_header_widget)
        self.batch_delete_btn.setObjectName("IconButton")
        self.batch_delete_btn.setIcon(create_trash_icon("#e03e3e", size=15))
        self.batch_delete_btn.setFixedSize(26, 26)
        self.batch_delete_btn.setToolTip("Delete selected folders")
        self.batch_delete_btn.setEnabled(False)
        self.batch_delete_btn.clicked.connect(self._on_batch_delete_clicked)
        batch_layout.addWidget(self.batch_delete_btn)

        # Vector checkmark icon button for done
        self.done_btn = QPushButton(parent=batch_header_widget)
        self.done_btn.setObjectName("IconButton")
        self.done_btn.setIcon(create_done_icon("#0a84ff", size=16))
        self.done_btn.setFixedSize(26, 26)
        self.done_btn.setToolTip("Done selecting")
        self.done_btn.clicked.connect(self.exit_selection_mode)
        batch_layout.addWidget(self.done_btn)

        self.header_stack.addWidget(batch_header_widget)
        layout.addWidget(self.header_stack, 0)

        # Folder List
        self.list_widget = QListWidget(parent=self)
        self.list_widget.setObjectName("SidebarList")
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        QScroller.grabGesture(self.list_widget.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self.list_widget, 1)

    def enter_selection_mode(self, initial_folder: Optional[Path] = None) -> None:
        """Enter folder selection mode."""
        self._is_selection_mode = True
        self._selected_folders = {initial_folder} if initial_folder else set()
        self.header_stack.setCurrentIndex(1)
        self._update_folder_items()
        self._update_batch_bar()

    def exit_selection_mode(self) -> None:
        """Exit folder selection mode and return to normal view."""
        self._is_selection_mode = False
        self._selected_folders.clear()
        self.header_stack.setCurrentIndex(0)
        self._update_folder_items()

    def _update_batch_bar(self) -> None:
        """Update counter and button states in folder selection header."""
        count = len(self._selected_folders)
        self.select_count_label.setText(f"{count} selected")
        self.batch_delete_btn.setEnabled(count > 0)
        self.batch_delete_btn.setText(f"Delete ({count})" if count > 0 else "Delete")

    def _on_batch_delete_clicked(self) -> None:
        """Emit batch delete signal for selected folders."""
        if self._selected_folders:
            self.delete_folders_batch_requested.emit(list(self._selected_folders))

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Toggle folder selection if in selection mode."""
        if not self._is_selection_mode:
            return
        folder = item.data(Qt.ItemDataRole.UserRole)
        if folder is None:
            # 'All Notes' cannot be selected for folder deletion
            return
        if folder in self._selected_folders:
            self._selected_folders.remove(folder)
        else:
            self._selected_folders.add(folder)
        self._update_folder_items()
        self._update_batch_bar()

    def _on_context_menu(self, pos: QPoint) -> None:
        """Display sleek context menu for folder."""
        item = self.list_widget.itemAt(pos)
        if item is None:
            return

        folder: Optional[Path] = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        if folder is not None:
            # Custom Folder
            rename_act = menu.addAction("Rename Folder...")
            select_act = menu.addAction("Select...")
            menu.addSeparator()
            delete_act = menu.addAction("Delete Folder")

            action = menu.exec(self.list_widget.viewport().mapToGlobal(pos))
            if action == rename_act:
                self.rename_folder_requested.emit(folder)
            elif action == select_act:
                self.enter_selection_mode(initial_folder=folder)
            elif action == delete_act:
                self.delete_folder_requested.emit(folder)
        else:
            # 'All Notes'
            select_act = menu.addAction("Select Notes...")
            action = menu.exec(self.list_widget.viewport().mapToGlobal(pos))
            if action == select_act:
                self.select_all_notes_requested.emit()

    def set_folders(self, folders: List[Path], current_selection: Optional[Path] = None) -> None:
        """Populate the sidebar with 'All Notes' and custom folders."""
        self._folders = folders
        self._update_folder_items(current_selection)

    def _update_folder_items(self, current_selection: Optional[Path] = None) -> None:
        """Render folder items with selection icons if in selection mode."""
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        # Item 0: All Notes (Root)
        all_notes_item = QListWidgetItem("All Notes")
        all_notes_item.setData(Qt.ItemDataRole.UserRole, None)
        self.list_widget.addItem(all_notes_item)

        selected_item = all_notes_item

        for folder in self._folders:
            item = QListWidgetItem(folder.name)
            item.setData(Qt.ItemDataRole.UserRole, folder)

            if self._is_selection_mode:
                if folder in self._selected_folders:
                    item.setIcon(create_check_icon(size=14))
                else:
                    item.setIcon(create_uncheck_icon(size=14))

            self.list_widget.addItem(item)
            if current_selection is not None and folder == current_selection:
                selected_item = item

        if not self._is_selection_mode:
            self.list_widget.setCurrentItem(selected_item)

        self.list_widget.blockSignals(False)

    def _on_selection_changed(self) -> None:
        if self._is_selection_mode:
            return
        current_item = self.list_widget.currentItem()
        if current_item is not None:
            folder_path = current_item.data(Qt.ItemDataRole.UserRole)
            self.folder_selected.emit(folder_path)

    def _on_add_folder_clicked(self) -> None:
        folder_name, ok = ModernInputDialog.get_text(
            self, "New Folder", "Enter folder name:"
        )
        if ok and folder_name.strip():
            self.create_folder_requested.emit(folder_name.strip())
