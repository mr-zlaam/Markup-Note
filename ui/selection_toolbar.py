"""Floating text formatting bubble toolbar for selected text (Notion aesthetic)."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from utils.icons import (
    create_bullet_list_icon,
    create_link_icon,
    create_number_list_icon,
)


class SelectionFormatToolbar(QFrame):
    """Floating pill toolbar anchored directly above highlighted/selected text."""

    format_requested = pyqtSignal(str)  # Emits format key: "bold", "italic", "strike", "underline", "link", "code"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setObjectName("SelectionFormatToolbar")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.setStyleSheet("""
            QFrame#SelectionFormatToolbar {
                background-color: #202024;
                border: 1px solid #36363a;
                border-radius: 8px;
            }
            QPushButton#FormatBtn {
                background-color: transparent;
                color: #e0e0e4;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                padding: 0px;
                min-width: 26px;
                min-height: 26px;
            }
            QPushButton#FormatBtn:hover {
                background-color: #323238;
                color: #ffffff;
            }
            QPushButton#FormatBtn:pressed {
                background-color: #3e3e46;
            }
            QFrame#VDivider {
                background-color: #36363a;
                width: 1px;
                max-width: 1px;
                margin: 4px 2px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(2)

        # 1. Bold Button
        self.bold_btn = QPushButton("B", parent=self)
        self.bold_btn.setObjectName("FormatBtn")
        self.bold_btn.setToolTip("Bold (**text**)")
        bold_font = QFont(self.font())
        bold_font.setPointSize(11)
        bold_font.setBold(True)
        self.bold_btn.setFont(bold_font)
        self.bold_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bold_btn.clicked.connect(lambda: self.format_requested.emit("bold"))
        layout.addWidget(self.bold_btn)

        # 2. Italic Button
        self.italic_btn = QPushButton("I", parent=self)
        self.italic_btn.setObjectName("FormatBtn")
        self.italic_btn.setToolTip("Italic (*text*)")
        italic_font = QFont(self.font())
        italic_font.setPointSize(11)
        italic_font.setItalic(True)
        self.italic_btn.setFont(italic_font)
        self.italic_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.italic_btn.clicked.connect(lambda: self.format_requested.emit("italic"))
        layout.addWidget(self.italic_btn)

        # 3. Strikethrough Button
        self.strike_btn = QPushButton("S", parent=self)
        self.strike_btn.setObjectName("FormatBtn")
        self.strike_btn.setToolTip("Strikethrough (~~text~~)")
        strike_font = QFont(self.font())
        strike_font.setPointSize(11)
        strike_font.setStrikeOut(True)
        self.strike_btn.setFont(strike_font)
        self.strike_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.strike_btn.clicked.connect(lambda: self.format_requested.emit("strike"))
        layout.addWidget(self.strike_btn)

        # 4. Underline Button
        self.underline_btn = QPushButton("U", parent=self)
        self.underline_btn.setObjectName("FormatBtn")
        self.underline_btn.setToolTip("Underline (<u>text</u>)")
        underline_font = QFont(self.font())
        underline_font.setPointSize(11)
        underline_font.setUnderline(True)
        self.underline_btn.setFont(underline_font)
        self.underline_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.underline_btn.clicked.connect(lambda: self.format_requested.emit("underline"))
        layout.addWidget(self.underline_btn)

        # Divider 1
        divider1 = QFrame(parent=self)
        divider1.setObjectName("VDivider")
        divider1.setFrameShape(QFrame.Shape.VLine)
        layout.addWidget(divider1)

        # 5. Bulleted List Button
        self.bullet_btn = QPushButton(parent=self)
        self.bullet_btn.setObjectName("FormatBtn")
        self.bullet_btn.setToolTip("Bulleted List (- item)")
        self.bullet_btn.setIcon(create_bullet_list_icon(color="#d0d0d4", size=14))
        self.bullet_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bullet_btn.clicked.connect(lambda: self.format_requested.emit("bullet"))
        layout.addWidget(self.bullet_btn)

        # 6. Numbered List Button
        self.number_btn = QPushButton(parent=self)
        self.number_btn.setObjectName("FormatBtn")
        self.number_btn.setToolTip("Numbered List (1. item)")
        self.number_btn.setIcon(create_number_list_icon(color="#d0d0d4", size=14))
        self.number_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.number_btn.clicked.connect(lambda: self.format_requested.emit("number"))
        layout.addWidget(self.number_btn)

        # Divider 2
        divider2 = QFrame(parent=self)
        divider2.setObjectName("VDivider")
        divider2.setFrameShape(QFrame.Shape.VLine)
        layout.addWidget(divider2)

        # 7. Link Button
        self.link_btn = QPushButton(parent=self)
        self.link_btn.setObjectName("FormatBtn")
        self.link_btn.setToolTip("Link ([text](url))")
        self.link_btn.setIcon(create_link_icon(color="#d0d0d4", size=14))
        self.link_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.link_btn.clicked.connect(lambda: self.format_requested.emit("link"))
        layout.addWidget(self.link_btn)

        # 8. Inline Code Button
        self.code_btn = QPushButton("</>", parent=self)
        self.code_btn.setObjectName("FormatBtn")
        self.code_btn.setToolTip("Inline Code (`code`)")
        code_font = QFont("Monospace", 9)
        self.code_btn.setFont(code_font)
        self.code_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.code_btn.clicked.connect(lambda: self.format_requested.emit("code"))
        layout.addWidget(self.code_btn)

        self.adjustSize()

    def show_above_rect(self, global_rect: QRect) -> None:
        """Position and display the toolbar centered directly above the selection bounds."""
        self.adjustSize()
        bar_w = self.width()
        bar_h = self.height()

        # Center horizontally over selection
        x = global_rect.center().x() - (bar_w // 2)
        # Position 6px above top of selection
        y = global_rect.top() - bar_h - 6

        # Screen boundary checks
        screen = self.screen()
        if screen:
            geom = screen.availableGeometry()
            # If toolbar would be clipped at top, place 6px below selection instead
            if y < geom.top():
                y = global_rect.bottom() + 6
            if x < geom.left() + 8:
                x = geom.left() + 8
            elif x + bar_w > geom.right() - 8:
                x = geom.right() - bar_w - 8

        self.move(x, y)
        self.show()
        self.raise_()
