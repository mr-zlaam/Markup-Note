#!/usr/bin/env bash
set -e

# ==============================================================================
# Markup Notes - Automated AppImage Build Script
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "==> Building Markup Notes AppImage..."
echo "    Project Root: $PROJECT_ROOT"

BUILD_DIR="$PROJECT_ROOT/build"
APPDIR="$BUILD_DIR/AppDir"
OUTPUT_APPIMAGE="$PROJECT_ROOT/MarkupNotes-x86_64.AppImage"

# Clean old build directories
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons"

# 1. Generate/verify standard XDG icons
echo "==> Ensuring standard XDG icon tiers are present..."
QT_QPA_PLATFORM=offscreen .venv/bin/python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from utils.icons import generate_standard_app_icons
generate_standard_app_icons()
"

# 2. Compile application with PyInstaller (lean, targeted for optimal size)
echo "==> Compiling application with PyInstaller (stripped of unused Qt modules)..."
.venv/bin/pyinstaller \
    --name markup-notes \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "$PROJECT_ROOT/assets:assets" \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import PyQt6.QtDBus \
    --exclude-module PyQt6.QtQuick \
    --exclude-module PyQt6.QtQuickWidgets \
    --exclude-module PyQt6.QtQuick3D \
    --exclude-module PyQt6.QtQml \
    --exclude-module PyQt6.Qt3DCore \
    --exclude-module PyQt6.Qt3DRender \
    --exclude-module PyQt6.Qt3DInput \
    --exclude-module PyQt6.Qt3DLogic \
    --exclude-module PyQt6.Qt3DExtras \
    --exclude-module PyQt6.Qt3DAnimation \
    --exclude-module PyQt6.QtMultimedia \
    --exclude-module PyQt6.QtMultimediaWidgets \
    --exclude-module PyQt6.QtBluetooth \
    --exclude-module PyQt6.QtNfc \
    --exclude-module PyQt6.QtSql \
    --exclude-module PyQt6.QtSensors \
    --exclude-module PyQt6.QtPositioning \
    --exclude-module PyQt6.QtLocation \
    --exclude-module PyQt6.QtWebChannel \
    --exclude-module PyQt6.QtWebSockets \
    --exclude-module PyQt6.QtRemoteObjects \
    --exclude-module PyQt6.QtTextToSpeech \
    --exclude-module PyQt6.QtSpatialAudio \
    --exclude-module PyQt6.QtDesigner \
    --exclude-module PyQt6.QtHelp \
    --distpath "$BUILD_DIR/dist" \
    --workpath "$BUILD_DIR/work" \
    --specpath "$BUILD_DIR" \
    main.py

# 3. Assemble AppDir structure
echo "==> Assembling AppDir structure..."
cp -r "$BUILD_DIR/dist/markup-notes" "$APPDIR/usr/bin/"

# Prune host-compiled desktop system libraries from AppDir to ensure universal glibc compatibility
echo "==> Pruning host-compiled system libraries from AppDir to ensure universal glibc compatibility..."
EXCLUDE_LIBS=(
    "libglib-2.0.so*"
    "libgobject-2.0.so*"
    "libgio-2.0.so*"
    "libgmodule-2.0.so*"
    "libgthread-2.0.so*"
    "libgtk-3.so*"
    "libgdk-3.so*"
    "libgdk_pixbuf-2.0.so*"
    "libcairo.so*"
    "libcairo-gobject.so*"
    "libpango-1.0.so*"
    "libpangocairo-1.0.so*"
    "libpangoft2-1.0.so*"
    "libatk-1.0.so*"
    "libatk-bridge-2.0.so*"
    "libatspi.so*"
    "libfontconfig.so*"
    "libfreetype.so*"
    "libdbus-1.so*"
    "libX11.so*"
    "libX11-xcb.so*"
    "libXext.so*"
    "libXcursor.so*"
    "libXrender.so*"
    "libXrandr.so*"
    "libXi.so*"
    "libXfixes.so*"
    "libXcomposite.so*"
    "libXdamage.so*"
    "libXinerama.so*"
    "libxkbcommon.so*"
    "libxkbcommon-x11.so*"
    "libxcb.so*"
    "libxcb-*.so*"
    "libasound.so*"
    "libz.so*"
    "libzstd.so*"
    "libsystemd.so*"
    "libudev.so*"
    "libcap.so*"
    "liblzma.so*"
    "libmount.so*"
    "libblkid.so*"
    "libcrypto.so*"
    "libssl.so*"
    "libglycin-2.so*"
    "libcloudproviders.so*"
    "libtinysparql-3.0.so*"
    "libjson-glib-1.0.so*"
    "libicuuc.so.78*"
    "libicudata.so.78*"
)

PRUNED_COUNT=0
for pattern in "${EXCLUDE_LIBS[@]}"; do
    for f in "$APPDIR/usr/bin/markup-notes/_internal"/$pattern; do
        if [ -f "$f" ] && [ ! -L "$f" ]; then
            rm -f "$f"
            PRUNED_COUNT=$((PRUNED_COUNT + 1))
        fi
    done
done
echo "    Pruned $PRUNED_COUNT host libraries from AppDir (AppImage will dynamically link to host desktop libraries)."

# Copy standard icons
cp -r "$PROJECT_ROOT/assets/icons/hicolor" "$APPDIR/usr/share/icons/"
# Copy root icons for AppImage specification
cp "$PROJECT_ROOT/assets/icons/markup-notes-512x512.png" "$APPDIR/markup-notes.png"
cp "$PROJECT_ROOT/assets/icons/markup-notes-512x512.png" "$APPDIR/.DirIcon"

# Write standard desktop entry inside AppDir
cat << 'EOF' > "$APPDIR/markup-notes.desktop"
[Desktop Entry]
Name=Markup Notes
Comment=Notes App for Electron haters
Exec=markup-notes %F
Icon=markup-notes
Terminal=false
Type=Application
Categories=Office;Utility;TextEditor;
Keywords=markdown;notes;editor;text;
StartupNotify=true
MimeType=text/markdown;text/plain;
EOF

cp "$APPDIR/markup-notes.desktop" "$APPDIR/usr/share/applications/"

# Write standard AppRun launcher with preflight checks and crash diagnostics
cat << 'EOF' > "$APPDIR/AppRun"
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${HERE}/usr/bin/markup-notes:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin/markup-notes/_internal:${HERE}/usr/bin/markup-notes/_internal/PyQt6/Qt6/lib:${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="${HERE}/usr/bin/markup-notes/_internal/PyQt6/Qt6/plugins"
export QML2_IMPORT_PATH="${HERE}/usr/bin/markup-notes/_internal/PyQt6/Qt6/qml"

# Universal Desktop Portal Support (GNOME, KDE, Niri, Hyprland, COSMIC)
if [ -z "${QT_QPA_PLATFORMTHEME}" ]; then
    export QT_QPA_PLATFORMTHEME="xdgdesktopportal"
fi

# Execute application
"${HERE}/usr/bin/markup-notes/markup-notes" "$@"
EXIT_CODE=$?

# If the application exited with failure, show diagnostics
if [ $EXIT_CODE -ne 0 ] && [ $EXIT_CODE -ne 124 ]; then
    echo "" >&2
    echo "================================================================================" >&2
    echo " [Markup Notes Startup Diagnostics]" >&2
    echo "================================================================================" >&2
    echo " Exit Code: $EXIT_CODE" >&2
    echo " If a system library was reported missing (e.g., libglib, libX11, libxcb), please" >&2
    echo " ensure your distribution's desktop base packages are installed:" >&2
    echo "   Ubuntu / Debian / Pop!_OS: sudo apt install libglib2.0-0 libx11-6 libxcb1" >&2
    echo "   Fedora / RHEL:             sudo dnf install glib2 libX11 libxcb" >&2
    echo "   Arch / Manjaro / CachyOS:  sudo pacman -S glib2 libx11 libxcb" >&2
    echo "================================================================================" >&2

    # If running in GUI session and a desktop dialog tool is available, display an error box
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        if command -v zenity >/dev/null 2>&1; then
            zenity --error --title="Markup Notes Error" \
                --text="Markup Notes encountered an error during launch (Exit Code: $EXIT_CODE).\nRun in a terminal to view detailed diagnostics." \
                --timeout=10 2>/dev/null || true
        elif command -v kdialog >/dev/null 2>&1; then
            kdialog --error "Markup Notes encountered an error during launch (Exit Code: $EXIT_CODE).\nRun in a terminal to view detailed diagnostics." \
                2>/dev/null || true
        fi
    fi
fi

exit $EXIT_CODE
EOF

chmod +x "$APPDIR/AppRun"
chmod +x "$APPDIR/usr/bin/markup-notes/markup-notes"

# 4. Package AppDir using appimagetool
echo "==> Packaging AppDir with appimagetool..."
export ARCH="x86_64"
rm -f "$OUTPUT_APPIMAGE"

RUNTIME_ARG=""
if [ -f "$PROJECT_ROOT/assets/runtime-x86_64" ]; then
    RUNTIME_ARG="--runtime-file $PROJECT_ROOT/assets/runtime-x86_64"
elif [ -f "$BUILD_DIR/runtime-x86_64" ]; then
    RUNTIME_ARG="--runtime-file $BUILD_DIR/runtime-x86_64"
fi

appimagetool --comp zstd $RUNTIME_ARG "$APPDIR" "$OUTPUT_APPIMAGE"

echo "==> AppImage created successfully!"
echo "    File: $OUTPUT_APPIMAGE"
ls -lh "$OUTPUT_APPIMAGE"
