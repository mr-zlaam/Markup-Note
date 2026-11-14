"""UI Package for Note Taker."""

from ui.context_menu import ModernContextMenu
from ui.dialogs import ModernConfirmDialog, ModernInputDialog
from ui.editor import EditorPanel, MarkdownEditor
from ui.highlighter import MarkdownHighlighter
from ui.main_window import MainWindow
from ui.note_list import NoteListPanel
from ui.sidebar import FolderSidebar
from ui.slash_menu import SlashCommandPalette
from ui.theme import apply_theme

__all__ = [
    "EditorPanel",
    "MainWindow",
    "MarkdownEditor",
    "MarkdownHighlighter",
    "ModernConfirmDialog",
    "ModernContextMenu",
    "ModernInputDialog",
    "NoteListPanel",
    "FolderSidebar",
    "SlashCommandPalette",
    "apply_theme",
]
