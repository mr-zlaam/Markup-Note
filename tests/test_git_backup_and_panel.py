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

        # Check authenticated clone url helper does not leak token in remote URL
        auth_url = client.build_authenticated_remote_url("https://github.com/testuser/notes.git", "ghp_faketesttoken12345")
        self.assertEqual(auth_url, "https://github.com/testuser/notes.git")
        self.assertNotIn("ghp_faketesttoken12345", auth_url)

        # Verify plaintext token is never stored in github_auth.json
        import json
        auth_file = config_dir / "github_auth.json"
        self.assertTrue(auth_file.exists())
        with open(auth_file, "r", encoding="utf-8") as f:
            auth_data = json.load(f)
            self.assertNotIn("token", auth_data)
            self.assertEqual(auth_data.get("login"), "testuser")

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

    def test_credential_store_fallback_and_vault(self) -> None:
        """Verify CredentialStore saves, loads, and deletes tokens securely with 0600 permissions."""
        from storage.credential_store import CredentialStore

        cfg_dir = self.temp_dir / "cred_test_config"
        store = CredentialStore(config_dir=cfg_dir)

        self.assertIsNone(store.get_token())

        ok_save = store.save_token("github_pat_testtoken999")
        self.assertTrue(ok_save)
        self.assertEqual(store.get_token(), "github_pat_testtoken999")

        # Verify vault file exists with restrictive 0600 permissions if file vault fallback used
        vault_file = cfg_dir / ".credentials.vault"
        if vault_file.exists():
            mode = vault_file.stat().st_mode & 0o777
            self.assertEqual(mode, 0o600)
            # Ensure plaintext token is not present in raw vault bytes
            raw_content = vault_file.read_bytes()
            self.assertNotIn(b"github_pat_testtoken999", raw_content)

        ok_del = store.delete_token()
        self.assertTrue(ok_del)
        self.assertIsNone(store.get_token())

    def test_legacy_token_migration(self) -> None:
        """Verify automatic migration of plaintext tokens from legacy github_auth.json."""
        import json
        config_dir = self.temp_dir / "legacy_config"
        config_dir.mkdir(parents=True, exist_ok=True)
        auth_file = config_dir / "github_auth.json"

        # Simulate legacy configuration storing plaintext token
        legacy_data = {
            "token": "ghp_legacyplainsecret123",
            "login": "legacyuser",
            "repo_url": "https://github.com/legacyuser/notes.git",
        }
        with open(auth_file, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        client = GitHubClient(config_dir=config_dir)
        retrieved_token = client.get_token()

        # Token should be successfully migrated and returned
        self.assertEqual(retrieved_token, "ghp_legacyplainsecret123")

        # Verify token was stripped from github_auth.json
        with open(auth_file, "r", encoding="utf-8") as f:
            updated_data = json.load(f)
            self.assertNotIn("token", updated_data)
            self.assertEqual(updated_data.get("login"), "legacyuser")

    def test_git_manager_sanitize_remote_url(self) -> None:
        """Verify sanitize_remote_url strips credentials while preserving host and path."""
        url_with_token = "https://oauth2:ghp_faketoken123@github.com/user/notes.git"
        clean = GitManager.sanitize_remote_url(url_with_token)
        self.assertEqual(clean, "https://github.com/user/notes.git")

        url_with_user_pass = "https://user:password@github.com/user/notes.git"
        clean_user_pass = GitManager.sanitize_remote_url(url_with_user_pass)
        self.assertEqual(clean_user_pass, "https://github.com/user/notes.git")

        clean_url = "https://github.com/user/notes.git"
        self.assertEqual(GitManager.sanitize_remote_url(clean_url), clean_url)

        ssh_url = "git@github.com:user/notes.git"
        self.assertEqual(GitManager.sanitize_remote_url(ssh_url), ssh_url)

    def test_git_manager_set_remote_sanitization(self) -> None:
        """Verify set_remote sanitizes URLs and prevents embedded tokens in git config."""
        git_dir = self.temp_dir / "notes_remote_test"
        mgr = GitManager(git_dir)
        mgr.init_repo()

        dirty_url = "https://oauth2:ghp_leakedsecret999@github.com/user/notes.git"
        mgr.set_remote(dirty_url)

        saved_remote = mgr.get_remote()
        self.assertEqual(saved_remote, "https://github.com/user/notes.git")
        self.assertNotIn("ghp_leakedsecret999", saved_remote or "")

        # Read .git/config directly to verify no credentials exist on disk
        git_config = (git_dir / ".git" / "config").read_text(encoding="utf-8")
        self.assertNotIn("ghp_leakedsecret999", git_config)
        self.assertNotIn("oauth2:", git_config)

    def test_github_auth_dialog_ui_components(self) -> None:
        """Verify ModernGitHubAuthDialog has eye toggle, Connect button, and stable layout."""
        from PyQt6.QtWidgets import QLineEdit, QPushButton
        from ui.github_auth_dialog import ModernCheckBox, ModernGitHubAuthDialog

        dlg = ModernGitHubAuthDialog()
        self.assertIsInstance(dlg.chk_create_repo, ModernCheckBox)
        self.assertTrue(dlg.chk_create_repo.isChecked())
        self.assertEqual(dlg.btn_connect.text(), "Connect")
        self.assertEqual(dlg.token_input.echoMode(), QLineEdit.EchoMode.Password)
        self.assertFalse(dlg.btn_show_token.icon().isNull())

        # Test toggle echo mode changes icon and mode
        dlg.btn_show_token.click()
        self.assertEqual(dlg.token_input.echoMode(), QLineEdit.EchoMode.Normal)
        self.assertEqual(dlg.btn_show_token.toolTip(), "Hide token")

        dlg.btn_show_token.click()
        self.assertEqual(dlg.token_input.echoMode(), QLineEdit.EchoMode.Password)
        self.assertEqual(dlg.btn_show_token.toolTip(), "Show token")

        # Verify button heights remain stable and uncompressed when status message is set
        btn_open = dlg.findChild(QPushButton, "SecondaryBtn")
        if btn_open:
            self.assertGreaterEqual(btn_open.height(), 36)
        dlg.status_lbl.setText("Opened GitHub in browser. Scroll to the bottom and click 'Generate token'.")
        dlg.adjustSize()
        if btn_open:
            self.assertGreaterEqual(btn_open.height(), 36)

        dlg.deleteLater()

    def test_github_token_url_and_expired_auth_detection(self) -> None:
        """Verify pre-scoped classic token URL and expired token detection."""
        client = GitHubClient()
        self.assertEqual(
            client.TOKEN_GENERATE_URL,
            "https://github.com/settings/tokens/new?scopes=repo&description=Markup+Notes",
        )

        # Test auth failure detection in GitManager
        self.assertTrue(GitManager._is_auth_failure("fatal: Authentication failed for 'https://github.com'"))
        self.assertTrue(GitManager._is_auth_failure("remote: Invalid username or token."))
        self.assertTrue(GitManager._is_auth_failure("remote: Bad credentials"))
        self.assertFalse(GitManager._is_auth_failure("Everything up-to-date"))


if __name__ == "__main__":
    unittest.main()
