"""Configuration manager with VS Code-style JSON persistence."""

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional

from utils.paths import get_config_dir


@dataclass
class WindowConfig:
    width: int = 1050
    height: int = 700
    maximized: bool = False


@dataclass
class LayoutConfig:
    folders_visible: bool = True
    notes_list_visible: bool = True
    folders_width: int = 190
    notes_list_width: int = 280


@dataclass
class EditorConfig:
    font_size: int = 16
    auto_save_delay_ms: int = 400


@dataclass
class AppSettings:
    window: WindowConfig = field(default_factory=WindowConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    editor: EditorConfig = field(default_factory=EditorConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        """Instantiate AppSettings with safe fallback defaults for any missing keys."""
        win_data = data.get("window", {})
        win = WindowConfig(
            width=int(win_data.get("width", 1050)),
            height=int(win_data.get("height", 700)),
            maximized=bool(win_data.get("maximized", False)),
        )

        lay_data = data.get("layout", {})
        lay = LayoutConfig(
            folders_visible=bool(lay_data.get("folders_visible", True)),
            notes_list_visible=bool(lay_data.get("notes_list_visible", True)),
            folders_width=int(lay_data.get("folders_width", 190)),
            notes_list_width=int(lay_data.get("notes_list_width", 280)),
        )

        ed_data = data.get("editor", {})
        ed = EditorConfig(
            font_size=int(ed_data.get("font_size", 16)),
            auto_save_delay_ms=int(ed_data.get("auto_save_delay_ms", 400)),
        )

        return cls(window=win, layout=lay, editor=ed)


class ConfigManager:
    """Manages application settings persisted in ~/.config/note-taker/settings.json."""

    def __init__(self, config_file: Optional[Path] = None) -> None:
        if config_file is not None:
            self.config_path = config_file
        else:
            self.config_path = get_config_dir() / "settings.json"

        self.settings: AppSettings = self.load()

    def load(self) -> AppSettings:
        """Load settings from JSON file, returning defaults if file does not exist or fails."""
        if not self.config_path.exists():
            default_settings = AppSettings()
            self._save_to_disk(default_settings)
            return default_settings

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return AppSettings.from_dict(data)
        except (json.JSONDecodeError, OSError, TypeError):
            # Degrade gracefully on corrupt JSON or read errors
            pass

        return AppSettings()

    def save(self) -> bool:
        """Persist current settings to disk atomically."""
        return self._save_to_disk(self.settings)

    def _save_to_disk(self, settings: AppSettings) -> bool:
        """Atomic file write to prevent configuration corruption."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            data = asdict(settings)
            json_text = json.dumps(data, indent=2)

            # Atomic write via temporary file
            with tempfile.NamedTemporaryFile(
                "w",
                dir=str(self.config_path.parent),
                encoding="utf-8",
                delete=False,
            ) as tf:
                tf.write(json_text)
                tf.flush()
                os.fsync(tf.fileno())
                temp_name = tf.name

            os.replace(temp_name, self.config_path)
            return True
        except OSError:
            return False

    def update_layout(
        self,
        folders_visible: Optional[bool] = None,
        notes_list_visible: Optional[bool] = None,
        folders_width: Optional[int] = None,
        notes_list_width: Optional[int] = None,
    ) -> None:
        """Update and save layout settings."""
        if folders_visible is not None:
            self.settings.layout.folders_visible = folders_visible
        if notes_list_visible is not None:
            self.settings.layout.notes_list_visible = notes_list_visible
        if folders_width is not None and folders_width > 50:
            self.settings.layout.folders_width = folders_width
        if notes_list_width is not None and notes_list_width > 50:
            self.settings.layout.notes_list_width = notes_list_width
        self.save()

    def update_window(self, width: int, height: int, maximized: bool = False) -> None:
        """Update and save window geometry settings."""
        if width > 300 and height > 200:
            self.settings.window.width = width
            self.settings.window.height = height
        self.settings.window.maximized = maximized
        self.save()
