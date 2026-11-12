"""Cursor utilities ensuring standard hand/pointer cursors across desktop environments."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import QAbstractButton, QApplication


class ButtonCursorFilter(QObject):
    """Global event filter ensuring all interactive buttons display PointingHandCursor on hover."""

    def eventFilter(self, watched: Optional[QObject], event: Optional[QEvent]) -> bool:
        if watched is not None and event is not None:
            if event.type() in (
                QEvent.Type.Enter,
                QEvent.Type.Show,
                QEvent.Type.Polish,
            ):
                if isinstance(watched, QAbstractButton):
                    if watched.cursor().shape() == Qt.CursorShape.ArrowCursor:
                        watched.setCursor(Qt.CursorShape.PointingHandCursor)
        return super().eventFilter(watched, event)


_cursor_filter_instance: Optional[ButtonCursorFilter] = None


def install_global_button_cursor_filter(app: QApplication) -> None:
    """Install application-level event filter ensuring pointing hand cursor on all buttons."""
    global _cursor_filter_instance
    if _cursor_filter_instance is None:
        _cursor_filter_instance = ButtonCursorFilter(app)
        app.installEventFilter(_cursor_filter_instance)
