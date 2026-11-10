"""Application entry point for Note Taker."""

import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> None:
    """Launch the Note Taker application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Note Taker")
    app.setOrganizationName("NoteTaker")

    # Apply modern Apple Notes dark theme
    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
