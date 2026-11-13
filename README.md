# Markup Notes

<div align="center">

![Markup Notes Icon](assets/markup-note.png)

### Lightweight, Native Markdown Notes for Linux (and Electron Haters)

[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)
[![Python: >=3.10](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI: PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52.svg?logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux%20%7C%20Wayland%20%7C%20X11-FCC624.svg?logo=linux&logoColor=black)](https://www.kernel.org/)

</div>

---

## ⚡ Why Markup Notes?

Most modern note-taking apps wrap Chromium and consume **300 MB to 1 GB of RAM** just to edit text files. 

**Markup Notes** is built from the ground up in Python and **PyQt6**, designed for Linux users who want:
* **Blazing Fast Startup:** Cold launch in under 0.5s.
* **Minimal Footprint:** Idles around **~40 MB of RAM**.
* **100% Local-First:** Plain `.md` files stored safely on your filesystem (`~/Documents/Markup Notes`). No mandatory clouds, proprietary sync databases, or vendor lock-in.
* **Native Wayland & Linux Desktop Integration:** Seamless support for COSMIC, GNOME, KDE Plasma, Niri, and Hyprland via native XDG Desktop Portals.

---

## ✨ Features

- **Intuitive Markdown Editor:** Seamless distraction-free writing with instant live preview.
- **Notion-Style Slash Commands (`/`):** Type `/` anywhere to summon formatting blocks:
  - Headers (`/h1`, `/h2`, `/h3`)
  - Task checkboxes (`/todo`, `/check`)
  - Blockquotes, code snippets, divider lines, and tables
- **Contextual Formatting Toolbar:** Highlight any text to summon a floating toolbar for quick formatting (Bold, Italic, Strikethrough, Monospace Code, Bullet Lists, Numbered Lists).
- **Deep Nested Folders:** Organize notes across multi-level directory trees with smooth chevron toggle animations, inline renaming, and duplicate-name guards.
- **Fast Find & Replace (`Ctrl+F`):** Case-sensitive, whole-word, and regex search with live match counting and immediate navigation.
- **Multi-Format Export:** Export your notes directly to:
  - 📄 **PDF** (High-quality print layout with custom CSS styles)
  - 🌐 **HTML** (Embedded Dark and Light themes)
  - 📝 **Markdown** (Raw markdown bundle)
- **Safe & Atomic Disk Writes:** Saves use atomic file replacement to guarantee zero file corruption even on unexpected power loss or crashes.

---

## 🚀 Quick Start

### 1. Download AppImage (Recommended)

Download the standalone executable from the [Releases](https://github.com/mr-zlaam/Note-Taker-Markdown/releases) page:

```bash
chmod +x MarkupNotes-x86_64.AppImage
./MarkupNotes-x86_64.AppImage
```

> **No dependencies needed.** The AppImage bundles its own isolated Python runtime, Qt6 libraries, and Wayland backends.

---

### 2. Run from Source

#### Prerequisites
* Linux (Wayland or X11)
* Python `>= 3.10`
* `uv` (recommended) or `pip`

#### Clone & Run
```bash
git clone https://github.com/mr-zlaam/Note-Taker-Markdown.git
cd Note-Taker-Markdown

# Using uv (fastest)
uv sync
uv run python3 main.py

# Or using standard venv + pip
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 main.py
```

---

## 🖥️ Desktop Integration

To add **Markup Notes** to your Linux application menu (GNOME, COSMIC, KDE, rofi, wofi):

```bash
bash scripts/install_desktop.sh
```

This installs high-DPI squircle icons into `~/.local/share/icons/hicolor/` and sets up `~/.local/share/applications/markup-notes.desktop`.

---

## 🛠️ Building the Standalone AppImage

To build a standalone, self-contained `MarkupNotes-x86_64.AppImage` locally:

```bash
# Ensure build requirements are installed
pip install pyinstaller appimagetool

# Run the automated build script
bash scripts/build_appimage.sh
```

The script automatically:
1. Strips out unused Qt modules (Qt3D, QML, Bluetooth, NFC, Multimedia).
2. Generates crisp, masked squircle hicolor icon tiers.
3. Applies high-efficiency `zstd` SquashFS compression.
4. Generates a lean **~73 MB** standalone executable in the project root.

---

## 📦 Flatpak Packaging

Markup Notes can be packaged and run as a native, sandboxed Flatpak targeting the **KDE 6.11** runtime.

### Prerequisites
Ensure the KDE 6.11 Platform and SDK are installed:
```bash
flatpak install flathub org.kde.Platform//6.11 org.kde.Sdk//6.11
```

### Build & Run
```bash
# Build, install to user scope, and launch immediately
bash scripts/build_flatpak.sh --run

# Export a standalone single-file .flatpak bundle
bash scripts/build_flatpak.sh --bundle
```

---

## 📁 Project Architecture

```text
markup-notes/
├── assets/                  # High-res icons, SVGs, and squircle master assets
├── core/                    # Core note management & atomic storage logic
├── ui/                      # PyQt6 interface components
│   ├── editor.py            # Markdown editor & live preview
│   ├── sidebar.py           # Nested folders & chevron tree navigation
│   ├── selection_toolbar.py # Floating context formatting toolbar
│   ├── slash_menu.py        # Notion-style slash command palette
│   ├── find_replace.py      # Search & replace floating dialog
│   └── export_dialog.py     # Multi-format export modal (PDF, HTML, MD)
├── utils/                   # Reusable helpers (paths, icons, themes, exports)
├── scripts/                 # Build and desktop integration scripts
├── main.py                  # Application entry point
├── pyproject.toml           # Project metadata & dependencies
└── LICENSE                  # GNU General Public License v2.0
```

---

## 📜 License

This project is licensed under the **GNU General Public License version 2.0 (GPL-2.0-only)** — the same license that powers the Linux Kernel. See the [LICENSE](LICENSE) file for details.
