"""Unit tests verifying touchpad vs touchscreen disambiguation and checkbox hover cursor."""

import os
import sys
import unittest
from pathlib import Path

# Ensure offscreen Qt platform for headless CI / testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import (
    QCursor,
    QGuiApplication,
    QInputDevice,
    QMouseEvent,
    QPointingDevice,
    QTextCursor,
)
from PyQt6.QtWidgets import QApplication

from ui.editor import MarkdownEditor
from utils.touch import TouchScrollTracker, is_touch_event


class TestTouchpadAndCheckboxHover(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self) -> None:
        self.editor = MarkdownEditor()
        self.editor.resize(800, 600)
        self.editor.show()

    def tearDown(self) -> None:
        self.editor.close()

    def test_touchpad_is_not_touch_event(self) -> None:
        """Verify that trackpad / touchpad pointing devices return False for is_touch_event."""
        # Create a mock touchpad pointing device
        touchpad_dev = QPointingDevice(
            "Synaptics TouchPad",
            1,
            QInputDevice.DeviceType.TouchPad,
            QPointingDevice.PointerType.Finger,
            QInputDevice.Capability.Position,
            1,
            0,
        )

        mouse_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(100.0, 100.0),
            QPointF(100.0, 100.0),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            touchpad_dev,
        )

        self.assertFalse(is_touch_event(mouse_event))

    def test_standard_mouse_is_not_touch_event(self) -> None:
        """Verify that regular mouse events return False for is_touch_event."""
        mouse_dev = QPointingDevice(
            "Logitech Mouse",
            2,
            QInputDevice.DeviceType.Mouse,
            QPointingDevice.PointerType.Generic,
            QInputDevice.Capability.Position,
            1,
            0,
        )

        mouse_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(150.0, 150.0),
            QPointF(150.0, 150.0),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            mouse_dev,
        )

        self.assertFalse(is_touch_event(mouse_event))

    def test_touchscreen_is_touch_event(self) -> None:
        """Verify that real direct touchscreens return True for is_touch_event."""
        touch_dev = QPointingDevice(
            "Wacom Touchscreen",
            3,
            QInputDevice.DeviceType.TouchScreen,
            QPointingDevice.PointerType.Finger,
            QInputDevice.Capability.Position,
            10,
            0,
        )

        touch_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(200.0, 200.0),
            QPointF(200.0, 200.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            touch_dev,
        )

        self.assertTrue(is_touch_event(touch_event))

    def test_checkbox_hover_sets_pointing_hand_cursor(self) -> None:
        """Verify that moving cursor over a checkbox changes cursor to PointingHandCursor."""
        text = "# Notes\n\n- [ ] Task to verify hover\n- [x] Completed task\n"
        self.editor.setPlainText(text)
        self.app.processEvents()

        # Find position of the first checkbox
        doc = self.editor.document()
        cb_block = doc.findBlockByNumber(2)  # Line index 2 is "- [ ] Task to verify hover"
        self.assertTrue(cb_block.isValid())

        # Determine checkbox position
        c = QTextCursor(cb_block)
        c.setPosition(cb_block.position())
        rect = self.editor.cursorRect(c)
        cb_x = float(rect.left() + 5.0)
        cb_y = float(rect.top() + rect.height() / 2.0)

        # Create mouse move event over checkbox
        touchpad_dev = QPointingDevice(
            "TouchPad",
            1,
            QInputDevice.DeviceType.TouchPad,
            QPointingDevice.PointerType.Finger,
            QInputDevice.Capability.Position,
            1,
            0,
        )
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(cb_x, cb_y),
            QPointF(cb_x, cb_y),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            touchpad_dev,
        )

        self.editor.mouseMoveEvent(move_event)
        self.assertEqual(
            self.editor.viewport().cursor().shape(),
            Qt.CursorShape.PointingHandCursor,
            "Hovering over checkbox must change cursor to PointingHandCursor",
        )

        # Move mouse away into regular text area
        away_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(cb_x + 150.0, cb_y),
            QPointF(cb_x + 150.0, cb_y),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            touchpad_dev,
        )
        self.editor.mouseMoveEvent(away_event)
        self.assertEqual(
            self.editor.viewport().cursor().shape(),
            Qt.CursorShape.IBeamCursor,
            "Moving away from checkbox must restore IBeamCursor",
        )

    def test_touchpad_press_does_not_activate_touch_tracker(self) -> None:
        """Verify that touchpad presses do not start touch kinetic scrolling."""
        touchpad_dev = QPointingDevice(
            "TouchPad",
            1,
            QInputDevice.DeviceType.TouchPad,
            QPointingDevice.PointerType.Finger,
            QInputDevice.Capability.Position,
            1,
            0,
        )
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(100.0, 100.0),
            QPointF(100.0, 100.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            touchpad_dev,
        )

        self.editor.mousePressEvent(press_event)
        self.assertFalse(self.editor._touch_tracker.is_active)

    def test_selection_format_bold_preserves_checkbox_prefix(self) -> None:
        """Verify that bolding a checkbox line wraps only the content, never the - [ ] prefix."""
        self.editor.setPlainText("- [ ] Buy groceries")
        c = self.editor.textCursor()
        c.select(QTextCursor.SelectionType.BlockUnderCursor)
        self.editor.setTextCursor(c)

        self.editor._apply_text_format("bold")
        self.assertEqual(self.editor.toPlainText().strip(), "- [ ] **Buy groceries**")

    def test_selection_format_todo_converts_line_to_checkbox(self) -> None:
        """Verify that applying todo/checkbox format transforms the whole line into a checkbox."""
        self.editor.setPlainText("Prepare presentation slides")
        c = self.editor.textCursor()
        c.setPosition(0)
        c.setPosition(7, QTextCursor.MoveMode.KeepAnchor)  # Select "Prepare"
        self.editor.setTextCursor(c)

        self.editor._apply_text_format("todo")
        self.assertEqual(self.editor.toPlainText().strip(), "- [ ] Prepare presentation slides")

        # Toggling again should convert back to plain text
        self.editor._apply_text_format("todo")
        self.assertEqual(self.editor.toPlainText().strip(), "Prepare presentation slides")

    def test_heading_sizes_reduced_by_one_step(self) -> None:
        """Verify that heading sizes are dropped by 1 step for sleek proportional layout."""
        from ui.highlighter import MarkdownHighlighter

        self.assertEqual(MarkdownHighlighter.HEADING_SIZES[1], 24)
        self.assertEqual(MarkdownHighlighter.HEADING_SIZES[2], 20)
        self.assertEqual(MarkdownHighlighter.HEADING_SIZES[3], 18)
        self.assertEqual(MarkdownHighlighter.HEADING_SIZES[4], 16)
        self.assertEqual(MarkdownHighlighter.HEADING_SIZES[5], 15)
        self.assertEqual(MarkdownHighlighter.HEADING_SIZES[6], 14)

    def test_slash_checkbox_on_existing_checkbox_line_ignored(self) -> None:
        """Verify selecting /checkbox on a line that is already a checkbox ignores duplicate insertion."""
        from ui.slash_menu import COMMANDS
        cmd = [c for c in COMMANDS if c.id == "checkbox"][0]

        # Case 1: Empty checkbox line with /checkbox
        self.editor.setPlainText("- [ ] /checkbox")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd)
        self.assertEqual(self.editor.toPlainText().strip(), "- [ ]")

        # Case 2: Checkbox line with text and /checkbox
        self.editor.setPlainText("- [ ] Buy milk /checkbox")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd)
        self.assertEqual(self.editor.toPlainText().strip(), "- [ ] Buy milk")

        # Case 3: Checked checkbox line with /check
        self.editor.setPlainText("- [x] Done item /check")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd)
        self.assertEqual(self.editor.toPlainText().strip(), "- [x] Done item")

    def test_slash_checkbox_on_plain_line_inserts_checkbox(self) -> None:
        """Verify selecting /checkbox on a non-checkbox line inserts the markdown checkbox prefix."""
        from ui.slash_menu import COMMANDS
        cmd = [c for c in COMMANDS if c.id == "checkbox"][0]

        self.editor.setPlainText("/checkbox")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd)
        self.assertEqual(self.editor.toPlainText().strip(), "- [ ]")

    def test_slash_command_transforms_line_between_list_types(self) -> None:
        """Verify slash commands transform the current line to the selected block format."""
        from ui.slash_menu import COMMANDS
        cmd_bullet = [c for c in COMMANDS if c.id == "bullet"][0]
        cmd_number = [c for c in COMMANDS if c.id == "number"][0]
        cmd_checkbox = [c for c in COMMANDS if c.id == "checkbox"][0]
        cmd_h1 = [c for c in COMMANDS if c.id == "h1"][0]
        cmd_quote = [c for c in COMMANDS if c.id == "quote"][0]

        # 1. Transform checkbox to bullet
        self.editor.setPlainText("- [ ] Buy milk /bullet")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd_bullet)
        self.assertEqual(self.editor.toPlainText().strip(), "- Buy milk")

        # 2. Transform bullet to number list
        self.editor.setPlainText("- Buy milk /number")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd_number)
        self.assertEqual(self.editor.toPlainText().strip(), "1. Buy milk")

        # 3. Transform number list to checkbox
        self.editor.setPlainText("1. Buy milk /checkbox")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd_checkbox)
        self.assertEqual(self.editor.toPlainText().strip(), "- [ ] Buy milk")

        # 4. Transform heading level
        self.editor.setPlainText("## Section Title /h1")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd_h1)
        self.assertEqual(self.editor.toPlainText().strip(), "# Section Title")

        # 5. Transform bullet to quote
        self.editor.setPlainText("- Quoted note /quote")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd_quote)
        self.assertEqual(self.editor.toPlainText().strip(), "> Quoted note")

        # 6. Transform empty checkbox to bullet
        self.editor.setPlainText("- [ ] /bullet")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd_bullet)
        self.assertEqual(self.editor.toPlainText().strip(), "-")

        # 7. Transform empty bullet to checkbox
        self.editor.setPlainText("- /checkbox")
        c = self.editor.textCursor()
        c.setPosition(len(self.editor.toPlainText()))
        self.editor.setTextCursor(c)
        self.editor._on_slash_command_selected(cmd_checkbox)
        self.assertEqual(self.editor.toPlainText().strip(), "- [ ]")

    def test_slash_command_with_slash_start_pos_populated(self) -> None:
        """Verify slash command execution when _slash_start_pos is populated (regression test for b_text UnboundLocalError)."""
        from ui.slash_menu import COMMANDS
        cmd_bullet = [c for c in COMMANDS if c.id == "bullet"][0]

        text = "- [ ] Features: Add icons for all small modals like rename, select delete /bul"
        self.editor.setPlainText(text)
        slash_idx = text.rfind("/")
        # _slash_start_pos is the index immediately following '/'
        self.editor._slash_start_pos = slash_idx + 1

        c = self.editor.textCursor()
        c.setPosition(len(text))
        self.editor.setTextCursor(c)

        # Must not raise UnboundLocalError: b_text
        self.editor._on_slash_command_selected(cmd_bullet)
        self.assertEqual(
            self.editor.toPlainText().strip(),
            "- Features: Add icons for all small modals like rename, select delete",
        )
        self.assertEqual(self.editor.textCursor().position(), len(self.editor.toPlainText()))

    def test_slash_command_mid_line_with_slash_start_pos(self) -> None:
        """Verify mid-line slash command transforms the line prefix and positions cursor correctly."""
        from ui.slash_menu import COMMANDS
        cmd_bullet = [c for c in COMMANDS if c.id == "bullet"][0]

        prefix = "Features: "
        query = "/bul"
        suffix = " more items"
        full_text = prefix + query + suffix
        self.editor.setPlainText(full_text)

        slash_idx = prefix.find("/") if "/" in prefix else len(prefix)
        self.editor._slash_start_pos = slash_idx + 1

        c = self.editor.textCursor()
        c.setPosition(slash_idx + len(query))
        self.editor.setTextCursor(c)

        self.editor._on_slash_command_selected(cmd_bullet)
        self.assertEqual(
            self.editor.toPlainText().strip(),
            "- Features: more items",
        )

    def test_checked_task_dimming_with_inline_formatting(self) -> None:
        """Verify that completed checkbox tasks dim all inline formatting (bold, italic, underline, code)."""
        from PyQt6.QtGui import QFont

        # 1. Checked checkbox with bold, italic, underline, and code
        self.editor.setPlainText("- [x] Done **bold** and *italic* and <u>underline</u> and `code`")
        self.app.processEvents()

        block = self.editor.document().firstBlock()
        ranges = block.layout().formats()

        slice_map = {}
        for r in ranges:
            text_slice = block.text()[r.start : r.start + r.length]
            slice_map[text_slice] = r.format

        dim_color = "#787880"
        self.assertIn("bold", slice_map)
        self.assertEqual(slice_map["bold"].fontWeight(), QFont.Weight.Bold)
        self.assertEqual(slice_map["bold"].foreground().color().name(), dim_color)

        self.assertIn("italic", slice_map)
        self.assertTrue(slice_map["italic"].fontItalic())
        self.assertEqual(slice_map["italic"].foreground().color().name(), dim_color)

        self.assertIn("underline", slice_map)
        self.assertTrue(slice_map["underline"].fontUnderline())
        self.assertEqual(slice_map["underline"].foreground().color().name(), dim_color)

        self.assertIn("code", slice_map)
        self.assertEqual(slice_map["code"].foreground().color().name(), dim_color)

        # 2. Unchecked checkbox retains bright formatting colors
        self.editor.setPlainText("- [ ] Todo **bold** and *italic* and <u>underline</u>")
        self.app.processEvents()

        block_uncheck = self.editor.document().firstBlock()
        ranges_uncheck = block_uncheck.layout().formats()

        slice_map_uncheck = {}
        for r in ranges_uncheck:
            text_slice = block_uncheck.text()[r.start : r.start + r.length]
            slice_map_uncheck[text_slice] = r.format

        self.assertIn("bold", slice_map_uncheck)
        self.assertEqual(slice_map_uncheck["bold"].fontWeight(), QFont.Weight.Bold)
        self.assertEqual(slice_map_uncheck["bold"].foreground().color().name(), "#ffffff")

        self.assertIn("italic", slice_map_uncheck)
        self.assertTrue(slice_map_uncheck["italic"].fontItalic())
        self.assertEqual(slice_map_uncheck["italic"].foreground().color().name(), "#dcdcdc")

    def test_checkbox_toggle_zero_layout_shift(self) -> None:
        """Verify that checking and unchecking a checkbox does not shift the text or checkbox position."""
        self.editor.setPlainText("- [ ] Layout stability test task")
        self.app.processEvents()

        block = self.editor.document().firstBlock()
        cursor_text = self.editor.textCursor()
        cursor_text.setPosition(6)  # Start of task text after '- [ ] '
        rect_text_uncheck = self.editor.cursorRect(cursor_text)

        cursor_cb = self.editor.textCursor()
        cursor_cb.setPosition(0)
        rect_cb_uncheck = self.editor.cursorRect(cursor_cb)

        # Toggle to checked
        self.editor._toggle_checkbox_at_block(block)
        self.app.processEvents()

        block_after = self.editor.document().firstBlock()
        cursor_text.setPosition(6)  # Start of task text after '- [x] '
        rect_text_check = self.editor.cursorRect(cursor_text)

        cursor_cb.setPosition(0)
        rect_cb_check = self.editor.cursorRect(cursor_cb)

        # Verify zero shift in both text starting point and checkbox origin
        self.assertEqual(rect_text_uncheck.x(), rect_text_check.x())
        self.assertEqual(rect_text_uncheck.y(), rect_text_check.y())
        self.assertEqual(rect_cb_uncheck.x(), rect_cb_check.x())
        self.assertEqual(rect_cb_uncheck.y(), rect_cb_check.y())


if __name__ == "__main__":
    unittest.main()
