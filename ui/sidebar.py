"""Sidebar widget displaying folders and navigation categories."""

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FolderSidebar(QWidget):
    """Left sidebar widget displaying folder hierarchy for notes."""

    # Signal emitted when a folder is selected. None represents 'All Notes'.
    folder_selected = pyqtSignal(object)
    # Signal emitted when user requests a new folder
    create_folder_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(6)

        # Header with title and "New Folder" button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 4, 6, 4)

        title_label = QLabel("Folders", parent=self)
        title_label.setStyleSheet("font-weight: 600; color: #888888; font-size: 11px; text-transform: uppercase;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.add_folder_btn = QPushButton("+", parent=self)
        self.add_folder_btn.setObjectName("ActionBtn")
        self.add_folder_btn.setToolTip("Create new folder")
        self.add_folder_btn.setFixedSize(24, 24)
        self.add_folder_btn.clicked.connect(self._on_add_folder_clicked)
        header_layout.addWidget(self.add_folder_btn)

        layout.addLayout(header_layout)

        # Folder List
        self.list_widget = QListWidget(parent=self)
        self.list_widget.setObjectName("SidebarList")
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

    def set_folders(self, folders: List[Path], current_selection: Optional[Path] = None) -> None:
        """Populate the sidebar with 'All Notes' and custom folders."""
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        # Item 0: All Notes (Root)
        all_notes_item = QListWidgetItem("📁  All Notes")
        all_notes_item.setData(Qt.ItemDataRole.UserRole, None)
        self.list_widget.addItem(all_notes_item)

        selected_item = all_notes_item

        for folder in folders:
            item = QListWidgetItem(f"📁  {folder.name}")
            item.setData(Qt.ItemDataRole.UserRole, folder)
            self.list_widget.addItem(item)
            if current_selection is not None and folder == current_selection:
                selected_item = item

        self.list_widget.setCurrentItem(selected_item)
        self.list_widget.blockSignals(False)

    def _on_selection_changed(self) -> None:
        current_item = self.list_widget.currentItem()
        if current_item is not None:
            folder_path = current_item.data(Qt.ItemDataRole.UserRole)
            self.folder_selected.emit(folder_path)

    def _on_add_folder_clicked(self) -> None:
        folder_name, ok = QInputDialog.getText(
            self, "New Folder", "Enter folder name:"
        )
        if ok and folder_name.strip():
            self.create_folder_requested.emit(folder_name.strip())
