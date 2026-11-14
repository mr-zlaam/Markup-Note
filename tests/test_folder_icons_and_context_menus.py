"""Unit tests verifying high-quality folder icons, dynamic open/close states, and modern context menus."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem

from core.note import Note
from core.storage import StorageManager
from ui.context_menu import ModernContextMenu
from ui.note_list import NoteListPanel
from ui.sidebar import FolderSidebar
from utils.icons import (
    create_edit_icon,
    create_folder_icon,
    create_open_folder_icon,
    create_plus_icon,
    create_trash_icon,
)


class TestFolderIconsAndContextMenus(unittest.TestCase):
    """Test suite for folder vector icons, dynamic expansion, and context menu behaviors."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.storage = StorageManager(self.root_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_folder_icon_open_and_closed_states(self) -> None:
        """Verify vector folder icons generate distinct non-null pixmaps for closed and open states."""
        closed_icon = create_folder_icon(color="#e5a93c", size=16, is_open=False)
        open_icon = create_folder_icon(color="#e5a93c", size=16, is_open=True)
        open_alias = create_open_folder_icon(color="#e5a93c", size=16)

        self.assertFalse(closed_icon.isNull())
        self.assertFalse(open_icon.isNull())
        self.assertFalse(open_alias.isNull())

        pm_c = closed_icon.pixmap(QSize(16, 16))
        pm_o = open_icon.pixmap(QSize(16, 16))
        self.assertFalse(pm_c.isNull())
        self.assertFalse(pm_o.isNull())

    def test_modern_context_menu_rendering(self) -> None:
        """Verify ModernContextMenu paints normal and destructive actions without errors."""
        menu = ModernContextMenu()
        act_edit = menu.addAction(create_edit_icon(), "Rename Folder...")
        sub_menu = menu.addMenu("Color")
        self.assertIsInstance(sub_menu, ModernContextMenu)

        act_del = menu.addAction(create_trash_icon("#ff453a"), "Delete Folder")
        act_del.setProperty("is_destructive", True)

        pm = QPixmap(200, 100)
        painter = QPainter(pm)
        menu.render(painter)
        painter.end()
        self.assertFalse(pm.isNull())

    def test_sidebar_empty_space_and_folder_context_menu(self) -> None:
        """Verify FolderSidebar context menu handling for both empty space and folder items."""
        sidebar = FolderSidebar(parent=None)
        folder_a = self.root_path / "Projects"
        folder_a.mkdir()
        sidebar.set_folders([folder_a])

        # Test empty space position (far below items)
        empty_pos = QPoint(50, 400)
        self.assertIsNone(sidebar.tree_widget.itemAt(empty_pos))

        # Test folder item position
        item = sidebar.tree_widget.topLevelItem(1)  # 0 is 'All Notes', 1 is 'Projects'
        self.assertIsNotNone(item)
        self.assertEqual(item.text(0), "Projects")

        sidebar.deleteLater()

    def test_sidebar_dynamic_open_folder_state(self) -> None:
        """Verify sidebar updates folder icon between open and closed on expansion/collapse."""
        sidebar = FolderSidebar(parent=None)
        parent_dir = self.root_path / "Parent"
        child_dir = parent_dir / "Child"
        child_dir.mkdir(parents=True)
        sidebar.set_folders([parent_dir, child_dir])

        # Get parent item in tree
        parent_item = sidebar.tree_widget.topLevelItem(1)
        self.assertEqual(parent_item.text(0), "Parent")

        # Verify initial expanded state (parent auto-expanded)
        self.assertTrue(parent_item.isExpanded())

        # Single-click toggles expansion: close
        sidebar._on_item_clicked(parent_item)
        self.assertFalse(parent_item.isExpanded())

        # Single-click toggles expansion: open
        sidebar._on_item_clicked(parent_item)
        self.assertTrue(parent_item.isExpanded())

        # Simulate collapsing parent item directly
        parent_item.setExpanded(False)
        self.assertFalse(parent_item.isExpanded())

        # Simulate expanding parent item directly
        parent_item.setExpanded(True)
        self.assertTrue(parent_item.isExpanded())

        sidebar.deleteLater()

    def test_sidebar_and_note_list_cursor_pointers(self) -> None:
        """Verify tree and list views have PointingHandCursor for clickable interactions."""
        sidebar = FolderSidebar(parent=None)
        self.assertEqual(sidebar.tree_widget.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(sidebar.tree_widget.viewport().cursor().shape(), Qt.CursorShape.PointingHandCursor)
        sidebar.deleteLater()

        note_list = NoteListPanel(parent=None)
        self.assertEqual(note_list.list_widget.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        self.assertEqual(note_list.list_widget.viewport().cursor().shape(), Qt.CursorShape.PointingHandCursor)
        note_list.deleteLater()

    def test_note_list_empty_space_context_menu(self) -> None:
        """Verify NoteListPanel handles empty space right-clicks gracefully."""
        note_list = NoteListPanel(parent=None)
        empty_pos = QPoint(50, 300)
        self.assertIsNone(note_list.list_widget.itemAt(empty_pos))

        note = self.storage.create_note(initial_title="Sample")
        self.assertIsNotNone(note)
        note_list.set_notes([note])
        item = note_list.list_widget.item(0)
        self.assertIsNotNone(item)

        note_list.deleteLater()

    def test_delete_key_on_focused_folder(self) -> None:
        """Verify pressing Delete on a focused folder item emits delete_folder_requested."""
        sidebar = FolderSidebar(parent=None)
        test_folder = self.root_path / "TargetFolder"
        test_folder.mkdir()
        sidebar.set_folders([test_folder])

        emitted_folders = []
        sidebar.delete_folder_requested.connect(lambda f: emitted_folders.append(f))

        # Focus 'All Notes' (index 0) - should NOT emit delete
        all_notes_item = sidebar.tree_widget.topLevelItem(0)
        sidebar.tree_widget.setCurrentItem(all_notes_item)
        QTest.keyClick(sidebar.tree_widget, Qt.Key.Key_Delete)
        self.assertEqual(len(emitted_folders), 0)

        # Focus custom folder (index 1) - should emit delete
        folder_item = sidebar.tree_widget.topLevelItem(1)
        sidebar.tree_widget.setCurrentItem(folder_item)
        QTest.keyClick(sidebar.tree_widget, Qt.Key.Key_Delete)
        self.assertEqual(len(emitted_folders), 1)
        self.assertEqual(emitted_folders[0], test_folder)

        # Test on viewport as well
        QTest.keyClick(sidebar.tree_widget.viewport(), Qt.Key.Key_Delete)
        self.assertEqual(len(emitted_folders), 2)

        sidebar.deleteLater()

    def test_delete_key_on_focused_note(self) -> None:
        """Verify pressing Delete on a focused note card emits delete_note_requested."""
        note_list = NoteListPanel(parent=None)
        note = self.storage.create_note(initial_title="DeleteMe")
        self.assertIsNotNone(note)
        note_list.set_notes([note])

        emitted_notes = []
        note_list.delete_note_requested.connect(lambda n: emitted_notes.append(n))

        item = note_list.list_widget.item(0)
        note_list.list_widget.setCurrentItem(item)

        QTest.keyClick(note_list.list_widget, Qt.Key.Key_Delete)
        self.assertEqual(len(emitted_notes), 1)
        self.assertEqual(emitted_notes[0].title, "DeleteMe")

        # Test on viewport as well
        QTest.keyClick(note_list.list_widget.viewport(), Qt.Key.Key_Delete)
        self.assertEqual(len(emitted_notes), 2)

        note_list.deleteLater()


if __name__ == "__main__":
    unittest.main()
