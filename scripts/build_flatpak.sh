#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Markup Notes - Automated Flatpak Build & Packaging Script
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

APP_ID="io.github.mr_zlaam.MarkupNotes"
MANIFEST="${PROJECT_ROOT}/flatpak/io.github.mr_zlaam.MarkupNotes.yml"
BUILD_DIR="${PROJECT_ROOT}/build/flatpak-build"
REPO_DIR="${PROJECT_ROOT}/build/flatpak-repo"
BUNDLE_FILE="${PROJECT_ROOT}/MarkupNotes-x86_64.flatpak"

DO_INSTALL=false
DO_RUN=false
DO_BUNDLE=false
DO_CLEAN=false

for arg in "$@"; do
    case "$arg" in
        --install|-i)
            DO_INSTALL=true
            ;;
        --run|-r)
            DO_INSTALL=true
            DO_RUN=true
            ;;
        --bundle|-b)
            DO_BUNDLE=true
            ;;
        --clean|-c)
            DO_CLEAN=true
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --install, -i   Install the built Flatpak into current user account (~/.local/share/flatpak)"
            echo "  --run, -r       Build, install, and immediately launch Markup Notes"
            echo "  --bundle, -b    Export a standalone single-file .flatpak bundle for distribution"
            echo "  --clean, -c     Clean build cache directories before starting"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
    esac
done

echo "==> Packaging Markup Notes Flatpak ($APP_ID)..."

# 1. Verify host prerequisites
if ! command -v flatpak-builder >/dev/null 2>&1; then
    echo "ERROR: flatpak-builder is not installed on host. Run: sudo pacman -S flatpak-builder" >&2
    exit 1
fi

if ! flatpak info org.kde.Sdk//6.11 >/dev/null 2>&1; then
    echo "ERROR: org.kde.Sdk//6.11 is not installed. Run: flatpak install flathub org.kde.Sdk//6.11" >&2
    exit 1
fi

if ! flatpak info org.kde.Platform//6.11 >/dev/null 2>&1; then
    echo "ERROR: org.kde.Platform//6.11 is not installed. Run: flatpak install flathub org.kde.Platform//6.11" >&2
    exit 1
fi

if [ "$DO_CLEAN" = true ]; then
    echo "==> Cleaning old build directories..."
    rm -rf "$BUILD_DIR" "$REPO_DIR" .flatpak-builder
fi

# 2. Build Flatpak
mkdir -p "$BUILD_DIR" "$REPO_DIR"

EXTRA_ARGS=()
if [ "$DO_INSTALL" = true ]; then
    EXTRA_ARGS+=(--user --install)
fi

echo "==> Running flatpak-builder..."
flatpak-builder \
    --force-clean \
    --disable-rofiles-fuse \
    --repo="$REPO_DIR" \
    "${EXTRA_ARGS[@]}" \
    "$BUILD_DIR" \
    "$MANIFEST"

echo "==> Build completed successfully!"

# 3. Optional: Export standalone .flatpak single-file bundle
if [ "$DO_BUNDLE" = true ]; then
    BRANCH="${FLATPAK_BRANCH:-master}"
    echo "==> Creating standalone bundle: $BUNDLE_FILE (branch: $BRANCH)"
    flatpak build-bundle "$REPO_DIR" "$BUNDLE_FILE" "$APP_ID" "$BRANCH"
    echo "    Bundle saved to: $BUNDLE_FILE"
fi

# 4. Optional: Run application
if [ "$DO_RUN" = true ]; then
    echo "==> Launching Markup Notes Flatpak..."
    flatpak run "$APP_ID"
fi
