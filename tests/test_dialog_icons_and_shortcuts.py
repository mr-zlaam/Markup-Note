"""Unit tests verifying visual icon badges and keyboard shortcuts across all modal dialogs."""

from __future__ import annotations

import os
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QKeyEvent, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel

from ui.dialogs import (
    ModernConfirmDialog,
    ModernExportDialog,
    ModernInputDialog,
    ModernLinkDialog,
    ModernMessageDialog,
)
from ui.diff_dialog import ModernDiffDialog
from utils.icons import (
    create_alert_icon,
    create_badge_pixmap,
    create_edit_icon,
    create_info_icon,
    create_trash_icon,
)


class TestDialogIconsAndShortcuts(unittest.TestCase):
    """Test suite covering dialog header badges and Enter/Return keyboard navigation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def test_icon_generators(self) -> None:
        """Verify vector icon generation functions return non-null pixmaps."""
        edit_icon = create_edit_icon("#0a84ff", size=16)
        alert_icon = create_alert_icon("#ff453a", size=16)
        info_icon = create_info_icon("#0a84ff", size=16)

        self.assertFalse(edit_icon.isNull())
        self.assertFalse(alert_icon.isNull())
        self.assertFalse(info_icon.isNull())

        pm_edit = edit_icon.pixmap(QSize(16, 16))
        self.assertFalse(pm_edit.isNull())

        badge = create_badge_pixmap(edit_icon, bg_color="#1a2638", border_color="#233b5d", badge_size=36, icon_size=20)
        self.assertFalse(badge.isNull())
        self.assertEqual(badge.devicePixelRatio(), 2.0)

    def test_confirm_dialog_badge_and_enter_key(self) -> None:
        """Verify ModernConfirmDialog has icon badge and pressing Enter accepts."""
        # Destructive mode (delete)
        dlg_destruct = ModernConfirmDialog(
            parent=None,
            title="Delete Note",
            message="Are you sure you want to delete this note?",
            confirm_text="Delete",
            is_destructive=True,
        )
        # Find 36x36 badge label
        labels = dlg_destruct.findChildren(QLabel)
        badge_lbls = [lbl for lbl in labels if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badge_lbls) >= 1)
        self.assertEqual(badge_lbls[0].size(), QSize(36, 36))

        # Confirm button must be default and focused
        self.assertTrue(dlg_destruct.confirm_btn.isDefault())
        self.assertTrue(dlg_destruct.confirm_btn.autoDefault())

        # Simulate Enter key press on dialog
        enter_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        self.app.sendEvent(dlg_destruct, enter_event)
        self.assertEqual(dlg_destruct.result(), ModernConfirmDialog.DialogCode.Accepted)
        dlg_destruct.deleteLater()

        # Non-destructive mode
        dlg_info = ModernConfirmDialog(
            parent=None,
            title="Confirm Action",
            message="Proceed with changes?",
            confirm_text="Continue",
            is_destructive=False,
        )
        labels_info = dlg_info.findChildren(QLabel)
        badge_info = [lbl for lbl in labels_info if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badge_info) >= 1)
        dlg_info.deleteLater()

    def test_input_dialog_badge_and_selection(self) -> None:
        """Verify ModernInputDialog renders icon badges and supports auto-inference."""
        # Rename mode
        dlg_rename = ModernInputDialog(
            parent=None,
            title="Rename Folder",
            prompt="Enter folder name:",
            default_text="OldName",
            confirm_text="Rename",
            icon_type="rename",
        )
        badges = [lbl for lbl in dlg_rename.findChildren(QLabel) if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badges) >= 1)
        self.assertEqual(badges[0].size(), QSize(36, 36))
        dlg_rename.deleteLater()

        # Inferred folder mode
        dlg_folder = ModernInputDialog(
            parent=None,
            title="New Folder",
            prompt="Enter folder name:",
            default_text="New Notes",
            confirm_text="Create",
        )
        badges_f = [lbl for lbl in dlg_folder.findChildren(QLabel) if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badges_f) >= 1)
        dlg_folder.deleteLater()

        # Inferred note mode
        dlg_note = ModernInputDialog(
            parent=None,
            title="Rename Note",
            prompt="Enter note title:",
            default_text="My Note",
        )
        badges_n = [lbl for lbl in dlg_note.findChildren(QLabel) if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badges_n) >= 1)
        dlg_note.deleteLater()

    def test_message_dialog_badge_and_enter_key(self) -> None:
        """Verify ModernMessageDialog renders badges for error and info and Enter accepts."""
        # Error dialog
        err_dlg = ModernMessageDialog(
            parent=None,
            title="Export Failed",
            message="Could not write file to disk.",
            confirm_text="OK",
            is_error=True,
        )
        badges_err = [lbl for lbl in err_dlg.findChildren(QLabel) if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badges_err) >= 1)
        self.assertEqual(badges_err[0].size(), QSize(36, 36))
        self.assertTrue(err_dlg.confirm_btn.isDefault())

        # Simulate Enter key press
        enter_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        self.app.sendEvent(err_dlg, enter_event)
        self.assertEqual(err_dlg.result(), ModernMessageDialog.DialogCode.Accepted)
        err_dlg.deleteLater()

        # Info dialog
        info_dlg = ModernMessageDialog(
            parent=None,
            title="Note Saved",
            message="Note was backed up successfully.",
            confirm_text="OK",
            is_error=False,
        )
        badges_info = [lbl for lbl in info_dlg.findChildren(QLabel) if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badges_info) >= 1)
        info_dlg.deleteLater()

    def test_link_and_export_and_diff_dialog_badges(self) -> None:
        """Verify ModernLinkDialog, ModernExportDialog, and ModernDiffDialog render header badges."""
        link_dlg = ModernLinkDialog(initial_text="GitHub", initial_url="https://github.com")
        badges_link = [lbl for lbl in link_dlg.findChildren(QLabel) if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badges_link) >= 1)
        link_dlg.deleteLater()

        export_dlg = ModernExportDialog(note_title="Documentation")
        badges_exp = [lbl for lbl in export_dlg.findChildren(QLabel) if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badges_exp) >= 1)
        export_dlg.deleteLater()

        diff_dlg = ModernDiffDialog(file_name="example.md", diff_text="- old\n+ new")
        badges_diff = [lbl for lbl in diff_dlg.findChildren(QLabel) if lbl.pixmap() is not None and not lbl.pixmap().isNull()]
        self.assertTrue(len(badges_diff) >= 1)
        diff_dlg.deleteLater()


if __name__ == "__main__":
    unittest.main()
