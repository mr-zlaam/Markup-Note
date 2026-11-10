"""Main application window with 3-column collapsible splitter layout."""

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QFileSystemWatcher, QTimer, Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QMainWindow, QSplitter, QWidget

from core.note import Note
from core.storage import StorageManager
from ui.dialogs import ModernConfirmDialog
from ui.editor import EditorPanel
from ui.note_list import NoteListPanel
from ui.sidebar import FolderSidebar


class MainWindow(QMainWindow):
    """Main window hosting the Apple Notes 3-pane interface."""

    def __init__(self, storage_manager: Optional[StorageManager] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Note Taker")
        self.resize(1000, 680)

        self.storage = storage_manager if storage_manager is not None else StorageManager()
        self._current_folder: Optional[Path] = None
        self._current_note: Optional[Note] = None
        self._all_current_notes: List[Note] = []
        self._is_saving_internally: bool = False

        # File system watcher for external edits
        self.watcher = QFileSystemWatcher(parent=self)
        self.watcher.directoryChanged.connect(self._on_external_change)

        self._init_ui()
        self._setup_shortcuts()
        self._load_initial_data()

    def _init_ui(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Horizontal, parent=self)
        self.splitter.setChildrenCollapsible(True)

        # 1. Left: Folders Sidebar
        self.sidebar = FolderSidebar(parent=self.splitter)
        self.sidebar.folder_selected.connect(self._on_folder_selected)
        self.sidebar.create_folder_requested.connect(self._on_create_folder)

        # 2. Middle: Note Cards List
        self.note_list = NoteListPanel(parent=self.splitter)
        self.note_list.note_selected.connect(self._on_note_selected)
        self.note_list.create_note_requested.connect(self._on_create_note)
        self.note_list.search_query_changed.connect(self._on_search_filter)

        # 3. Right: Editor Canvas
        self.editor = EditorPanel(parent=self.splitter)
        self.editor.content_saved.connect(self._on_content_saved)
        self.editor.create_note_with_content.connect(self._on_create_note_with_content)
        self.editor.delete_requested.connect(self._on_delete_note)

        # Set initial splitter proportions (180px, 260px, remaining)
        self.splitter.setSizes([190, 280, 530])
        self.setCentralWidget(self.splitter)

    def _setup_shortcuts(self) -> None:
        """Register productivity shortcuts."""
        # New Note (Ctrl+N)
        new_note_sc = QShortcut(QKeySequence("Ctrl+N"), self)
        new_note_sc.activated.connect(self._on_create_note)

        # New Folder (Ctrl+Shift+N)
        new_folder_sc = QShortcut(QKeySequence("Ctrl+Shift+N"), self)
        new_folder_sc.activated.connect(self.sidebar._on_add_folder_clicked)

        # Toggle Folders Sidebar (Ctrl+\)
        toggle_sidebar_sc = QShortcut(QKeySequence("Ctrl+\\"), self)
        toggle_sidebar_sc.activated.connect(self._toggle_sidebar)

        # Focus Search (Ctrl+F)
        search_sc = QShortcut(QKeySequence("Ctrl+F"), self)
        search_sc.activated.connect(self.note_list.search_bar.setFocus)

        # Delete Note (Ctrl+D)
        delete_sc = QShortcut(QKeySequence("Ctrl+D"), self)
        delete_sc.activated.connect(self._on_delete_note)

    def _load_initial_data(self) -> None:
        """Load folders and notes on launch."""
        folders = self.storage.get_folders()
        self.sidebar.set_folders(folders)
        self._update_watcher_paths()
        self._refresh_notes()

        # If no notes exist on launch, auto-create one so user can type immediately
        if not self._all_current_notes:
            self._on_create_note()
        elif self._current_note is not None:
            self.editor.editor.setFocus()

    def _update_watcher_paths(self) -> None:
        """Update watched directories for external modifications."""
        dirs_to_watch = [str(self.storage.root_dir)]
        for f in self.storage.get_folders():
            dirs_to_watch.append(str(f))
        current_watched = self.watcher.directories()
        if current_watched:
            self.watcher.removePaths(current_watched)
        if dirs_to_watch:
            self.watcher.addPaths(dirs_to_watch)

    def _on_external_change(self, path: str) -> None:
        """Handle external changes to notes directory without interrupting active typing."""
        if self._is_saving_internally:
            return
        current_path = str(self._current_note.path) if self._current_note else None
        self._refresh_notes(preserve_path=current_path, emit_selection=False)

    def _clear_saving_flag(self) -> None:
        """Reset internal saving guard flag."""
        self._is_saving_internally = False

    def _refresh_notes(self, preserve_path: Optional[str] = None, emit_selection: bool = True) -> None:
        """Reload notes for the current folder."""
        self._all_current_notes = self.storage.list_notes(self._current_folder)
        query = self.note_list.search_bar.text().strip().lower()

        if query:
            filtered = [
                n for n in self._all_current_notes
                if query in n.title.lower() or query in n.content.lower()
            ]
        else:
            filtered = self._all_current_notes

        self.note_list.set_notes(
            filtered,
            preserve_selection_path=preserve_path,
            emit_selection=emit_selection,
        )

        # If list is empty, clear editor
        if not filtered and emit_selection:
            self._current_note = None
            self.editor.load_note(None)

    def _on_folder_selected(self, folder: Optional[Path]) -> None:
        self._current_folder = folder
        self._refresh_notes()

    def _on_create_folder(self, folder_name: str) -> None:
        new_folder = self.storage.create_folder(folder_name)
        if new_folder is not None:
            folders = self.storage.get_folders()
            self.sidebar.set_folders(folders, current_selection=new_folder)
            self._current_folder = new_folder
            self._update_watcher_paths()
            self._refresh_notes()

    def _on_note_selected(self, note: Note) -> None:
        if self._current_note is not None and self._current_note.path == note.path:
            return
        self._current_note = note
        self.editor.load_note(note)

    def _on_create_note(self) -> None:
        self._is_saving_internally = True
        new_note = self.storage.create_note(folder=self._current_folder)
        if new_note is not None:
            self._current_note = None
            self._refresh_notes(preserve_path=str(new_note.path), emit_selection=True)
            self.editor.editor.setFocus()
        QTimer.singleShot(500, self._clear_saving_flag)

    def _on_create_note_with_content(self, initial_content: str) -> None:
        """Create a new note with typed content when user writes on empty canvas."""
        self._is_saving_internally = True
        title, _ = Note.parse_title_and_snippet(initial_content, fallback_title="New Note")
        new_note = self.storage.create_note(folder=self._current_folder, initial_title=title)
        if new_note is not None:
            self.storage.save_note_content(new_note.path, initial_content)
            self._current_note = Note.from_file(new_note.path)
            if self._current_note is not None:
                self.editor.update_meta(self._current_note)
                self._refresh_notes(preserve_path=str(new_note.path), emit_selection=False)
        QTimer.singleShot(500, self._clear_saving_flag)

    def _on_content_saved(self, new_content: str) -> None:
        if self._current_note is None:
            return

        self._is_saving_internally = True
        current_path = self._current_note.path
        success = self.storage.save_note_content(current_path, new_content)
        if not success:
            self._is_saving_internally = False
            return

        # Update note model
        new_title, new_snippet = Note.parse_title_and_snippet(
            new_content, fallback_title=current_path.stem
        )

        # Rename file if title changed
        renamed_path = self.storage.rename_note_file(current_path, new_title)

        # Update current note instance and card in-place without reloading editor
        self._current_note = Note.from_file(renamed_path)
        if self._current_note is not None:
            self.editor.update_meta(self._current_note)
            self.note_list.update_note_card(str(current_path), self._current_note)
            self._all_current_notes = self.storage.list_notes(self._current_folder)

        QTimer.singleShot(500, self._clear_saving_flag)

    def _on_delete_note(self) -> None:
        if self._current_note is None:
            return

        confirmed = ModernConfirmDialog.ask(
            self,
            title="Delete Note",
            message=f"Are you sure you want to delete '{self._current_note.title}'?",
            confirm_text="Delete",
            is_destructive=True,
        )
        if confirmed:
            self.storage.delete_note(self._current_note.path)
            self._current_note = None
            self._refresh_notes()

    def _on_search_filter(self, query: str) -> None:
        if not query:
            self.note_list.set_notes(self._all_current_notes)
            return

        filtered = [
            n for n in self._all_current_notes
            if query in n.title.lower() or query in n.content.lower()
        ]
        self.note_list.set_notes(filtered)

    def _toggle_sidebar(self) -> None:
        sizes = self.splitter.sizes()
        if sizes[0] > 0:
            # Collapse sidebar
            self._previous_sidebar_width = sizes[0]
            self.splitter.setSizes([0, sizes[1] + sizes[0], sizes[2]])
        else:
            # Restore sidebar
            restore_w = getattr(self, "_previous_sidebar_width", 190)
            self.splitter.setSizes([restore_w, sizes[1] - restore_w, sizes[2]])
