"""Unit tests verifying PointingHandCursor is configured on all buttons throughout the application."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from core.git_manager import GitManager
from core.storage import StorageManager
from ui.backup_panel import BackupPanel
from ui.dialogs import (
    ModernConfirmDialog,
    ModernExportDialog,
    ModernInputDialog,
    ModernLinkDialog,
    ModernMessageDialog,
)
from ui.diff_dialog import ModernDiffDialog
from ui.editor import EditorPanel
from ui.find_replace import FindReplaceBar
from ui.github_auth_dialog import ModernGitHubAuthDialog
from ui.note_list import NoteListPanel
from ui.selection_toolbar import SelectionFormatToolbar
from ui.sidebar import FolderSidebar
from utils.cursors import install_global_button_cursor_filter


class TestButtonCursors(unittest.TestCase):
    """Test suite ensuring all interactive buttons display PointingHandCursor."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
        install_global_button_cursor_filter(cls.app)

    def test_sidebar_buttons_cursor(self) -> None:
        """Verify all buttons in FolderSidebar have PointingHandCursor."""
        sidebar = FolderSidebar()
        self.assertEqual(sidebar.add_folder_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(sidebar.collapse_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(sidebar.select_all_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(sidebar.batch_delete_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(sidebar.cancel_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)

    def test_note_list_buttons_cursor(self) -> None:
        """Verify all buttons in NoteListPanel have PointingHandCursor."""
        panel = NoteListPanel()
        self.assertEqual(panel.toggle_folders_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(panel.new_note_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(panel.collapse_notes_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(panel.select_all_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(panel.batch_delete_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(panel.cancel_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)

    def test_editor_header_buttons_cursor(self) -> None:
        """Verify header action buttons in EditorPanel have PointingHandCursor."""
        editor_panel = EditorPanel()
        self.assertEqual(editor_panel.expand_notes_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(editor_panel.backup_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(editor_panel.open_file_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(editor_panel.export_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)

    def test_selection_toolbar_buttons_cursor(self) -> None:
        """Verify all formatting buttons in SelectionFormatToolbar have PointingHandCursor."""
        toolbar = SelectionFormatToolbar()
        buttons = [
            toolbar.bold_btn,
            toolbar.italic_btn,
            toolbar.strike_btn,
            toolbar.underline_btn,
            toolbar.bullet_btn,
            toolbar.number_btn,
            toolbar.todo_btn,
            toolbar.link_btn,
            toolbar.code_btn,
        ]
        for btn in buttons:
            self.assertEqual(
                btn.cursor().shape(),
                Qt.CursorShape.PointingHandCursor,
                f"Button {btn.text() or btn.toolTip()} must have PointingHandCursor",
            )

    def test_find_replace_buttons_cursor(self) -> None:
        """Verify all control buttons in FindReplaceBar have PointingHandCursor."""
        widget = FindReplaceBar()
        buttons = [
            widget.toggle_replace_btn,
            widget.case_btn,
            widget.word_btn,
            widget.prev_btn,
            widget.next_btn,
            widget.close_btn,
            widget.replace_btn,
            widget.replace_all_btn,
        ]
        for btn in buttons:
            self.assertEqual(
                btn.cursor().shape(),
                Qt.CursorShape.PointingHandCursor,
                f"Button {btn.text() or btn.toolTip()} must have PointingHandCursor",
            )

    def test_backup_panel_buttons_cursor(self) -> None:
        """Verify all interactive buttons and lists in BackupPanel have PointingHandCursor."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sm = StorageManager(Path(tmp_dir))
            panel = BackupPanel(storage_manager=sm)
            self.assertEqual(panel.btn_refresh.cursor().shape(), Qt.CursorShape.PointingHandCursor)
            self.assertEqual(panel.btn_close.cursor().shape(), Qt.CursorShape.PointingHandCursor)
            self.assertEqual(panel.account_action_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
            self.assertEqual(panel.btn_sync.cursor().shape(), Qt.CursorShape.PointingHandCursor)
            self.assertEqual(panel.btn_backup_all.cursor().shape(), Qt.CursorShape.PointingHandCursor)
            self.assertEqual(panel.toggle_auto_backup.cursor().shape(), Qt.CursorShape.PointingHandCursor)

    def test_dialog_buttons_cursor(self) -> None:
        """Verify all modal dialog buttons have PointingHandCursor."""
        input_dlg = ModernInputDialog(parent=None, title="Rename", default_text="Test")
        self.assertEqual(input_dlg.cancel_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(input_dlg.ok_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)

        link_dlg = ModernLinkDialog(initial_text="Example", initial_url="https://example.com")
        self.assertEqual(link_dlg.cancel_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(link_dlg.ok_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)

        confirm_dlg = ModernConfirmDialog(parent=None, title="Delete Note", message="Are you sure?")
        self.assertEqual(confirm_dlg.cancel_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(confirm_dlg.confirm_btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)

        msg_dlg = ModernMessageDialog(parent=None, title="Notice", message="Info", cancel_text="Cancel")
        msg_buttons = msg_dlg.findChildren(QPushButton)
        self.assertEqual(len(msg_buttons), 2)
        self.assertEqual(msg_buttons[0].cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(msg_buttons[1].cursor().shape(), Qt.CursorShape.PointingHandCursor)

    def test_export_dialog_buttons_cursor(self) -> None:
        """Verify ModernExportDialog buttons and folder chips have PointingHandCursor."""
        export_dlg = ModernExportDialog(note_title="My Test Note")
        chips = [
            export_dlg.btn_pdf,
            export_dlg.btn_html_dark,
            export_dlg.btn_html_light,
            export_dlg.btn_md,
            export_dlg.btn_chip_docs,
            export_dlg.btn_chip_down,
            export_dlg.btn_chip_desk,
            export_dlg.btn_browse,
            export_dlg.export_action_btn,
        ]
        for chip in chips:
            self.assertEqual(chip.cursor().shape(), Qt.CursorShape.PointingHandCursor)

    def test_diff_and_auth_dialog_buttons_cursor(self) -> None:
        """Verify DiffDialog and GitHubAuthDialog buttons have PointingHandCursor."""
        diff_dlg = ModernDiffDialog(parent=None, file_name="test.md", diff_text="+ line 1\n", can_revert=True)
        self.assertEqual(diff_dlg.btn_revert.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(diff_dlg.btn_close.cursor().shape(), Qt.CursorShape.PointingHandCursor)

        auth_dlg = ModernGitHubAuthDialog()
        self.assertEqual(auth_dlg.btn_show_token.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(auth_dlg.btn_cancel.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(auth_dlg.btn_connect.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(auth_dlg.chk_create_repo.cursor().shape(), Qt.CursorShape.PointingHandCursor)

    def test_global_cursor_filter_automatically_sets_hand_cursor(self) -> None:
        """Verify that the application event filter automatically assigns PointingHandCursor on Enter/Show."""
        raw_btn = QPushButton("Test Unconfigured Button")
        # Simulate Show event
        show_event = QEvent(QEvent.Type.Show)
        self.app.sendEvent(raw_btn, show_event)
        self.assertEqual(
            raw_btn.cursor().shape(),
            Qt.CursorShape.PointingHandCursor,
            "Global event filter must set PointingHandCursor on button Show event",
        )


if __name__ == "__main__":
    unittest.main()
