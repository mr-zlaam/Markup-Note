"""Pure-Python vector LaTeX math parser and typesetter for PyQt6."""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTextDocument,
)

LATEX_SYMBOLS: Dict[str, str] = {
    # Lowercase Greek
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ϵ",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "varpi": "ϖ", "rho": "ρ", "varrho": "ϱ", "sigma": "σ",
    "varsigma": "ς", "tau": "τ", "upsilon": "υ", "phi": "ϕ", "varphi": "φ",
    "chi": "χ", "psi": "ψ", "omega": "ω",
    # Uppercase Greek
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    # Big Operators
    "sum": "∑", "prod": "∏", "coprod": "∐", "int": "∫", "iint": "∬",
    "iiint": "∭", "oint": "∮", "bigcup": "⋃", "bigcap": "⋂", "bigoplus": "⨁",
    "bigotimes": "⨂",
    # Binary operators & relations
    "pm": "±", "mp": "∓", "times": "×", "div": "÷", "cdot": "·", "ast": "∗",
    "star": "⋆", "circ": "∘", "bullet": "•", "oplus": "⊕", "ominus": "⊖",
    "otimes": "⊗", "oslash": "⊘", "odot": "⊙", "leq": "≤", "le": "≤",
    "geq": "≥", "ge": "≥", "neq": "≠", "ne": "≠", "approx": "≈", "equiv": "≡",
    "cong": "≅", "sim": "∼", "simeq": "≃", "propto": "∝", "ll": "≪", "gg": "≫",
    "subset": "⊂", "supset": "⊃", "subseteq": "⊆", "supseteq": "⊇",
    "in": "∈", "notin": "∉", "ni": "∋", "cup": "∪", "cap": "∩",
    "setminus": "∖", "emptyset": "∅", "varnothing": "∅",
    # Logic & quantifiers
    "forall": "∀", "exists": "∃", "nexists": "∄", "neg": "¬", "lnot": "¬",
    "land": "∧", "lor": "∨", "top": "⊤", "bot": "⊥", "vdash": "⊢", "models": "⊨",
    # Arrows
    "to": "→", "rightarrow": "→", "leftarrow": "←", "leftrightarrow": "↔",
    "Rightarrow": "⇒", "Leftarrow": "⇐", "Leftrightarrow": "⇔",
    "implies": "⟹", "iff": "⟺", "mapsto": "↦", "uparrow": "↑", "downarrow": "↓",
    "longrightarrow": "⟶", "longleftarrow": "⟵", "Longrightarrow": "⟹",
    # Calculus & misc
    "infty": "∞", "partial": "∂", "nabla": "∇", "aleph": "ℵ", "hbar": "ℏ",
    "ell": "ℓ", "wp": "℘", "Re": "ℜ", "Im": "ℑ", "angle": "∠", "triangle": "△",
    "perp": "⊥", "parallel": "∥", "mid": "∣", "|": "∥", "dots": "…", "ldots": "…", "cdots": "⋯",
    "vdots": "⋮", "ddots": "⋱", "prime": "′", "deg": "°", "quad": "  ",
    "qquad": "    ", ",": " ", ";": " ", ":": " ", "!": "",
}

BIG_OPS = {"∑", "∏", "∐", "∫", "∬", "∭", "∮", "⋃", "⋂", "⨁", "⨂", "lim", "max", "min", "sup", "inf"}
UPRIGHT_FUNCS = {"sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "log", "ln", "exp", "lim", "max", "min", "sup", "inf", "det", "dim", "ker", "deg", "gcd", "Pr", "mod"}
BLACKBOARD_MAP = {
    "R": "ℝ", "N": "ℕ", "Z": "ℤ", "Q": "ℚ", "C": "ℂ", "P": "ℙ", "E": "𝔼", "F": "𝔽", "H": "ℍ",
}

INLINE_MATH_RE = re.compile(r"(?:(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$|\\+\((.+?)\\+\))")
SINGLE_LINE_DISPLAY_MATH_RE = re.compile(r"^\s*(?:\$\$|\\+\[)\s*(.+?)\s*(?:\$\$|\\+\])\s*$")
FENCE_OPEN_MATH_RE = re.compile(r"^\s*(?:\$\$|\\+\[)\s*$")
FENCE_CLOSE_MATH_RE = re.compile(r"^\s*(?:\$\$|\\+\])\s*$")
FENCE_DISPLAY_MATH_RE = re.compile(r"^\s*(?:\$\$|\\+\[|\\+\])\s*$")

_PIXMAP_CACHE: Dict[Tuple[str, int, bool], QPixmap] = {}


def sanitize_latex(latex: str) -> str:
    """Pre-process and unescape markdown-escaped LaTeX strings."""
    s = re.sub(r"\\_", "_", latex)
    s = re.sub(r"\\\^", "^", s)
    s = re.sub(r"\\\\([,;:!])", r"\\\1", s)
    s = re.sub(r"\\\\(quad|qquad)", r"\\\1", s)
    s = re.sub(r"\\{3,}", r"\\\\", s)
    return s


@dataclass
class MathRegion:
    """Represents a display math block ($$ ... $$, \\[ ... \\], or \\[ ... \\]) in the document."""

    start_block: int
    end_block: int
    latex: str


def find_display_math_regions(doc: QTextDocument) -> List[MathRegion]:
    """Scan a QTextDocument for single-line or multi-line display math blocks."""
    regions: List[MathRegion] = []
    total = doc.blockCount()
    i = 0
    while i < total:
        text = doc.findBlockByNumber(i).text()
        single = SINGLE_LINE_DISPLAY_MATH_RE.match(text)
        if single:
            regions.append(MathRegion(start_block=i, end_block=i, latex=single.group(1).strip()))
            i += 1
            continue

        if FENCE_OPEN_MATH_RE.match(text):
            lines: List[str] = []
            j = i + 1
            closed = False
            while j < total:
                jt = doc.findBlockByNumber(j).text()
                if FENCE_CLOSE_MATH_RE.match(jt):
                    closed = True
                    break
                lines.append(jt)
                j += 1
            if closed and lines:
                regions.append(MathRegion(start_block=i, end_block=j, latex="\n".join(lines).strip()))
                i = j + 1
                continue
        i += 1
    return regions


class MathBox:
    """Base layout box with width, ascent (above baseline), and descent (below baseline)."""

    def __init__(self, width: float = 0.0, ascent: float = 0.0, descent: float = 0.0) -> None:
        self.width = width
        self.ascent = ascent
        self.descent = descent

    @property
    def height(self) -> float:
        return self.ascent + self.descent

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        """Draw the box with its left edge at x and baseline at baseline_y."""


class GlyphBox(MathBox):
    """Renders a string of characters with a specific QFont."""

    def __init__(self, text: str, font: QFont, color: str = "#f2f2f7") -> None:
        self.text = text
        self.font = font
        self.color = color
        fm = QFontMetricsF(font)
        w = fm.horizontalAdvance(text)
        super().__init__(width=w, ascent=fm.ascent(), descent=fm.descent())

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        painter.save()
        painter.setFont(self.font)
        painter.setPen(QColor(self.color))
        painter.drawText(QPointF(x, baseline_y), self.text)
        painter.restore()


class RowBox(MathBox):
    """Horizontal sequence of MathBoxes aligned on their baseline."""

    def __init__(self, children: List[MathBox]) -> None:
        self.children = children
        w = sum(c.width for c in children)
        asc = max((c.ascent for c in children), default=8.0)
        desc = max((c.descent for c in children), default=3.0)
        super().__init__(width=w, ascent=asc, descent=desc)

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        curr_x = x
        for child in self.children:
            child.draw(painter, curr_x, baseline_y)
            curr_x += child.width


class SpaceBox(MathBox):
    """Horizontal spacing box."""

    def __init__(self, width: float) -> None:
        super().__init__(width=width, ascent=0.0, descent=0.0)


class FractionBox(MathBox):
    """Renders numerator over denominator with a horizontal fraction bar."""

    def __init__(self, num: MathBox, den: MathBox, font_size: float, has_bar: bool = True) -> None:
        self.num = num
        self.den = den
        self.has_bar = has_bar
        self.axis_offset = font_size * 0.32
        self.gap = max(2.5, font_size * 0.16)
        self.pad = max(4.0, font_size * 0.25)

        w = max(num.width, den.width) + self.pad * 2
        asc = self.axis_offset + self.gap + num.height
        desc = max(0.0, den.height + self.gap - self.axis_offset)
        super().__init__(width=w, ascent=asc, descent=desc)

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        bar_y = baseline_y - self.axis_offset
        num_x = x + (self.width - self.num.width) / 2.0
        num_baseline = bar_y - self.gap - self.num.descent
        self.num.draw(painter, num_x, num_baseline)

        den_x = x + (self.width - self.den.width) / 2.0
        den_baseline = bar_y + self.gap + self.den.ascent
        self.den.draw(painter, den_x, den_baseline)

        if self.has_bar:
            painter.save()
            painter.setPen(QPen(QColor("#f2f2f7"), 1.35))
            painter.drawLine(QPointF(x + 2.0, bar_y), QPointF(x + self.width - 2.0, bar_y))
            painter.restore()


class SqrtBox(MathBox):
    """Renders a radical sign and vinculum bar over an inner MathBox."""

    def __init__(self, inner: MathBox, index_box: Optional[MathBox], font_size: float) -> None:
        self.inner = inner
        self.index_box = index_box
        self.pad_top = max(3.0, font_size * 0.18)
        self.hook_w = max(9.0, font_size * 0.58)
        self.extra_left = max(0.0, index_box.width - self.hook_w * 0.45) if index_box else 0.0

        w = self.extra_left + self.hook_w + inner.width + 3.0
        asc = inner.ascent + self.pad_top + 2.0
        desc = inner.descent + 1.0
        super().__init__(width=w, ascent=asc, descent=desc)

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        start_x = x + self.extra_left
        top_y = baseline_y - self.inner.ascent - self.pad_top
        bot_y = baseline_y + self.inner.descent

        if self.index_box is not None:
            idx_x = x + 1.0
            idx_y = top_y + (bot_y - top_y) * 0.45
            self.index_box.draw(painter, idx_x, idx_y)

        inner_x = start_x + self.hook_w
        self.inner.draw(painter, inner_x, baseline_y)

        painter.save()
        pen = QPen(QColor("#f2f2f7"), 1.35)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        path = QPainterPath()
        mid_y = top_y + (bot_y - top_y) * 0.58
        path.moveTo(start_x + 1.0, mid_y)
        path.lineTo(start_x + self.hook_w * 0.28, mid_y - 2.0)
        path.lineTo(start_x + self.hook_w * 0.58, bot_y)
        path.lineTo(inner_x, top_y)
        path.lineTo(inner_x + self.inner.width + 2.0, top_y)
        painter.drawPath(path)
        painter.restore()


class ScriptsBox(MathBox):
    """Renders superscripts and/or subscripts on a base MathBox (or stacked limits on big ops)."""

    def __init__(
        self,
        base: MathBox,
        sub: Optional[MathBox],
        sup: Optional[MathBox],
        stack_limits: bool = False,
    ) -> None:
        self.base = base
        self.sub = sub
        self.sup = sup
        self.stack_limits = stack_limits

        if stack_limits:
            w = max(
                base.width,
                sub.width if sub else 0.0,
                sup.width if sup else 0.0,
            ) + 4.0
            asc = base.ascent + (sup.height + 2.0 if sup else 0.0)
            desc = base.descent + (sub.height + 2.0 if sub else 0.0)
        else:
            script_w = max(sub.width if sub else 0.0, sup.width if sup else 0.0) + 1.5
            w = base.width + script_w
            sup_shift = max(base.ascent * 0.55, 5.0)
            sub_shift = max(base.descent + 2.5, 4.0)
            asc = max(base.ascent, (sup_shift + sup.ascent) if sup else 0.0)
            desc = max(base.descent, (sub_shift + sub.descent) if sub else 0.0)
            self._sup_shift = sup_shift
            self._sub_shift = sub_shift

        super().__init__(width=w, ascent=asc, descent=desc)

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        if self.stack_limits:
            bx = x + (self.width - self.base.width) / 2.0
            self.base.draw(painter, bx, baseline_y)
            if self.sup:
                sx = x + (self.width - self.sup.width) / 2.0
                sy = baseline_y - self.base.ascent - 2.0 - self.sup.descent
                self.sup.draw(painter, sx, sy)
            if self.sub:
                subx = x + (self.width - self.sub.width) / 2.0
                suby = baseline_y + self.base.descent + 2.0 + self.sub.ascent
                self.sub.draw(painter, subx, suby)
        else:
            self.base.draw(painter, x, baseline_y)
            sx = x + self.base.width + 1.0
            if self.sup:
                self.sup.draw(painter, sx, baseline_y - self._sup_shift)
            if self.sub:
                self.sub.draw(painter, sx, baseline_y + self._sub_shift)


class AccentBox(MathBox):
    """Renders a math accent (hat, bar, vec, tilde, dot) above a base box."""

    def __init__(self, base: MathBox, kind: str) -> None:
        self.base = base
        self.kind = kind
        super().__init__(width=base.width, ascent=base.ascent + 5.0, descent=base.descent)

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        self.base.draw(painter, x, baseline_y)
        top_y = baseline_y - self.base.ascent - 1.5
        mid_x = x + self.base.width / 2.0
        w = max(6.0, self.base.width * 0.85)

        painter.save()
        painter.setPen(QPen(QColor("#f2f2f7"), 1.3))
        if self.kind in ("bar", "overline"):
            painter.drawLine(QPointF(mid_x - w / 2.0, top_y), QPointF(mid_x + w / 2.0, top_y))
        elif self.kind == "hat":
            path = QPainterPath()
            path.moveTo(mid_x - 4.0, top_y + 1.5)
            path.lineTo(mid_x, top_y - 2.0)
            path.lineTo(mid_x + 4.0, top_y + 1.5)
            painter.drawPath(path)
        elif self.kind == "vec":
            painter.drawLine(QPointF(mid_x - w / 2.0, top_y), QPointF(mid_x + w / 2.0, top_y))
            painter.drawLine(QPointF(mid_x + w / 2.0 - 3.0, top_y - 2.2), QPointF(mid_x + w / 2.0, top_y))
            painter.drawLine(QPointF(mid_x + w / 2.0 - 3.0, top_y + 2.2), QPointF(mid_x + w / 2.0, top_y))
        elif self.kind == "dot":
            painter.setBrush(QColor("#f2f2f7"))
            painter.drawEllipse(QPointF(mid_x, top_y), 1.3, 1.3)
        elif self.kind == "tilde":
            path = QPainterPath()
            path.moveTo(mid_x - 4.0, top_y + 1.0)
            path.cubicTo(mid_x - 1.5, top_y - 2.5, mid_x + 1.5, top_y + 3.5, mid_x + 4.0, top_y - 1.0)
            painter.drawPath(path)
        painter.restore()


class BoxedBox(MathBox):
    """Renders a border box around an inner MathBox (LaTeX \\boxed{...})."""

    def __init__(self, inner: MathBox, font_size: float) -> None:
        self.inner = inner
        self.pad_x = max(6.0, font_size * 0.38)
        self.pad_y = max(4.0, font_size * 0.26)
        w = inner.width + self.pad_x * 2
        asc = inner.ascent + self.pad_y
        desc = inner.descent + self.pad_y
        super().__init__(width=w, ascent=asc, descent=desc)

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        self.inner.draw(painter, x + self.pad_x, baseline_y)

        painter.save()
        pen = QPen(QColor("#a1a1a6"), 1.3)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(x + 1.0, baseline_y - self.ascent + 1.0, self.width - 2.0, self.height - 2.0)
        painter.drawRect(rect)
        painter.restore()


class MatrixBox(MathBox):
    """Renders a 2D matrix grid with optional surrounding brackets (), [], ||, or {}."""

    def __init__(self, rows: List[List[MathBox]], bracket_type: str, font_size: float) -> None:
        self.rows = rows
        self.bracket_type = bracket_type
        self.col_gap = max(10.0, font_size * 0.75)
        self.row_gap = max(5.0, font_size * 0.35)
        self.bracket_w = 7.0 if bracket_type else 2.0

        num_cols = max((len(r) for r in rows), default=1)
        self.col_widths = [0.0] * num_cols
        self.row_ascents: List[float] = []
        self.row_descents: List[float] = []

        for r in rows:
            self.row_ascents.append(max((c.ascent for c in r), default=8.0))
            self.row_descents.append(max((c.descent for c in r), default=3.0))
            for c_idx, cell in enumerate(r):
                self.col_widths[c_idx] = max(self.col_widths[c_idx], cell.width)

        grid_w = sum(self.col_widths) + self.col_gap * max(0, num_cols - 1)
        total_h = (
            sum(self.row_ascents)
            + sum(self.row_descents)
            + self.row_gap * max(0, len(rows) - 1)
            + 6.0
        )
        axis = font_size * 0.32
        asc = total_h / 2.0 + axis
        desc = max(0.0, total_h - asc)
        super().__init__(width=grid_w + self.bracket_w * 2 + 4.0, ascent=asc, descent=desc)

    def draw(self, painter: QPainter, x: float, baseline_y: float) -> None:
        top_y = baseline_y - self.ascent + 2.0
        bot_y = baseline_y + self.descent - 2.0

        curr_y = top_y + 2.0
        start_x = x + self.bracket_w + 2.0
        for r_idx, r in enumerate(self.rows):
            row_base = curr_y + self.row_ascents[r_idx]
            curr_x = start_x
            for c_idx, cell in enumerate(r):
                col_w = self.col_widths[c_idx]
                cx = curr_x + (col_w - cell.width) / 2.0
                cell.draw(painter, cx, row_base)
                curr_x += col_w + self.col_gap
            curr_y += self.row_ascents[r_idx] + self.row_descents[r_idx] + self.row_gap

        if not self.bracket_type:
            return

        painter.save()
        painter.setPen(QPen(QColor("#f2f2f7"), 1.4))
        lx = x + 1.5
        rx = x + self.width - 1.5
        if self.bracket_type == "p":  # ( )
            path = QPainterPath()
            path.moveTo(lx + 5.0, top_y)
            path.quadTo(lx - 1.5, (top_y + bot_y) / 2.0, lx + 5.0, bot_y)
            path.moveTo(rx - 5.0, top_y)
            path.quadTo(rx + 1.5, (top_y + bot_y) / 2.0, rx - 5.0, bot_y)
            painter.drawPath(path)
        elif self.bracket_type == "b":  # [ ]
            painter.drawLine(QPointF(lx + 4.5, top_y), QPointF(lx, top_y))
            painter.drawLine(QPointF(lx, top_y), QPointF(lx, bot_y))
            painter.drawLine(QPointF(lx, bot_y), QPointF(lx + 4.5, bot_y))
            painter.drawLine(QPointF(rx - 4.5, top_y), QPointF(rx, top_y))
            painter.drawLine(QPointF(rx, top_y), QPointF(rx, bot_y))
            painter.drawLine(QPointF(rx, bot_y), QPointF(rx - 4.5, bot_y))
        elif self.bracket_type == "v":  # | |
            painter.drawLine(QPointF(lx + 2.0, top_y), QPointF(lx + 2.0, bot_y))
            painter.drawLine(QPointF(rx - 2.0, top_y), QPointF(rx - 2.0, bot_y))
        painter.restore()


class LatexParser:
    """Recursive-descent parser converting a LaTeX math string into a MathBox tree."""

    def __init__(self, text: str, base_size: float, display_mode: bool) -> None:
        self.text = sanitize_latex(text.strip())
        self.pos = 0
        self.base_size = base_size
        self.display_mode = display_mode

    def parse(self) -> MathBox:
        return self._parse_sequence(self.base_size, stop_chars=set())

    def _skip_spaces(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in " \t\r\n":
            self.pos += 1

    def _parse_group(self, font_size: float) -> MathBox:
        self._skip_spaces()
        if self.pos >= len(self.text):
            return SpaceBox(0.0)
        if self.text[self.pos] == "{":
            self.pos += 1
            box = self._parse_sequence(font_size, stop_chars={"}"})
            if self.pos < len(self.text) and self.text[self.pos] == "}":
                self.pos += 1
            return box
        return self._parse_atom(font_size)

    def _parse_sequence(self, font_size: float, stop_chars: set[str]) -> MathBox:
        boxes: List[MathBox] = []
        while self.pos < len(self.text):
            self._skip_spaces()
            if self.pos >= len(self.text) or self.text[self.pos] in stop_chars:
                break

            base = self._parse_atom(font_size)
            is_big_op = isinstance(base, GlyphBox) and base.text in BIG_OPS

            # Check for trailing subscripts/superscripts (_ and ^)
            sub_box: Optional[MathBox] = None
            sup_box: Optional[MathBox] = None
            script_size = max(7.5, font_size * 0.70)

            for _ in range(2):
                self._skip_spaces()
                if self.pos < len(self.text) and self.text[self.pos] == "_":
                    self.pos += 1
                    sub_box = self._parse_group(script_size)
                elif self.pos < len(self.text) and self.text[self.pos] == "^":
                    self.pos += 1
                    sup_box = self._parse_group(script_size)
                else:
                    break

            if sub_box is not None or sup_box is not None:
                boxes.append(
                    ScriptsBox(
                        base,
                        sub=sub_box,
                        sup=sup_box,
                        stack_limits=(is_big_op and self.display_mode),
                    )
                )
            else:
                boxes.append(base)

        if not boxes:
            return SpaceBox(0.0)
        if len(boxes) == 1:
            return boxes[0]
        return RowBox(boxes)

    def _parse_atom(self, font_size: float) -> MathBox:
        self._skip_spaces()
        if self.pos >= len(self.text):
            return SpaceBox(0.0)

        ch = self.text[self.pos]
        if ch == "{":
            return self._parse_group(font_size)

        if ch == "\\":
            self.pos += 1
            if self.pos >= len(self.text):
                return SpaceBox(0.0)
            # Escaped punctuation like \{, \}, \,
            if not self.text[self.pos].isalpha():
                esc = self.text[self.pos]
                self.pos += 1
                if esc in LATEX_SYMBOLS:
                    return self._make_glyph(LATEX_SYMBOLS[esc], font_size, italic=False)
                return self._make_glyph(esc, font_size, italic=False)

            start = self.pos
            while self.pos < len(self.text) and self.text[self.pos].isalpha():
                self.pos += 1
            cmd = self.text[start : self.pos]
            return self._handle_command(cmd, font_size)

        self.pos += 1
        if ch in "+-=<>":
            return RowBox([
                SpaceBox(font_size * 0.22),
                self._make_glyph("−" if ch == "-" else ch, font_size, italic=False),
                SpaceBox(font_size * 0.22),
            ])
        if ch.isalpha():
            return self._make_glyph(ch, font_size, italic=True)
        return self._make_glyph(ch, font_size, italic=False)

    def _handle_command(self, cmd: str, font_size: float) -> MathBox:
        if cmd in ("frac", "dfrac", "tfrac", "binom"):
            frac_size = font_size * (0.88 if not self.display_mode and cmd != "dfrac" else 0.96)
            num = self._parse_group(frac_size)
            den = self._parse_group(frac_size)
            fbox = FractionBox(num, den, font_size=font_size, has_bar=(cmd != "binom"))
            if cmd == "binom":
                return MatrixBox([[num], [den]], bracket_type="p", font_size=font_size)
            return fbox

        if cmd == "boxed":
            inner = self._parse_group(font_size)
            return BoxedBox(inner, font_size=font_size)

        if cmd == "operatorname":
            name = self._read_braced_str()
            return RowBox([
                self._make_glyph(name, font_size, italic=False),
                SpaceBox(font_size * 0.16),
            ])

        if cmd == "sqrt":
            self._skip_spaces()
            idx_box: Optional[MathBox] = None
            if self.pos < len(self.text) and self.text[self.pos] == "[":
                self.pos += 1
                idx_box = self._parse_sequence(max(7.0, font_size * 0.62), stop_chars={"]"})
                if self.pos < len(self.text) and self.text[self.pos] == "]":
                    self.pos += 1
            inner = self._parse_group(font_size)
            return SqrtBox(inner, idx_box, font_size=font_size)

        if cmd in ("hat", "bar", "overline", "vec", "tilde", "dot"):
            inner = self._parse_group(font_size)
            return AccentBox(inner, kind=cmd)

        if cmd in ("text", "mathrm", "textbf", "mathbf", "mathbb", "mathcal"):
            self._skip_spaces()
            raw = ""
            if self.pos < len(self.text) and self.text[self.pos] == "{":
                raw = self._read_braced_str()
            elif self.pos < len(self.text) and not self.text[self.pos].isspace():
                raw = self.text[self.pos]
                self.pos += 1
            if cmd == "mathbb":
                mapped = "".join(BLACKBOARD_MAP.get(c, c) for c in raw)
                return self._make_glyph(mapped, font_size, italic=False, bold=True)
            return self._make_glyph(raw, font_size, italic=False, bold=(cmd in ("textbf", "mathbf")))

        if cmd in ("left", "right"):
            self._skip_spaces()
            if self.pos < len(self.text):
                delim = self.text[self.pos]
                self.pos += 1
                if delim == ".":
                    return SpaceBox(0.0)
                return self._make_glyph(delim, font_size * 1.12, italic=False)
            return SpaceBox(0.0)

        if cmd == "begin":
            env = self._read_braced_str()
            end_marker = f"\\end{{{env}}}"
            end_idx = self.text.find(end_marker, self.pos)
            if end_idx == -1:
                body = self.text[self.pos :]
                self.pos = len(self.text)
            else:
                body = self.text[self.pos : end_idx]
                self.pos = end_idx + len(end_marker)

            row_strs = [r.strip() for r in re.split(r"\\{2,}", body) if r.strip()]
            grid: List[List[MathBox]] = []
            for r_str in row_strs:
                cells = [
                    LatexParser(c.strip(), font_size * 0.92, False).parse()
                    for c in r_str.split("&")
                ]
                grid.append(cells)

            btype = ""
            if env == "pmatrix":
                btype = "p"
            elif env == "bmatrix":
                btype = "b"
            elif env == "vmatrix":
                btype = "v"
            return MatrixBox(grid, bracket_type=btype, font_size=font_size)

        if cmd in UPRIGHT_FUNCS:
            return RowBox([
                self._make_glyph(cmd, font_size, italic=False),
                SpaceBox(font_size * 0.16),
            ])

        if cmd in LATEX_SYMBOLS:
            sym = LATEX_SYMBOLS[cmd]
            if sym in BIG_OPS:
                op_size = font_size * (1.35 if self.display_mode else 1.12)
                return RowBox([
                    SpaceBox(2.0),
                    self._make_glyph(sym, op_size, italic=False),
                    SpaceBox(2.0),
                ])
            if sym in ("±", "∓", "×", "÷", "·", "≤", "≥", "≠", "≈", "≡", "∼", "∝", "∈", "∉", "⊂", "⊆", "∪", "∩", "→", "←", "↔", "⇒", "⇐", "⇔", "⟹", "⟺", "↦"):
                return RowBox([
                    SpaceBox(font_size * 0.22),
                    self._make_glyph(sym, font_size, italic=False, color="#64d2ff" if sym in ("→", "⇒", "⇔", "⟹", "⟺") else "#f2f2f7"),
                    SpaceBox(font_size * 0.22),
                ])
            return self._make_glyph(sym, font_size, italic=(cmd[0].islower() and len(sym) == 1 and sym.isalpha()))

        return self._make_glyph(cmd, font_size, italic=False)

    def _read_braced_str(self) -> str:
        self._skip_spaces()
        if self.pos < len(self.text) and self.text[self.pos] == "{":
            self.pos += 1
            start = self.pos
            depth = 1
            while self.pos < len(self.text) and depth > 0:
                if self.text[self.pos] == "{":
                    depth += 1
                elif self.text[self.pos] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                self.pos += 1
            val = self.text[start : self.pos]
            if self.pos < len(self.text) and self.text[self.pos] == "}":
                self.pos += 1
            return val.strip()
        return ""

    def _make_glyph(
        self, text: str, font_size: float, italic: bool = False, bold: bool = False, color: str = "#f2f2f7"
    ) -> GlyphBox:
        font = QFont("DejaVu Serif", -1)
        font.setPixelSize(max(8, int(round(font_size))))
        font.setItalic(italic)
        if bold:
            font.setWeight(QFont.Weight.Bold)
        return GlyphBox(text, font, color=color)


def render_math_to_pixmap(latex: str, font_size: float = 17.0, display_mode: bool = False) -> QPixmap:
    """Render a LaTeX math string to a high-DPI cached QPixmap."""
    key = (latex.strip(), int(round(font_size * 10)), display_mode)
    cached = _PIXMAP_CACHE.get(key)
    if cached is not None:
        return cached

    box = LatexParser(latex, base_size=font_size, display_mode=display_mode).parse()
    dpr = 2.0
    pad_x = 6.0
    pad_y = 4.0
    logical_w = max(12, int(box.width + pad_x * 2))
    logical_h = max(16, int(box.height + pad_y * 2))

    pix = QPixmap(int(logical_w * dpr), int(logical_h * dpr))
    pix.setDevicePixelRatio(dpr)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    box.draw(painter, pad_x, pad_y + box.ascent)
    painter.end()

    if len(_PIXMAP_CACHE) > 256:
        _PIXMAP_CACHE.clear()
    _PIXMAP_CACHE[key] = pix
    return pix
