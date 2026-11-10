"""Obsidian-style in-editor syntax highlighter for Markdown in PyQt6."""

import re
from typing import List, Tuple

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument


class MarkdownHighlighter(QSyntaxHighlighter):
    """Applies live rich styling to markdown directly within the editor canvas."""

    def __init__(self, parent: QTextDocument) -> None:
        super().__init__(parent)
        self._highlighting_rules: List[Tuple[QRegularExpression, QTextCharFormat]] = []
        self._init_formats()
        self._init_rules()

    def _init_formats(self) -> None:
        # Heading 1
        self.h1_format = QTextCharFormat()
        self.h1_format.setFontPointSize(20)
        self.h1_format.setFontWeight(QFont.Weight.Bold)
        self.h1_format.setForeground(QColor("#ffffff"))

        # Heading 2
        self.h2_format = QTextCharFormat()
        self.h2_format.setFontPointSize(17)
        self.h2_format.setFontWeight(QFont.Weight.Bold)
        self.h2_format.setForeground(QColor("#f2f2f7"))

        # Heading 3
        self.h3_format = QTextCharFormat()
        self.h3_format.setFontPointSize(15)
        self.h3_format.setFontWeight(QFont.Weight.Bold)
        self.h3_format.setForeground(QColor("#e5e5ea"))

        # Heading 4-6
        self.h4_format = QTextCharFormat()
        self.h4_format.setFontPointSize(13)
        self.h4_format.setFontWeight(QFont.Weight.Bold)
        self.h4_format.setForeground(QColor("#d1d1d6"))

        # Bold
        self.bold_format = QTextCharFormat()
        self.bold_format.setFontWeight(QFont.Weight.Bold)
        self.bold_format.setForeground(QColor("#ffffff"))

        # Italic
        self.italic_format = QTextCharFormat()
        self.italic_format.setFontItalic(True)
        self.italic_format.setForeground(QColor("#dcdcdc"))

        # Inline Code
        self.inline_code_format = QTextCharFormat()
        self.inline_code_format.setFontFamily("monospace")
        self.inline_code_format.setForeground(QColor("#f09a52"))
        self.inline_code_format.setBackground(QColor("#2c2c2e"))

        # Blockquote
        self.quote_format = QTextCharFormat()
        self.quote_format.setFontItalic(True)
        self.quote_format.setForeground(QColor("#98989d"))

        # Horizontal Rule
        self.hr_format = QTextCharFormat()
        self.hr_format.setForeground(QColor("#48484a"))
        self.hr_format.setFontWeight(QFont.Weight.Bold)

        # Markdown Link
        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#0a84ff"))
        self.link_format.setFontUnderline(True)

        # Tag
        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(QColor("#bf5af2"))
        self.tag_format.setFontWeight(QFont.Weight.DemiBold)

        # Checkbox bracket unchecked
        self.checkbox_uncheck_format = QTextCharFormat()
        self.checkbox_uncheck_format.setForeground(QColor("#0a84ff"))
        self.checkbox_uncheck_format.setFontWeight(QFont.Weight.Bold)

        # Checkbox bracket checked
        self.checkbox_check_format = QTextCharFormat()
        self.checkbox_check_format.setForeground(QColor("#30d158"))
        self.checkbox_check_format.setFontWeight(QFont.Weight.Bold)

        # Checked line strikethrough text
        self.strike_format = QTextCharFormat()
        self.strike_format.setFontStrikeOut(True)
        self.strike_format.setForeground(QColor("#636366"))

        # Code block line format
        self.code_block_format = QTextCharFormat()
        self.code_block_format.setFontFamily("monospace")
        self.code_block_format.setForeground(QColor("#f09a52"))
        self.code_block_format.setBackground(QColor("#242426"))

    def _init_rules(self) -> None:
        # Headers (must start at line start)
        self._highlighting_rules.append((QRegularExpression(r"^#\s+.*$"), self.h1_format))
        self._highlighting_rules.append((QRegularExpression(r"^##\s+.*$"), self.h2_format))
        self._highlighting_rules.append((QRegularExpression(r"^###\s+.*$"), self.h3_format))
        self._highlighting_rules.append((QRegularExpression(r"^####+\s+.*$"), self.h4_format))

        # Horizontal rules
        self._highlighting_rules.append((QRegularExpression(r"^(\-{3,}|\*{3,}|_{3,})$"), self.hr_format))

        # Quotes
        self._highlighting_rules.append((QRegularExpression(r"^>\s+.*$"), self.quote_format))

        # Bold: **bold** or __bold__
        self._highlighting_rules.append((QRegularExpression(r"(\*\*|__)(.*?)\1"), self.bold_format))

        # Italic: *italic* or _italic_ (avoiding conflict with bold)
        self._highlighting_rules.append((QRegularExpression(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)"), self.italic_format))

        # Inline Code: `code`
        self._highlighting_rules.append((QRegularExpression(r"`([^`\n]+)`"), self.inline_code_format))

        # Markdown links: [text](url)
        self._highlighting_rules.append((QRegularExpression(r"\[([^\]]+)\]\(([^)]+)\)"), self.link_format))

        # Tags: #tag (word boundaries, not headers)
        self._highlighting_rules.append((QRegularExpression(r"(?<=\s)#[\w\d_-]+"), self.tag_format))

    def highlightBlock(self, text: str) -> None:
        """Apply formatting to the text block."""
        # 1. Check for multi-line code blocks
        is_in_code_block = self._handle_code_blocks(text)
        if is_in_code_block:
            return

        # 2. Check for Checkbox Checklist items
        cb_match = QRegularExpression(r"^(\s*[-*+]\s*\[)([ xX])(\]\s*)(.*)$").match(text)
        if cb_match.hasMatch():
            status = cb_match.captured(2)
            # Format the bracket area
            bracket_start = cb_match.capturedStart(1)
            bracket_len = cb_match.capturedLength(1) + cb_match.capturedLength(2) + cb_match.capturedLength(3)
            fmt = self.checkbox_check_format if status.lower() == "x" else self.checkbox_uncheck_format
            self.setFormat(bracket_start, bracket_len, fmt)

            # If checked, apply strikethrough to the remaining text
            if status.lower() == "x":
                text_start = cb_match.capturedStart(4)
                text_len = cb_match.capturedLength(4)
                if text_len > 0:
                    self.setFormat(text_start, text_len, self.strike_format)
                    return  # Strikethrough takes priority on checked items

        # 3. Apply standard rules
        for pattern, fmt in self._highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

    def _handle_code_blocks(self, text: str) -> bool:
        """Handle code block fences (```). Returns True if current block is part of code block."""
        # State: 1 = in code block, 0 = normal
        prev_state = self.previousBlockState()
        fence_match = re.match(r"^\s*```", text)

        if prev_state == 1:
            # We are inside a code block
            self.setFormat(0, len(text), self.code_block_format)
            if fence_match:
                self.setCurrentBlockState(0)  # Close code block
            else:
                self.setCurrentBlockState(1)
            return True
        else:
            if fence_match:
                # Open code block
                self.setFormat(0, len(text), self.code_block_format)
                self.setCurrentBlockState(1)
                return True
            else:
                self.setCurrentBlockState(0)
                return False
