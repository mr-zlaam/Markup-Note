"""Automated and visual test for Notion-style Slash Command Palette."""

import sys
import tempfile
import shutil
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QKeyEvent

from ui.main_window import MainWindow
from ui.theme import apply_theme
from core.storage import StorageManager


def run_tests():
    test_dir = Path(tempfile.mkdtemp(prefix="slash_menu_test_"))
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        apply_theme(app)

        window = MainWindow()
        window.resize(1100, 750)
        window.show()

        window.storage = StorageManager(root_dir=test_dir)
        window._current_folder = None
        window.config_manager.config_dir = test_dir / ".config"

        # Create a note
        note = window.storage.create_note()
        assert note is not None
        window._refresh_notes(preserve_path=str(note.path), emit_selection=True)
        app.processEvents()

        editor = window.editor.editor
        editor.setFocus()
        editor.setPlainText("")
        app.processEvents()

        # 1. Test typing '/' triggers the slash palette
        print("Testing '/' trigger...")
        slash_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Slash, Qt.KeyboardModifier.NoModifier, "/")
        editor.keyPressEvent(slash_event)
        app.processEvents()

        assert editor.slash_palette.isVisible(), "Slash palette should be visible after typing '/'"
        assert editor.toPlainText() == "/", f"Document should contain '/', got: {repr(editor.toPlainText())}"
        print("Slash trigger: PASS")

        # Capture screenshot of slash menu open
        app.processEvents()
        window_pixmap = window.grab()
        artifact_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_slash_palette_open.png")
        window_pixmap.save(str(artifact_path), "PNG")
        print(f"Screenshot saved to {artifact_path}")

        # 2. Test typing 'checkbox' or 'check' filters the palette to To-do list
        print("Testing filter query 'checkbox'...")
        for ch in "checkbox":
            key_code = getattr(Qt.Key, f"Key_{ch.upper()}")
            char_event = QKeyEvent(QKeyEvent.Type.KeyPress, key_code, Qt.KeyboardModifier.NoModifier, ch)
            editor.keyPressEvent(char_event)
            app.processEvents()

        assert editor.toPlainText() == "/checkbox", f"Document text should be '/checkbox', got: {repr(editor.toPlainText())}"
        assert editor.slash_palette.isVisible(), "Slash palette should still be visible while filtering"
        current_cmd = editor.slash_palette.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        assert current_cmd is not None
        assert current_cmd.id == "checkbox", f"Expected 'checkbox' command selected, got {current_cmd.id}"
        assert current_cmd.title == "Checkbox", f"Expected title 'Checkbox', got {current_cmd.title}"
        print("Filter query: PASS ('checkbox' selected for '/checkbox')")

        # 3. Test pressing Enter executes command and replaces '/checkbox' with '- [ ] '
        print("Testing Enter execution...")
        enter_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        editor.keyPressEvent(enter_event)
        app.processEvents()

        assert not editor.slash_palette.isVisible(), "Slash palette should be hidden after Enter"
        assert editor.toPlainText() == "- [ ] ", f"Expected '- [ ] ', got: {repr(editor.toPlainText())}"
        assert editor.textCursor().position() == len("- [ ] "), "Cursor should be positioned right after prefix"
        print("Enter execution: PASS ('- [ ] ' inserted)")

        # 4. Type task description and press Enter -> checklist auto-continues
        print("Testing checklist typing and auto-continuation...")
        for ch in "Buy groceries":
            key_code = getattr(Qt.Key, f"Key_{ch.upper()}", Qt.Key.Key_Space if ch == ' ' else Qt.Key.Key_A)
            char_event = QKeyEvent(QKeyEvent.Type.KeyPress, key_code, Qt.KeyboardModifier.NoModifier, ch)
            editor.keyPressEvent(char_event)
            app.processEvents()

        assert editor.toPlainText() == "- [ ] Buy groceries"

        # Press Enter to continue checklist
        enter_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        editor.keyPressEvent(enter_event)
        app.processEvents()

        expected = "- [ ] Buy groceries\n- [ ] "
        assert editor.toPlainText() == expected, f"Expected {repr(expected)}, got: {repr(editor.toPlainText())}"
        print("Checklist continuation: PASS")

        # 5. Test '/bullet'
        # One backspace clears the empty '- [ ] ' prefix, leaving a blank line
        bs_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
        editor.keyPressEvent(bs_event)
        app.processEvents()

        # Type '/bullet'
        slash_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Slash, Qt.KeyboardModifier.NoModifier, "/")
        editor.keyPressEvent(slash_event)
        for ch in "bullet":
            key_code = getattr(Qt.Key, f"Key_{ch.upper()}")
            char_event = QKeyEvent(QKeyEvent.Type.KeyPress, key_code, Qt.KeyboardModifier.NoModifier, ch)
            editor.keyPressEvent(char_event)
            app.processEvents()

        current_cmd = editor.slash_palette.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        assert current_cmd.id == "bullet"
        editor.keyPressEvent(enter_event)
        app.processEvents()

        assert editor.toPlainText().endswith("- "), f"Expected line to end with '- ', got: {repr(editor.toPlainText())}"
        print("Bulleted list slash command: PASS")

        # 6. Test Escape closes palette
        slash_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Slash, Qt.KeyboardModifier.NoModifier, "/")
        editor.keyPressEvent(slash_event)
        app.processEvents()
        assert editor.slash_palette.isVisible()

        esc_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        editor.keyPressEvent(esc_event)
        app.processEvents()
        assert not editor.slash_palette.isVisible(), "Escape should close the palette"
        print("Escape dismissal: PASS")

        # Take final screenshot of rendered note
        app.processEvents()
        final_pixmap = window.grab()
        final_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_slash_result.png")
        final_pixmap.save(str(final_path), "PNG")
        print(f"Final screenshot saved to {final_path}")

        window.close()
        print("ALL SLASH MENU TESTS PASSED PERFECTLY!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    run_tests()
