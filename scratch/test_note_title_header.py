"""Test Note Title Header feature, 'Untitled' sequence, and keyboard navigation."""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QKeyEvent, QTextCursor

from ui.main_window import MainWindow
from ui.theme import apply_theme
from core.storage import StorageManager
from core.config import ConfigManager


def run_tests():
    # Use temporary directory for testing
    test_dir = Path(tempfile.mkdtemp(prefix="note_title_test_"))
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        apply_theme(app)

        window = MainWindow()
        window.resize(1100, 700)
        window.show()

        # Point storage and config to temporary directory
        window.storage = StorageManager(root_dir=test_dir)
        window._current_folder = None
        window.config_manager.config_dir = test_dir / ".config"

        # 1. Test "+ Note" default naming sequence
        print("Testing note creation sequence...")
        note1 = window.storage.create_note()
        assert note1 is not None
        assert note1.path.name == "Untitled.md", f"Expected Untitled.md, got {note1.path.name}"
        assert note1.title == "Untitled"

        note2 = window.storage.create_note()
        assert note2 is not None
        assert note2.path.name == "Untitled 1.md", f"Expected 'Untitled 1.md', got {note2.path.name}"
        assert note2.title == "Untitled 1"

        note3 = window.storage.create_note()
        assert note3 is not None
        assert note3.path.name == "Untitled 2.md", f"Expected 'Untitled 2.md', got {note3.path.name}"
        assert note3.title == "Untitled 2"
        print("Note creation sequence: PASS (Untitled, Untitled 1, Untitled 2)")

        # 2. Test loading note into editor and title_edit display
        window._refresh_notes(preserve_path=str(note1.path), emit_selection=True)
        app.processEvents()

        assert window.editor.title_edit.text() == "Untitled"
        assert window.editor.title_edit.isEnabled()

        # 3. Test editing title renames file on disk
        print("Testing title editing & file renaming...")
        window.editor.title_edit.setText("My Project Ideas")
        window.editor._flush_title_change()
        app.processEvents()

        # Check new file path exists and old is gone
        new_path = test_dir / "My Project Ideas.md"
        assert new_path.exists(), f"File should have been renamed to {new_path}"
        assert not (test_dir / "Untitled.md").exists(), "Old Untitled.md should not exist"
        assert window._current_note.title == "My Project Ideas"
        print("Title editing & file renaming: PASS")

        # 4. Test typing in Markdown body does NOT rename the file
        print("Testing body typing does not rename file...")
        window.editor.editor.setPlainText("# Header Inside Body\n\nThis is the markdown body paragraph.")
        window.editor._trigger_auto_save()
        app.processEvents()

        assert new_path.exists(), "File should still be 'My Project Ideas.md'"
        assert window._current_note.title == "My Project Ideas", f"Title should remain 'My Project Ideas', got {window._current_note.title}"
        saved_content = new_path.read_text(encoding="utf-8")
        assert "This is the markdown body paragraph" in saved_content
        print("Body typing independence: PASS")

        # 5. Test keyboard navigation:
        # Title Edit -> Enter jumps to editor
        print("Testing keyboard navigation...")
        window.editor.title_edit.setFocus()
        app.processEvents()
        assert window.editor.title_edit.hasFocus()

        enter_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        window.editor.title_edit.keyPressEvent(enter_event)
        app.processEvents()
        assert window.editor.editor.hasFocus(), "Focus should have jumped to MarkdownEditor"
        assert window.editor.editor.textCursor().position() == 0, "Cursor should be at position 0"

        # Editor -> Up arrow at (0, 0) jumps back to Title Edit
        up_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        window.editor.editor.keyPressEvent(up_event)
        app.processEvents()
        assert window.editor.title_edit.hasFocus(), "Focus should have jumped back to NoteTitleEdit"
        print("Keyboard navigation: PASS")

        # 6. Render screenshot for visual verification
        app.processEvents()
        pixmap = window.grab()
        artifact_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_note_title_header.png")
        pixmap.save(str(artifact_path), "PNG")
        print(f"Screenshot saved to {artifact_path}")

        # Crop the editor area specifically
        editor_geom = window.editor.geometry()
        editor_pixmap = window.grab(editor_geom)
        crop_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_note_title_editor_crop.png")
        editor_pixmap.save(str(crop_path), "PNG")
        print(f"Editor crop saved to {crop_path}")

        window.close()
        print("ALL TESTS PASSED SUCCESSFULLY!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    run_tests()
