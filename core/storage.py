"""Storage manager handling file-system operations, atomic saves, and directories."""

import os
from pathlib import Path
import re
import tempfile
from typing import List, Optional

from core.note import Note
from utils.paths import get_default_notes_dir


class StorageManager:
    """Manages markdown notes stored directly in the local file system."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = root_dir if root_dir is not None else get_default_notes_dir()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get_folders(self) -> List[Path]:
        """Return all subdirectories under root_dir (representing note folders)."""
        folders: List[Path] = []
        try:
            for item in sorted(self.root_dir.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    folders.append(item)
        except (PermissionError, FileNotFoundError):
            pass
        return folders

    def create_folder(self, folder_name: str) -> Optional[Path]:
        """Create a new subfolder under root_dir."""
        safe_name = self.sanitize_filename(folder_name)
        if not safe_name:
            return None
        folder_path = self.root_dir / safe_name
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            return folder_path
        except (PermissionError, OSError):
            return None

    def list_notes(self, folder: Optional[Path] = None) -> List[Note]:
        """List all markdown notes in the specified folder (or root if None).

        Returns notes sorted by most recently modified first.
        """
        target_dir = folder if folder is not None else self.root_dir
        if not target_dir.exists() or not target_dir.is_dir():
            return []

        notes: List[Note] = []
        try:
            for file_path in target_dir.glob("*.md"):
                if file_path.name.startswith("."):
                    continue
                note = Note.from_file(file_path)
                if note is not None:
                    notes.append(note)
        except (PermissionError, OSError):
            return []

        # Sort newest modified first
        notes.sort(key=lambda n: n.modified_at, reverse=True)
        return notes

    def create_note(self, folder: Optional[Path] = None, initial_title: str = "New Note") -> Optional[Note]:
        """Create a new empty markdown note file and return its Note instance."""
        target_dir = folder if folder is not None else self.root_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        base_name = self.sanitize_filename(initial_title) or "Note"
        file_path = target_dir / f"{base_name}.md"

        counter = 1
        while file_path.exists():
            file_path = target_dir / f"{base_name} {counter}.md"
            counter += 1

        initial_content = ""
        if self.save_note_content(file_path, initial_content):
            return Note.from_file(file_path)
        return None

    def save_note_content(self, path: Path, content: str) -> bool:
        """Atomically save content to a markdown file to prevent corruption."""
        directory = path.parent
        directory.mkdir(parents=True, exist_ok=True)

        try:
            # Write to temporary file in the same directory for atomic replace
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                delete=False,
                prefix=".tmp_save_",
            ) as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                temp_path = Path(tmp_file.name)

            # Atomic replace
            temp_path.replace(path)
            return True
        except (PermissionError, OSError):
            return False

    def rename_note_file(self, current_path: Path, new_title: str) -> Path:
        """Rename note file to match new title if safe and possible.

        Returns the new Path (or old Path if rename wasn't needed or failed).
        """
        safe_title = self.sanitize_filename(new_title)
        if not safe_title:
            return current_path

        target_path = current_path.parent / f"{safe_title}.md"
        if target_path == current_path:
            return current_path

        # If another file already has this name, append suffix
        counter = 1
        candidate_path = target_path
        while candidate_path.exists() and candidate_path != current_path:
            candidate_path = current_path.parent / f"{safe_title} {counter}.md"
            counter += 1

        try:
            current_path.rename(candidate_path)
            return candidate_path
        except (PermissionError, OSError):
            return current_path

    def delete_note(self, path: Path) -> bool:
        """Delete a note file by moving it to the .trash folder."""
        trash_dir = self.root_dir / ".trash"
        try:
            trash_dir.mkdir(parents=True, exist_ok=True)
            trash_target = trash_dir / path.name
            counter = 1
            while trash_target.exists():
                trash_target = trash_dir / f"{path.stem}_{counter}{path.suffix}"
                counter += 1
            path.rename(trash_target)
            return True
        except (PermissionError, OSError):
            return False

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Remove invalid filesystem characters from a string."""
        # Replace slashes, colons, null bytes, backslashes
        cleaned = re.sub(r'[/\\:*?"<>|\x00]', "", name).strip()
        # Cap length to 100 characters for safety
        return cleaned[:100].strip()
