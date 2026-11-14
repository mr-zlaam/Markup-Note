"""Main application window with 3-column collapsible splitter layout."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from PyQt6.QtCore import QEasingCurve, QFileSystemWatcher, QTimer, QVariantAnimation, Qt
from PyQt6.QtGui import QCloseEvent, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplitter, QWidget

from core.config import ConfigManager
from core.note import Note
from core.storage import StorageManager
from ui.backup_panel import BackupPanel
from ui.dialogs import ModernConfirmDialog, ModernInputDialog, ModernMessageDialog
from ui.editor import EditorPanel
from ui.note_list import NoteListPanel
from ui.sidebar import FolderSidebar
from utils.file_validator import validate_markdown_file


class MainWindow(QMainWindow):
    """Main window hosting the Apple Notes 3-pane interface."""

    def __init__(
        self,
        storage_manager: Optional[StorageManager] = None,
        config_manager: Optional[ConfigManager] = None,
        initial_path: Optional[Path] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)
        self._initial_path = initial_path
        self.setWindowTitle("Markup Notes")

        app_icon = QIcon()
        icons_dir = Path(__file__).resolve().parent.parent / "assets" / "icons"
        if icons_dir.exists():
            for size in (16, 24, 32, 48, 64, 128, 256, 512):
                size_path = icons_dir / f"markup-notes-{size}x{size}.png"
                if size_path.exists():
                    app_icon.addFile(str(size_path))
        if app_icon.isNull():
            fallback_icon = Path(__file__).resolve().parent.parent / "assets" / "markup-note.png"
            if fallback_icon.exists():
                app_icon = QIcon(str(fallback_icon))
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        # Load persisted settings from ~/.config/markup-notes/settings.json
        self.config_manager = config_manager if config_manager is not None else ConfigManager()
        self.config = self.config_manager.settings

        self.resize(self.config.window.width, self.config.window.height)
        if self.config.window.maximized:
            self.showMaximized()

        self.storage = storage_manager if storage_manager is not None else StorageManager()
        self._current_folder: Optional[Path] = None
        self._current_note: Optional[Note] = None
        self._all_current_notes: List[Note] = []
        self._is_saving_internally: bool = False
        self._active_pane_anim: Optional[QVariantAnimation] = None

        # File system watcher for external edits
        self.watcher = QFileSystemWatcher(parent=self)
        self.watcher.directoryChanged.connect(self._on_external_change)

        self._init_ui()
        self._setup_shortcuts()
        self._load_initial_data()

    def _init_ui(self) -> None:
        from utils.cursors import install_global_button_cursor_filter

        app = QApplication.instance()
        if app is not None and isinstance(app, QApplication):
            install_global_button_cursor_filter(app)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, parent=self)
        self.splitter.setChildrenCollapsible(True)

        # 1. Left: Folders Sidebar
        self.sidebar = FolderSidebar(parent=self.splitter)
        self.sidebar.folder_selected.connect(self._on_folder_selected)
        self.sidebar.create_folder_requested.connect(self._on_create_folder)
        self.sidebar.collapse_requested.connect(self._toggle_sidebar)
        self.sidebar.rename_folder_requested.connect(self._on_rename_folder)
        self.sidebar.delete_folder_requested.connect(self._on_delete_folder)
        self.sidebar.delete_folders_batch_requested.connect(self._on_delete_folders_batch)
        self.sidebar.select_all_notes_requested.connect(self._on_select_all_notes_requested)
        self.sidebar.folder_color_changed.connect(self._on_folder_color_changed)

        # 2. Middle: Note Cards List
        self.note_list = NoteListPanel(parent=self.splitter)
        self.note_list.note_selected.connect(self._on_note_selected)
        self.note_list.create_note_requested.connect(self._on_create_note)
        self.note_list.search_query_changed.connect(self._on_search_filter)
        self.note_list.toggle_folders_requested.connect(self._toggle_sidebar)
        self.note_list.collapse_notes_requested.connect(self._toggle_notes_list)
        self.note_list.rename_note_requested.connect(self._on_rename_note)
        self.note_list.delete_note_requested.connect(self._on_delete_single_note)
        self.note_list.delete_notes_batch_requested.connect(self._on_delete_notes_batch)
        self.note_list.note_color_changed.connect(self._on_note_color_changed)

        # 3. Middle-Right: Editor Canvas
        self.editor = EditorPanel(parent=self.splitter)
        self.editor.content_saved.connect(self._on_content_saved)
        self.editor.title_changed.connect(self._on_note_title_changed)
        self.editor.create_note_with_content.connect(self._on_create_note_with_content)
        self.editor.delete_requested.connect(self._on_delete_note)
        self.editor.expand_notes_requested.connect(self._toggle_notes_list)
        self.editor.open_file_requested.connect(self._on_open_file_dialog)
        self.editor.backup_requested.connect(self.toggle_backup_panel)

        # 4. Far Right: Backup & Version History Panel
        self.backup_panel = BackupPanel(
            storage_manager=self.storage,
            config_manager=self.config_manager,
            parent=self.splitter,
        )
        self.backup_panel.close_requested.connect(self.toggle_backup_panel)
        self.backup_panel.changes_updated.connect(self.editor.set_backup_changes_count)
        self.backup_panel.note_reverted.connect(self._on_note_reverted)
        self.backup_panel.sync_completed.connect(self._on_sync_completed)

        # Restore layout from configuration
        folders_w = self.config.layout.folders_width if self.config.layout.folders_visible else 0
        notes_w = self.config.layout.notes_list_width if self.config.layout.notes_list_visible else 0
        total_w = self.config.window.width
        editor_w = max(300, total_w - folders_w - notes_w)

        self.splitter.setSizes([folders_w, notes_w, editor_w, 0])
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        self._update_panel_buttons()

        self.setCentralWidget(self.splitter)

    def _setup_shortcuts(self) -> None:
        """Register productivity shortcuts."""
        # New Note (Ctrl+N)
        new_note_sc = QShortcut(QKeySequence("Ctrl+N"), self)
        new_note_sc.activated.connect(self._on_create_note)

        # Open Markdown File (Ctrl+O)
        open_file_sc = QShortcut(QKeySequence("Ctrl+O"), self)
        open_file_sc.activated.connect(self._on_open_file_dialog)

        # Toggle Cloud Backup Panel (Ctrl+Shift+B)
        backup_sc = QShortcut(QKeySequence("Ctrl+Shift+B"), self)
        backup_sc.activated.connect(self.toggle_backup_panel)

        # Quick Cloud Sync (Ctrl+Shift+S)
        sync_sc = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        sync_sc.activated.connect(self._on_quick_sync)

        # Open Notes Folder (Ctrl+Shift+O)
        open_folder_sc = QShortcut(QKeySequence("Ctrl+Shift+O"), self)
        open_folder_sc.activated.connect(self._on_open_folder_dialog)

        # New Folder (Ctrl+Shift+N)
        new_folder_sc = QShortcut(QKeySequence("Ctrl+Shift+N"), self)
        new_folder_sc.activated.connect(self.sidebar._on_add_folder_clicked)

        # Toggle Folders Sidebar (Ctrl+\)
        toggle_sidebar_sc = QShortcut(QKeySequence("Ctrl+\\"), self)
        toggle_sidebar_sc.activated.connect(self._toggle_sidebar)

        # Toggle Notes List (Ctrl+Shift+\)
        toggle_notes_sc = QShortcut(QKeySequence("Ctrl+Shift+\\"), self)
        toggle_notes_sc.activated.connect(self._toggle_notes_list)

        # Focus Search (Ctrl+F) / In-note Find
        search_sc = QShortcut(QKeySequence("Ctrl+F"), self)
        search_sc.activated.connect(self._on_ctrl_f)

        # Global Notes List Search (Ctrl+Shift+F)
        global_search_sc = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        global_search_sc.activated.connect(self.note_list.search_bar.setFocus)

        # In-note Replace (Ctrl+H)
        replace_sc = QShortcut(QKeySequence("Ctrl+H"), self)
        replace_sc.activated.connect(self._on_ctrl_h)

        # Export Note (Ctrl+E)
        export_sc = QShortcut(QKeySequence("Ctrl+E"), self)
        export_sc.activated.connect(self.editor.export_current_note)

        # Delete Note (Ctrl+D)
        delete_sc = QShortcut(QKeySequence("Ctrl+D"), self)
        delete_sc.activated.connect(self._on_delete_note)

        # Cancel Selection / Escape (Esc)
        esc_sc = QShortcut(QKeySequence("Esc"), self)
        esc_sc.activated.connect(self._on_escape_pressed)

        # Quit Application (Ctrl+Q)
        quit_sc = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_sc.activated.connect(self.close)

        # Keyboard Shortcuts Cheatsheet (Ctrl+/ and F1)
        shortcuts_help_sc = QShortcut(QKeySequence("Ctrl+/"), self)
        shortcuts_help_sc.activated.connect(self._show_shortcuts_cheatsheet)

        f1_sc = QShortcut(QKeySequence("F1"), self)
        f1_sc.activated.connect(self._show_shortcuts_cheatsheet)

    def _show_shortcuts_cheatsheet(self) -> None:
        """Open the modern keyboard shortcuts reference cheatsheet dialog."""
        from ui.shortcuts_dialog import ModernShortcutsDialog
        ModernShortcutsDialog.show_shortcuts(self)

    def _on_ctrl_f(self) -> None:
        """Open in-note Find bar if a note is loaded, else focus sidebar search."""
        if self.editor._current_note is not None:
            self.editor.open_find(replace_mode=False)
        else:
            self.note_list.search_bar.setFocus()

    def _on_ctrl_h(self) -> None:
        """Open in-note Find & Replace bar with Replace row expanded."""
        if self.editor._current_note is not None:
            self.editor.open_find(replace_mode=True)

    def _on_escape_pressed(self) -> None:
        """Cancel selection mode if active in sidebar or note list, or close find bar."""
        if hasattr(self.editor, "find_replace_bar") and self.editor.find_replace_bar.isVisible():
            self.editor.close_find()
            return
        if self.sidebar.is_selection_mode:
            self.sidebar.exit_selection_mode()
        elif self.note_list.is_selection_mode:
            self.note_list.exit_selection_mode()

    def _on_folder_color_changed(self, folder_name: str, color: Optional[str]) -> None:
        """Persist folder color change to configuration."""
        self.config_manager.set_folder_color(folder_name, color)

    def _on_note_color_changed(self, note: Note, color: Optional[str]) -> None:
        """Persist note color change to configuration."""
        self.config_manager.set_note_color(str(note.path), color)

    def _transfer_note_color(self, old_path_str: str, new_path_str: str) -> None:
        """Transfer custom color when a note file is renamed."""
        color = self.config_manager.get_note_color(old_path_str)
        if color:
            self.config_manager.set_note_color(old_path_str, None)
            self.config_manager.set_note_color(new_path_str, color)
            self.note_list.set_note_colors(self.config.appearance.note_colors)

    def _transfer_folder_color(self, old_name: str, new_name: str) -> None:
        """Transfer custom color when a folder is renamed."""
        color = self.config_manager.get_folder_color(old_name)
        if color:
            self.config_manager.set_folder_color(old_name, None)
            self.config_manager.set_folder_color(new_name, color)
            self.sidebar.set_folder_colors(self.config.appearance.folder_colors)

    def _load_initial_data(self) -> None:
        """Load folders and notes on launch."""
        self.sidebar.set_folder_colors(self.config.appearance.folder_colors)
        self.note_list.set_note_colors(self.config.appearance.note_colors)
        folders = self.storage.get_folders()
        self.sidebar.set_folders(folders)
        self._update_watcher_paths()
        self._refresh_notes()

        # If an initial file or directory was requested (CLI or file manager), open it
        if self._initial_path is not None:
            self.open_file_or_folder(self._initial_path)
            return

        # If no notes exist on launch, auto-create one so user can type immediately
        if not self._all_current_notes:
            self._on_create_note()
        elif self._current_note is not None:
            self.editor.editor.setFocus()

    def open_file_or_folder(self, target: Union[str, Path]) -> bool:
        """Open a Markdown file in the editor or a folder as the active workspace.

        Validates that files are genuine Markdown/text documents and rejects binary/unsupported formats.
        """
        path = Path(target).resolve()
        is_valid, err_title, err_msg = validate_markdown_file(path)
        if not is_valid:
            QMessageBox.warning(self, err_title or "Error", err_msg or f"Cannot open '{path.name}'.")
            return False

        # Case 1: Target is a directory -> open directory as notes root
        if path.is_dir():
            self.storage.root_dir = path
            folders = self.storage.get_folders()
            self.sidebar.set_folders(folders)
            self._current_folder = None
            self._update_watcher_paths()
            self._refresh_notes()
            self.setWindowTitle(f"{path.name} — Markup Notes")
            return True

        # Case 2: Target is a Markdown / text file
        # Check if it is inside the current storage root
        try:
            rel = path.relative_to(self.storage.root_dir)
            parent_folder = path.parent if path.parent != self.storage.root_dir else None
            self._current_folder = parent_folder
            self._refresh_notes(preserve_path=str(path), emit_selection=True)
            self.setWindowTitle(f"{path.stem} — Markup Notes")
            return True
        except ValueError:
            # External file outside the notes workspace -> clone and persist it into the workspace
            external_note = Note.from_file(path)
            if external_note is None:
                QMessageBox.warning(self, "Read Error", f"Unable to read content from '{path.name}'.")
                return False

            # Create a new note in the active workspace and copy external content
            imported_note = self.storage.create_note(
                folder=self._current_folder,
                initial_title=path.stem or "Untitled",
            )
            if imported_note is not None:
                self.storage.save_note_content(imported_note.path, external_note.content)
                reloaded = Note.from_file(imported_note.path)
                if reloaded is not None:
                    imported_note = reloaded
                else:
                    imported_note.content = external_note.content
                self._refresh_notes(preserve_path=str(imported_note.path), emit_selection=True)
                self.editor.load_note(imported_note)
                self.setWindowTitle(f"{imported_note.title} — Markup Notes")
            else:
                self._current_note = external_note
                self.editor.load_note(external_note)
                self.setWindowTitle(f"{path.name} — Markup Notes")
            return True

    def _on_open_file_dialog(self) -> None:
        """Open native XDG Desktop Portal file dialog to select and load a Markdown file."""
        from PyQt6.QtWidgets import QFileDialog

        start_dir = (
            str(self.storage.root_dir)
            if self.storage.root_dir.exists()
            else str(Path.home())
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            start_dir,
            "Markdown Files (*.md *.markdown *.mdown *.mkd *.txt);;All Files (*)",
        )
        if file_path:
            self.open_file_or_folder(Path(file_path))

    def _on_open_folder_dialog(self) -> None:
        """Open native XDG Desktop Portal dialog to select a folder as workspace."""
        from PyQt6.QtWidgets import QFileDialog

        start_dir = (
            str(self.storage.root_dir)
            if self.storage.root_dir.exists()
            else str(Path.home())
        )
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Open Notes Folder",
            start_dir,
        )
        if folder_path:
            self.open_file_or_folder(Path(folder_path))

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

    def _on_create_folder(
        self, folder_name: str, parent_folder: Optional[Path] = None
    ) -> None:
        safe_name = self.storage.sanitize_filename(folder_name)
        if not safe_name:
            ModernMessageDialog.show_error(
                self,
                "Invalid Folder Name",
                "Please enter a valid folder name containing letters or numbers.",
            )
            return

        base_dir = (
            parent_folder
            if (parent_folder is not None and parent_folder.exists())
            else self.storage.root_dir
        )
        target_path = base_dir / safe_name
        if target_path.exists():
            loc = f"inside '{parent_folder.name}'" if parent_folder else "in Folders"
            ModernMessageDialog.show_error(
                self,
                "Folder Already Exists",
                f"A folder named '{folder_name}' already exists {loc}.\nPlease choose a different name.",
            )
            return

        new_folder = self.storage.create_folder(folder_name, parent_folder=parent_folder)
        if new_folder is not None:
            folders = self.storage.get_folders()
            self.sidebar.set_folders(folders, current_selection=new_folder)
            self._current_folder = new_folder
            self._update_watcher_paths()
            self._refresh_notes()
        else:
            ModernMessageDialog.show_error(
                self,
                "Folder Creation Failed",
                f"Could not create folder '{folder_name}'. Please check disk permissions.",
            )

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
            self.editor.title_edit.setFocus()
            self.editor.title_edit.selectAll()
            self.backup_panel.refresh_status()
            self.backup_panel.schedule_auto_backup()
        QTimer.singleShot(500, self._clear_saving_flag)

    def _on_create_note_with_content(self, initial_content: str) -> None:
        """Create a new note with typed content when user writes on empty canvas."""
        self._is_saving_internally = True
        new_note = self.storage.create_note(folder=self._current_folder, initial_title="Untitled")
        if new_note is not None:
            self.storage.save_note_content(new_note.path, initial_content)
            self._current_note = Note.from_file(new_note.path)
            if self._current_note is not None:
                self.editor.update_meta(self._current_note)
                self._refresh_notes(preserve_path=str(new_note.path), emit_selection=False)
                self.backup_panel.refresh_status()
                self.backup_panel.schedule_auto_backup()
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

        # Update current note instance and card preview snippet without renaming file
        self._current_note = Note.from_file(current_path)
        if self._current_note is not None:
            self.editor.update_meta(self._current_note)
            self.note_list.update_note_card(str(current_path), self._current_note)
            self._all_current_notes = self.storage.list_notes(self._current_folder)
            self.backup_panel.refresh_status()
            self.backup_panel.schedule_auto_backup()

        QTimer.singleShot(500, self._clear_saving_flag)

    def _on_note_title_changed(self, new_title: str) -> None:
        """Rename note file when user edits the title in the editor panel."""
        if self._current_note is None:
            return

        sanitized_title = self.storage.sanitize_filename(new_title)
        if not sanitized_title:
            return

        current_path = self._current_note.path
        if sanitized_title == current_path.stem:
            return

        self._is_saving_internally = True
        renamed_path = self.storage.rename_note_file(current_path, sanitized_title)
        if renamed_path != current_path:
            self._transfer_note_color(str(current_path), str(renamed_path))
            self._current_note = Note.from_file(renamed_path)
            if self._current_note is not None:
                self.editor.update_meta(self._current_note)
                self.note_list.update_note_card(str(current_path), self._current_note)
                self._all_current_notes = self.storage.list_notes(self._current_folder)
                self.backup_panel.refresh_status()
                self.backup_panel.schedule_auto_backup()

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
            self.config_manager.set_note_color(str(self._current_note.path), None)
            self.storage.delete_note(self._current_note.path)
            self._current_note = None
            self._refresh_notes()
            self.backup_panel.refresh_status()
            self.backup_panel.schedule_auto_backup()

    def _on_rename_folder(self, folder_path: Path) -> None:
        """Rename an existing folder."""
        new_name, ok = ModernInputDialog.get_text(
            self,
            title="Rename Folder",
            prompt="Enter new folder name:",
            default=folder_path.name,
            confirm_text="Rename",
            icon_type="rename",
        )
        if ok and new_name and new_name != folder_path.name:
            safe_name = self.storage.sanitize_filename(new_name)
            if not safe_name:
                ModernMessageDialog.show_error(
                    self,
                    "Invalid Folder Name",
                    "Please enter a valid folder name containing letters or numbers.",
                )
                return
            target_path = folder_path.parent / safe_name
            if target_path.exists() and target_path != folder_path:
                ModernMessageDialog.show_error(
                    self,
                    "Folder Already Exists",
                    f"A folder named '{new_name}' already exists in this location.\nPlease choose a different name.",
                )
                return

            renamed_folder = self.storage.rename_folder(folder_path, new_name)
            if renamed_folder is not None:
                self._transfer_folder_color(folder_path.name, new_name)
                if self._current_folder == folder_path:
                    self._current_folder = renamed_folder
                self._update_watcher_paths()
                self.sidebar.set_folders(self.storage.get_folders(), current_selection=self._current_folder)
                self._refresh_notes()
            else:
                ModernMessageDialog.show_error(
                    self,
                    "Rename Failed",
                    f"Could not rename folder '{folder_path.name}'. Please check disk permissions.",
                )

    def _on_delete_folder(self, folder_path: Path) -> None:
        """Delete an existing folder and all notes inside it."""
        notes = self.storage.list_notes(folder_path)
        count = len(notes)
        msg = (
            f"Are you sure you want to delete folder '{folder_path.name}' and all {count} notes inside it? They will be moved to Trash."
            if count > 0
            else f"Are you sure you want to delete folder '{folder_path.name}'?"
        )
        confirmed = ModernConfirmDialog.ask(
            self,
            title="Delete Folder",
            message=msg,
            confirm_text="Delete",
            is_destructive=True,
        )
        if confirmed:
            self.config_manager.set_folder_color(folder_path.name, None)
            self.storage.delete_folder(folder_path)
            if self._current_folder == folder_path:
                self._current_folder = None
            self._update_watcher_paths()
            self.sidebar.set_folders(self.storage.get_folders(), current_selection=self._current_folder)
            self._refresh_notes()

    def _on_delete_folders_batch(self, folders: List[Path]) -> None:
        """Delete multiple selected folders in batch."""
        count = len(folders)
        if count == 0:
            return
        msg = f"Are you sure you want to delete {count} selected folders and all notes inside them? They will be moved to Trash."
        confirmed = ModernConfirmDialog.ask(
            self,
            title=f"Delete {count} Folders",
            message=msg,
            confirm_text="Delete",
            is_destructive=True,
        )
        if confirmed:
            for f in folders:
                self.config_manager.set_folder_color(f.name, None)
            self.storage.delete_folders_batch(folders)
            if self._current_folder in folders:
                self._current_folder = None
            self._update_watcher_paths()
            self.sidebar.exit_selection_mode()
            self.sidebar.set_folders(self.storage.get_folders(), current_selection=self._current_folder)
            self._refresh_notes()

    def _on_rename_note(self, note: Note) -> None:
        """Rename a note from right-click context menu."""
        new_title, ok = ModernInputDialog.get_text(
            self,
            title="Rename Note",
            prompt="Enter new note title:",
            default=note.title,
            confirm_text="Rename",
            icon_type="rename",
        )
        if ok and new_title and new_title != note.title:
            self._is_saving_internally = True
            renamed_path = self.storage.rename_note_file(note.path, new_title)
            if renamed_path != note.path:
                self._transfer_note_color(str(note.path), str(renamed_path))

            updated_note = Note.from_file(renamed_path)
            if updated_note is not None:
                if self._current_note and self._current_note.path == note.path:
                    self._current_note = updated_note
                    self.editor.load_note(updated_note)
                self.note_list.update_note_card(str(note.path), updated_note)
                self._refresh_notes(preserve_path=str(renamed_path), emit_selection=False)
                self.backup_panel.refresh_status()
                self.backup_panel.schedule_auto_backup()

            QTimer.singleShot(500, self._clear_saving_flag)

    def _on_delete_single_note(self, note: Note) -> None:
        """Delete a single note from right-click context menu."""
        confirmed = ModernConfirmDialog.ask(
            self,
            title="Delete Note",
            message=f"Are you sure you want to delete '{note.title}'?",
            confirm_text="Delete",
            is_destructive=True,
        )
        if confirmed:
            self.config_manager.set_note_color(str(note.path), None)
            self.storage.delete_note(note.path)
            if self._current_note and self._current_note.path == note.path:
                self._current_note = None
                self.editor.load_note(None)
            self._refresh_notes()
            self.backup_panel.refresh_status()
            self.backup_panel.schedule_auto_backup()

    def _on_delete_notes_batch(self, notes: List[Note]) -> None:
        """Delete multiple notes in one batch from selection mode."""
        count = len(notes)
        if count == 0:
            return
        confirmed = ModernConfirmDialog.ask(
            self,
            title=f"Delete {count} Notes",
            message=f"Are you sure you want to delete {count} selected notes? They will be moved to Trash.",
            confirm_text="Delete",
            is_destructive=True,
        )
        if confirmed:
            paths = [n.path for n in notes]
            for n in notes:
                self.config_manager.set_note_color(str(n.path), None)
            self.storage.delete_notes_batch(paths)
            if self._current_note and self._current_note.path in paths:
                self._current_note = None
                self.editor.load_note(None)
            self.note_list.exit_selection_mode()
            self._refresh_notes()
            self.backup_panel.refresh_status()
            self.backup_panel.schedule_auto_backup()

    def _on_select_all_notes_requested(self) -> None:
        """Enter selection mode on notes list from sidebar All Notes right-click."""
        self.note_list.enter_selection_mode()

    def _on_search_filter(self, query: str) -> None:
        if not query:
            self.note_list.set_notes(self._all_current_notes)
            return

        filtered = [
            n for n in self._all_current_notes
            if query in n.title.lower() or query in n.content.lower()
        ]
        self.note_list.set_notes(filtered)

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Track manual splitter adjustments and sync to configuration."""
        sizes = self.splitter.sizes()
        if sizes[0] > 50:
            self.config.layout.folders_width = sizes[0]
            self.config.layout.folders_visible = True
        elif sizes[0] == 0:
            self.config.layout.folders_visible = False

        if sizes[1] > 50:
            self.config.layout.notes_list_width = sizes[1]
            self.config.layout.notes_list_visible = True
        elif sizes[1] == 0:
            self.config.layout.notes_list_visible = False

        self._update_panel_buttons()
        self.config_manager.save()

    def _update_panel_buttons(self) -> None:
        """Synchronize toggle button visibilities and tooltips with current state."""
        folders_open = self.config.layout.folders_visible
        notes_open = self.config.layout.notes_list_visible

        # 1. Folders domain: Sidebar owns its collapse button when open
        self.sidebar.collapse_btn.setVisible(folders_open)
        self.sidebar.collapse_btn.setToolTip("Collapse Folders (Ctrl+\\)")

        # 2. Folders restore button in Note List header: only visible when Folders is collapsed
        self.note_list.toggle_folders_btn.setVisible(not folders_open)
        self.note_list.toggle_folders_btn.setToolTip("Show Folders (Ctrl+\\)")

        # 3. Notes domain: Note List owns its collapse button when open
        self.note_list.collapse_notes_btn.setVisible(notes_open)
        self.note_list.collapse_notes_btn.setToolTip("Collapse Notes (Ctrl+Shift+\\)")

        # 4. Notes restore button in Editor header: only visible when Notes is collapsed
        self.editor.expand_notes_btn.setVisible(not notes_open)
        self.editor.expand_notes_btn.setToolTip("Show Notes (Ctrl+Shift+\\)")

    def _animate_splitter_pane(self, pane_index: int, target_w: int) -> None:
        """Smoothly slide a splitter pane to target_w using QVariantAnimation."""
        if self._active_pane_anim is not None:
            self._active_pane_anim.stop()
            self._active_pane_anim = None

        sizes = list(self.splitter.sizes())
        start_w = sizes[pane_index]
        if start_w == target_w:
            self._update_panel_buttons()
            return

        total_w = sum(sizes)
        other_pane_index = 1 if pane_index == 0 else 0
        other_w = sizes[other_pane_index]

        # Dynamic handoff: if expanding, immediately hide the adjacent restore button
        if pane_index == 0 and target_w > 0:
            self.note_list.toggle_folders_btn.setVisible(False)
        elif pane_index == 1 and target_w > 0:
            self.editor.expand_notes_btn.setVisible(False)

        anim = QVariantAnimation(self)
        anim.setDuration(220)
        anim.setStartValue(start_w)
        anim.setEndValue(target_w)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_step(val: object) -> None:
            curr_w = int(val)
            backup_w = self.splitter.sizes()[3] if len(self.splitter.sizes()) > 3 else 0
            if pane_index == 0:
                editor_w = max(100, total_w - curr_w - other_w - backup_w)
                self.splitter.setSizes([curr_w, other_w, editor_w, backup_w])
            else:
                editor_w = max(100, total_w - other_w - curr_w - backup_w)
                self.splitter.setSizes([other_w, curr_w, editor_w, backup_w])

        def _on_finish() -> None:
            self._active_pane_anim = None
            backup_w = self.splitter.sizes()[3] if len(self.splitter.sizes()) > 3 else 0
            if pane_index == 0:
                editor_w = max(100, total_w - target_w - other_w - backup_w)
                self.splitter.setSizes([target_w, other_w, editor_w, backup_w])
            else:
                editor_w = max(100, total_w - other_w - target_w - backup_w)
                self.splitter.setSizes([other_w, target_w, editor_w, backup_w])

            self._update_panel_buttons()
            self.config_manager.save()

        anim.valueChanged.connect(_on_step)
        anim.finished.connect(_on_finish)
        self._active_pane_anim = anim
        anim.start()

    def _toggle_sidebar(self) -> None:
        """Toggle left folders sidebar between collapsed (0px) and expanded with smooth slide."""
        if self.config.layout.folders_visible:
            # Currently visible -> Collapse
            curr_w = self.splitter.sizes()[0]
            if curr_w > 80:
                self.config.layout.folders_width = curr_w
            self.config.layout.folders_visible = False
            self._animate_splitter_pane(pane_index=0, target_w=0)
        else:
            # Currently collapsed -> Restore
            restore_w = self.config.layout.folders_width
            if restore_w < 120:
                restore_w = 190
            self.config.layout.folders_visible = True
            self._animate_splitter_pane(pane_index=0, target_w=restore_w)

    def _toggle_notes_list(self) -> None:
        """Toggle middle notes list between collapsed (0px) and expanded with smooth slide."""
        if self.config.layout.notes_list_visible:
            # Currently visible -> Collapse (distraction-free editor mode)
            curr_w = self.splitter.sizes()[1]
            if curr_w > 100:
                self.config.layout.notes_list_width = curr_w
            self.config.layout.notes_list_visible = False
            self._animate_splitter_pane(pane_index=1, target_w=0)
        else:
            # Currently collapsed -> Restore
            restore_w = self.config.layout.notes_list_width
            if restore_w < 150:
                restore_w = 280
            self.config.layout.notes_list_visible = True
            self._animate_splitter_pane(pane_index=1, target_w=restore_w)

    def toggle_backup_panel(self) -> None:
        """Toggle right-side Backup & Version History panel."""
        sizes = list(self.splitter.sizes())
        if len(sizes) < 4:
            return

        folders_w, notes_w, editor_w, backup_w = sizes
        if backup_w > 20:
            # Collapse backup panel
            new_editor_w = editor_w + backup_w
            self.splitter.setSizes([folders_w, notes_w, new_editor_w, 0])
        else:
            # Expand backup panel to 320px
            target_w = 320
            new_editor_w = max(200, editor_w - target_w)
            self.splitter.setSizes([folders_w, notes_w, new_editor_w, target_w])
            self.backup_panel.refresh_status()

    def _on_quick_sync(self) -> None:
        """Execute quick cloud sync (Ctrl+Shift+S)."""
        self.backup_panel.trigger_sync()

    def _on_sync_completed(self, success: bool, message: str) -> None:
        """Refresh sidebar folders and note list when remote notes are imported or synchronized."""
        if success:
            self.sidebar.set_folders(self.storage.get_folders(), current_selection=self._current_folder)
            self._update_watcher_paths()
            current_path = str(self._current_note.path) if self._current_note else None
            self._refresh_notes(preserve_path=current_path, emit_selection=False)

    def _on_note_reverted(self, rel_path: str) -> None:
        """Handle note reverted event from backup panel."""
        reverted_file = self.storage.root_dir / rel_path
        if self._current_note and self._current_note.path == reverted_file:
            reloaded = Note.from_file(reverted_file)
            if reloaded:
                self.editor.load_note(reloaded)
        self._refresh_notes(preserve_path=str(reverted_file) if reverted_file.exists() else None)

    def flush_pending_save(self) -> None:
        """Flush any unsaved debounced editor changes immediately."""
        self.editor.flush_pending_save()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Ensure any pending note edits and window geometry are persisted before exit."""
        self.flush_pending_save()
        if not self.isMaximized():
            self.config.window.width = self.width()
            self.config.window.height = self.height()
            self.config.window.maximized = False
        else:
            self.config.window.maximized = True
        self.config_manager.save()
        super().closeEvent(event)
