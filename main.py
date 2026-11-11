"""Application entry point for Markup Notes."""

import os
import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Optional

# Universal Linux Desktop Integration:
# Ensure Qt delegates file dialogs and desktop features to XDG Desktop Portals
# (GNOME/Nautilus, KDE/Dolphin, GTK) on all Wayland compositors (Niri, Hyprland, Sway)
# and desktop environments, ensuring users always see their native system file chooser.
if "QT_QPA_PLATFORMTHEME" not in os.environ:
    os.environ["QT_QPA_PLATFORMTHEME"] = "xdgdesktopportal"

try:
    from PyQt6.QtCore import QTimer
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication

    from ui.main_window import MainWindow
    from ui.theme import apply_theme
except Exception as import_err:
    try:
        from utils.diagnostics import print_startup_error

        print_startup_error(import_err, context="PyQt6 Library Loading")
    except Exception:
        sys.stderr.write(
            f"\n[Markup Notes Critical Error] Failed to load Qt6: {import_err}\n"
        )
    sys.exit(1)


def main() -> None:
    """Launch the Markup Notes application with clean Ctrl+C terminal signal handling."""
    app = QApplication(sys.argv)
    app.setApplicationName("Markup Notes")
    app.setOrganizationName("MarkupNotes")

    app_icon = QIcon()
    icons_dir = Path(__file__).resolve().parent / "assets" / "icons"
    if icons_dir.exists():
        for size in (16, 24, 32, 48, 64, 128, 256, 512):
            size_path = icons_dir / f"markup-notes-{size}x{size}.png"
            if size_path.exists():
                app_icon.addFile(str(size_path))

    if app_icon.isNull():
        fallback_icon = Path(__file__).resolve().parent / "assets" / "markup-note.png"
        if fallback_icon.exists():
            app_icon = QIcon(str(fallback_icon))

    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Apply modern Apple Notes dark theme
    apply_theme(app)

    window = MainWindow()
    window.show()

    def _handle_sigint(signum: int, frame: Optional[FrameType]) -> None:
        window.flush_pending_save()
        app.quit()

    signal.signal(signal.SIGINT, _handle_sigint)
    signal.signal(signal.SIGTERM, _handle_sigint)

    # Periodic no-op timer wakes the Python interpreter from Qt's C++ event loop
    # so Ctrl+C (SIGINT) in the terminal is processed immediately.
    sig_timer = QTimer()
    sig_timer.start(150)
    sig_timer.timeout.connect(lambda: None)

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exit_err:
        if exit_err.code not in (0, None):
            try:
                from utils.diagnostics import print_startup_error

                print_startup_error(exit_err, context="Application Exit")
            except Exception:
                pass
        raise
    except Exception as runtime_err:
        try:
            from utils.diagnostics import print_startup_error

            print_startup_error(runtime_err, context="Application Runtime")
        except Exception:
            sys.stderr.write(f"\n[Markup Notes Runtime Error] {runtime_err}\n")
        sys.exit(1)
