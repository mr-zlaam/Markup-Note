"""Tests for the floating Find & Replace overlay bar in EditorPanel."""

import unittest
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout

from ui.editor import EditorPanel

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestFindOverlay(unittest.TestCase):
    """Test suite for floating Find & Replace bar positioning, responsiveness, and zero layout shift."""

    def _create_panel(self, width: int = 800, height: int = 600) -> tuple[QWidget, EditorPanel]:
        win = QWidget()
        win.setFixedSize(width, height)
        layout = QVBoxLayout(win)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = EditorPanel(parent=win)
        layout.addWidget(panel)
        win.show()
        if app is not None:
            app.processEvents()
        return win, panel

    def test_zero_layout_shift_on_open_and_close(self) -> None:
        """Verify opening and closing find bar does not shift editor canvas or title positions."""
        win, panel = self._create_panel(800, 600)
        try:
            editor_geom_before = panel.editor.geometry()
            title_geom_before = panel.title_edit.geometry()

            # Open Find
            panel.open_find(replace_mode=False)
            if app is not None:
                app.processEvents()

            editor_geom_open = panel.editor.geometry()
            title_geom_open = panel.title_edit.geometry()

            self.assertEqual(editor_geom_before, editor_geom_open)
            self.assertEqual(title_geom_before, title_geom_open)
            self.assertTrue(panel.find_replace_bar.isVisible())

            # Close Find
            panel.close_find()
            if app is not None:
                app.processEvents()

            editor_geom_closed = panel.editor.geometry()
            title_geom_closed = panel.title_edit.geometry()

            self.assertEqual(editor_geom_before, editor_geom_closed)
            self.assertEqual(title_geom_before, title_geom_closed)
            self.assertFalse(panel.find_replace_bar.isVisible())
        finally:
            win.close()
            win.deleteLater()
            if app is not None:
                app.processEvents()

    def test_floating_overlay_position_below_header(self) -> None:
        """Verify the overlay is positioned directly below the top-right header."""
        win, panel = self._create_panel(800, 600)
        try:
            panel.open_find(replace_mode=False)
            if app is not None:
                app.processEvents()

            bar_geom = panel.find_replace_bar.geometry()
            # Top position should be just below the header bar (~39-42px)
            self.assertGreaterEqual(bar_geom.y(), 36)
            self.assertLessEqual(bar_geom.y(), 46)

            # Right edge should be 16px from the right boundary
            expected_right = panel.width() - 16
            actual_right = bar_geom.x() + bar_geom.width()
            self.assertEqual(actual_right, expected_right)
        finally:
            win.close()
            win.deleteLater()
            if app is not None:
                app.processEvents()

    def test_responsive_width_on_wide_screen(self) -> None:
        """Verify bar width caps at 400px on wider screens and adapts responsively."""
        win, panel = self._create_panel(1400, 800)
        try:
            panel.open_find(replace_mode=False)
            if app is not None:
                app.processEvents()

            bar_geom = panel.find_replace_bar.geometry()
            self.assertEqual(bar_geom.width(), 400)
            self.assertEqual(bar_geom.x() + bar_geom.width(), 1400 - 16)
        finally:
            win.close()
            win.deleteLater()
            if app is not None:
                app.processEvents()

    def test_responsive_width_on_narrow_screen(self) -> None:
        """Verify bar width scales down on narrower screens without overflowing."""
        win, panel = self._create_panel(500, 600)
        try:
            panel.open_find(replace_mode=False)
            if app is not None:
                app.processEvents()

            bar_geom = panel.find_replace_bar.geometry()
            self.assertLessEqual(bar_geom.width(), 500 - 32)
            self.assertEqual(bar_geom.x() + bar_geom.width(), 500 - 16)
        finally:
            win.close()
            win.deleteLater()
            if app is not None:
                app.processEvents()

    def test_replace_toggle_height_expansion(self) -> None:
        """Verify toggling replace row adjusts height while maintaining position."""
        win, panel = self._create_panel(800, 600)
        try:
            panel.open_find(replace_mode=False)
            if app is not None:
                app.processEvents()

            initial_height = panel.find_replace_bar.geometry().height()
            self.assertLess(initial_height, 50)

            # Expand Replace row
            panel.find_replace_bar.toggle_replace_row()
            if app is not None:
                app.processEvents()

            expanded_height = panel.find_replace_bar.geometry().height()
            self.assertGreater(expanded_height, 70)

            # Collapse Replace row
            panel.find_replace_bar.toggle_replace_row()
            if app is not None:
                app.processEvents()

            collapsed_height = panel.find_replace_bar.geometry().height()
            self.assertEqual(collapsed_height, initial_height)
        finally:
            win.close()
            win.deleteLater()
            if app is not None:
                app.processEvents()


if __name__ == "__main__":
    unittest.main()
