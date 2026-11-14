"""Modern modal dialog displaying visual diffs and change comparisons for modified notes."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.icons import create_badge_pixmap, create_diff_icon


class ModernDiffDialog(QDialog):
    """Sleek dark-themed diff viewer for comparing edited notes with their last backup."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        file_name: str = "",
        diff_text: str = "",
        can_revert: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Changes in {file_name}")
        self.resize(680, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.revert_requested = False

        self.setStyleSheet("""
            QDialog {
                background-color: #202024;
                color: #f0f0f0;
                border: 1px solid #36363c;
                border-radius: 12px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
            QLabel#TitleLabel {
                font-size: 15px;
                font-weight: 600;
                color: #ffffff;
            }
            QLabel#SubtitleLabel {
                font-size: 12px;
                color: #9c9ca4;
            }
            QTextEdit#DiffView {
                background-color: #161619;
                border: 1px solid #32323a;
                border-radius: 8px;
                padding: 10px;
                font-family: "JetBrains Mono", "Fira Code", monospace;
                font-size: 12px;
                line-height: 1.45;
                color: #d8d8e0;
                selection-background-color: #0a84ff;
            }
            QPushButton#PrimaryBtn {
                background-color: #0a84ff;
                color: #ffffff;
                font-weight: 600;
                border: none;
                border-radius: 7px;
                padding: 8px 18px;
                font-size: 13px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #0071e3;
            }
            QPushButton#SecondaryBtn {
                background-color: #2c2c32;
                color: #d6d6dc;
                border: 1px solid #3a3a42;
                border-radius: 7px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #383840;
                color: #ffffff;
            }
            QPushButton#DangerBtn {
                background-color: #3a1e22;
                color: #ff6961;
                border: 1px solid #5a2e34;
                border-radius: 7px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton#DangerBtn:hover {
                background-color: #4a262c;
                color: #ff8580;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # Header
        hdr_layout = QHBoxLayout()
        hdr_layout.setSpacing(12)
        hdr_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        badge_lbl = QLabel(parent=self)
        badge_lbl.setFixedSize(36, 36)
        diff_icon = create_diff_icon("#0a84ff", size=18)
        badge_lbl.setPixmap(
            create_badge_pixmap(
                diff_icon,
                bg_color="#1a2638",
                border_color="#233b5d",
                badge_size=36,
                icon_size=18,
            )
        )
        hdr_layout.addWidget(badge_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        title_lbl = QLabel(f"Comparing: {file_name}", parent=self)
        title_lbl.setObjectName("TitleLabel")
        title_vbox.addWidget(title_lbl)

        sub_lbl = QLabel("Showing lines modified compared to the latest backup snapshot.", parent=self)
        sub_lbl.setObjectName("SubtitleLabel")
        title_vbox.addWidget(sub_lbl)

        hdr_layout.addLayout(title_vbox, stretch=1)
        layout.addLayout(hdr_layout)

        # Diff View TextEdit
        self.diff_view = QTextEdit(parent=self)
        self.diff_view.setObjectName("DiffView")
        self.diff_view.setReadOnly(True)
        self._format_diff_content(diff_text)
        layout.addWidget(self.diff_view)

        # Footer Actions
        footer = QHBoxLayout()
        footer.setSpacing(10)

        if can_revert:
            self.btn_revert = QPushButton("Revert Note to Last Backup", parent=self)
            self.btn_revert.setObjectName("DangerBtn")
            self.btn_revert.setToolTip("Discard all uncommitted edits made to this note.")
            self.btn_revert.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_revert.clicked.connect(self._on_revert_clicked)
            footer.addWidget(self.btn_revert)

        footer.addStretch()

        self.btn_close = QPushButton("Close", parent=self)
        self.btn_close.setObjectName("PrimaryBtn")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.accept)
        footer.addWidget(self.btn_close)

        layout.addLayout(footer)

    def _format_diff_content(self, raw_diff: str) -> None:
        """Render unified diff with colored line blocks."""
        if not raw_diff.strip():
            self.diff_view.setPlainText("No text changes detected.")
            return

        html_lines = []
        for line in raw_diff.splitlines():
            escaped = (
                line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            if line.startswith("+") and not line.startswith("+++"):
                html_lines.append(
                    f'<div style="background-color: #14321d; color: #56d364; padding: 2px 6px; font-family: monospace;">{escaped}</div>'
                )
            elif line.startswith("-") and not line.startswith("---"):
                html_lines.append(
                    f'<div style="background-color: #381a1f; color: #f85149; padding: 2px 6px; font-family: monospace;">{escaped}</div>'
                )
            elif line.startswith("@@"):
                html_lines.append(
                    f'<div style="background-color: #1d2b3a; color: #58a6ff; padding: 2px 6px; font-weight: bold; font-family: monospace;">{escaped}</div>'
                )
            else:
                html_lines.append(
                    f'<div style="color: #9c9ca4; padding: 2px 6px; font-family: monospace;">{escaped}</div>'
                )

        self.diff_view.setHtml("".join(html_lines))

    def _on_revert_clicked(self) -> None:
        from ui.dialogs import ModernMessageDialog

        if ModernMessageDialog.confirm(
            self,
            "Revert Note",
            "Are you sure you want to discard your edits and revert this note to the last backup?",
            confirm_text="Revert Note",
        ):
            self.revert_requested = True
            self.accept()
