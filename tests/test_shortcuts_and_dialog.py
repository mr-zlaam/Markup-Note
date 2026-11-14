"""Tests for keyboard shortcuts cheatsheet modal and universal markdown editor shortcuts."""

import unittest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QTextCursor
from PyQt6.QtWidgets import QApplication

from ui.editor import EditorPanel, MarkdownEditor
from ui.main_window import MainWindow
from ui.shortcuts_dialog import ModernShortcutsDialog, SHORTCUT_GROUPS
from utils.icons import create_keyboard_icon


app = QApplication.instance() or QApplication([])


class TestKeyboardShortcuts(unittest.TestCase):
    """Test keyboard icon, shortcuts cheatsheet dialog, and editor markdown formatting shortcuts."""

    def setUp(self) -> None:
        self.editor = MarkdownEditor()
        self.panel = EditorPanel()

    def tearDown(self) -> None:
        self.editor.deleteLater()
        self.panel.deleteLater()

    def test_keyboard_icon_generation(self) -> None:
        """Verify keyboard icon creates a valid QIcon with pixmap."""
        icon = create_keyboard_icon("#8e8e93", size=16)
        self.assertFalse(icon.isNull())
        pm = icon.pixmap(16, 16)
        self.assertFalse(pm.isNull())
        self.assertEqual(pm.width(), 16)
        self.assertEqual(pm.height(), 16)

    def test_shortcuts_dialog_initialization_and_filtering(self) -> None:
        """Verify shortcuts modal builds categories, items, and filters on query."""
        dialog = ModernShortcutsDialog()
        dialog.show()
        self.assertIsNotNone(dialog.search_edit)
        self.assertTrue(len(dialog._shortcut_rows) > 15)

        # Total rows should match the total items defined in SHORTCUT_GROUPS
        total_items = sum(len(items) for _, items in SHORTCUT_GROUPS)
        self.assertEqual(len(dialog._shortcut_rows), total_items)

        # Test search query filtering
        dialog.search_edit.setText("bold")
        visible_rows = [row for row, _ in dialog._shortcut_rows if not row.isHidden()]
        self.assertTrue(any(row.title_text == "Bold" for row in visible_rows))

        dialog.search_edit.setText("nonexistent_action_xyz")
        visible_rows = [row for row, _ in dialog._shortcut_rows if not row.isHidden()]
        self.assertEqual(len(visible_rows), 0)

        dialog.search_edit.setText("")
        visible_rows = [row for row, _ in dialog._shortcut_rows if not row.isHidden()]
        self.assertEqual(len(visible_rows), total_items)
        dialog.close()
        dialog.deleteLater()

    def test_editor_panel_shortcuts_button(self) -> None:
        """Verify EditorPanel header has keyboard shortcuts button with correct styling."""
        self.assertTrue(hasattr(self.panel, "shortcuts_btn"))
        btn = self.panel.shortcuts_btn
        self.assertEqual(btn.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(btn.width(), 26)
        self.assertEqual(btn.height(), 26)
        self.assertIn("Ctrl+/", btn.toolTip())

    def test_markdown_bold_with_selection(self) -> None:
        """Verify Ctrl+B wraps and unwraps selected text."""
        self.editor.setPlainText("Hello world")
        cursor = self.editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(5, QTextCursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)

        # Trigger bold
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
        self.editor.keyPressEvent(event)
        self.assertEqual(self.editor.toPlainText(), "**Hello** world")

        # Toggle bold off
        self.editor.keyPressEvent(event)
        self.assertEqual(self.editor.toPlainText(), "Hello world")

    def test_markdown_bold_without_selection_on_word(self) -> None:
        """Verify Ctrl+B without selection selects word under cursor and toggles bold."""
        self.editor.setPlainText("Sample text")
        cursor = self.editor.textCursor()
        cursor.setPosition(3)  # Inside "Sample"
        self.editor.setTextCursor(cursor)

        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
        self.editor.keyPressEvent(event)
        self.assertEqual(self.editor.toPlainText(), "**Sample** text")

        # Toggle off
        cursor = self.editor.textCursor()
        cursor.setPosition(4)  # Inside "Sample"
        self.editor.setTextCursor(cursor)
        self.editor.keyPressEvent(event)
        self.assertEqual(self.editor.toPlainText(), "Sample text")

    def test_markdown_bold_without_selection_on_whitespace(self) -> None:
        """Verify Ctrl+B on empty space inserts empty pair and positions cursor in middle."""
        self.editor.setPlainText("")
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
        self.editor.keyPressEvent(event)
        self.assertEqual(self.editor.toPlainText(), "****")
        self.assertEqual(self.editor.textCursor().position(), 2)

        # Pressing Ctrl+B again immediately deletes the empty pair
        self.editor.keyPressEvent(event)
        self.assertEqual(self.editor.toPlainText(), "")

    def test_markdown_italic_and_underline(self) -> None:
        """Verify Ctrl+I for italic and Ctrl+U for underline."""
        self.editor.setPlainText("Text")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self.editor.setTextCursor(cursor)

        # Italic
        event_i = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_I, Qt.KeyboardModifier.ControlModifier)
        self.editor.keyPressEvent(event_i)
        self.assertEqual(self.editor.toPlainText(), "*Text*")

        self.editor.keyPressEvent(event_i)
        self.assertEqual(self.editor.toPlainText(), "Text")

        # Underline
        event_u = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_U, Qt.KeyboardModifier.ControlModifier)
        cursor.select(QTextCursor.SelectionType.Document)
        self.editor.setTextCursor(cursor)
        self.editor.keyPressEvent(event_u)
        self.assertEqual(self.editor.toPlainText(), "<u>Text</u>")

        self.editor.keyPressEvent(event_u)
        self.assertEqual(self.editor.toPlainText(), "Text")

    def test_markdown_strikethrough_and_code(self) -> None:
        """Verify Ctrl+Shift+X for strikethrough and Ctrl+Shift+C for inline code."""
        self.editor.setPlainText("Delete me")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self.editor.setTextCursor(cursor)

        event_strike = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_X,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        self.editor.keyPressEvent(event_strike)
        self.assertEqual(self.editor.toPlainText(), "~~Delete me~~")

        self.editor.keyPressEvent(event_strike)
        self.assertEqual(self.editor.toPlainText(), "Delete me")

        # Inline code
        event_code = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_C,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        cursor.select(QTextCursor.SelectionType.Document)
        self.editor.setTextCursor(cursor)
        self.editor.keyPressEvent(event_code)
        self.assertEqual(self.editor.toPlainText(), "`Delete me`")

    def test_markdown_code_block(self) -> None:
        """Verify Ctrl+Shift+K wraps selection in multiline fenced code block."""
        self.editor.setPlainText("console.log('hi');")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self.editor.setTextCursor(cursor)

        event_cb = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_K,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        self.editor.keyPressEvent(event_cb)
        self.assertIn("```\nconsole.log('hi');\n```", self.editor.toPlainText())

    def test_markdown_heading_shortcuts(self) -> None:
        """Verify Ctrl+1, Ctrl+2, and Ctrl+3 toggle heading levels on lines."""
        self.editor.setPlainText("Heading Title")
        cursor = self.editor.textCursor()
        cursor.setPosition(4)
        self.editor.setTextCursor(cursor)

        # Ctrl+1 -> H1 (# )
        event_h1 = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_1, Qt.KeyboardModifier.ControlModifier)
        self.editor.keyPressEvent(event_h1)
        self.assertEqual(self.editor.toPlainText(), "# Heading Title")

        # Ctrl+2 on existing heading changes to H2 (## )
        event_h2 = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_2, Qt.KeyboardModifier.ControlModifier)
        self.editor.keyPressEvent(event_h2)
        self.assertEqual(self.editor.toPlainText(), "## Heading Title")

        # Ctrl+2 again toggles off back to normal paragraph
        self.editor.keyPressEvent(event_h2)
        self.assertEqual(self.editor.toPlainText(), "Heading Title")

    def test_markdown_blockquote_shortcut(self) -> None:
        """Verify Ctrl+Shift+Q toggles blockquote prefix (> )."""
        self.editor.setPlainText("Inspiring thought")
        cursor = self.editor.textCursor()
        cursor.setPosition(5)
        self.editor.setTextCursor(cursor)

        event_quote = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Q,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        self.editor.keyPressEvent(event_quote)
        self.assertEqual(self.editor.toPlainText(), "> Inspiring thought")

        self.editor.keyPressEvent(event_quote)
        self.assertEqual(self.editor.toPlainText(), "Inspiring thought")

    def test_markdown_list_shortcuts_without_selection(self) -> None:
        """Verify list and task shortcuts work without selection on active line."""
        self.editor.setPlainText("Item One")
        cursor = self.editor.textCursor()
        cursor.setPosition(2)
        self.editor.setTextCursor(cursor)

        # Bullet list: Ctrl+Shift+U
        event_bullet = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_U,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        self.editor.keyPressEvent(event_bullet)
        self.assertEqual(self.editor.toPlainText(), "- Item One")

        # Task checklist: Ctrl+Shift+T
        event_todo = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_T,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        self.editor.keyPressEvent(event_todo)
        self.assertEqual(self.editor.toPlainText(), "- [ ] Item One")

        # Numbered list: Ctrl+Shift+O
        event_number = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_O,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        self.editor.keyPressEvent(event_number)
        self.assertEqual(self.editor.toPlainText(), "1. Item One")

        # Toggle off
        self.editor.keyPressEvent(event_number)
        self.assertEqual(self.editor.toPlainText(), "Item One")


if __name__ == "__main__":
    unittest.main()
