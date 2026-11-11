#!/usr/bin/env bash
set -e

# ==============================================================================
# Markup Notes - Desktop Launcher & Icon Installer (Per-User)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Installing Markup Notes desktop launcher and icons..."

# 1. Install hicolor icons
ICONS_DEST="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
mkdir -p "$ICONS_DEST"
cp -r "$PROJECT_ROOT/assets/icons/hicolor" "$ICONS_DEST/"

# 2. Install desktop entry
APPS_DEST="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APPS_DEST"

cat << EOF > "$APPS_DEST/markup-notes.desktop"
[Desktop Entry]
Name=Markup Notes
Comment=Notes App for Electron haters
Exec=python3 $PROJECT_ROOT/main.py %F
Icon=markup-notes
Terminal=false
Type=Application
Categories=Office;Utility;TextEditor;
Keywords=markdown;notes;editor;text;
StartupNotify=true
MimeType=text/markdown;text/plain;
EOF

chmod +x "$APPS_DEST/markup-notes.desktop"

# 3. Update icon and desktop databases if utilities exist
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DEST" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$ICONS_DEST/hicolor" >/dev/null 2>&1 || true
fi

echo "==> Markup Notes installed successfully to $APPS_DEST/markup-notes.desktop"
