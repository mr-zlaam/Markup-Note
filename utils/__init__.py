"""Utilities package for Note Taker."""

from utils.cursors import install_global_button_cursor_filter
from utils.date_format import format_relative_time
from utils.markdown import (
    get_auto_continue_prefix,
    get_checkbox_info,
    is_checkbox_line,
    toggle_checkbox_line,
)
from utils.paths import get_config_dir, get_default_notes_dir

__all__ = [
    "format_relative_time",
    "get_auto_continue_prefix",
    "get_checkbox_info",
    "get_config_dir",
    "get_default_notes_dir",
    "install_global_button_cursor_filter",
    "is_checkbox_line",
    "toggle_checkbox_line",
]
