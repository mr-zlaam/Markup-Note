"""Unit tests verifying GitManager, GitHubClient, BackupPanel, and MainWindow backup toggle."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure offscreen Qt platform for headless CI / testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from core.git_manager import GitCommit, GitManager, GitStatus
from core.github_client import GitHubClient, GitHubRepo, GitHubUser
from core.storage import StorageManager
from ui.backup_panel import BackupPanel
from ui.diff_dialog import ModernDiffDialog
from ui.main_window import MainWindow
from utils.icons import (
    create_backup_icon,
    create_diff_icon,
    create_github_icon,
    create_history_icon,
    create_sync_icon,
)


class TestGitBackupAndPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="markup_notes_test_git_"))
        self.notes_dir = self.temp_dir / "Markup Notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.git_manager = GitManager(self.notes_dir)
        self.storage = StorageManager(self.notes_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_backup_and_git_icons_generation(self) -> None:
        """Verify vector backup, github, sync, history, and diff icons generate valid non-null icons."""
        backup_icon = create_backup_icon(color="#8e8e93", size=16, has_dot=True)
        self.assertFalse(backup_icon.isNull())

        gh_icon = create_github_icon(color="#ffffff", size=16)
        self.assertFalse(gh_icon.isNull())

        sync_icon = create_sync_icon(color="#ffffff", size=16)
        self.assertFalse(sync_icon.isNull())

        history_icon = create_history_icon(color="#8e8e93", size=14)
        self.assertFalse(history_icon.isNull())

        diff_icon = create_diff_icon(color="#8e8e93", size=14)
        self.assertFalse(diff_icon.isNull())

    def test_git_manager_init_and_lifecycle(self) -> None:
        """Verify Git repository initialization, status checking, and staging/committing."""
        if not self.git_manager.is_git_installed():
            self.skipTest("Git CLI is not installed on this test environment.")

        # Initially not a repo
        self.assertFalse(self.git_manager.is_repo())

        # Initialize
        ok, msg = self.git_manager.init_repo()
        self.assertTrue(ok)
        self.assertTrue(self.git_manager.is_repo())

        # Create a new note file
        test_file = self.notes_dir / "Test Note.md"
        test_file.write_text("# Hello World\nInitial content\n", encoding="utf-8")

        # Status check
        status = self.git_manager.get_status()
        self.assertTrue(status.is_repo)
        self.assertFalse(status.is_clean)
        self.assertIn("Test Note.md", status.untracked)

        # Stage and commit
        ok_com, _ = self.git_manager.stage_and_commit("Add Test Note")
        self.assertTrue(ok_com)

        # Status should now be clean
        status_clean = self.git_manager.get_status()
        self.assertTrue(status_clean.is_clean)
        self.assertEqual(status_clean.total_changes, 0)

        # Modify the note file
        test_file.write_text("# Hello World\nModified content here\n", encoding="utf-8")
        status_mod = self.git_manager.get_status()
        self.assertIn("Test Note.md", status_mod.modified)

        # Check diff
        diff = self.git_manager.get_file_diff("Test Note.md")
        self.assertIn("+Modified content here", diff)
        self.assertIn("-Initial content", diff)

        # Revert file
        ok_rev, _ = self.git_manager.revert_file("Test Note.md")
        self.assertTrue(ok_rev)
        self.assertEqual(test_file.read_text(encoding="utf-8"), "# Hello World\nInitial content\n")

        # History check
        history = self.git_manager.get_history(limit=5)
        self.assertTrue(len(history) >= 1)
        self.assertEqual(history[0].message, "Add Test Note")

    def test_git_manager_remote_configuration(self) -> None:
        """Verify setting and getting Git remote URL."""
        if not self.git_manager.is_git_installed():
            self.skipTest("Git CLI is not installed.")

        self.git_manager.init_repo()
        ok, _ = self.git_manager.set_remote("https://github.com/testuser/notes.git")
        self.assertTrue(ok)
        self.assertEqual(self.git_manager.get_remote(), "https://github.com/testuser/notes.git")

    def test_github_client_token_management(self) -> None:
        """Verify GitHub client saves, retrieves, and clears auth tokens securely."""
        config_dir = self.temp_dir / "config"
        client = GitHubClient(config_dir=config_dir)

        self.assertIsNone(client.get_token())

        ok_save = client.save_token("ghp_faketesttoken12345", login="testuser", repo_url="https://github.com/testuser/notes.git")
        self.assertTrue(ok_save)
        self.assertEqual(client.get_token(), "ghp_faketesttoken12345")

        login, repo = client.get_stored_profile()
        self.assertEqual(login, "testuser")
        self.assertEqual(repo, "https://github.com/testuser/notes.git")

        # Check authenticated clone url helper
        auth_url = client.build_authenticated_remote_url("https://github.com/testuser/notes.git", "ghp_faketesttoken12345")
        self.assertIn("oauth2:ghp_faketesttoken12345@github.com", auth_url)

        # Clear token
        ok_clear = client.clear_token()
        self.assertTrue(ok_clear)
        self.assertIsNone(client.get_token())

    def test_backup_panel_ui_components_and_signals(self) -> None:
        """Verify BackupPanel initializes UI, reflects changes, and handles close signal."""
        panel = BackupPanel(storage_manager=self.storage)
        self.assertIsNotNone(panel.btn_sync)
        self.assertIsNotNone(panel.btn_close)
        self.assertIsNotNone(panel.changes_list)
        self.assertIsNotNone(panel.history_list)

        # Test close requested emission
        closed = []
        panel.close_requested.connect(lambda: closed.append(True))
        panel.btn_close.click()
        self.assertEqual(len(closed), 1)
        panel.deleteLater()

    def test_diff_dialog_formatting(self) -> None:
        """Verify ModernDiffDialog renders diff text with html highlight styling."""
        raw_diff = "--- a/note.md\n+++ b/note.md\n@@ -1,1 +1,1 @@\n-Old Line\n+New Line\n Unchanged"
        dlg = ModernDiffDialog(file_name="note.md", diff_text=raw_diff, can_revert=True)
        html = dlg.diff_view.toHtml()
        self.assertIn("New Line", html)
        self.assertIn("Old Line", html)
        dlg.deleteLater()

    def test_main_window_backup_button_and_toggle(self) -> None:
        """Verify MainWindow top-right backup button triggers backup panel expansion and collapse."""
        window = MainWindow(storage_manager=self.storage)
        window.resize(1200, 700)
        window.show()
        self.assertTrue(hasattr(window.editor, "backup_btn"))
        self.assertTrue(window.editor.backup_btn.isEnabled())

        # Initial splitter sizes: 4 panes, index 3 (backup_panel) is 0
        sizes = window.splitter.sizes()
        self.assertEqual(len(sizes), 4)
        self.assertEqual(sizes[3], 0)

        # Clicking backup button opens the panel
        window.editor.backup_btn.click()
        new_sizes = window.splitter.sizes()
        self.assertTrue(new_sizes[3] >= 280)

        # Clicking again closes it
        window.editor.backup_btn.click()
        closed_sizes = window.splitter.sizes()
        self.assertEqual(closed_sizes[3], 0)

        # Test change count badge indicator
        window.editor.set_backup_changes_count(3)
        self.assertIn("3 unsynced changes", window.editor.backup_btn.toolTip())

        window.editor.set_backup_changes_count(0)
        self.assertIn("Cloud Backup", window.editor.backup_btn.toolTip())

        window.close()
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
