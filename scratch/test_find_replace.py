"""Comprehensive automated test for In-Note Find & Replace and Modern Dark Tooltips."""

import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QPainter, QTextCursor
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QToolTip

from core.storage import StorageManager
from ui.main_window import MainWindow
from ui.theme import DARK_THEME_QSS, apply_theme


def run_tests() -> None:
    test_dir = Path(tempfile.mkdtemp(prefix="find_replace_test_"))
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        apply_theme(app)

        window = MainWindow()
        window.resize(1100, 750)
        window.show()

        window.storage = StorageManager(root_dir=test_dir)
        window._current_folder = None
        window.config_manager.config_dir = test_dir / ".config"

        # -------------------------------------------------------------
        # 1. Test Modern Dark Tooltip Styling
        # -------------------------------------------------------------
        print("Testing Modern Tooltip QSS configuration...")
        assert "QToolTip" in DARK_THEME_QSS, "QToolTip must be configured in DARK_THEME_QSS"
        assert "background-color: #202024" in DARK_THEME_QSS
        assert "border-radius: 6px" in DARK_THEME_QSS
        print("Tooltip QSS styling: PASS")

        # -------------------------------------------------------------
        # 2. Setup Note & Editor Canvas
        # -------------------------------------------------------------
        note = window.storage.create_note()
        assert note is not None
        window._refresh_notes(preserve_path=str(note.path), emit_selection=True)
        app.processEvents()

        editor_panel = window.editor
        editor = editor_panel.editor
        find_bar = editor_panel.find_replace_bar

        sample_text = "Mathematics provides a framework. The framework describes physical systems and abstract framework models."
        editor.setPlainText(sample_text)
        app.processEvents()

        # -------------------------------------------------------------
        # 3. Test Find Bar Activation & Selection Pre-fill
        # -------------------------------------------------------------
        print("Testing Find Bar Activation (Ctrl+F) with pre-fill...")
        # Highlight "framework" (pos 23 to 32)
        c = editor.textCursor()
        c.setPosition(23)
        c.setPosition(32, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(c)
        app.processEvents()

        # Trigger Find
        editor_panel.open_find(replace_mode=False)
        app.processEvents()

        assert find_bar.isVisible(), "Find bar should be visible"
        assert not find_bar._replace_visible, "Replace row should be collapsed in find-only mode"
        assert find_bar.find_input.text() == "framework", f"Expected 'framework', got '{find_bar.find_input.text()}'"
        print("Find Bar pre-fill: PASS")

        # -------------------------------------------------------------
        # 4. Test Match Counting & ExtraSelection Highlights
        # -------------------------------------------------------------
        print("Testing Match Counting & In-Document Highlighting...")
        # "framework" appears 3 times in sample_text
        curr_idx, total = editor.find_matches("framework", match_case=False, whole_word=False)
        assert total == 3, f"Expected 3 occurrences, found {total}"
        assert curr_idx == 1, f"Expected match index 1, got {curr_idx}"
        assert len(editor.extraSelections()) == 3, f"Expected 3 ExtraSelection highlights, got {len(editor.extraSelections())}"
        assert find_bar.match_label.text() == "1 / 3"
        print("Match Counting & ExtraSelection highlights: PASS (3/3 matches highlighted)")

        # -------------------------------------------------------------
        # 5. Test Next & Previous Navigation
        # -------------------------------------------------------------
        print("Testing Next & Previous Match Navigation...")
        # Next -> 2 / 3
        curr_idx, total = editor.find_next()
        assert curr_idx == 2
        find_bar.set_match_status(curr_idx, total)
        assert find_bar.match_label.text() == "2 / 3"

        # Next -> 3 / 3
        curr_idx, total = editor.find_next()
        assert curr_idx == 3
        find_bar.set_match_status(curr_idx, total)
        assert find_bar.match_label.text() == "3 / 3"

        # Next wraps -> 1 / 3
        curr_idx, total = editor.find_next()
        assert curr_idx == 1
        find_bar.set_match_status(curr_idx, total)
        assert find_bar.match_label.text() == "1 / 3"

        # Prev wraps -> 3 / 3
        curr_idx, total = editor.find_prev()
        assert curr_idx == 3
        find_bar.set_match_status(curr_idx, total)
        assert find_bar.match_label.text() == "3 / 3"
        print("Next & Previous navigation: PASS")

        # -------------------------------------------------------------
        # 6. Test Case Sensitivity & Whole Word
        # -------------------------------------------------------------
        print("Testing Case Sensitivity and Whole Word filters...")
        editor.setPlainText("Frame framework FRAMEwork frameworking")
        app.processEvents()

        # Case-sensitive search for "FRAMEwork"
        curr_idx, total = editor.find_matches("FRAMEwork", match_case=True, whole_word=False)
        assert total == 1, f"Expected 1 case-sensitive match, got {total}"

        # Case-insensitive search for "framework"
        curr_idx, total = editor.find_matches("framework", match_case=False, whole_word=False)
        assert total == 3, f"Expected 3 matches, got {total}"

        # Whole word search for "framework" (should match 'framework' and 'FRAMEwork', not 'frameworking')
        curr_idx, total = editor.find_matches("framework", match_case=False, whole_word=True)
        assert total == 2, f"Expected 2 whole-word matches, got {total}"
        print("Case Sensitivity and Whole Word: PASS")

        # -------------------------------------------------------------
        # 7. Test Replace Mode (Ctrl+H) & Single Replacement
        # -------------------------------------------------------------
        print("Testing Replace Mode (Ctrl+H) and Single Replacement...")
        editor.setPlainText("alpha beta alpha gamma alpha")
        app.processEvents()

        editor_panel.open_find(replace_mode=True)
        app.processEvents()
        assert find_bar._replace_visible, "Replace row should be visible"
        assert find_bar.replace_widget.isVisible(), "Replace widget should be visible"

        find_bar.find_input.setText("alpha")
        find_bar.replace_input.setText("omega")
        app.processEvents()

        curr_idx, total = editor.find_matches("alpha", match_case=False, whole_word=False)
        assert total == 3

        # Replace first occurrence
        editor_panel._on_replace_current("omega")
        app.processEvents()

        assert editor.toPlainText() == "omega beta alpha gamma alpha", f"Got: {editor.toPlainText()}"
        assert len(editor._search_matches) == 2, f"Expected 2 matches remaining, got {len(editor._search_matches)}"
        print("Single Replace: PASS")

        # -------------------------------------------------------------
        # 8. Test Replace All & Single Undo Block (Ctrl+Z)
        # -------------------------------------------------------------
        print("Testing Replace All & Single Undo Block...")
        # Replace all remaining "alpha" with "delta"
        editor_panel._on_replace_all("alpha", "delta", match_case=False, whole_word=False)
        app.processEvents()

        assert editor.toPlainText() == "omega beta delta gamma delta", f"Got: {editor.toPlainText()}"
        print("Replace All: PASS")

        # Test single-step undo
        editor.undo()
        app.processEvents()
        assert editor.toPlainText() == "omega beta alpha gamma alpha", f"Undo failed, got: {editor.toPlainText()}"
        print("Atomic Undo (Ctrl+Z) for Replace All: PASS")

        # -------------------------------------------------------------
        # 9. Test Visual Capture
        # -------------------------------------------------------------
        print("Capturing Find & Replace visual screenshot...")
        editor.setPlainText("Mathematics provides a framework. The framework describes physical systems and abstract framework models.")
        editor_panel.open_find(replace_mode=True)
        find_bar.find_input.setText("framework")
        find_bar.replace_input.setText("foundation")
        app.processEvents()

        win_pix = window.grab()
        out_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_find_replace.png")
        win_pix.save(str(out_path), "PNG")
        print(f"Screenshot saved to {out_path}")

        # -------------------------------------------------------------
        # 10. Test Escape Dismissal & Cleanup
        # -------------------------------------------------------------
        print("Testing Escape Dismissal...")
        esc_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        find_bar.find_input.keyPressEvent(esc_event)
        app.processEvents()

        assert not find_bar.isVisible(), "Find bar should be hidden after Escape"
        assert len(editor.extraSelections()) == 0, "All highlights should be cleared on close"
        print("Escape dismissal and highlight cleanup: PASS")

        window.close()
        print("ALL FIND & REPLACE TESTS PASSED WITH 100% SUCCESS!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    run_tests()
