"""Unit tests verifying automatic backup toggle and debounced auto-sync functionality."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from core.config import AppSettings, ConfigManager
from core.git_manager import GitManager
from core.storage import StorageManager
from ui.backup_panel import BackupPanel


class TestAutoBackup(unittest.TestCase):
    """Test suite verifying auto-backup toggle persistence and background sync scheduling."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.config_file = self.root / "settings.json"
        self.config_manager = ConfigManager(config_file=self.config_file)
        self.storage = StorageManager(self.root / "notes")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_config_defaults_and_persistence(self) -> None:
        """Verify BackupConfig defaults to False and persists changes."""
        self.assertFalse(self.config_manager.get_auto_backup())

        self.config_manager.set_auto_backup(True)
        self.assertTrue(self.config_manager.get_auto_backup())

        # Reload from disk
        reloaded = ConfigManager(config_file=self.config_file)
        self.assertTrue(reloaded.get_auto_backup())

        # Test from_dict deserialization
        settings = AppSettings.from_dict({"backup": {"auto_backup": True}})
        self.assertTrue(settings.backup.auto_backup)

        settings_false = AppSettings.from_dict({})
        self.assertFalse(settings_false.backup.auto_backup)

    def test_backup_panel_toggle_integration(self) -> None:
        """Verify BackupPanel initializes toggle state from ConfigManager and updates on toggle."""
        self.config_manager.set_auto_backup(True)
        panel = BackupPanel(storage_manager=self.storage, config_manager=self.config_manager)

        self.assertTrue(panel.toggle_auto_backup.isChecked())
        self.assertTrue(panel.is_auto_backup_enabled())

        # Toggle OFF
        panel.toggle_auto_backup.setChecked(False)
        self.assertFalse(panel.is_auto_backup_enabled())
        self.assertFalse(self.config_manager.get_auto_backup())

        # Toggle ON
        panel.toggle_auto_backup.setChecked(True)
        self.assertTrue(panel.is_auto_backup_enabled())
        self.assertTrue(self.config_manager.get_auto_backup())

    def test_schedule_auto_backup_behavior(self) -> None:
        """Verify schedule_auto_backup starts debounce timer only when enabled and in repo."""
        panel = BackupPanel(storage_manager=self.storage, config_manager=self.config_manager)
        panel.git_manager.init_repo()

        # When auto backup is disabled
        panel.toggle_auto_backup.setChecked(False)
        panel.schedule_auto_backup()
        self.assertFalse(panel._auto_backup_timer.isActive())

        # When auto backup is enabled
        panel.toggle_auto_backup.setChecked(True)
        panel.schedule_auto_backup()
        self.assertTrue(panel._auto_backup_timer.isActive())

        # Toggling off stops active timer
        panel.toggle_auto_backup.setChecked(False)
        self.assertFalse(panel._auto_backup_timer.isActive())
