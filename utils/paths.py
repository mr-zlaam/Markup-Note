"""Utility functions for standard system paths and file resolution."""

import os
from pathlib import Path


def get_default_notes_dir() -> Path:
    """Return the default directory for storing markdown notes.

    Respects the standard Linux ~/Documents directory or falls back to ~/Notes.
    """
    documents_dir = Path.home() / "Documents" / "Notes"
    documents_dir.mkdir(parents=True, exist_ok=True)
    return documents_dir


def get_config_dir() -> Path:
    """Return the XDG compliant configuration directory for the application."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        base_dir = Path(xdg_config_home)
    else:
        base_dir = Path.home() / ".config"

    config_dir = base_dir / "note-taker"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
