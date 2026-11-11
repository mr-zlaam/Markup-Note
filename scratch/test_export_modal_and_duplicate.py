"""Verification suite for Modern Export Dialog, Duplicate Folder Prevention, and Sidebar Chevrons."""

import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication

from core.storage import StorageManager
from ui.main_window import MainWindow
from ui.dialogs import ModernExportDialog, ModernMessageDialog
from ui.theme import apply_theme


def main() -> None:
    app = QApplication(sys.argv)
    apply_theme(app)

    temp_dir = Path(tempfile.mkdtemp(prefix="markup_notes_test_"))
    try:
        storage = StorageManager(root_dir=temp_dir)
        window = MainWindow(storage_manager=storage)
        window.resize(1100, 700)
        window.show()
        app.processEvents()

        # -------------------------------------------------------------
        # 1. Test Duplicate Folder Prevention
        # -------------------------------------------------------------
        print("1. Testing Duplicate Folder Prevention...")
        f_hero = storage.create_folder("Hero")
        assert f_hero is not None, "Hero folder should be created"
        folders = storage.get_folders()
        window.sidebar.set_folders(folders, current_selection=f_hero)
        app.processEvents()

        error_shown = False
        orig_show_error = ModernMessageDialog.show_error
        def mock_show_error(parent, title, message):
            nonlocal error_shown
            error_shown = True
            print(f"   [Intercepted Error Modal] Title: '{title}', Message: '{message}'")
        ModernMessageDialog.show_error = mock_show_error

        # Attempt to create duplicate 'Hero' at root
        window._on_create_folder("Hero", parent_folder=None)
        assert error_shown, "Creating duplicate root folder must trigger error modal!"
        print("   Duplicate root folder prevention: PASS")

        # Create subfolder inside Hero
        error_shown = False
        f_sub = storage.create_folder("ZeroSub", parent_folder=f_hero)
        assert f_sub is not None, "ZeroSub subfolder should be created"
        window.sidebar.set_folders(storage.get_folders(), current_selection=f_sub)
        app.processEvents()

        # Attempt to create duplicate 'ZeroSub' inside Hero
        window._on_create_folder("ZeroSub", parent_folder=f_hero)
        assert error_shown, "Creating duplicate subfolder must trigger error modal!"
        print("   Duplicate subfolder prevention: PASS")

        # Attempt to rename SecondSub to ZeroSub (already exists in same folder)
        f_sub2 = storage.create_folder("SecondSub", parent_folder=f_hero)
        error_shown = False
        from ui.dialogs import ModernInputDialog
        orig_get_text = ModernInputDialog.get_text
        ModernInputDialog.get_text = staticmethod(lambda parent, title, prompt, default="", confirm_text="OK": ("ZeroSub", True))
        try:
            window._on_rename_folder(f_sub2)
        finally:
            ModernInputDialog.get_text = orig_get_text

        assert error_shown, "Renaming folder to an existing sibling name must trigger error modal!"
        print("   Duplicate sibling rename prevention: PASS")

        ModernMessageDialog.show_error = orig_show_error

        # -------------------------------------------------------------
        # 2. Test Modern Export Dialog
        # -------------------------------------------------------------
        print("2. Testing Modern Export Dialog...")
        note = storage.create_note(folder=f_hero, initial_title="Information Theory & Quantum Physics")
        storage.save_note_content(note.path, "# Header\n\n- [x] Mathematics of Quantum\n- [ ] Classical Entropy\n\n```python\nprint('hello')\n```")
        window.editor.load_note(note)
        app.processEvents()

        export_dlg = ModernExportDialog(
            parent=window,
            note_title=note.title,
            markdown_content=note.content,
        )
        export_dlg.show()
        app.processEvents()

        # Verify initial state: PDF mode
        assert export_dlg._format_mode == "pdf"
        assert export_dlg.filename_input.text().endswith(".pdf")
        print("   Initial format PDF: PASS")

        # Test switching format pills
        export_dlg._set_format("html_dark")
        assert export_dlg.filename_input.text().endswith(".html")
        print("   Format switch to HTML (Dark): PASS")

        export_dlg._set_format("md")
        assert export_dlg.filename_input.text().endswith(".md")
        print("   Format switch to Markdown: PASS")

        # Test destination directory chips
        export_dlg._set_dest_dir(temp_dir)
        assert export_dlg._target_dir == temp_dir
        print("   Destination directory setting: PASS")

        # Test actual export file generation
        export_dlg._set_format("pdf")
        export_dlg._do_export()
        assert export_dlg.exported_path is not None
        assert export_dlg.exported_path.exists()
        assert export_dlg.exported_path.suffix == ".pdf"
        print(f"   Export execution: PASS ({export_dlg.exported_path.name}, {export_dlg.exported_path.stat().st_size} bytes)")

        # Capture ModernExportDialog visual
        export_dlg_capture = ModernExportDialog(
            parent=window,
            note_title=note.title,
            markdown_content=note.content,
        )
        export_dlg_capture.show()
        app.processEvents()
        modal_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_modern_export_modal.png")
        export_dlg_capture.grab().save(str(modal_path))
        print(f"   Export modal screenshot saved to {modal_path}")
        export_dlg_capture.close()

        # -------------------------------------------------------------
        # 3. Test Sidebar Tree Chevrons & Slide Animation
        # -------------------------------------------------------------
        print("3. Testing Sidebar Tree Chevrons & Slide Animation...")
        assert window.sidebar.tree_widget.isAnimated(), "Sidebar tree widget must have animation enabled!"
        print("   Tree slide animation enabled: PASS")

        window.sidebar.set_folders(storage.get_folders(), current_selection=f_hero)
        app.processEvents()

        # Find Hero item
        hero_item = None
        for i in range(window.sidebar.tree_widget.topLevelItemCount()):
            item = window.sidebar.tree_widget.topLevelItem(i)
            if item.text(0) == "Hero":
                hero_item = item
                break
        assert hero_item is not None, "Hero item should exist in sidebar tree"
        assert hero_item.childCount() >= 1, "Hero should have children"
        assert hero_item.isExpanded(), "Hero should be expanded"
        print("   Hero item has children and is expanded: PASS")

        # Capture sidebar with expanded chevron
        tree_expanded_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_sidebar_chevrons_expanded.png")
        window.sidebar.grab().save(str(tree_expanded_path))
        print(f"   Sidebar expanded screenshot saved to {tree_expanded_path}")

        # Collapse Hero and let the slide animation complete
        hero_item.setExpanded(False)
        import time
        for _ in range(35):
            app.processEvents()
            time.sleep(0.01)

        tree_collapsed_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_sidebar_chevrons_collapsed.png")
        window.sidebar.grab().save(str(tree_collapsed_path))
        print(f"   Sidebar collapsed screenshot saved to {tree_collapsed_path}")

        # Full app screenshot
        full_app_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_full_app_chevrons.png")
        window.grab().save(str(full_app_path))
        print(f"   Full application screenshot saved to {full_app_path}")

        print("\nALL VERIFICATION TESTS COMPLETED WITH 100% SUCCESS!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
