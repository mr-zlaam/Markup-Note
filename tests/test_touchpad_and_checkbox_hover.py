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


if __name__ == "__main__":
    unittest.main()
