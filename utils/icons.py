"""Native high-DPI vector icon generation utilities for Note Taker UI."""

from typing import List, Optional, Tuple
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


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

    # Highlight middle pane (notes list) subtly
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    mid_rect = QRectF(bar1_x + 1.0, frame.top() + 1.2, bar2_x - bar1_x - 1.0, frame.height() - 2.4)
    painter.drawRoundedRect(mid_rect, 1.0, 1.0)

    painter.end()
    return QIcon(pixmap)


def create_chevron_icon(
    direction: str = "right",
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a clean chevron arrow icon (left, right, up, down)."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    mid = float(size) / 2.0
    path = QPainterPath()

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


# Curated color presets for folders and notes (name, hex_code or None for default)
PRESET_COLORS: List[Tuple[str, Optional[str]]] = [
    ("Default", None),
    ("Blue", "#0a84ff"),
    ("Purple", "#bf5af2"),
    ("Green", "#30d158"),
    ("Yellow", "#ffd60a"),
    ("Orange", "#ff9f0a"),
    ("Red", "#ff453a"),
    ("Teal", "#64d2ff"),
    ("Pink", "#ff375f"),
]


def create_color_circle_icon(
    color: Optional[str] = None,
    size: int = 12,
) -> QIcon:
    """Generate a clean circular color swatch icon for menus."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    rect = QRectF(1.0, 1.0, float(size) - 2.0, float(size) - 2.0)
    if color is None:
        painter.setPen(QPen(QColor("#8e8e93"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)
        painter.drawLine(
            QPointF(rect.left() + 2.0, rect.top() + 2.0),
            QPointF(rect.right() - 2.0, rect.bottom() - 2.0),
        )
    else:
        painter.setPen(QPen(QColor(color).lighter(120), 0.8))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(rect)

    painter.end()
    return QIcon(pixmap)


def create_folder_icon(
    color: str = "#e5a93c",
    size: int = 16,
) -> QIcon:
    """Generate a crisp, native vector folder icon with custom tint."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Folder outline and tab
    path = QPainterPath()
    path.moveTo(2.0, 4.0)
    path.lineTo(2.0, 12.0)
    path.arcTo(QRectF(2.0, 10.5, 2.5, 2.5), 180, -90)
    path.lineTo(12.5, 13.0)
    path.arcTo(QRectF(11.5, 10.5, 2.5, 2.5), 270, -90)
    path.lineTo(14.0, 5.5)
    path.arcTo(QRectF(11.5, 3.5, 2.5, 2.5), 0, 90)
    path.lineTo(7.5, 3.5)
    path.lineTo(6.2, 2.5)
    path.arcTo(QRectF(4.2, 2.0, 2.0, 2.0), 90, 90)
    path.lineTo(2.0, 3.8)
    path.closeSubpath()

    painter.setPen(QPen(QColor(color), 1.25))
    fill_col = QColor(color)
    fill_col.setAlpha(55)
    painter.setBrush(QBrush(fill_col))
    painter.drawPath(path)

    painter.end()
    return QIcon(pixmap)


def create_all_notes_icon(
    color: str = "#0a84ff",
    size: int = 16,
) -> QIcon:
    """Generate a crisp vector icon for 'All Notes' (stacked notes tray)."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Back card
    painter.setPen(QPen(QColor(color), 1.1))
    fill_back = QColor(color)
    fill_back.setAlpha(20)
    painter.setBrush(QBrush(fill_back))
    painter.drawRoundedRect(QRectF(4.0, 2.0, 9.5, 9.5), 2.0, 2.0)

    # Front card
    fill_front = QColor(color)
    fill_front.setAlpha(45)
    painter.setBrush(QBrush(fill_front))
    painter.drawRoundedRect(QRectF(2.0, 4.5, 9.5, 9.5), 2.0, 2.0)

    # Content lines on front card
    painter.setBrush(Qt.BrushStyle.NoBrush)
    line_pen = QPen(QColor(color), 1.0)
    line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(line_pen)
    painter.drawLine(QPointF(4.0, 7.5), QPointF(9.5, 7.5))
    painter.drawLine(QPointF(4.0, 9.8), QPointF(8.0, 9.8))

    painter.end()
    return QIcon(pixmap)


def create_markdown_icon(
    color: str = "#8e8e93",
    size: int = 14,
) -> QIcon:
    """Generate a crisp vector Markdown emblem (rounded box, 'M', and '↓')."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Outer rounded box
    rect = QRectF(1.0, 2.0, 12.0, 10.0)
    pen = QPen(QColor(color), 1.1)
    painter.setPen(pen)
    fill = QColor(color)
    fill.setAlpha(25)
    painter.setBrush(QBrush(fill))
    painter.drawRoundedRect(rect, 2.0, 2.0)

    # 'M' on left
    painter.setBrush(Qt.BrushStyle.NoBrush)
    m_pen = QPen(QColor(color), 1.15)
    m_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    m_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(m_pen)

    m_path = QPainterPath()
    m_path.moveTo(2.8, 9.5)
    m_path.lineTo(2.8, 4.5)
    m_path.lineTo(4.8, 7.0)
    m_path.lineTo(6.8, 4.5)
    m_path.lineTo(6.8, 9.5)
    painter.drawPath(m_path)

    # Arrow '↓' on right
    painter.drawLine(QPointF(10.0, 4.5), QPointF(10.0, 9.5))
    arr_path = QPainterPath()
    arr_path.moveTo(8.5, 7.8)
    arr_path.lineTo(10.0, 9.5)
    arr_path.lineTo(11.5, 7.8)
    painter.drawPath(arr_path)

    painter.end()
    return QIcon(pixmap)


def draw_checkbox_badge(
    painter: QPainter,
    badge_rect: QRect,
    color: str = "#0a84ff",
    box_color: str = "#8e8e93",
) -> None:
    """Draw a crisp vector checkbox icon with checkmark centered in badge_rect."""
    cx = float(badge_rect.center().x())
    cy = float(badge_rect.center().y())
    box_size = 15.0
    half = box_size / 2.0
    box_rect = QRectF(cx - half, cy - half, box_size, box_size)

    # Rounded box
    box_pen = QPen(QColor(box_color), 1.4)
    painter.setPen(box_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(box_rect, 3.5, 3.5)

    # Checkmark inside
    check_pen = QPen(QColor(color), 1.5)
    check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(check_pen)

    path = QPainterPath()
    path.moveTo(cx - 3.8, cy + 0.3)
    path.lineTo(cx - 1.0, cy + 3.1)
    path.lineTo(cx + 4.2, cy - 2.7)
    painter.drawPath(path)


def create_checkbox_icon(
    color: str = "#0a84ff",
    box_color: str = "#8e8e93",
    size: int = 16,
) -> QIcon:
    """Generate a crisp square checkbox icon with checkmark."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    margin = 1.0
    box_size = float(size) - (margin * 2.0)
    box_rect = QRectF(margin, margin, box_size, box_size)

    box_pen = QPen(QColor(box_color), 1.4)
    painter.setPen(box_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(box_rect, 3.5, 3.5)

    cx = float(size) / 2.0
    cy = float(size) / 2.0
    check_pen = QPen(QColor(color), 1.5)
    check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(check_pen)

    path = QPainterPath()
    path.moveTo(cx - 3.8, cy + 0.3)
    path.lineTo(cx - 1.0, cy + 3.1)
    path.lineTo(cx + 4.2, cy - 2.7)
    painter.drawPath(path)

    painter.end()
    return QIcon(pixmap)


def create_link_icon(
    color: str = "#8e8e93",
    size: int = 14,
    stroke_width: float = 1.4,
) -> QIcon:
    """Generate a crisp vector chain link icon at 45 degrees."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), stroke_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Diagonal link line
    painter.drawLine(QPointF(4.8, 9.2), QPointF(9.2, 4.8))

    # Upper-right link
    p_up = QPainterPath()
    p_up.moveTo(6.8, 3.2)
    p_up.lineTo(9.5, 3.2)
    p_up.arcTo(QRectF(7.5, 1.2, 4.5, 4.5), 90, -90)
    p_up.lineTo(12.0, 5.5)
    p_up.arcTo(QRectF(7.5, 3.5, 4.5, 4.5), 0, -90)
    p_up.lineTo(10.8, 7.2)
    painter.drawPath(p_up)

    # Lower-left link
    p_down = QPainterPath()
    p_down.moveTo(3.2, 6.8)
    p_down.lineTo(2.0, 6.8)
    p_down.arcTo(QRectF(2.0, 6.0, 4.5, 4.5), 90, 90)
    p_down.lineTo(4.5, 12.0)
    p_down.arcTo(QRectF(2.0, 7.5, 4.5, 4.5), 0, 90)
    p_down.lineTo(7.2, 10.8)
    painter.drawPath(p_down)

    painter.end()
    return QIcon(pixmap)
