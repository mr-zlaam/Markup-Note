"""Markdown table parsing, auto-formatting, navigation, and custom vector rendering."""

from dataclasses import dataclass
import re
from typing import List, Optional, Tuple

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPen,
    QTextDocument,
)

TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP_CELL_RE = re.compile(r"^\s*:?-{2,}:?\s*$")


def clean_cell_text(text: str) -> str:
    """Clean markdown links, escaped symbols, and inline markers for table cell rendering."""
    # 1. Clean markdown links [label](url) -> label
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # 2. Clean LaTeX parallel / norm before table pipe unescaping
    s = re.sub(r"\\+parallel\b|\\{2,}\|", "∥", s)
    s = s.replace(r"\|", "|").replace(r"\$", "$")
    # 3. Clean markdown delimiters **, __, ~~, `, *
    s = re.sub(r"(\*\*|__|~~|`|\*)", "", s)
    # 4. Clean LaTeX inline delimiters \\( ... \\), \( ... \), and $ ... $
    s = re.sub(r"\\+\((.+?)\\+\)", r"\1", s)
    s = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$", r"\1", s)
    # 5. Clean LaTeX commands in table cells
    s = re.sub(r"\\(?:operatorname|mathrm|mathbf|textbf|text)\{([^}]+)\}", r"\1", s)
    s = re.sub(r"\\det(?=[^a-zA-Z]|$)", "det", s)
    s = re.sub(r"\\log(?=[^a-zA-Z]|$)", "log", s)
    s = re.sub(r"\\ln(?=[^a-zA-Z]|$)", "ln", s)
    s = re.sub(r"\\lambda(?=[^a-zA-Z]|$)", "λ", s)
    s = re.sub(r"\\mu(?=[^a-zA-Z]|$)", "μ", s)
    s = re.sub(r"\\pi(?=[^a-zA-Z]|$)", "π", s)
    s = re.sub(r"\\cdot(?=[^a-zA-Z]|$)", "·", s)
    s = re.sub(r"\\(?:parallel|\\\|)", "∥", s)
    s = re.sub(r"\\_", "_", s)
    # 6. Pretty superscripts and subscripts
    sub_map = {
        "^T": "ᵀ",
        "^{-1}": "⁻¹",
        "^-1": "⁻¹",
        "^2": "²",
        "^3": "³",
        "^n": "ⁿ",
        "_i": "ᵢ",
        "_n": "ₙ",
        "_0": "₀",
        "_1": "₁",
        "_2": "₂",
    }
    for k, v in sub_map.items():
        s = s.replace(k, v)
    return s.strip()


@dataclass
class TableRegion:
    """Represents a contiguous Markdown table in the document."""

    start_block: int
    end_block: int
    headers: List[str]
    alignments: List[Qt.AlignmentFlag]
    rows: List[Tuple[int, List[str]]]  # (block_number, cells)


def is_table_row(line: str) -> bool:
    """Return True if the line looks like a pipe-delimited Markdown table row."""
    return TABLE_ROW_RE.match(line) is not None


def is_table_separator(line: str) -> bool:
    """Return True if the line is a Markdown table alignment separator row (e.g. |---|---|)."""
    if not is_table_row(line):
        return False
    cells = split_table_cells(line)
    if not cells:
        return False
    return all(TABLE_SEP_CELL_RE.match(c) is not None for c in cells)


def split_table_cells(line: str) -> List[str]:
    r"""Extract stripped cell strings from a pipe-delimited table row, respecting escaped pipes \|."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith(r"\|"):
        stripped = stripped[:-1]

    cells: List[str] = []
    current: List[str] = []
    escaped = False

    for ch in stripped:
        if escaped:
            current.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
            current.append(ch)
        elif ch == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    cells.append("".join(current).strip())
    return cells


def parse_alignments(sep_line: str, num_cols: int) -> List[Qt.AlignmentFlag]:
    """Parse column alignments (:---, :---:, ---:) from the separator row."""
    cells = split_table_cells(sep_line)
    alignments: List[Qt.AlignmentFlag] = []
    for i in range(num_cols):
        cell = cells[i].strip() if i < len(cells) else "---"
        if cell.startswith(":") and cell.endswith(":"):
            alignments.append(Qt.AlignmentFlag.AlignCenter)
        elif cell.endswith(":"):
            alignments.append(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            alignments.append(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return alignments


def find_table_regions(doc: QTextDocument) -> List[TableRegion]:
    """Scan a QTextDocument and return all valid Markdown tables (header + separator + rows)."""
    regions: List[TableRegion] = []
    block = doc.firstBlock()
    total_blocks = doc.blockCount()

    i = 0
    while i < total_blocks:
        b = doc.findBlockByNumber(i)
        text = b.text()
        if is_table_row(text) and (i + 1) < total_blocks:
            next_b = doc.findBlockByNumber(i + 1)
            next_text = next_b.text()
            if is_table_separator(next_text):
                headers = split_table_cells(text)
                num_cols = max(len(headers), len(split_table_cells(next_text)))
                while len(headers) < num_cols:
                    headers.append("")
                alignments = parse_alignments(next_text, num_cols)

                rows: List[Tuple[int, List[str]]] = []
                end_block = i + 1
                j = i + 2
                while j < total_blocks:
                    row_b = doc.findBlockByNumber(j)
                    row_text = row_b.text()
                    if not is_table_row(row_text):
                        break
                    if not is_table_separator(row_text):
                        cells = split_table_cells(row_text)
                        while len(cells) < num_cols:
                            cells.append("")
                        rows.append((j, cells[:num_cols]))
                    end_block = j
                    j += 1

                regions.append(
                    TableRegion(
                        start_block=i,
                        end_block=end_block,
                        headers=headers[:num_cols],
                        alignments=alignments,
                        rows=rows,
                    )
                )
                i = end_block + 1
                continue
        i += 1

    return regions


def format_table_lines(lines: List[str]) -> List[str]:
    """Pad and align columns of a Markdown table for clean source editing."""
    if len(lines) < 2:
        return lines

    parsed_rows = [split_table_cells(line) for line in lines]
    num_cols = max(len(r) for r in parsed_rows)
    col_widths = [3] * num_cols

    for row_idx, row in enumerate(parsed_rows):
        if is_table_separator(lines[row_idx]):
            continue
        for col_idx in range(num_cols):
            val = row[col_idx] if col_idx < len(row) else ""
            col_widths[col_idx] = max(col_widths[col_idx], len(val))

    formatted: List[str] = []
    for row_idx, row in enumerate(parsed_rows):
        is_sep = is_table_separator(lines[row_idx])
        out_cells: List[str] = []
        for col_idx in range(num_cols):
            val = row[col_idx] if col_idx < len(row) else ""
            w = col_widths[col_idx]
            if is_sep:
                left_colon = val.startswith(":")
                right_colon = val.endswith(":")
                dashes = "-" * max(w - int(left_colon) - int(right_colon), 2)
                sep_str = f"{':' if left_colon else ''}{dashes}{':' if right_colon else ''}"
                out_cells.append(f" {sep_str} ")
            else:
                out_cells.append(f" {val.ljust(w)} ")
        formatted.append("|" + "|".join(out_cells) + "|")

    return formatted


def is_empty_table_row(line: str) -> bool:
    """Return True if a table row has only empty cells (e.g. '|   |   |')."""
    if not is_table_row(line) or is_table_separator(line):
        return False
    return all(c == "" for c in split_table_cells(line))


def create_empty_table_row(num_cols: int) -> str:
    """Create a blank Markdown table row with the given number of columns."""
    return "|" + "|".join("   " for _ in range(max(1, num_cols))) + "|"


def find_next_cell_pos(line: str, pos_in_block: int) -> Optional[int]:
    """Return the cursor offset inside the next table cell on the line, or None if at last cell."""
    pipes = [m.start() for m in re.finditer(r"\|", line)]
    if len(pipes) < 2:
        return None
    for idx in range(len(pipes) - 1):
        if pipes[idx] > pos_in_block:
            target = pipes[idx] + 2
            return min(target, pipes[idx + 1])
    return None


def find_prev_cell_pos(line: str, pos_in_block: int) -> Optional[int]:
    """Return the cursor offset inside the previous table cell on the line, or None if at first cell."""
    pipes = [m.start() for m in re.finditer(r"\|", line)]
    if len(pipes) < 2:
        return None
    # Find which cell we are currently in
    current_cell_start_pipe = 0
    for idx in range(len(pipes) - 1):
        if pipes[idx] <= pos_in_block <= pipes[idx + 1]:
            current_cell_start_pipe = idx
            break
    if current_cell_start_pipe <= 0:
        return None
    prev_pipe = pipes[current_cell_start_pipe - 1]
    return min(prev_pipe + 2, pipes[current_cell_start_pipe])


def get_table_column_widths(
    region: TableRegion,
    base_font: QFont,
    container_width: float,
) -> Tuple[float, List[float]]:
    """Compute (content_width, col_widths) based on text content without artificial truncation."""
    num_cols = max(1, len(region.headers))
    header_font = QFont(base_font)
    header_font.setWeight(QFont.Weight.Bold)
    body_font = QFont(base_font)
    fm_h = QFontMetricsF(header_font)
    fm_b = QFontMetricsF(body_font)

    natural_widths: List[float] = []
    for c_idx in range(num_cols):
        h_text = clean_cell_text(region.headers[c_idx])
        h_w = fm_h.horizontalAdvance(h_text) + 28.0
        col_w = max(80.0, h_w)
        for _, r_cells in region.rows:
            if c_idx < len(r_cells):
                c_text = clean_cell_text(r_cells[c_idx])
                col_w = max(col_w, fm_b.horizontalAdvance(c_text) + 28.0)
        natural_widths.append(col_w)

    total_natural = sum(natural_widths)
    if total_natural <= container_width:
        col_widths = [(w / total_natural) * container_width for w in natural_widths]
        return container_width, col_widths
    else:
        return total_natural, natural_widths


def get_table_scrollbar_geometry(
    table_rect: QRectF, content_width: float, scroll_x: float
) -> Optional[Tuple[QRectF, QRectF, float]]:
    """Return (track_rect, thumb_rect, max_scroll) if table content is wider than container."""
    if content_width <= table_rect.width() + 1.0:
        return None
    max_scroll = content_width - table_rect.width()
    clamped_scroll = max(0.0, min(scroll_x, max_scroll))
    track_h = 5.0
    track_y = table_rect.bottom() - track_h - 2.0
    track_rect = QRectF(table_rect.left() + 8.0, track_y, max(10.0, table_rect.width() - 16.0), track_h)
    track_w = track_rect.width()
    thumb_w = max(36.0, min(track_w, track_w * (table_rect.width() / content_width)))
    scroll_range = max(1.0, track_w - thumb_w)
    thumb_x = track_rect.left() + (clamped_scroll / max_scroll) * scroll_range
    thumb_rect = QRectF(thumb_x, track_y, thumb_w, track_h)
    return track_rect, thumb_rect, max_scroll


def render_table(
    painter: QPainter,
    table_rect: QRectF,
    region: TableRegion,
    base_font: QFont,
    scroll_x: float = 0.0,
) -> List[Tuple[int, int, QRectF]]:
    """Draw a styled vector table inside table_rect with horizontal scrolling support."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    num_cols = max(1, len(region.headers))
    total_rows = 1 + len(region.rows)
    row_height = table_rect.height() / max(1, total_rows)

    header_font = QFont(base_font)
    header_font.setWeight(QFont.Weight.Bold)
    body_font = QFont(base_font)

    content_w, col_widths = get_table_column_widths(region, base_font, table_rect.width())
    max_scroll = max(0.0, content_w - table_rect.width())
    clamped_scroll = max(0.0, min(scroll_x, max_scroll))

    # Outer table card background
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor("#202024")))
    painter.drawRoundedRect(table_rect, 6.0, 6.0)

    # Header background across visible width
    header_rect = QRectF(table_rect.left(), table_rect.top(), table_rect.width(), row_height)
    painter.setBrush(QBrush(QColor("#2a2a30")))
    painter.drawRoundedRect(header_rect, 6.0, 6.0)
    if len(region.rows) > 0:
        painter.drawRect(
            QRectF(table_rect.left(), table_rect.top() + row_height - 6.0, table_rect.width(), 6.0)
        )

    # Alternating row backgrounds across visible width
    for r_idx in range(len(region.rows)):
        y = table_rect.top() + (r_idx + 1) * row_height
        r_rect = QRectF(table_rect.left(), y, table_rect.width(), row_height)
        if r_idx % 2 == 1:
            painter.setBrush(QBrush(QColor("#242429")))
            painter.setPen(Qt.PenStyle.NoPen)
            if r_idx == len(region.rows) - 1:
                painter.drawRoundedRect(r_rect, 6.0, 6.0)
                painter.drawRect(QRectF(table_rect.left(), y, table_rect.width(), 6.0))
            else:
                painter.drawRect(r_rect)

    # Set clipping region for cell contents and vertical dividers
    body_clip = table_rect.adjusted(1.0, 1.0, -1.0, -1.0)
    painter.setClipRect(body_clip)

    hit_cells: List[Tuple[int, int, QRectF]] = []

    # Draw Header Cells shifted by clamped_scroll
    x_cursor = table_rect.left() - clamped_scroll
    painter.setFont(header_font)
    painter.setPen(QColor("#ffffff"))
    for c_idx in range(num_cols):
        w = col_widths[c_idx]
        c_rect = QRectF(x_cursor, table_rect.top(), w, row_height)
        hit_cells.append((region.start_block, c_idx, c_rect))
        text_rect = c_rect.adjusted(10.0, 0.0, -10.0, 0.0)
        clean_text = clean_cell_text(region.headers[c_idx])
        painter.drawText(text_rect, int(region.alignments[c_idx]), clean_text)
        x_cursor += w

    # Draw Body Cells shifted by clamped_scroll
    painter.setFont(body_font)
    painter.setPen(QColor("#e5e5ea"))
    for r_idx, (block_num, r_cells) in enumerate(region.rows):
        y = table_rect.top() + (r_idx + 1) * row_height
        x_cursor = table_rect.left() - clamped_scroll
        for c_idx in range(num_cols):
            w = col_widths[c_idx]
            c_rect = QRectF(x_cursor, y, w, row_height)
            hit_cells.append((block_num, c_idx, c_rect))
            text_rect = c_rect.adjusted(10.0, 0.0, -10.0, 0.0)
            cell_val = r_cells[c_idx] if c_idx < len(r_cells) else ""
            clean_text = clean_cell_text(cell_val)
            painter.drawText(text_rect, int(region.alignments[c_idx]), clean_text)
            x_cursor += w

    # Vertical column dividers (inside clip)
    grid_pen = QPen(QColor("#38383f"), 1.0)
    painter.setPen(grid_pen)
    x_cursor = table_rect.left() - clamped_scroll
    for c_idx in range(num_cols - 1):
        x_cursor += col_widths[c_idx]
        painter.drawLine(
            int(x_cursor),
            int(table_rect.top()),
            int(x_cursor),
            int(table_rect.bottom()),
        )

    # Disable clipping for horizontal lines and outer border
    painter.setClipping(False)

    # Horizontal row dividers across visible width
    for r_idx in range(1, total_rows):
        y = table_rect.top() + r_idx * row_height
        if r_idx == 1:
            painter.setPen(QPen(QColor("#484852"), 1.4))
        else:
            painter.setPen(grid_pen)
        painter.drawLine(
            int(table_rect.left()),
            int(y),
            int(table_rect.right()),
            int(y),
        )

    # Horizontal scrollbar if table overflows
    sb_info = get_table_scrollbar_geometry(table_rect, content_w, clamped_scroll)
    if sb_info is not None:
        track_rect, thumb_rect, _ = sb_info
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#18181c")))
        painter.drawRoundedRect(track_rect, 2.5, 2.5)
        painter.setBrush(QBrush(QColor("#52525a")))
        painter.drawRoundedRect(thumb_rect, 2.5, 2.5)

    # Outer border
    painter.setPen(QPen(QColor("#42424a"), 1.2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(table_rect, 6.0, 6.0)

    painter.restore()
    return hit_cells
