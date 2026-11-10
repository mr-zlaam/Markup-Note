"""Utility functions for parsing and manipulating Markdown text."""

import re
from typing import Optional, Tuple

CHECKBOX_PATTERN = re.compile(r"^(\s*)([-*+]\s*\[([ xX]?)\]\s?)(.*)$")
LIST_PATTERN = re.compile(r"^(\s*)([-*+]|\d+\.)(\s+)(.*)$")
LINK_PATTERN = re.compile(
    r"\[(?P<label>[^\]]+)\]\((?P<url>[^\s)]+)\)|<(?P<autourl>https?://[^\s>]+)>|(?P<rawurl>https?://[^\s<>\)\]]+)"
)


def find_link_at_offset(text: str, offset: int) -> Optional[Tuple[int, int, str]]:
    """Return (start, end, url) if offset falls within a Markdown link or URL in text."""
    for m in LINK_PATTERN.finditer(text):
        start, end = m.span()
        if start <= offset <= end:
            url = m.group("url") or m.group("autourl") or m.group("rawurl")
            return start, end, url
    return None


def is_checkbox_line(line: str) -> bool:
    """Return True if the line contains a markdown checklist item."""
    return CHECKBOX_PATTERN.match(line) is not None


def get_checkbox_info(line: str) -> Optional[Tuple[int, int, int, bool]]:
    """Return (bracket_start, bracket_end, prefix_end, is_checked) if present.

    Example:
        For "- [ ] task", returns (2, 5, 6, False)
        For "- [] task", returns (2, 4, 5, False)
    """
    match = CHECKBOX_PATTERN.match(line)
    if not match:
        return None

    indent, prefix, status_char, _ = match.groups()
    is_checked = status_char.lower() == "x"
    bracket_start = line.find("[", len(indent))
    bracket_end = line.find("]", bracket_start) + 1
    prefix_end = len(indent) + len(prefix)
    return bracket_start, bracket_end, prefix_end, is_checked


def toggle_checkbox_line(line: str) -> str:
    """Toggle the checkbox state between '- [ ]' and '- [x]' in a line."""
    match = CHECKBOX_PATTERN.match(line)
    if not match:
        return line

    indent, prefix, status_char, rest = match.groups()
    marker = prefix.strip()[0]
    new_char = " " if status_char.lower() == "x" else "x"
    return f"{indent}{marker} [{new_char}] {rest}"


def get_auto_continue_prefix(line: str) -> Optional[str]:
    """Determine the prefix to continue on the next line when Enter is pressed.

    Returns:
        - None if line is not a list/checkbox
        - Empty string "" if line was an empty list marker (signaling to delete it)
        - Continued prefix (e.g. "- [ ] ", "- ", "2. ") if line had content
    """
    # Checkbox item
    cb_match = CHECKBOX_PATTERN.match(line)
    if cb_match:
        indent, prefix, _, rest = cb_match.groups()
        if not rest.strip():
            # Empty checkbox item -> terminate list
            return ""
        # Return new unchecked box for next line with same indent
        marker = prefix.strip()[0]  # '-', '*', or '+'
        return f"{indent}{marker} [ ] "

    # Regular bullet or numbered list
    list_match = LIST_PATTERN.match(line)
    if list_match:
        indent, marker, space, rest = list_match.groups()
        if not rest.strip():
            # Empty list item -> terminate list
            return ""
        if marker.isdigit() or marker.endswith("."):
            num = int(marker[:-1])
            return f"{indent}{num + 1}. "
        return f"{indent}{marker}{space}"

    return None
