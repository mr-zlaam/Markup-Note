"""Native high-DPI vector icon generation utilities for Note Taker UI.

Powered by Lucide vector icons on a standardized 24x24 optical grid.
No third-party packages required; renders directly via PyQt6.QtSvg.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import List, Optional, Tuple

from PyQt6.QtCore import QByteArray, QPointF, QRect, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from utils.lucide_icons import render_lucide_icon, render_lucide_pixmap


def create_search_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a crisp magnifying glass search vector icon."""
    return render_lucide_icon("search", color=color, size=size, stroke_width=stroke_width)


def create_plus_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.8,
) -> QIcon:
    """Generate a clean vector plus (+) icon with rounded terminal caps."""
    return render_lucide_icon("plus", color=color, size=size, stroke_width=stroke_width)


def create_sidebar_toggle_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.4,
    sidebar_on_left: bool = True,
    fill_sidebar: bool = True,
) -> QIcon:
    """Generate a modern window sidebar toggle vector icon."""
    return render_lucide_icon("panel-left", color=color, size=size, stroke_width=stroke_width)


def create_notes_toggle_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.4,
    fill_notes_pane: bool = True,
) -> QIcon:
    """Generate a modern notes-list pane toggle vector icon."""
    return render_lucide_icon("panel-left-close", color=color, size=size, stroke_width=stroke_width)


def create_chevron_icon(
    direction: str = "down",
    color: str = "#8e8e93",
    size: int = 14,
    stroke_width: float = 1.8,
) -> QIcon:
    """Generate a clean chevron vector icon for collapsible headers."""
    name = f"chevron-{direction}"
    return render_lucide_icon(name, color=color, size=size, stroke_width=stroke_width)


def create_check_icon(
    color: str = "#0a84ff",
    bg_color: Optional[str] = None,
    size: int = 16,
    stroke_width: float = 1.8,
) -> QIcon:
    """Generate a crisp checkmark vector icon."""
    return render_lucide_icon("check", color=color, size=size, stroke_width=stroke_width)


def create_uncheck_icon(
    color: str = "#484852",
    border_color: Optional[str] = None,
    size: int = 14,
    stroke_width: float = 1.4,
) -> QIcon:
    """Generate an unchecked empty square indicator icon."""
    col = border_color if border_color is not None else color
    return render_lucide_icon("square", color=col, size=size, stroke_width=stroke_width)


def create_trash_icon(
    color: str = "#e03e3e",
    size: int = 16,
) -> QIcon:
    """Generate a clean vector trash can icon for delete actions."""
    return render_lucide_icon("trash-2", color=color, size=size, stroke_width=1.6)


def create_done_icon(
    color: str = "#8e8e93",
    size: int = 16,
) -> QIcon:
    """Generate a clean 'Done' check-circle action icon."""
    return render_lucide_icon("check-circle-2", color=color, size=size, stroke_width=1.6)


def create_close_icon(
    color: str = "#8e8e93",
    size: int = 14,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a clean vector close (x) icon."""
    return render_lucide_icon("x", color=color, size=size, stroke_width=stroke_width)


def create_color_circle_icon(
    hex_color: str = "#0a84ff",
    color: Optional[str] = None,
    size: int = 12,
) -> QIcon:
    """Generate a smooth antialiased circular color badge for menus."""
    target_color = color if color is not None else hex_color
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setPen(QPen(QColor("#404048"), 1.0))
    painter.setBrush(QBrush(QColor(target_color)))
    painter.drawEllipse(QRectF(1.0, 1.0, float(size) - 2.0, float(size) - 2.0))

    painter.end()
    return QIcon(pixmap)


def create_folder_icon(
    color: str = "#e5a93c",
    size: int = 16,
    is_open: bool = False,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a crisp, high-precision vector folder icon (open or closed state)."""
    name = "folder-open" if is_open else "folder"
    return render_lucide_icon(
        name,
        color=color,
        size=size,
        stroke_width=stroke_width,
    )


def create_open_folder_icon(
    color: str = "#e5a93c",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Convenience helper to generate an open state vector folder icon."""
    return create_folder_icon(color=color, size=size, is_open=True, stroke_width=stroke_width)


def create_all_notes_icon(
    color: str = "#0a84ff",
    size: int = 16,
) -> QIcon:
    """Generate a crisp vector icon for 'All Notes' (stacked notes tray)."""
    return render_lucide_icon("files", color=color, size=size, stroke_width=1.6)


def create_markdown_icon(
    color: str = "#8e8e93",
    size: int = 14,
) -> QIcon:
    """Generate a crisp vector Markdown note emblem."""
    return render_lucide_icon("file-text", color=color, size=size, stroke_width=1.6)


def draw_checkbox_badge(
    painter: QPainter,
    badge_rect: QRect,
    color: str = "#0a84ff",
    box_color: Optional[str] = None,
) -> None:
    """Draw a standalone completed-checkbox badge into an existing painter."""
    pen = QPen(QColor(box_color or color), 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Box outline
    x, y, w, h = badge_rect.x(), badge_rect.y(), badge_rect.width(), badge_rect.height()
    pad = 3
    box = QRectF(x + pad, y + pad, w - pad * 2, h - pad * 2)
    painter.drawRoundedRect(box, 3.0, 3.0)

    # Checkmark
    check_pen = QPen(QColor(color), 1.6)
    check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(check_pen)

    path = QPainterPath()
    path.moveTo(box.left() + 3.0, box.top() + box.height() * 0.52)
    path.lineTo(box.left() + box.width() * 0.40, box.bottom() - 3.2)
    path.lineTo(box.right() - 3.0, box.top() + 3.5)
    painter.drawPath(path)


def create_checkbox_icon(
    color: str = "#0a84ff",
    box_color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a crisp vector checkbox icon."""
    return render_lucide_icon("check-square", color=color, size=size, stroke_width=stroke_width)


def create_link_icon(
    color: str = "#8e8e93",
    size: int = 14,
    stroke_width: float = 1.35,
) -> QIcon:
    """Generate a crisp vector chain link icon."""
    return render_lucide_icon("link", color=color, size=size, stroke_width=stroke_width)


def create_bullet_list_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a clean bulleted-list vector icon."""
    return render_lucide_icon("list", color=color, size=size, stroke_width=stroke_width)


def create_number_list_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a clean numbered-list vector icon."""
    return render_lucide_icon("list-ordered", color=color, size=size, stroke_width=stroke_width)


def create_export_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.5,
) -> QIcon:
    """Generate a clean vector export/share icon."""
    return render_lucide_icon("share", color=color, size=size, stroke_width=stroke_width)


def create_open_file_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a vector icon for opening a note file."""
    return render_lucide_icon("folder-input", color=color, size=size, stroke_width=stroke_width)


def create_backup_icon(
    color: str = "#8e8e93",
    size: int = 16,
    has_dot: bool = False,
    dot_color: str = "#ff9f0a",
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a clean vector backup / cloud upload icon with optional notification dot."""
    if not has_dot:
        return render_lucide_icon("cloud", color=color, size=size, stroke_width=stroke_width)
    pm = render_lucide_pixmap("cloud", color=color, size=size, stroke_width=stroke_width).copy()
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(dot_color))
    # Dot in top right corner (note pm devicePixelRatio is 2.0)
    d = 4.0 * pm.devicePixelRatio()
    x = pm.width() - d - 1.0
    y = 1.0
    painter.drawEllipse(QRectF(x, y, d, d))
    painter.end()
    return QIcon(pm)


def create_github_icon(color: str = "#ffffff", size: int = 16) -> QIcon:
    """Generate a high-precision vector icon of the official GitHub Invertocat logo."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    svg_data = f"""<svg viewBox="0 0 24 24" fill="{color}" xmlns="http://www.w3.org/2000/svg">
    <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
    </svg>"""

    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def create_sync_icon(color: str = "#ffffff", size: int = 16, stroke_width: float = 1.45) -> QIcon:
    """Generate a clean rotating sync icon."""
    return render_lucide_icon("refresh-cw", color=color, size=size, stroke_width=stroke_width)


def create_history_icon(color: str = "#8e8e93", size: int = 14, stroke_width: float = 1.35) -> QIcon:
    """Generate a clean vector history / clock-rewind icon."""
    return render_lucide_icon("history", color=color, size=size, stroke_width=stroke_width)


def create_diff_icon(color: str = "#8e8e93", size: int = 14, stroke_width: float = 1.35) -> QIcon:
    """Generate a clean vector comparison / git-diff icon."""
    return render_lucide_icon("git-compare", color=color, size=size, stroke_width=stroke_width)


def create_eye_icon(
    open_eye: bool = True,
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.4,
) -> QIcon:
    """Generate a clean vector eye (or eye-off) visibility icon."""
    name = "eye" if open_eye else "eye-off"
    return render_lucide_icon(name, color=color, size=size, stroke_width=stroke_width)


def create_edit_icon(
    color: str = "#0a84ff",
    size: int = 16,
    stroke_width: float = 1.4,
) -> QIcon:
    """Generate a crisp vector pencil / edit icon."""
    return render_lucide_icon("pencil", color=color, size=size, stroke_width=stroke_width)


def create_alert_icon(
    color: str = "#0a84ff",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a crisp vector alert / exclamation warning icon."""
    return render_lucide_icon("alert-circle", color=color, size=size, stroke_width=stroke_width)


def create_info_icon(
    color: str = "#0a84ff",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a crisp vector information icon."""
    return render_lucide_icon("info", color=color, size=size, stroke_width=stroke_width)


def create_keyboard_icon(
    color: str = "#8e8e93",
    size: int = 16,
    stroke_width: float = 1.6,
) -> QIcon:
    """Generate a crisp vector keyboard icon for shortcuts."""
    return render_lucide_icon("keyboard", color=color, size=size, stroke_width=stroke_width)


def create_badge_pixmap(
    icon: QIcon,
    bg_color: str = "#1a2638",
    border_color: str = "#233b5d",
    badge_size: int = 36,
    icon_size: int = 20,
    corner_radius: float = 8.0,
) -> QPixmap:
    """Generate a crisp high-DPI rounded badge container pixmap embedding an icon."""
    pixmap = QPixmap(badge_size * 2, badge_size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    rect = QRectF(0.5, 0.5, float(badge_size) - 1.0, float(badge_size) - 1.0)
    painter.setPen(QPen(QColor(border_color), 1.0))
    painter.setBrush(QBrush(QColor(bg_color)))
    painter.drawRoundedRect(rect, corner_radius, corner_radius)

    offset = int((badge_size - icon_size) / 2)
    icon.paint(painter, offset, offset, icon_size, icon_size)
    painter.end()

    return pixmap


def ensure_chevron_assets(target_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """Ensure crisp high-DPI vector chevron PNGs exist for QTreeWidget branch styling."""
    assets_dir = (
        target_dir
        if target_dir is not None
        else Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "assets"
    )
    assets_dir.mkdir(parents=True, exist_ok=True)
    right_path = assets_dir / "chevron_right.png"
    down_path = assets_dir / "chevron_down.png"

    r_icon = create_chevron_icon("right", color="#8e8e93", size=14, stroke_width=1.8)
    r_icon.pixmap(QSize(28, 28)).save(str(right_path), "PNG")

    d_icon = create_chevron_icon("down", color="#8e8e93", size=14, stroke_width=1.8)
    d_icon.pixmap(QSize(28, 28)).save(str(down_path), "PNG")

    return right_path, down_path


STANDARD_ICON_SIZES: List[int] = [16, 24, 32, 48, 64, 128, 256, 512]
PRESET_COLORS: List[Tuple[str, str]] = [
    ("Blue", "#0a84ff"),
    ("Purple", "#bf5af2"),
    ("Pink", "#ff375f"),
    ("Red", "#ff453a"),
    ("Orange", "#ff9f0a"),
    ("Yellow", "#ffd60a"),
    ("Green", "#30d158"),
    ("Teal", "#64d2ff"),
    ("Indigo", "#5e5ce6"),
    ("Gray", "#8e8e93"),
]


def mask_squircle(image: "QImage", radius_ratio: float = 0.2237) -> "QImage":
    """Mask image with a smooth continuous squircle (rounded superellipse) with transparent corners."""
    from PyQt6.QtGui import QImage, QPainter, QPainterPath

    w, h = image.width(), image.height()
    radius = w * radius_ratio

    masked = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    masked.fill(Qt.GlobalColor.transparent)

    painter = QPainter(masked)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
    painter.setClipPath(path)
    painter.drawImage(0, 0, image)
    painter.end()

    return masked


def generate_standard_app_icons(
    source_icon_path: Optional[Path] = None,
    assets_root: Optional[Path] = None,
    apply_squircle: bool = True,
) -> List[Path]:
    """Generate all standard Linux XDG hicolor icon sizes from the master app icon."""
    from PyQt6.QtGui import QImage

    project_root = Path(__file__).resolve().parent.parent
    original_src = project_root / "assets" / "markup-note-original.png"
    if source_icon_path is not None:
        src = source_icon_path
    elif original_src.exists():
        src = original_src
    else:
        src = project_root / "assets" / "markup-note.png"

    if not src.exists():
        return []

    orig_image = QImage(str(src))
    if orig_image.isNull():
        return []

    master_image = mask_squircle(orig_image) if apply_squircle else orig_image
    dest_master = project_root / "assets" / "markup-note.png"
    master_image.save(str(dest_master), "PNG")

    base_assets = assets_root if assets_root is not None else project_root / "assets"
    generated_paths: List[Path] = []

    for size in STANDARD_ICON_SIZES:
        scaled = master_image.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        hicolor_dir = base_assets / "icons" / "hicolor" / f"{size}x{size}" / "apps"
        hicolor_dir.mkdir(parents=True, exist_ok=True)
        hicolor_file = hicolor_dir / "markup-notes.png"
        scaled.save(str(hicolor_file), "PNG")
        generated_paths.append(hicolor_file)

        flat_dir = base_assets / "icons"
        flat_dir.mkdir(parents=True, exist_ok=True)
        flat_file = flat_dir / f"markup-notes-{size}x{size}.png"
        scaled.save(str(flat_file), "PNG")
        generated_paths.append(flat_file)

    return generated_paths
