"""Native high-DPI vector icon generation utilities for Note Taker UI."""

from typing import Optional
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def create_search_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a crisp magnifying glass search vector icon."""
    pixmap = QPixmap(size * 2, size * 2)  # 2x for high-DPI crispness
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Circle (glass head)
    glass_radius = 4.2
    glass_center_x = 6.2
    glass_center_y = 6.2
    painter.drawEllipse(QPointF(glass_center_x, glass_center_y), glass_radius, glass_radius)

    # Handle (slanted line at bottom-right)
    handle_start_x = 9.2
    handle_start_y = 9.2
    handle_end_x = 13.5
    handle_end_y = 13.5
    painter.drawLine(QPointF(handle_start_x, handle_start_y), QPointF(handle_end_x, handle_end_y))

    painter.end()
    return QIcon(pixmap)


def create_plus_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.8,
) -> QIcon:
    """Generate a clean vector plus (+) icon with rounded terminal caps."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)

    mid = float(size) / 2.0
    inset = 3.5

    # Horizontal bar
    painter.drawLine(QPointF(inset, mid), QPointF(float(size) - inset, mid))
    # Vertical bar
    painter.drawLine(QPointF(mid, inset), QPointF(mid, float(size) - inset))

    painter.end()
    return QIcon(pixmap)


def create_sidebar_toggle_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.4,
    sidebar_on_left: bool = True,
    fill_sidebar: bool = True,
) -> QIcon:
    """Generate a modern window sidebar toggle vector icon (similar to VS Code / Apple Notes)."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Outer window frame
    frame = QRectF(1.5, 2.0, float(size) - 3.0, float(size) - 4.0)
    painter.drawRoundedRect(frame, 2.5, 2.5)

    # Dividing vertical bar representing the sidebar
    bar_x = frame.left() + frame.width() * 0.35 if sidebar_on_left else frame.right() - frame.width() * 0.35
    painter.drawLine(QPointF(bar_x, frame.top()), QPointF(bar_x, frame.bottom()))

    # If active, fill the sidebar portion subtly
    if fill_sidebar:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        if sidebar_on_left:
            sb_rect = QRectF(frame.left() + 1.2, frame.top() + 1.2, bar_x - frame.left() - 1.2, frame.height() - 2.4)
        else:
            sb_rect = QRectF(bar_x, frame.top() + 1.2, frame.right() - bar_x - 1.2, frame.height() - 2.4)
        painter.drawRoundedRect(sb_rect, 1.2, 1.2)

    painter.end()
    return QIcon(pixmap)


def create_notes_toggle_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.4,
) -> QIcon:
    """Generate a 3-pane layout toggle vector icon with middle pane highlighted."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Outer window frame
    frame = QRectF(1.5, 2.0, float(size) - 3.0, float(size) - 4.0)
    painter.drawRoundedRect(frame, 2.5, 2.5)

    # Two dividing bars for 3 panes
    bar1_x = frame.left() + frame.width() * 0.3
    bar2_x = frame.left() + frame.width() * 0.65
    painter.drawLine(QPointF(bar1_x, frame.top()), QPointF(bar1_x, frame.bottom()))
    painter.drawLine(QPointF(bar2_x, frame.top()), QPointF(bar2_x, frame.bottom()))

    # Fill middle pane subtly
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    mid_rect = QRectF(bar1_x + 0.6, frame.top() + 1.0, bar2_x - bar1_x - 1.2, frame.height() - 2.0)
    painter.drawRect(mid_rect)

    painter.end()
    return QIcon(pixmap)


def create_chevron_icon(
    direction: str = "left",
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a clean vector chevron icon ('left', 'right', 'up', 'down')."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    path = QPainterPath()
    mid = float(size) / 2.0
    if direction == "left":
        path.moveTo(mid + 2.5, mid - 4.5)
        path.lineTo(mid - 2.5, mid)
        path.lineTo(mid + 2.5, mid + 4.5)
    elif direction == "right":
        path.moveTo(mid - 2.5, mid - 4.5)
        path.lineTo(mid + 2.5, mid)
        path.lineTo(mid - 2.5, mid + 4.5)
    elif direction == "up":
        path.moveTo(mid - 4.5, mid + 2.5)
        path.lineTo(mid, mid - 2.5)
        path.lineTo(mid + 4.5, mid + 2.5)
    else:  # down
        path.moveTo(mid - 4.5, mid - 2.5)
        path.lineTo(mid, mid + 2.5)
        path.lineTo(mid + 4.5, mid - 2.5)

    painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)


def create_check_icon(
    color: str = "#ffffff",
    bg_color: str = "#0a84ff",
    size: int = 16,
) -> QIcon:
    """Generate a crisp circular checkmark icon for selected items."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Filled circle
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(bg_color))
    painter.drawEllipse(QRectF(1.0, 1.0, float(size) - 2.0, float(size) - 2.0))

    # Checkmark
    pen = QPen(QColor(color), 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    path = QPainterPath()
    path.moveTo(4.5, float(size) * 0.52)
    path.lineTo(float(size) * 0.42, float(size) * 0.72)
    path.lineTo(float(size) - 4.5, float(size) * 0.32)
    painter.drawPath(path)

    painter.end()
    return QIcon(pixmap)


def create_uncheck_icon(
    border_color: str = "#5c5c64",
    size: int = 16,
) -> QIcon:
    """Generate an empty circular icon for unselected items."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(border_color), 1.5)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QRectF(1.5, 1.5, float(size) - 3.0, float(size) - 3.0))

    painter.end()
    return QIcon(pixmap)


def create_trash_icon(
    color: str = "#e03e3e",
    size: int = 16,
) -> QIcon:
    """Generate a clean vector trash can icon for delete actions."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), 1.4)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Can body
    path = QPainterPath()
    path.moveTo(4.0, 5.0)
    path.lineTo(4.8, 14.0)
    path.lineTo(11.2, 14.0)
    path.lineTo(12.0, 5.0)
    painter.drawPath(path)

    # Lid line
    painter.drawLine(QPointF(2.5, 5.0), QPointF(13.5, 5.0))
    # Lid handle
    painter.drawLine(QPointF(6.0, 3.0), QPointF(10.0, 3.0))

    # Inner ribs
    painter.drawLine(QPointF(6.5, 7.5), QPointF(6.8, 11.5))
    painter.drawLine(QPointF(9.5, 7.5), QPointF(9.2, 11.5))

    painter.end()
    return QIcon(pixmap)


def create_done_icon(
    color: str = "#0a84ff",
    size: int = 16,
) -> QIcon:
    """Generate a clean vector checkmark icon for done actions."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    path = QPainterPath()
    path.moveTo(3.5, 8.5)
    path.lineTo(6.8, 12.0)
    path.lineTo(12.8, 4.5)
    painter.drawPath(path)

    painter.end()
    return QIcon(pixmap)


def create_close_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a clean vector X (cross) icon for canceling/closing."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)

    inset = 4.5
    painter.drawLine(QPointF(inset, inset), QPointF(float(size) - inset, float(size) - inset))
    painter.drawLine(QPointF(float(size) - inset, inset), QPointF(inset, float(size) - inset))

    painter.end()
    return QIcon(pixmap)
