"""Unit tests verifying line height, non-collapsing checkbox lines, and title clear behavior."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# Ensure offscreen Qt platform for headless CI / testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QApplication

from core.note import Note
from ui.editor import EditorPanel, MarkdownEditor


class TestLineHeightAndTitleClear(unittest.TestCase):
    """Test suite covering line height preservation and non-destructive title clearing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self) -> None:
        self.editor = MarkdownEditor()
        self.editor.resize(800, 600)
        self.editor.show()

        self.panel = EditorPanel()
        self.panel.resize(800, 600)
        self.panel.show()

    def tearDown(self) -> None:
        self.editor.close()
        self.panel.close()

    def test_empty_checkbox_line_retains_full_line_height(self) -> None:
        """Verify that an empty checkbox item (- [ ]) does not collapse to 2px."""
        self.editor.setPlainText("- [ ]\n- [ ] Second item\nRegular text line")
        self.app.processEvents()

        doc = self.editor.document()
        b1 = doc.firstBlock()
        b2 = b1.next()
        b3 = b2.next()

        rect1 = self.editor.cursorRect(QTextCursor(b1))
        rect2 = self.editor.cursorRect(QTextCursor(b2))
        rect3 = self.editor.cursorRect(QTextCursor(b3))

        # Line 1 (- [ ]) must have normal height (at least 20px, not collapsed 2px)
        self.assertGreaterEqual(
            rect1.height(),
            20,
            f"Empty checkbox line height ({rect1.height()}px) must not collapse to 2px",
        )
        # Line 2 must not be cramped against Line 1 (120% line height gives ~5-6px gap)
        vertical_gap = rect2.top() - rect1.bottom()
        self.assertGreaterEqual(
            vertical_gap,
            4,
            f"Vertical gap between lines ({vertical_gap}px) must provide comfortable line spacing",
        )
        self.assertLessEqual(
            vertical_gap,
            8,
            f"Vertical gap between lines ({vertical_gap}px) should not be overly loose",
        )

    def test_checkbox_horizontal_gap_is_natural(self) -> None:
        """Verify that the horizontal gap between checkbox box and text is natural (~16-20px)."""
        self.editor.setPlainText("- [ ] Hello world")
        self.app.processEvents()

        doc = self.editor.document()
        b = doc.firstBlock()

        c_box = QTextCursor(b)
        c_box.setPosition(b.position())
        r_box = self.editor.cursorRect(c_box)
        box_right = r_box.left() + 3 + 14.0

        c_text = QTextCursor(b)
        c_text.setPosition(b.position() + 6)
        r_text = self.editor.cursorRect(c_text)
        text_left = float(r_text.left())

        horizontal_gap = text_left - box_right
        self.assertGreaterEqual(
            horizontal_gap,
            14.0,
            f"Horizontal gap ({horizontal_gap}px) must comfortably clear the box",
        )
        self.assertLessEqual(
            horizontal_gap,
            24.0,
            f"Horizontal gap ({horizontal_gap}px) must not be overly wide",
        )

    def test_bullet_and_numbered_list_horizontal_gaps_match_checkbox(self) -> None:
        """Verify that bullet and numbered lists have matching ~18-22px horizontal margins in Live Preview."""
        self.editor.setPlainText("- Bullet item\n1. Numbered item\n")
        # Move cursor to the empty trailing line so bullet and numbered lists render in Live Preview
        cur = self.editor.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        self.editor.setTextCursor(cur)
        self.app.processEvents()

        doc = self.editor.document()
        b_bl = doc.firstBlock()
        b_num = b_bl.next()

        # Bullet gap
        r_bl = self.editor.cursorRect(QTextCursor(b_bl))
        c_bl_t = QTextCursor(b_bl)
        c_bl_t.setPosition(b_bl.position() + 2)
        r_bl_t = self.editor.cursorRect(c_bl_t)
        bullet_right = r_bl.left() + 10.0 + 3.0
        bullet_gap = r_bl_t.left() - bullet_right

        self.assertGreaterEqual(bullet_gap, 15.0, "Bullet dot must not touch text")
        self.assertLessEqual(bullet_gap, 25.0, "Bullet gap must be natural")

        # Numbered list gap
        c_num_m = QTextCursor(b_num)
        c_num_m.setPosition(b_num.position() + 2)
        r_num_m = self.editor.cursorRect(c_num_m)
        c_num_t = QTextCursor(b_num)
        c_num_t.setPosition(b_num.position() + 3)
        r_num_t = self.editor.cursorRect(c_num_t)
        num_gap = r_num_t.left() - r_num_m.left()

        self.assertGreaterEqual(num_gap, 15.0, "Numbered marker must not touch text")
        self.assertLessEqual(num_gap, 25.0, "Numbered gap must be natural")

    def test_checkboxes_on_adjacent_lines_do_not_touch(self) -> None:
        """Verify that checkboxes painted on adjacent lines have a healthy vertical gap."""
        self.editor.setPlainText("- [ ]\n- [ ] Task below")
        self.app.processEvents()

        doc = self.editor.document()
        b1 = doc.firstBlock()
        b2 = b1.next()

        r1 = self.editor.cursorRect(QTextCursor(b1))
        r2 = self.editor.cursorRect(QTextCursor(b2))

        # Checkbox geometry is drawn centered at (height - 14) / 2
        box1_top = float(r1.top()) + (r1.height() - 14.0) / 2.0
        box1_bottom = box1_top + 14.0

        box2_top = float(r2.top()) + (r2.height() - 14.0) / 2.0

        gap_between_boxes = box2_top - box1_bottom
        self.assertGreaterEqual(
            gap_between_boxes,
            12.0,
            f"Checkboxes must have at least 12px separation (got {gap_between_boxes:.1f}px)",
        )

    def test_clearing_title_does_not_forcibly_rewrite_untitled(self) -> None:
        """Verify that clearing the title input leaves it empty without auto-rewriting 'Untitled'."""
        dummy_note = Note(
            path=Path("/tmp/test_note.md"),
            title="Untitled",
            content="# Hello",
            modified_at=1000.0,
            preview_snippet="Hello",
        )
        self.panel.load_note(dummy_note)
        self.assertEqual(self.panel.title_edit.text(), "Untitled")

        # Simulate user selecting all and deleting the title
        self.panel.title_edit.setText("")
        self.panel.title_edit.textEdited.emit("")

        # Force the debounce timer to timeout and flush
        self.panel._flush_title_change()
        self.app.processEvents()

        # Input must remain empty so user can freely type their custom title
        self.assertEqual(
            self.panel.title_edit.text(),
            "",
            "Title input must stay empty after deletion, allowing the user to type",
        )
        # Placeholder text must still show 'Untitled'
        self.assertEqual(self.panel.title_edit.placeholderText(), "Untitled")

        # Fallback get_title() should still return 'Untitled' when empty
        self.assertEqual(self.panel.get_title(), "Untitled")

    def test_heading_marker_reveals_only_near_syntax(self) -> None:
        """Verify that # stays hidden when cursor is in heading text and reveals only near the prefix."""
        self.editor.setPlainText("# Hello word")
        self.app.processEvents()

        # 1. Cursor at end of heading text (pos 12) -> # must be hidden
        cur = self.editor.textCursor()
        cur.setPosition(12)
        self.editor.setTextCursor(cur)
        self.app.processEvents()

        b0 = self.editor.document().firstBlock()
        fmt_at_end = b0.layout().formats()[0].format
        self.assertEqual(fmt_at_end.fontPointSize(), 1.0, "# must be hidden when typing heading text")

        # 2. Cursor beside first letter 'H' (pos 2) -> # must be revealed in gray
        cur.setPosition(2)
        self.editor.setTextCursor(cur)
        self.app.processEvents()

        fmt_beside = b0.layout().formats()[0].format
        self.assertEqual(fmt_beside.fontPointSize(), 24.0, "# must be revealed when caret is beside prefix")

    def test_bullet_marker_reveals_only_near_syntax(self) -> None:
        """Verify that - stays hidden when cursor is in bullet text and reveals only near the prefix."""
        self.editor.setPlainText("- hello world")
        self.app.processEvents()

        # 1. Cursor at end of bullet text (pos 13) -> - must be hidden (transparent)
        cur = self.editor.textCursor()
        cur.setPosition(13)
        self.editor.setTextCursor(cur)
        self.app.processEvents()

        b0 = self.editor.document().firstBlock()
        fmt_at_end = b0.layout().formats()[0].format
        self.assertEqual(fmt_at_end.foreground().color().alpha(), 0, "- must stay hidden when typing text")

        # 2. Cursor beside first letter 'h' (pos 2) -> - must be revealed
        cur.setPosition(2)
        self.editor.setTextCursor(cur)
        self.app.processEvents()

        fmt_beside = b0.layout().formats()[0].format
        self.assertEqual(fmt_beside.foreground().color().alpha(), 255, "- must be revealed when caret is beside prefix")


if __name__ == "__main__":
    unittest.main()
