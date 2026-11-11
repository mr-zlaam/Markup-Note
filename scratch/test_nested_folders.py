"""Automated test for Nested Subfolder Hierarchy in Markup Notes."""

import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from core.storage import StorageManager
from ui.main_window import MainWindow
from ui.theme import apply_theme


def run_tests() -> None:
    test_dir = Path(tempfile.mkdtemp(prefix="nested_test_"))
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        apply_theme(app)

        window = MainWindow()
        window.resize(1100, 750)
        window.show()

        window.storage = StorageManager(root_dir=test_dir)
        window._current_folder = None
        window.config_manager.config_dir = test_dir / ".config"

        storage = window.storage
        sidebar = window.sidebar

        # -------------------------------------------------------------
        # 1. Test Folder and Subfolder Creation
        # -------------------------------------------------------------
        print("Testing Subfolder Creation at multiple depths...")
        work_folder = storage.create_folder("Work")
        assert work_folder is not None and work_folder.exists()

        projects_folder = storage.create_folder("Projects", parent_folder=work_folder)
        assert projects_folder is not None and projects_folder.exists()
        assert projects_folder == work_folder / "Projects"

        app_folder = storage.create_folder("Markup-Notes", parent_folder=projects_folder)
        assert app_folder is not None and app_folder.exists()
        assert app_folder == projects_folder / "Markup-Notes"

        personal_folder = storage.create_folder("Personal")
        assert personal_folder is not None and personal_folder.exists()

        folders = storage.get_folders()
        assert len(folders) == 4, f"Expected 4 folders, found {len(folders)}"
        rel_paths = [str(f.relative_to(test_dir)) for f in folders]
        assert "Work" in rel_paths
        assert "Work/Projects" in rel_paths
        assert "Work/Projects/Markup-Notes" in rel_paths
        assert "Personal" in rel_paths
        print("Folder and Subfolder creation: PASS")

        # -------------------------------------------------------------
        # 2. Test Note Creation in Nested Folders & Recursive Retrieval
        # -------------------------------------------------------------
        print("Testing Note Creation inside Nested Folders...")
        n_deep = storage.create_note(folder=app_folder, initial_title="Architecture Spec")
        assert n_deep is not None and n_deep.path.exists()
        assert n_deep.path.parent == app_folder

        n_work = storage.create_note(folder=work_folder, initial_title="Quarterly Roadmap")
        assert n_work is not None and n_work.path.parent == work_folder

        n_personal = storage.create_note(folder=personal_folder, initial_title="Book Recommendations")
        assert n_personal is not None and n_personal.path.parent == personal_folder

        # Test recursive list_notes(None)
        all_notes = storage.list_notes(None)
        assert len(all_notes) == 3, f"Expected 3 total notes across all folders, got {len(all_notes)}"

        # Test folder-specific list_notes
        app_notes = storage.list_notes(app_folder)
        assert len(app_notes) == 1
        assert app_notes[0].title == "Architecture Spec"
        print("Note creation and recursive listing: PASS")

        # -------------------------------------------------------------
        # 3. Test Sidebar Tree Rendering & Parent-Child Expansion
        # -------------------------------------------------------------
        print("Testing Sidebar Tree Widget hierarchy...")
        sidebar.set_folders(folders, current_selection=app_folder)
        app.processEvents()

        tree = sidebar.tree_widget
        # Top-level items: "All Notes", "Personal", "Work"
        assert tree.topLevelItemCount() == 3, f"Expected 3 top-level items, got {tree.topLevelItemCount()}"

        all_notes_item = tree.topLevelItem(0)
        assert all_notes_item.text(0) == "All Notes"

        # Find "Work" item
        work_item = None
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            if item.text(0) == "Work":
                work_item = item
                break
        assert work_item is not None, "Work item must exist in tree"
        assert work_item.childCount() == 1, f"Work item should have 1 child (Projects), got {work_item.childCount()}"
        assert work_item.isExpanded(), "Work item should be expanded"

        projects_item = work_item.child(0)
        assert projects_item.text(0) == "Projects"
        assert projects_item.childCount() == 1, f"Projects item should have 1 child (Markup-Notes), got {projects_item.childCount()}"
        assert projects_item.isExpanded(), "Projects item should be expanded"

        app_item = projects_item.child(0)
        assert app_item.text(0) == "Markup-Notes"
        print("Sidebar Tree hierarchy and automatic expansion: PASS")

        # -------------------------------------------------------------
        # 4. Test Subfolder Renaming Preserves Hierarchy
        # -------------------------------------------------------------
        print("Testing Subfolder Renaming...")
        renamed_folder = storage.rename_folder(projects_folder, "Active-Projects")
        assert renamed_folder is not None
        assert renamed_folder == work_folder / "Active-Projects", f"Expected inside Work, got {renamed_folder}"
        assert renamed_folder.exists()
        assert (renamed_folder / "Markup-Notes").exists(), "Child folder should still exist inside renamed parent"
        print("Subfolder renaming: PASS")

        # -------------------------------------------------------------
        # 5. Visual Capture
        # -------------------------------------------------------------
        print("Capturing Sidebar Tree with nested subfolders...")
        updated_folders = storage.get_folders()
        sidebar.set_folders(updated_folders, current_selection=renamed_folder / "Markup-Notes")
        app.processEvents()

        win_pix = window.grab()
        out_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_nested_folders.png")
        win_pix.save(str(out_path), "PNG")
        print(f"Screenshot saved to {out_path}")

        window.close()
        print("ALL NESTED SUBFOLDER TESTS PASSED WITH 100% SUCCESS!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    run_tests()
