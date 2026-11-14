"""Modern dark-themed context menu component with support for destructive actions."""

from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import QPoint, QRect, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPaintEvent, QPainter
from PyQt6.QtWidgets import QMenu, QWidget


class ModernContextMenu(QMenu):
    """Sleek dark-themed QMenu with custom rendering for destructive actions (e.g. Delete)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def addAction(self, *args: Any, **kwargs: Any) -> Any:
        """Add an action and ensure icon visibility on all Linux desktop platforms."""
        act = super().addAction(*args, **kwargs)
        if hasattr(act, "setIconVisibleInMenu"):
            act.setIconVisibleInMenu(True)
        return act

    def addMenu(self, *args: Any, **kwargs: Any) -> ModernContextMenu:
        """Create and attach a child submenu retaining ModernContextMenu styling."""
        if len(args) == 1 and isinstance(args[0], str):
            submenu = ModernContextMenu(self)
            submenu.setTitle(args[0])
            act = super().addMenu(submenu)
            if hasattr(act, "setIconVisibleInMenu"):
                act.setIconVisibleInMenu(True)
            return submenu
        return super().addMenu(*args, **kwargs)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint menu items with special treatment for destructive items."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        active_act = self.activeAction()

        for act in self.actions():
            if act.property("is_destructive"):
                rect = self.actionGeometry(act)
                if rect.isEmpty():
                    continue

                is_selected = active_act == act
                adj_rect = QRectF(rect).adjusted(1.0, 1.0, -1.0, -1.0)

                # Clear background underneath and paint tinted pill
                bg_col = QColor("#381b1e") if is_selected else QColor("#242428")
                painter.fillRect(rect, QColor("#242428"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(bg_col)
                painter.drawRoundedRect(adj_rect, 5.0, 5.0)

                # Draw icon if present
                x = rect.left() + 12
                icon = act.icon()
                if not icon.isNull():
                    icon_pm = icon.pixmap(14, 14)
                    y = rect.top() + (rect.height() - 14) // 2
                    painter.drawPixmap(x, y, icon_pm)
                    x += 14 + 10

                # Draw text in red
                text_col = QColor("#ff6961") if is_selected else QColor("#ff453a")
                painter.setPen(text_col)
                font = self.font()
                font.setPointSize(10)
                font.setWeight(QFont.Weight.Medium)
                painter.setFont(font)

                text_rect = QRect(x, rect.top(), rect.width() - x - 10, rect.height())
                painter.drawText(
                    text_rect,
                    int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                    act.text(),
                )

        painter.end()
