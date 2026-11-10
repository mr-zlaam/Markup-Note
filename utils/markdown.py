"""Utility functions for parsing and manipulating Markdown text."""

import re
from typing import Optional, Tuple

CHECKBOX_PATTERN = re.compile(r"^(\s*[-*+]\s*\[)([ xX])(\]\s*)(.*)$")
LIST_PATTERN = re.compile(r"^(\s*)([-*+]|\d+\.)(\s+)(.*)$")


def is_checkbox_line(line: str) -> bool:
    """Return True if the line contains a markdown checklist item."""
    return CHECKBOX_PATTERN.match(line) is not None


def get_checkbox_info(line: str) -> Optional[Tuple[int, int, bool]]:
    """Return (start_idx, end_idx, is_checked) of the checkbox bracket if present.

    Example:
        For "- [ ] task", returns (2, 5, False) corresponding to "[ ]"
    """
    match = CHECKBOX_PATTERN.match(line)
    if not match:
        return None

    prefix = match.group(1)
    status_char = match.group(2)
    start_pos = len(prefix) - 1  # character position of the space or 'x'
    is_checked = status_char.lower() == "x"
    # The checkbox bounds are from the bracket start to closing bracket
    bracket_start = line.find("[")
    bracket_end = line.find("]", bracket_start) + 1
    return bracket_start, bracket_end, is_checked


def toggle_checkbox_line(line: str) -> str:
    """Toggle the checkbox state between '- [ ]' and '- [x]' in a line."""
    match = CHECKBOX_PATTERN.match(line)
    if not match:
        return line

    prefix, status_char, suffix, rest = match.groups()
    new_char = " " if status_char.lower() == "x" else "x"
    return f"{prefix}{new_char}{suffix}{rest}"


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
        prefix, _, suffix, rest = cb_match.groups()
        if not rest.strip():
            # Empty checkbox item -> terminate list
            return ""
        # Return new unchecked box for next line with same indent
        indent = re.match(r"^\s*", prefix).group(0)
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
