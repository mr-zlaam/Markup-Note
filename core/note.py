"""Note data model and content parsing."""

from dataclasses import dataclass
from pathlib import Path
import os
import re
from typing import Optional

from utils.date_format import format_relative_time


@dataclass
class Note:
    """Represents a single Markdown note in the file system."""

    path: Path
    title: str
    content: str
    modified_at: float
    preview_snippet: str
    is_pinned: bool = False

    @property
    def formatted_time(self) -> str:
        """Return the relative human-friendly time for this note."""
        return format_relative_time(self.modified_at)

    @classmethod
    def from_file(cls, path: Path) -> Optional["Note"]:
        """Read a markdown file from disk and return a Note instance.

        Returns None if the file cannot be read.
        """
        try:
            stat_info = path.stat()
            content = path.read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError, UnicodeDecodeError):
            return None

        title, snippet = cls.parse_title_and_snippet(content, fallback_title=path.stem)
        return cls(
            path=path,
            title=title,
            content=content,
            modified_at=stat_info.st_mtime,
            preview_snippet=snippet,
            is_pinned=False,
        )

    @staticmethod
    def parse_title_and_snippet(
        content: str, fallback_title: str = "New Note"
    ) -> tuple[str, str]:
        """Extract the note's title and a 2-line preview snippet from markdown content.

        The title is the first non-empty line (with markdown headers `#` stripped).
        The snippet is composed of the following non-empty lines, with markdown syntax cleaned.
        """
        lines = [line.strip() for line in content.splitlines()]
        non_empty = [line for line in lines if line]

        if not non_empty:
            return fallback_title, "No additional text"

        # First line is title
        raw_first = non_empty[0]
        title = re.sub(
            r"^(\s*[-*+]\s*\[[ xX]?\]\s*|\s*\\?#+\s*|\s*>+\s*)", "", raw_first
        ).strip()
        title = re.sub(r"(\*\*|__|~~|`|\*)", "", title).strip()
        if not title:
            title = fallback_title

        # Collect subsequent lines for the snippet
        snippet_lines = []
        for line in non_empty[1:]:
            # Clean common markdown markers from snippet (checkboxes, bullets, headers, inline markers)
            cleaned = re.sub(
                r"^(\s*[-*+]\s*\[[ xX]?\]\s*|\s*[-*+]\s*|\s*\d+\.\s*|\s*\\?#+\s*|\s*>+\s*)",
                "",
                line,
            ).strip()
            cleaned = re.sub(r"(\*\*|__|~~|`|\*)", "", cleaned).strip()
            if cleaned:
                snippet_lines.append(cleaned)
            if len(snippet_lines) >= 2:
                break

        snippet = " ".join(snippet_lines) if snippet_lines else "No additional text"
        return title, snippet
