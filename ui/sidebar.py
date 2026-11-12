"""Sidebar widget displaying folders tree hierarchy, navigation categories, and folder management."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set

from PyQt6.QtCore import QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScroller,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs import ModernColorDialog, ModernInputDialog
from utils.icons import (
    PRESET_COLORS,
    create_all_notes_icon,
    create_check_icon,
    create_close_icon,
    create_color_circle_icon,
    create_folder_icon,
    create_plus_icon,
    create_sidebar_toggle_icon,
    create_trash_icon,
    create_uncheck_icon,
)


class FolderSidebar(QWidget):
    """Left sidebar widget displaying folder hierarchy tree for notes with subfolder creation."""

    # Signal emitted when a folder is selected. None represents 'All Notes'.
    folder_selected = pyqtSignal(object)
    # Signal emitted when user requests a new folder or subfolder: (folder_name, parent_folder_or_None)
    create_folder_requested = pyqtSignal(str, object)
    # Signal emitted when user clicks the sidebar collapse button
    collapse_requested = pyqtSignal()
    # Folder management signals
    rename_folder_requested = pyqtSignal(object)  # Emits Path
    delete_folder_requested = pyqtSignal(object)  # Emits Path
    delete_folders_batch_requested = pyqtSignal(list)  # Emits List[Path]
    select_all_notes_requested = pyqtSignal()
    folder_color_changed = pyqtSignal(str, object)  # Emits (folder_name, hex_color_or_None)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._folders: List[Path] = []
        self._is_selection_mode: bool = False
        self._selected_folders: Set[Path] = set()
        self._folder_colors: Dict[str, str] = {}
        self._init_ui()

    def set_folder_colors(self, colors: Dict[str, str]) -> None:
        """Update cached folder colors and refresh UI."""
        self._folder_colors = dict(colors)
        self._update_folder_items()

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
        title_label.setStyleSheet(
            "font-weight: 600; color: #888888; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;"
        )
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
        batch_layout.setContentsMargins(6, 2, 4, 2)
        batch_layout.setSpacing(4)

        self.select_count_label = QLabel("0 selected", parent=batch_header_widget)
        self.select_count_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #a8a8b0;")
        batch_layout.addWidget(self.select_count_label)

        self.select_all_btn = QPushButton("Select All", parent=batch_header_widget)
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c30;
                color: #e0e0e0;
                font-size: 10px;
                font-weight: 500;
                border: 1px solid #3c3c44;
                border-radius: 4px;
                padding: 2px 5px;
            }
            QPushButton:hover {
                background-color: #383840;
                color: #ffffff;
            }
        """)
        self.select_all_btn.setToolTip("Select or deselect all folders")
        self.select_all_btn.clicked.connect(self._on_toggle_select_all)
        batch_layout.addWidget(self.select_all_btn)

        batch_layout.addStretch()

        # Vector trash icon button for batch delete
        self.batch_delete_btn = QPushButton(parent=batch_header_widget)
        self.batch_delete_btn.setObjectName("IconButton")
        self.batch_delete_btn.setIcon(create_trash_icon("#e03e3e", size=15))
        self.batch_delete_btn.setFixedSize(24, 24)
        self.batch_delete_btn.setToolTip("Delete selected folders")
        self.batch_delete_btn.setEnabled(False)
        self.batch_delete_btn.clicked.connect(self._on_batch_delete_clicked)
        batch_layout.addWidget(self.batch_delete_btn)

        # Vector close/cross icon button for cancel
        self.cancel_btn = QPushButton(parent=batch_header_widget)
        self.cancel_btn.setObjectName("IconButton")
        self.cancel_btn.setIcon(create_close_icon("#8e8e93", size=15))
        self.cancel_btn.setFixedSize(24, 24)
        self.cancel_btn.setToolTip("Cancel selection (Esc)")
        self.cancel_btn.clicked.connect(self.exit_selection_mode)
        batch_layout.addWidget(self.cancel_btn)

        self.header_stack.addWidget(batch_header_widget)
        layout.addWidget(self.header_stack, 0)

        # Folder Tree Widget
        self.tree_widget = QTreeWidget(parent=self)
        self.tree_widget.setObjectName("SidebarTree")
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(16)
        self.tree_widget.setAnimated(True)
        self.tree_widget.setIconSize(QSize(18, 18))
        self.tree_widget.setVerticalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        self.tree_widget.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        QScroller.grabGesture(
            self.tree_widget.viewport(), QScroller.ScrollerGestureType.TouchGesture
        )

        self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree_widget.itemClicked.connect(self._on_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self.tree_widget, 1)

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
        self.batch_delete_btn.setToolTip(
            f"Delete {count} selected folder{'s' if count != 1 else ''}"
            if count > 0
            else "Delete selected folders"
        )
        if count == len(self._folders) and len(self._folders) > 0:
            self.select_all_btn.setText("Deselect All")
        else:
            self.select_all_btn.setText("Select All")

    def _on_toggle_select_all(self) -> None:
        """Toggle selecting all custom folders."""
        if len(self._selected_folders) == len(self._folders) and len(self._folders) > 0:
            self._selected_folders.clear()
        else:
            self._selected_folders = set(self._folders)
        self._update_folder_items()
        self._update_batch_bar()

    def keyPressEvent(self, event) -> None:
        """Handle Escape key to cancel selection mode."""
        if self._is_selection_mode and event.key() == Qt.Key.Key_Escape:
            self.exit_selection_mode()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_batch_delete_clicked(self) -> None:
        """Emit batch delete signal for selected folders."""
        if self._selected_folders:
            self.delete_folders_batch_requested.emit(list(self._selected_folders))

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int = 0) -> None:
        """Toggle folder selection if in selection mode."""
        if not self._is_selection_mode:
            return
        folder = item.data(0, Qt.ItemDataRole.UserRole)
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
        item = self.tree_widget.itemAt(pos)
        if item is None:
            return

        folder: Optional[Path] = item.data(0, Qt.ItemDataRole.UserRole)
        folder_name = folder.name if folder is not None else "All Notes"
        menu = QMenu(self)

        if folder is not None:
            # Custom Folder or Subfolder
            new_subfolder_act = menu.addAction("New Subfolder...")
            rename_act = menu.addAction("Rename Folder...")
            select_act = menu.addAction("Select...")

            # Color options submenu
            color_menu = menu.addMenu("Color")
            self._populate_color_menu(color_menu, folder_name)

            menu.addSeparator()
            delete_act = menu.addAction("Delete Folder")

            action = menu.exec(self.tree_widget.viewport().mapToGlobal(pos))
            if action == new_subfolder_act:
                subfolder_name, ok = ModernInputDialog.get_text(
                    self, "New Subfolder", f"Create subfolder inside '{folder.name}':"
                )
                if ok and subfolder_name.strip():
                    self.create_folder_requested.emit(subfolder_name.strip(), folder)
            elif action == rename_act:
                self.rename_folder_requested.emit(folder)
            elif action == select_act:
                self.enter_selection_mode(initial_folder=folder)
            elif action == delete_act:
                self.delete_folder_requested.emit(folder)
        else:
            # 'All Notes'
            new_folder_act = menu.addAction("New Folder...")
            select_act = menu.addAction("Select Notes...")

            color_menu = menu.addMenu("Color")
            self._populate_color_menu(color_menu, folder_name)

            action = menu.exec(self.tree_widget.viewport().mapToGlobal(pos))
            if action == new_folder_act:
                self._on_add_folder_clicked()
            elif action == select_act:
                self.select_all_notes_requested.emit()

    def _populate_color_menu(self, color_menu: QMenu, folder_name: str) -> None:
        """Populate the color submenu with color presets and custom color picker."""
        for name, hex_code in PRESET_COLORS:
            icon = create_color_circle_icon(hex_code, size=12)
            act = color_menu.addAction(icon, name)
            act.triggered.connect(
                lambda checked=False, fn=folder_name, col=hex_code: self._apply_folder_color(fn, col)
            )

        color_menu.addSeparator()
        custom_act = color_menu.addAction("Custom Color...")
        custom_act.triggered.connect(
            lambda checked=False, fn=folder_name: self._pick_custom_folder_color(fn)
        )

    def _apply_folder_color(self, folder_name: str, color: Optional[str]) -> None:
        """Apply color to folder and emit change signal."""
        if color:
            self._folder_colors[folder_name] = color
        else:
            self._folder_colors.pop(folder_name, None)
        self._update_folder_items()
        self.folder_color_changed.emit(folder_name, color)

    def _pick_custom_folder_color(self, folder_name: str) -> None:
        """Open modern color dialog for custom color selection."""
        fallback = "#0a84ff" if folder_name == "All Notes" else "#e5a93c"
        initial = QColor(self._folder_colors.get(folder_name, fallback))
        color = ModernColorDialog.get_color(initial, self, f"Choose Color for {folder_name}")
        if color.isValid():
            self._apply_folder_color(folder_name, color.name())

    def set_folders(self, folders: List[Path], current_selection: Optional[Path] = None) -> None:
        """Populate the sidebar with 'All Notes' and custom folders tree."""
        self._folders = folders
        self._update_folder_items(current_selection)

    def _update_folder_items(self, current_selection: Optional[Path] = None) -> None:
        """Render folder items in hierarchical tree with expansion and selection icons."""
        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()

        # Item 0: All Notes (Pinned Root)
        all_notes_item = QTreeWidgetItem(["All Notes"])
        all_notes_item.setData(0, Qt.ItemDataRole.UserRole, None)
        all_notes_color = self._folder_colors.get("All Notes") or "#0a84ff"
        all_notes_item.setIcon(0, create_all_notes_icon(color=all_notes_color, size=16))
        self.tree_widget.addTopLevelItem(all_notes_item)

        selected_item = all_notes_item

        # Map Path -> QTreeWidgetItem to parent subfolders cleanly
        item_map: Dict[Path, QTreeWidgetItem] = {}

        # Sort folders so parent directories always appear before their children
        sorted_folders = sorted(self._folders, key=lambda p: (len(p.parts), str(p)))

        for folder in sorted_folders:
            item = QTreeWidgetItem([folder.name])
            item.setData(0, Qt.ItemDataRole.UserRole, folder)

            if self._is_selection_mode:
                if folder in self._selected_folders:
                    item.setIcon(0, create_check_icon(size=14))
                else:
                    item.setIcon(0, create_uncheck_icon(size=14))
            else:
                folder_color = self._folder_colors.get(folder.name) or "#e5a93c"
                item.setIcon(0, create_folder_icon(color=folder_color, size=16))

            parent_path = folder.parent
            if parent_path in item_map:
                item_map[parent_path].addChild(item)
                item_map[parent_path].setExpanded(True)
            else:
                self.tree_widget.addTopLevelItem(item)

            item_map[folder] = item

            if current_selection is not None and folder == current_selection:
                selected_item = item

        if not self._is_selection_mode:
            self.tree_widget.setCurrentItem(selected_item)

        self.tree_widget.blockSignals(False)

    def _on_selection_changed(self) -> None:
        if self._is_selection_mode:
            return
        current_item = self.tree_widget.currentItem()
        if current_item is not None:
            folder_path = current_item.data(0, Qt.ItemDataRole.UserRole)
            self.folder_selected.emit(folder_path)

    def _on_add_folder_clicked(self) -> None:
        # If currently a folder is selected, ask whether to create inside or at root
        current_item = self.tree_widget.currentItem()
        current_folder = (
            current_item.data(0, Qt.ItemDataRole.UserRole)
            if current_item is not None
            else None
        )

        title = "New Folder"
        prompt = "Enter folder name:"
        if current_folder is not None:
            title = f"New Subfolder inside '{current_folder.name}'"
            prompt = f"Enter subfolder name for '{current_folder.name}':"

        folder_name, ok = ModernInputDialog.get_text(self, title, prompt)
        if ok and folder_name.strip():
            self.create_folder_requested.emit(folder_name.strip(), current_folder)
