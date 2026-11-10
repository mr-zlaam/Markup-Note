"""Obsidian-style cursor-aware Markdown syntax highlighter for PyQt6."""

import re
from typing import Dict, List, Optional, Set, Tuple

from PyQt6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)

from utils.math_engine import (
    FENCE_DISPLAY_MATH_RE,
    INLINE_MATH_RE,
    SINGLE_LINE_DISPLAY_MATH_RE,
    MathRegion,
    find_display_math_regions,
    render_math_to_pixmap,
)
from utils.mermaid_engine import (
    MERMAID_CLOSE_RE,
    MERMAID_OPEN_RE,
    MermaidRegion,
    find_mermaid_regions,
    render_mermaid_to_pixmap,
)
from utils.table import (
    TableRegion,
    find_table_regions,
    is_table_separator,
)

HEADING_RE = re.compile(r"^(#{1,6})(\s+)(.*)$")
CHECKBOX_RE = re.compile(r"^(\s*)([-*+]\s*\[([ xX]?)\]\s?)(.*)$")
QUOTE_RE = re.compile(r"^(>+\s*)(.*)$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)(\s+)(.*)$")
HR_RE = re.compile(r"^(\-{3,}|\*{3,}|_{3,})\s*$")
FENCE_RE = re.compile(r"^\s*```.*$")

BOLD_RE = re.compile(r"(\*\*|__)(.+?)\1")
ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
INLINE_CODE_RE = re.compile(r"(`)([^`\n]+)\1")
STRIKE_RE = re.compile(r"(~~)(.+?)\1")
LINK_RE = re.compile(r"(\[)([^\]]+)(\]\([^)]+\))")
TAG_RE = re.compile(r"(?:^|(?<=\s))(#[\w\d_-]+)")


class MarkdownHighlighter(QSyntaxHighlighter):
    """Applies live rich styling and hides markdown syntax on inactive lines and blocks."""

    HEADING_SIZES = {1: 24, 2: 19, 3: 16, 4: 14, 5: 13, 6: 12}
    HEADING_COLORS = {
        1: "#ffffff",
        2: "#f5f5f7",
        3: "#e5e5ea",
        4: "#d1d1d6",
        5: "#c7c7cc",
        6: "#aeaeb2",
    }

    def __init__(self, parent: QTextDocument) -> None:
        super().__init__(parent)
        self.active_block_number: int = 0
        self.table_regions: List[TableRegion] = []
        self.math_regions: List[MathRegion] = []
        self.mermaid_regions: List[MermaidRegion] = []
        self._block_modes: Dict[int, Tuple[str, int]] = {}
        self._init_formats()

    def _init_formats(self) -> None:
        # Format used to collapse and hide markdown syntax markers on inactive lines
        self.hidden_format = QTextCharFormat()
        self.hidden_format.setFontPointSize(1)
        self.hidden_format.setForeground(QColor(0, 0, 0, 0))

        # Transparent format preserving normal line height (used for inactive tables)
        self.transparent_line_format = QTextCharFormat()
        self.transparent_line_format.setForeground(QColor(0, 0, 0, 0))

        # Muted syntax marker format when cursor is on the active line
        self.marker_format = QTextCharFormat()
        self.marker_format.setForeground(QColor("#636366"))

        # Inline code
        self.inline_code_format = QTextCharFormat()
        self.inline_code_format.setFontFamilies(["monospace"])
        self.inline_code_format.setFontFixedPitch(True)
        self.inline_code_format.setForeground(QColor("#f09a52"))
        self.inline_code_format.setBackground(QColor("#2c2c2e"))

        # Multi-line code block
        self.code_block_format = QTextCharFormat()
        self.code_block_format.setFontFamilies(["monospace"])
        self.code_block_format.setFontFixedPitch(True)
        self.code_block_format.setForeground(QColor("#f09a52"))
        self.code_block_format.setBackground(QColor("#242426"))

        # Active math editing format
        self.math_source_format = QTextCharFormat()
        self.math_source_format.setFontFamilies(["monospace"])
        self.math_source_format.setFontFixedPitch(True)
        self.math_source_format.setForeground(QColor("#64d2ff"))

        # Active table pipe format
        self.table_pipe_format = QTextCharFormat()
        self.table_pipe_format.setForeground(QColor("#0a84ff"))
        self.table_pipe_format.setFontWeight(QFont.Weight.Bold)

        # Blockquote
        self.quote_format = QTextCharFormat()
        self.quote_format.setFontItalic(True)
        self.quote_format.setForeground(QColor("#98989d"))

        self.quote_bar_format = QTextCharFormat()
        self.quote_bar_format.setForeground(QColor("#0a84ff"))
        self.quote_bar_format.setFontWeight(QFont.Weight.Bold)

        # Horizontal rule
        self.hr_format = QTextCharFormat()
        self.hr_format.setForeground(QColor("#48484a"))
        self.hr_format.setFontWeight(QFont.Weight.Bold)

        # Link
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#0a84ff"))
        self.link_format.setFontUnderline(True)

        # Tag
        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(QColor("#bf5af2"))
        self.tag_format.setFontWeight(QFont.Weight.DemiBold)

        # List bullet / number
        self.list_marker_format = QTextCharFormat()
        self.list_marker_format.setForeground(QColor("#0a84ff"))
        self.list_marker_format.setFontWeight(QFont.Weight.Bold)

        # Checkboxes (transparent fixed-width prefix at full line height so paintEvent draws the custom box)
        self.checkbox_prefix_format = QTextCharFormat()
        self.checkbox_prefix_format.setFontFamilies(["monospace"])
        self.checkbox_prefix_format.setFontFixedPitch(True)
        self.checkbox_prefix_format.setFontLetterSpacingType(
            QFont.SpacingType.PercentageSpacing
        )
        self.checkbox_prefix_format.setFontLetterSpacing(55.0)
        self.checkbox_prefix_format.setForeground(QColor(0, 0, 0, 0))

        # Strikethrough (completed tasks & ~~strike~~)
        self.strike_format = QTextCharFormat()
        self.strike_format.setFontStrikeOut(True)
        self.strike_format.setForeground(QColor("#686868"))

    def refresh_regions(self) -> Set[int]:
        """Re-scan document for tables, display math, and mermaid blocks, returning changed block numbers."""
        doc = self.document()
        if doc is None:
            return set()

        old_modes = dict(self._block_modes)
        self.table_regions = find_table_regions(doc)
        self.math_regions = find_display_math_regions(doc)
        self.mermaid_regions = find_mermaid_regions(doc)

        new_modes: Dict[int, Tuple[str, int]] = {}

        # 1. Tables
        for tr in self.table_regions:
            active_in_table = tr.start_block <= self.active_block_number <= tr.end_block
            mode = "active_table" if active_in_table else "inactive_table"
            for b in range(tr.start_block, tr.end_block + 1):
                new_modes[b] = (mode, 12)

        # 2. Display Math ($$ ... $$)
        for mr in self.math_regions:
            active_in_math = mr.start_block <= self.active_block_number <= mr.end_block
            if active_in_math:
                for b in range(mr.start_block, mr.end_block + 1):
                    new_modes[b] = ("active_math", 12)
            else:
                pix = render_math_to_pixmap(mr.latex, font_size=19.0, display_mode=True)
                target_h = (pix.height() / pix.devicePixelRatio()) + 20.0
                non_empty = [
                    b
                    for b in range(mr.start_block, mr.end_block + 1)
                    if len(doc.findBlockByNumber(b).text()) > 0
                ]
                count = max(1, len(non_empty))
                pt_size = max(12, int(round((target_h / count) * 0.56)))
                for b in range(mr.start_block, mr.end_block + 1):
                    new_modes[b] = ("inactive_math", pt_size)

        # 3. Mermaid Diagrams (```mermaid ... ```)
        for mmd in self.mermaid_regions:
            active_in_mmd = mmd.start_block <= self.active_block_number <= mmd.end_block
            if active_in_mmd:
                for b in range(mmd.start_block, mmd.end_block + 1):
                    new_modes[b] = ("active_mermaid", 12)
            else:
                pix = render_mermaid_to_pixmap(mmd.source)
                target_h = (pix.height() / pix.devicePixelRatio()) + 16.0
                non_empty = [
                    b
                    for b in range(mmd.start_block, mmd.end_block + 1)
                    if len(doc.findBlockByNumber(b).text()) > 0
                ]
                count = max(1, len(non_empty))
                pt_size = max(12, int(round((target_h / count) * 0.56)))
                for b in range(mmd.start_block, mmd.end_block + 1):
                    new_modes[b] = ("inactive_mermaid", pt_size)

        self._block_modes = new_modes
        changed_blocks: Set[int] = set()
        all_keys = set(old_modes.keys()) | set(new_modes.keys())
        for k in all_keys:
            if old_modes.get(k) != new_modes.get(k):
                changed_blocks.add(k)
        return changed_blocks

    def highlightBlock(self, text: str) -> None:
        """Apply cursor-aware Obsidian-style highlighting to the current block."""
        block_num = self.currentBlock().blockNumber()
        is_active = block_num == self.active_block_number

        # 0. Check multi-line region overrides (Tables, Display Math, Mermaid)
        if block_num in self._block_modes:
            mode, pt_size = self._block_modes[block_num]
            if mode == "inactive_table":
                self.setCurrentBlockState(0)
                self.setFormat(0, len(text), self.transparent_line_format)
                return

            if mode == "active_table":
                self.setCurrentBlockState(0)
                if is_table_separator(text):
                    self.setFormat(0, len(text), self.marker_format)
                else:
                    self._apply_inline_rules(text, is_active=True, base_point_size=None, base_bold=False, base_color=None)
                    for m in re.finditer(r"\|", text):
                        self.setFormat(m.start(), 1, self.table_pipe_format)
                return

            if mode in ("inactive_math", "inactive_mermaid"):
                self.setCurrentBlockState(0)
                if len(text) > 0:
                    self.setFormat(0, len(text), self.hidden_format)
                    tall_fmt = QTextCharFormat()
                    tall_fmt.setFontPointSize(pt_size)
                    tall_fmt.setForeground(QColor(0, 0, 0, 0))
                    self.setFormat(0, 1, tall_fmt)
                return

            if mode == "active_math":
                self.setCurrentBlockState(0)
                self.setFormat(0, len(text), self.math_source_format)
                if FENCE_DISPLAY_MATH_RE.match(text):
                    self.setFormat(0, len(text), self.marker_format)
                elif SINGLE_LINE_DISPLAY_MATH_RE.match(text):
                    open_idx = text.find("$$")
                    close_idx = text.rfind("$$")
                    self.setFormat(open_idx, 2, self.marker_format)
                    self.setFormat(close_idx, 2, self.marker_format)
                return

            if mode == "active_mermaid":
                self.setCurrentBlockState(0)
                if MERMAID_OPEN_RE.match(text) or MERMAID_CLOSE_RE.match(text):
                    self.setFormat(0, len(text), self.marker_format)
                else:
                    self.setFormat(0, len(text), self.code_block_format)
                return

        # 1. Multi-line fenced code blocks (```)
        if self._handle_code_blocks(text, is_active):
            return

        # 2. Horizontal rules (---, ***, ___)
        if HR_RE.match(text):
            self.setFormat(0, len(text), self.hr_format)
            return

        base_point_size: Optional[int] = None
        base_bold: bool = False
        base_color: Optional[QColor] = None

        # 3. Headings (# H1 .. ###### H6)
        h_match = HEADING_RE.match(text)
        if h_match:
            hashes, spaces, _ = h_match.groups()
            level = len(hashes)
            prefix_len = len(hashes) + len(spaces)
            base_point_size = self.HEADING_SIZES.get(level, 13)
            base_bold = True
            base_color = QColor(self.HEADING_COLORS.get(level, "#ffffff"))

            h_fmt = QTextCharFormat()
            h_fmt.setFontPointSize(base_point_size)
            h_fmt.setFontWeight(QFont.Weight.Bold)
            h_fmt.setForeground(base_color)
            self.setFormat(0, len(text), h_fmt)

            if is_active:
                active_marker = QTextCharFormat(h_fmt)
                active_marker.setForeground(QColor("#636366"))
                self.setFormat(0, prefix_len, active_marker)
            else:
                self.setFormat(0, prefix_len, self.hidden_format)

        # 4. Checkboxes (- [ ] / - [] / - [x])
        cb_match = CHECKBOX_RE.match(text) if not h_match else None
        if cb_match:
            indent, prefix, status, _ = cb_match.groups()
            prefix_start = len(indent)
            prefix_len = len(prefix)
            is_checked = status.lower() == "x"
            self.setFormat(prefix_start, prefix_len, self.checkbox_prefix_format)

            if is_checked:
                text_start = prefix_start + prefix_len
                self.setFormat(text_start, len(text) - text_start, self.strike_format)
                return

        # 5. Blockquotes (> quote)
        q_match = QUOTE_RE.match(text) if not (h_match or cb_match) else None
        if q_match:
            prefix = q_match.group(1)
            self.setFormat(0, len(text), self.quote_format)
            if is_active:
                self.setFormat(0, len(prefix), self.quote_bar_format)
            else:
                self.setFormat(0, len(prefix), self.hidden_format)

        # 6. Standard Bullet / Numbered Lists (- item, 1. item)
        list_match = LIST_RE.match(text) if not (h_match or cb_match or q_match) else None
        if list_match:
            indent, marker, space, _ = list_match.groups()
            self.setFormat(len(indent), len(marker) + len(space), self.list_marker_format)

        # 7. Inline formatting (**bold**, *italic*, `code`, ~~strike~~, [link](url), $math$, #tag)
        self._apply_inline_rules(text, is_active, base_point_size, base_bold, base_color)

    def _apply_inline_rules(
        self,
        text: str,
        is_active: bool,
        base_point_size: Optional[int],
        base_bold: bool,
        base_color: Optional[QColor],
    ) -> None:
        """Apply inline markdown styles and hide syntax markers when line is inactive."""
        # Bold: **text** or __text__
        for m in BOLD_RE.finditer(text):
            marker_len = len(m.group(1))
            start, end = m.span()
            fmt = QTextCharFormat()
            if base_point_size:
                fmt.setFontPointSize(base_point_size)
            fmt.setFontWeight(QFont.Weight.Bold)
            fmt.setForeground(QColor("#ffffff"))
            self.setFormat(start + marker_len, (end - start) - 2 * marker_len, fmt)
            self._format_markers(start, end, marker_len, is_active, base_point_size)

        # Italic: *text*
        for m in ITALIC_RE.finditer(text):
            start, end = m.span()
            fmt = QTextCharFormat()
            if base_point_size:
                fmt.setFontPointSize(base_point_size)
            if base_bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            fmt.setFontItalic(True)
            fmt.setForeground(base_color if base_color else QColor("#dcdcdc"))
            self.setFormat(start + 1, (end - start) - 2, fmt)
            self._format_markers(start, end, 1, is_active, base_point_size)

        # Inline code: `code`
        for m in INLINE_CODE_RE.finditer(text):
            start, end = m.span()
            fmt = QTextCharFormat(self.inline_code_format)
            if base_point_size:
                fmt.setFontPointSize(base_point_size)
            self.setFormat(start + 1, (end - start) - 2, fmt)
            self._format_markers(start, end, 1, is_active, base_point_size)

        # Inline Math: $...$
        for m in INLINE_MATH_RE.finditer(text):
            start, end = m.span()
            expr = m.group(1)
            if is_active:
                fmt = QTextCharFormat(self.math_source_format)
                if base_point_size:
                    fmt.setFontPointSize(base_point_size)
                self.setFormat(start + 1, (end - start) - 2, fmt)
                self._format_markers(start, end, 1, is_active=True, base_point_size=base_point_size)
            else:
                pix = render_math_to_pixmap(expr, font_size=15.0, display_mode=False)
                target_w = pix.width() / pix.devicePixelRatio()
                span_len = max(1, end - start)
                self.setFormat(start, span_len, self.hidden_format)
                spacer_fmt = QTextCharFormat()
                spacer_fmt.setForeground(QColor(0, 0, 0, 0))
                spacer_fmt.setFontLetterSpacingType(QFont.SpacingType.AbsoluteSpacing)
                spacer_fmt.setFontLetterSpacing(max(0.0, target_w - 6.0))
                self.setFormat(start, 1, spacer_fmt)

        # Strikethrough: ~~text~~
        for m in STRIKE_RE.finditer(text):
            start, end = m.span()
            fmt = QTextCharFormat(self.strike_format)
            if base_point_size:
                fmt.setFontPointSize(base_point_size)
            self.setFormat(start + 2, (end - start) - 4, fmt)
            self._format_markers(start, end, 2, is_active, base_point_size)

        # Links: [text](url)
        for m in LINK_RE.finditer(text):
            g1_start, g1_end = m.span(1)
            g2_start, g2_end = m.span(2)
            g3_start, g3_end = m.span(3)
            fmt = QTextCharFormat(self.link_format)
            if base_point_size:
                fmt.setFontPointSize(base_point_size)
            self.setFormat(g2_start, g2_end - g2_start, fmt)
            syntax_fmt = self.marker_format if is_active else self.hidden_format
            self.setFormat(g1_start, g1_end - g1_start, syntax_fmt)
            self.setFormat(g3_start, g3_end - g3_start, syntax_fmt)

        # Tags: #tag (not headings)
        if not base_point_size:
            for m in TAG_RE.finditer(text):
                start, end = m.span(1)
                self.setFormat(start, end - start, self.tag_format)

    def _format_markers(
        self,
        start: int,
        end: int,
        marker_len: int,
        is_active: bool,
        base_point_size: Optional[int],
    ) -> None:
        """Style opening and closing inline markdown delimiters."""
        if is_active:
            m_fmt = QTextCharFormat(self.marker_format)
            if base_point_size:
                m_fmt.setFontPointSize(base_point_size)
            self.setFormat(start, marker_len, m_fmt)
            self.setFormat(end - marker_len, marker_len, m_fmt)
        else:
            self.setFormat(start, marker_len, self.hidden_format)
            self.setFormat(end - marker_len, marker_len, self.hidden_format)

    def _handle_code_blocks(self, text: str, is_active: bool) -> bool:
        """Handle multi-line fenced code blocks (```)."""
        prev_state = self.previousBlockState()
        is_fence = FENCE_RE.match(text) is not None

        if prev_state == 1:
            if is_fence:
                self.setCurrentBlockState(0)
                self.setFormat(
                    0,
                    len(text),
                    self.marker_format if is_active else self.hidden_format,
                )
            else:
                self.setCurrentBlockState(1)
                self.setFormat(0, len(text), self.code_block_format)
            return True

        if is_fence:
            self.setCurrentBlockState(1)
            self.setFormat(
                0,
                len(text),
                self.marker_format if is_active else self.hidden_format,
            )
            return True

        self.setCurrentBlockState(0)
        return False
