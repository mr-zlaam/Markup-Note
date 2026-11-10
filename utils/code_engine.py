"""Syntax highlighting and native vector card renderer for code blocks."""

from dataclasses import dataclass
import re
from typing import List, Tuple

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPen,
    QTextDocument,
)

FENCE_CODE_RE = re.compile(r"^\s*(?:>+\s*)*```([a-zA-Z0-9_-]*)")

PYTHON_KEYWORDS = {
    "def", "class", "return", "if", "else", "elif", "for", "while", "in", "is",
    "not", "and", "or", "import", "from", "as", "try", "except", "finally",
    "raise", "with", "lambda", "pass", "break", "continue", "yield", "assert",
    "None", "True", "False", "async", "await", "self",
}
PYTHON_BUILTINS = {
    "print", "range", "len", "int", "str", "float", "list", "dict", "set",
    "tuple", "open", "type", "ValueError", "TypeError", "Exception", "sum",
    "max", "min", "abs", "enumerate", "zip", "map", "filter", "all", "any",
}

JS_KEYWORDS = {
    "function", "const", "let", "var", "return", "if", "else", "for", "while",
    "import", "export", "from", "default", "class", "new", "this", "async",
    "await", "true", "false", "null", "undefined", "try", "catch", "throw",
    "typeof", "instanceof", "switch", "case", "break",
}
JS_BUILTINS = {
    "console", "log", "error", "warn", "document", "window", "Math", "JSON",
    "Promise", "Array", "Object", "String", "Number", "Boolean", "Set", "Map",
}

BASH_KEYWORDS = {
    "echo", "sudo", "cd", "ls", "grep", "mkdir", "rm", "cat", "curl", "chmod",
    "export", "source", "if", "then", "else", "elif", "fi", "for", "do",
    "done", "case", "esac", "return", "exit",
}

TOKEN_RE = re.compile(
    r"""
    (?P<COMMENT>(?:\#|//).*$)
    |(?P<STRING>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
    |(?P<NUMBER>\b\d+(?:\.\d+)?\b)
    |(?P<IDENT>[a-zA-Z_]\w*)
    |(?P<OP>===|!==|==|!=|<=|>=|\+=|-=|\*=|/=|%=|\*\*|//|=>|[+\-*/%=<>!&|^~])
    |(?P<SPACE>\s+)
    |(?P<OTHER>.)
    """,
    re.VERBOSE,
)


@dataclass
class CodeRegion:
    """Represents a fenced code block in the document."""

    start_block: int
    end_block: int
    language: str
    lines: List[str]


def find_code_regions(doc: QTextDocument) -> List[CodeRegion]:
    """Scan a QTextDocument for ```lang ... ``` fenced code blocks (skipping mermaid)."""
    regions: List[CodeRegion] = []
    total = doc.blockCount()
    i = 0
    while i < total:
        text = doc.findBlockByNumber(i).text()
        m = FENCE_CODE_RE.match(text)
        if m:
            lang = m.group(1).lower().strip()
            if lang != "mermaid":
                lines: List[str] = []
                j = i + 1
                closed = False
                while j < total:
                    jt = doc.findBlockByNumber(j).text()
                    if FENCE_CODE_RE.match(jt):
                        closed = True
                        break
                    # Strip blockquote prefix if embedded
                    clean_line = re.sub(r"^(?:>\s*)+", "", jt)
                    lines.append(clean_line)
                    j += 1
                if closed:
                    regions.append(CodeRegion(start_block=i, end_block=j, language=lang, lines=lines))
                    i = j + 1
                    continue
        i += 1
    return regions


def tokenize_code_line(line: str, lang: str) -> List[Tuple[str, QColor]]:
    """Tokenize a single code line into (text, color) tuples."""
    tokens: List[Tuple[str, QColor]] = []
    is_js = lang in ("javascript", "js", "typescript", "ts")
    is_bash = lang in ("bash", "sh", "shell", "zsh")

    if is_js:
        keywords = JS_KEYWORDS
        builtins = JS_BUILTINS
    elif is_bash:
        keywords = BASH_KEYWORDS
        builtins = set()
    else:
        # Default Python + generic
        keywords = PYTHON_KEYWORDS | JS_KEYWORDS
        builtins = PYTHON_BUILTINS | JS_BUILTINS

    for m in TOKEN_RE.finditer(line):
        kind = m.lastgroup
        val = m.group(0)
        if kind == "IDENT":
            if val in keywords:
                col = QColor("#ff7b72")  # Salmon / coral keyword
            elif val in builtins:
                col = QColor("#79c0ff")  # Sky blue builtin
            else:
                col = QColor("#e6edf3")  # Light gray text
        elif kind == "STRING":
            col = QColor("#a5d6ff")  # Soft cyan string
        elif kind == "NUMBER":
            col = QColor("#d2a8ff")  # Purple number
        elif kind == "COMMENT":
            col = QColor("#8b949e")  # Muted gray comment
        elif kind == "OP":
            col = QColor("#f0883e")  # Orange operator
        else:
            col = QColor("#e6edf3")
        tokens.append((val, col))
    return tokens


def render_code_card(
    painter: QPainter,
    card_rect: QRectF,
    region: CodeRegion,
) -> None:
    """Render a rounded code card container with macOS header dots and syntax highlighting."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 1. Card container background & border
    painter.setPen(QPen(QColor("#323238"), 1.2))
    painter.setBrush(QBrush(QColor("#16161a")))
    painter.drawRoundedRect(card_rect, 8.0, 8.0)

    # 2. Header bar (28px)
    header_h = 28.0
    header_rect = QRectF(card_rect.left(), card_rect.top(), card_rect.width(), header_h)
    painter.setBrush(QBrush(QColor("#202026")))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(header_rect, 8.0, 8.0)
    painter.drawRect(QRectF(card_rect.left(), card_rect.top() + 18.0, card_rect.width(), 10.0))

    # Divider line under header
    painter.setPen(QPen(QColor("#2c2c34"), 1.0))
    painter.drawLine(
        QPointF(card_rect.left(), card_rect.top() + header_h),
        QPointF(card_rect.right(), card_rect.top() + header_h),
    )

    # 3. macOS window dots
    dots = [
        (QColor("#ff5f56"), 14.0),
        (QColor("#ffbd2e"), 26.0),
        (QColor("#27c93f"), 38.0),
    ]
    painter.setPen(Qt.PenStyle.NoPen)
    for col, dx in dots:
        painter.setBrush(col)
        painter.drawEllipse(QPointF(card_rect.left() + dx, card_rect.top() + 14.0), 4.2, 4.2)

    # 4. Language badge
    badge_name = region.language.upper() if region.language else "CODE"
    badge_font = QFont("Cantarell", -1)
    badge_font.setPixelSize(11)
    badge_font.setWeight(QFont.Weight.Bold)
    painter.setFont(badge_font)
    painter.setPen(QColor("#8e8e93"))
    painter.drawText(
        QRectF(card_rect.right() - 114.0, card_rect.top(), 100.0, header_h),
        int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
        badge_name,
    )

    # 5. Code body lines
    code_font = QFont("DejaVu Sans Mono", -1)
    code_font.setPixelSize(13)
    painter.setFont(code_font)
    fm = QFontMetricsF(code_font)
    line_h = 22.0

    # Clip to card body so code never spills outside card boundaries
    body_clip = card_rect.adjusted(1.0, header_h + 1.0, -1.0, -1.0)
    painter.setClipRect(body_clip)

    curr_y = card_rect.top() + header_h + 8.0 + fm.ascent()
    for line in region.lines:
        curr_x = card_rect.left() + 16.0
        tokens = tokenize_code_line(line, region.language)
        for val, col in tokens:
            painter.setPen(col)
            painter.drawText(QPointF(curr_x, curr_y), val)
            curr_x += fm.horizontalAdvance(val)
        curr_y += line_h

    painter.restore()
