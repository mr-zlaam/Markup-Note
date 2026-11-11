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

    # Optional subtle tint inside the sidebar partition
    if fill_sidebar:
        fill_color = QColor(color)
        fill_color.setAlpha(45)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill_color)
        if sidebar_on_left:
            fill_rect = QRectF(frame.left(), frame.top(), bar_x - frame.left(), frame.height())
        else:
            fill_rect = QRectF(bar_x, frame.top(), frame.right() - bar_x, frame.height())
        painter.drawRoundedRect(fill_rect, 2.0, 2.0)

    painter.end()
    return QIcon(pixmap)


def create_notes_toggle_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.4,
) -> QIcon:
    """Generate a vector icon representing toggling the middle note cards panel."""
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

    # Draw two dividers creating a 3-column representation
    x1 = frame.left() + frame.width() * 0.30
    x2 = frame.left() + frame.width() * 0.65
    painter.drawLine(QPointF(x1, frame.top()), QPointF(x1, frame.bottom()))
    painter.drawLine(QPointF(x2, frame.top()), QPointF(x2, frame.bottom()))

    # Highlight middle column (Note list)
    fill_color = QColor(color)
    fill_color.setAlpha(45)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(fill_color)
    mid_rect = QRectF(x1, frame.top(), x2 - x1, frame.height())
    painter.drawRect(mid_rect)

    painter.end()
    return QIcon(pixmap)


def create_chevron_icon(
    direction: str = "left",
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a clean vector chevron icon (< or >)."""
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

    mid_y = float(size) / 2.0
    h_span = 3.6
    v_span = 4.2

    path = QPainterPath()
    if direction == "left":
        cx = float(size) / 2.0 + 1.0
        path.moveTo(cx + h_span / 2.0, mid_y - v_span)
        path.lineTo(cx - h_span / 2.0, mid_y)
        path.lineTo(cx + h_span / 2.0, mid_y + v_span)
    else:
        cx = float(size) / 2.0 - 1.0
        path.moveTo(cx - h_span / 2.0, mid_y - v_span)
        path.lineTo(cx + h_span / 2.0, mid_y)
        path.lineTo(cx - h_span / 2.0, mid_y + v_span)

    painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)
