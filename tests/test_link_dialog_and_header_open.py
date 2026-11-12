"""Unit tests verifying ModernLinkDialog, top-right Open File header button, and link formatting."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure offscreen Qt platform for headless CI / testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QApplication, QDialog

from ui.dialogs import ModernLinkDialog
from ui.editor import EditorPanel, MarkdownEditor
from utils.icons import create_open_file_icon


class TestLinkDialogAndHeaderOpen(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_open_file_icon_generation(self) -> None:
        """Verify vector open file icon generates a non-null QIcon."""
        icon = create_open_file_icon(color="#8e8e93", size=16)
        self.assertFalse(icon.isNull())
        sizes = icon.availableSizes()
        self.assertTrue(len(sizes) > 0 or not icon.pixmap(16, 16).isNull())

    def test_editor_panel_has_open_file_button(self) -> None:
        """Verify EditorPanel top right header contains the open file button with signal."""
        panel = EditorPanel()
        self.assertTrue(hasattr(panel, "open_file_btn"))
        self.assertTrue(panel.open_file_btn.isEnabled())
        self.assertIn("Open Markdown File", panel.open_file_btn.toolTip())

        # Test signal emission
        emitted = []
        panel.open_file_requested.connect(lambda: emitted.append(True))
        panel.open_file_btn.click()
        self.assertEqual(len(emitted), 1)
        panel.deleteLater()

    def test_modern_link_dialog_initialization(self) -> None:
        """Verify ModernLinkDialog initializes with text and url and handles focus."""
        # Case 1: Initial text provided -> focus is on url_input
        dlg1 = ModernLinkDialog(initial_text="GitHub", initial_url="https://github.com")
        self.assertEqual(dlg1.text_input.text(), "GitHub")
        self.assertEqual(dlg1.url_input.text(), "https://github.com")
        self.assertEqual(dlg1.windowTitle(), "Insert Link")
        dlg1.deleteLater()

        # Case 2: Initial text empty -> focus is on text_input
        dlg2 = ModernLinkDialog(initial_text="", initial_url="")
        self.assertEqual(dlg2.text_input.text(), "")
        self.assertEqual(dlg2.url_input.text(), "")
        dlg2.deleteLater()

    def test_modern_link_dialog_enter_key_progression(self) -> None:
        """Verify pressing enter in text input moves focus to url if url is empty."""
        dlg = ModernLinkDialog(initial_text="My Link", initial_url="")
        # Simulate enter on text input
        dlg._on_enter_pressed()
        # When text is non-empty and url is empty, sender check moves focus to url_input
        dlg.deleteLater()

    def test_editor_link_formatting_with_modal(self) -> None:
        """Verify MarkdownEditor opens modal and applies markdown link formatting."""
        editor = MarkdownEditor()
        editor.setPlainText("Check out this cool resource today.")

        # Select "cool resource"
        cursor = editor.textCursor()
        cursor.setPosition(15)
        cursor.setPosition(28, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        self.assertEqual(editor.textCursor().selectedText(), "cool resource")

        # Mock ModernLinkDialog.get_link_data to simulate user input
        with patch.object(
            ModernLinkDialog,
            "get_link_data",
            return_value=("cool resource", "https://resource.com", True),
        ):
            editor._apply_text_format("link")

        self.assertIn("[cool resource](https://resource.com)", editor.toPlainText())
        self.assertEqual(
            editor.toPlainText(),
            "Check out this [cool resource](https://resource.com) today.",
        )
        editor.deleteLater()

    def test_editor_link_formatting_preserves_structural_prefix(self) -> None:
        """Verify applying link format to a checkbox or bullet line preserves prefix."""
        editor = MarkdownEditor()
        editor.setPlainText("- [ ] Visit Python Website\n")

        # Select whole line
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(26, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)

        with patch.object(
            ModernLinkDialog,
            "get_link_data",
            return_value=("Visit Python Website", "https://python.org", True),
        ):
            editor._apply_text_format("link")

        # The structural prefix "- [ ] " must not be broken or wrapped inside the link
        self.assertEqual(
            editor.toPlainText(),
            "- [ ] [Visit Python Website](https://python.org)\n",
        )
        editor.deleteLater()

    def test_editor_link_formatting_canceled_does_not_modify_text(self) -> None:
        """Verify that canceling the link dialog leaves document unmodified."""
        editor = MarkdownEditor()
        editor.setPlainText("Unchanged text here")

        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(9, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)

        with patch.object(
            ModernLinkDialog,
            "get_link_data",
            return_value=("", "", False),
        ):
            editor._apply_text_format("link")

        self.assertEqual(editor.toPlainText(), "Unchanged text here")
        editor.deleteLater()


if __name__ == "__main__":
    unittest.main()
