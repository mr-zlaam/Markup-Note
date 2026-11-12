"""Unit and integration tests for Markdown file opening, validation, and error handling."""

import os
import sys
import tempfile
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.file_validator import validate_markdown_file


def test_file_validator() -> None:
    """Test validation logic against valid and invalid file formats."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Valid markdown file
        valid_md = tmp_path / "valid_note.md"
        valid_md.write_text("# Hello World\n\nThis is a test note.", encoding="utf-8")
        is_valid, err_title, err_msg = validate_markdown_file(valid_md)
        assert is_valid is True, f"Expected valid, got: {err_title}: {err_msg}"
        assert err_title is None

        # 2. Valid plain text file
        valid_txt = tmp_path / "valid_note.txt"
        valid_txt.write_text("Plain text content here.", encoding="utf-8")
        is_valid, err_title, err_msg = validate_markdown_file(valid_txt)
        assert is_valid is True, f"Expected valid, got: {err_title}: {err_msg}"

        # 3. Valid directory
        sub_dir = tmp_path / "sub_notes"
        sub_dir.mkdir()
        is_valid, err_title, err_msg = validate_markdown_file(sub_dir)
        assert is_valid is True, "Directory should be considered valid for workspace opening."

        # 4. Non-existent file
        missing_file = tmp_path / "does_not_exist.md"
        is_valid, err_title, err_msg = validate_markdown_file(missing_file)
        assert is_valid is False
        assert err_title == "File Not Found"

        # 5. Unsupported file format (e.g. .pdf, .png, .exe)
        pdf_file = tmp_path / "document.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 header")
        is_valid, err_title, err_msg = validate_markdown_file(pdf_file)
        assert is_valid is False
        assert err_title == "Unsupported File Format"

        png_file = tmp_path / "photo.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        is_valid, err_title, err_msg = validate_markdown_file(png_file)
        assert is_valid is False
        assert err_title == "Unsupported File Format"

        # 6. Binary file disguised as .md (contains null bytes)
        fake_md = tmp_path / "binary_disguised.md"
        fake_md.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff")
        is_valid, err_title, err_msg = validate_markdown_file(fake_md)
        assert is_valid is False
        assert err_title == "Binary File Detected"

    print("test_file_validator: PASS")


def test_main_window_open_file() -> None:
    """Test MainWindow loading external markdown and updating content."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["markup-notes"])

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create external markdown document
        ext_doc = tmp_path / "external_spec.md"
        ext_doc.write_text("# External Document\n\nContent from external path.", encoding="utf-8")

        # Initialize MainWindow
        window = MainWindow()

        # Open external file
        success = window.open_file_or_folder(ext_doc)
        assert success is True, "Failed to open external markdown file"
        assert window._current_note is not None
        assert window._current_note.title.startswith("external_spec") or window._current_note.title == "External Document"
        assert "Content from external path." in window.editor.editor.toPlainText()

        # Simulate editing and saving
        window.editor.editor.setPlainText("# External Document\n\nUpdated external content.")
        window._on_content_saved("# External Document\n\nUpdated external content.")

        # Verify persisted into workspace note
        saved_disk_content = window._current_note.path.read_text(encoding="utf-8")
        assert "Updated external content." in saved_disk_content
        assert window._current_note.path.is_relative_to(window.storage.root_dir)

        # Test opening directory as workspace
        workspace_dir = tmp_path / "my_custom_vault"
        workspace_dir.mkdir()
        (workspace_dir / "vault_note.md").write_text("# Vault Note", encoding="utf-8")

        success_dir = window.open_file_or_folder(workspace_dir)
        assert success_dir is True
        assert window.storage.root_dir == workspace_dir

        window.close()

    print("test_main_window_open_file: PASS")


if __name__ == "__main__":
    test_file_validator()
    test_main_window_open_file()
    print("\nALL FILE OPENING & VALIDATION TESTS PASSED SUCCESSFULLY!")
