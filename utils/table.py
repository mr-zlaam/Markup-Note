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
INLINE_CLEAN_RE = re.compile(r"(\*\*|__|~~|`|\*)")


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
    """Extract stripped cell strings from a pipe-delimited table row."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


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


def render_table(
    painter: QPainter,
    table_rect: QRectF,
    region: TableRegion,
    base_font: QFont,
) -> List[Tuple[int, int, QRectF]]:
    """Draw a styled vector table inside table_rect and return [(block_num, col_idx, cell_rect)]."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    num_cols = max(1, len(region.headers))
    total_rows = 1 + len(region.rows)
    row_height = table_rect.height() / max(1, total_rows)

    # Calculate proportional column widths based on text content
    header_font = QFont(base_font)
    header_font.setWeight(QFont.Weight.Bold)
    body_font = QFont(base_font)
    fm_h = QFontMetricsF(header_font)
    fm_b = QFontMetricsF(body_font)

    natural_widths: List[float] = []
    for c_idx in range(num_cols):
        h_text = INLINE_CLEAN_RE.sub("", region.headers[c_idx])
        max_w = fm_h.horizontalAdvance(h_text) + 28.0
        for _, r_cells in region.rows:
            if c_idx < len(r_cells):
                c_text = INLINE_CLEAN_RE.sub("", r_cells[c_idx])
                max_w = max(max_w, fm_b.horizontalAdvance(c_text) + 28.0)
        natural_widths.append(max(70.0, max_w))

    total_natural = sum(natural_widths)
    avail_width = min(table_rect.width(), max(total_natural, min(table_rect.width(), num_cols * 130.0)))
    col_widths = [(w / total_natural) * avail_width for w in natural_widths]

    actual_rect = QRectF(table_rect.left(), table_rect.top(), avail_width, table_rect.height())

    # Outer table card background & border
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor("#202024")))
    painter.drawRoundedRect(actual_rect, 6.0, 6.0)

    # Header background (top rounded)
    header_rect = QRectF(actual_rect.left(), actual_rect.top(), avail_width, row_height)
    painter.setBrush(QBrush(QColor("#2a2a30")))
    painter.drawRoundedRect(header_rect, 6.0, 6.0)
    if len(region.rows) > 0:
        # Square off bottom corners of header
        painter.drawRect(
            QRectF(actual_rect.left(), actual_rect.top() + row_height - 6.0, avail_width, 6.0)
        )

    hit_cells: List[Tuple[int, int, QRectF]] = []

    # Draw alternating row backgrounds
    for r_idx in range(len(region.rows)):
        y = actual_rect.top() + (r_idx + 1) * row_height
        r_rect = QRectF(actual_rect.left(), y, avail_width, row_height)
        if r_idx % 2 == 1:
            painter.setBrush(QBrush(QColor("#242429")))
            painter.setPen(Qt.PenStyle.NoPen)
            if r_idx == len(region.rows) - 1:
                painter.drawRoundedRect(r_rect, 6.0, 6.0)
                painter.drawRect(QRectF(actual_rect.left(), y, avail_width, 6.0))
            else:
                painter.drawRect(r_rect)

    # Draw Header Cells
    x_cursor = actual_rect.left()
    painter.setFont(header_font)
    painter.setPen(QColor("#ffffff"))
    for c_idx in range(num_cols):
        w = col_widths[c_idx]
        c_rect = QRectF(x_cursor, actual_rect.top(), w, row_height)
        hit_cells.append((region.start_block, c_idx, c_rect))
        text_rect = c_rect.adjusted(10.0, 0.0, -10.0, 0.0)
        clean_text = INLINE_CLEAN_RE.sub("", region.headers[c_idx])
        painter.drawText(text_rect, int(region.alignments[c_idx]), clean_text)
        x_cursor += w

    # Draw Body Cells
    painter.setFont(body_font)
    painter.setPen(QColor("#e5e5ea"))
    for r_idx, (block_num, r_cells) in enumerate(region.rows):
        y = actual_rect.top() + (r_idx + 1) * row_height
        x_cursor = actual_rect.left()
        for c_idx in range(num_cols):
            w = col_widths[c_idx]
            c_rect = QRectF(x_cursor, y, w, row_height)
            hit_cells.append((block_num, c_idx, c_rect))
            text_rect = c_rect.adjusted(10.0, 0.0, -10.0, 0.0)
            cell_val = r_cells[c_idx] if c_idx < len(r_cells) else ""
            clean_text = INLINE_CLEAN_RE.sub("", cell_val)
            painter.drawText(text_rect, int(region.alignments[c_idx]), clean_text)
            x_cursor += w

    # Grid lines & outer border
    grid_pen = QPen(QColor("#38383f"), 1.0)
    painter.setPen(grid_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Horizontal row dividers
    for r_idx in range(1, total_rows):
        y = actual_rect.top() + r_idx * row_height
        if r_idx == 1:
            painter.setPen(QPen(QColor("#484852"), 1.4))
        else:
            painter.setPen(grid_pen)
        painter.drawLine(
            int(actual_rect.left()),
            int(y),
            int(actual_rect.right()),
            int(y),
        )

    # Vertical column dividers
    painter.setPen(grid_pen)
    x_cursor = actual_rect.left()
    for c_idx in range(num_cols - 1):
        x_cursor += col_widths[c_idx]
        painter.drawLine(
            int(x_cursor),
            int(actual_rect.top()),
            int(x_cursor),
            int(actual_rect.bottom()),
        )

    # Outer border
    painter.setPen(QPen(QColor("#42424a"), 1.2))
    painter.drawRoundedRect(actual_rect, 6.0, 6.0)

    painter.restore()
    return hit_cells
