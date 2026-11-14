"""Modern modal dialog for connecting GitHub accounts and configuring private note vaults."""

from __future__ import annotations

from typing import Optional, Tuple

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QUrl
from PyQt6.QtGui import (
    QColor,
    QDesktopServices,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.github_client import GitHubClient, GitHubUser
from utils.icons import create_eye_icon, create_github_icon


class ModernCheckBox(QCheckBox):
    """Clean dark-themed checkbox with custom vector checkmark."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent=parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(24)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        indicator_size = 16
        y_pos = (self.height() - indicator_size) // 2
        box_rect = QRectF(0.0, float(y_pos), float(indicator_size), float(indicator_size))

        is_checked = self.isChecked()
        is_hover = self.underMouse()

        if is_checked:
            bg_color = QColor("#0071e3") if is_hover else QColor("#0a84ff")
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg_color)
            painter.drawRoundedRect(box_rect, 4.0, 4.0)

            # Draw crisp white checkmark
            pen = QPen(QColor("#ffffff"), 1.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            path = QPainterPath()
            path.moveTo(box_rect.left() + 3.8, box_rect.top() + 7.8)
            path.lineTo(box_rect.left() + 6.6, box_rect.top() + 11.2)
            path.lineTo(box_rect.left() + 12.2, box_rect.top() + 4.8)
            painter.drawPath(path)
        else:
            border_color = QColor("#5c5c68") if is_hover else QColor("#484852")
            painter.setPen(QPen(border_color, 1.2))
            painter.setBrush(QColor("#1a1a1e"))
            painter.drawRoundedRect(box_rect.adjusted(0.6, 0.6, -0.6, -0.6), 4.0, 4.0)

        # Draw label text
        if self.text():
            painter.setPen(QColor("#d0d0d8"))
            f = self.font()
            f.setPointSize(10)
            painter.setFont(f)
            text_rect = self.rect().adjusted(indicator_size + 8, 0, 0, 0)
            painter.drawText(
                text_rect,
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                self.text(),
            )

        painter.end()


class ModernGitHubAuthDialog(QDialog):
    """Sleek dark-themed modal dialog for authenticating with GitHub."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Connect GitHub Backup")
        self.setFixedWidth(480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.github_client = GitHubClient()
        self.authenticated_token: Optional[str] = None
        self.authenticated_user: Optional[GitHubUser] = None
        self.created_repo_url: Optional[str] = None

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
                font-size: 17px;
                font-weight: 600;
                color: #ffffff;
            }
            QLabel#SubtitleLabel {
                font-size: 13px;
                color: #9c9ca4;
                line-height: 1.4;
            }
            QLabel#FieldLabel {
                font-size: 12px;
                font-weight: 600;
                color: #c0c0c8;
            }
            QLabel#StatusLabel {
                font-size: 12px;
                color: #9c9ca4;
            }
            QLineEdit#ModernInput {
                background-color: #161619;
                border: 1px solid #383840;
                border-radius: 7px;
                padding: 9px 12px;
                color: #ffffff;
                font-size: 13px;
                selection-background-color: #0a84ff;
            }
            QLineEdit#ModernInput:focus {
                border: 1px solid #0a84ff;
                background-color: #1a1a1e;
            }
            QPushButton#PrimaryBtn {
                background-color: #0a84ff;
                color: #ffffff;
                font-weight: 600;
                border: none;
                border-radius: 7px;
                padding: 8px 20px;
                font-size: 13px;
                min-height: 20px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #0071e3;
            }
            QPushButton#PrimaryBtn:disabled {
                background-color: #383840;
                color: #7a7a82;
            }
            QPushButton#SecondaryBtn {
                background-color: #2c2c32;
                color: #d6d6dc;
                border: 1px solid #3a3a42;
                border-radius: 7px;
                padding: 8px 16px;
                font-size: 13px;
                min-height: 20px;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #383840;
                color: #ffffff;
            }
            QPushButton#IconButton {
                background-color: #2c2c32;
                border: 1px solid #3a3a42;
                border-radius: 7px;
                padding: 0;
            }
            QPushButton#IconButton:hover {
                background-color: #383840;
                border-color: #4a4a54;
            }
            QCheckBox {
                font-size: 12px;
                color: #d0d0d8;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #484852;
                background-color: #1a1a1e;
            }
            QCheckBox::indicator:checked {
                background-color: #0a84ff;
                border-color: #0a84ff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(14)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        # Header with GitHub Logo
        hdr_layout = QHBoxLayout()
        hdr_layout.setSpacing(12)

        logo_lbl = QLabel(parent=self)
        logo_lbl.setPixmap(create_github_icon("#ffffff", size=30).pixmap(30, 30))
        logo_lbl.setFixedSize(32, 32)
        hdr_layout.addWidget(logo_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        title_lbl = QLabel("Connect to GitHub", parent=self)
        title_lbl.setObjectName("TitleLabel")
        title_vbox.addWidget(title_lbl)

        subtitle_lbl = QLabel("Sync notes to a secure private cloud vault.", parent=self)
        subtitle_lbl.setObjectName("SubtitleLabel")
        title_vbox.addWidget(subtitle_lbl)

        hdr_layout.addLayout(title_vbox)
        layout.addLayout(hdr_layout)

        # Helper step 1: Open GitHub token generator button
        step1_box = QVBoxLayout()
        step1_box.setSpacing(4)
        step1_lbl = QLabel("1. Generate Token on GitHub", parent=self)
        step1_lbl.setObjectName("FieldLabel")
        step1_box.addWidget(step1_lbl)

        step1_hint = QLabel(
            "Scope 'repo' is pre-selected. Simply scroll down and click 'Generate token'.",
            parent=self,
        )
        step1_hint.setStyleSheet("font-size: 11px; color: #8e8e93;")
        step1_box.addWidget(step1_hint)

        btn_open_github = QPushButton("Open GitHub Token Generator", parent=self)
        btn_open_github.setObjectName("SecondaryBtn")
        btn_open_github.setFixedHeight(36)
        btn_open_github.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_github.clicked.connect(self._open_token_page)
        step1_box.addWidget(btn_open_github)
        layout.addLayout(step1_box)

        # Helper step 2: Paste token input
        step2_box = QVBoxLayout()
        step2_box.setSpacing(6)
        step2_lbl = QLabel("2. Paste Personal Access Token", parent=self)
        step2_lbl.setObjectName("FieldLabel")
        step2_box.addWidget(step2_lbl)

        token_row = QHBoxLayout()
        token_row.setSpacing(8)
        self.token_input = QLineEdit(parent=self)
        self.token_input.setObjectName("ModernInput")
        self.token_input.setFixedHeight(38)
        self.token_input.setPlaceholderText("ghp_xxxxxxxxxxxxxxxxxxxx")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.returnPressed.connect(self._do_verify_and_connect)
        self.token_input.textChanged.connect(self._on_token_changed)
        token_row.addWidget(self.token_input)

        self.btn_show_token = QPushButton(parent=self)
        self.btn_show_token.setObjectName("IconButton")
        self.btn_show_token.setFixedSize(38, 38)
        self.btn_show_token.setIcon(create_eye_icon(open_eye=True, color="#9c9ca4", size=16))
        self.btn_show_token.setIconSize(QSize(18, 18))
        self.btn_show_token.setToolTip("Show token")
        self.btn_show_token.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_show_token.clicked.connect(self._toggle_echo_mode)
        token_row.addWidget(self.btn_show_token)
        step2_box.addLayout(token_row)
        layout.addLayout(step2_box)

        # Auto-create private repo checkbox
        self.chk_create_repo = ModernCheckBox("Create private repository 'markup-notes' automatically", parent=self)
        self.chk_create_repo.setChecked(True)
        layout.addWidget(self.chk_create_repo)

        # Status feedback with reserved minimum height so dialog layout never jumps or compresses
        self.status_lbl = QLabel("", parent=self)
        self.status_lbl.setObjectName("StatusLabel")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setMinimumHeight(32)
        layout.addWidget(self.status_lbl)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel", parent=self)
        self.btn_cancel.setObjectName("SecondaryBtn")
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_connect = QPushButton("Connect", parent=self)
        self.btn_connect.setObjectName("PrimaryBtn")
        self.btn_connect.setFixedHeight(36)
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self._do_verify_and_connect)
        btn_layout.addWidget(self.btn_connect)

        layout.addLayout(btn_layout)

        # Auto-fill if system already has token
        saved_token = self.github_client.get_token()
        if saved_token:
            self.token_input.setText(saved_token)

    def _open_token_page(self) -> None:
        """Open browser to the official GitHub Personal Access Token creation page."""
        QDesktopServices.openUrl(QUrl(self.github_client.TOKEN_GENERATE_URL))
        self.status_lbl.setStyleSheet("color: #0a84ff;")
        self.status_lbl.setText("Opened GitHub in browser. Scroll to the bottom and click 'Generate token'.")
        self.adjustSize()

    def _toggle_echo_mode(self) -> None:
        if self.token_input.echoMode() == QLineEdit.EchoMode.Password:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_show_token.setIcon(create_eye_icon(open_eye=False, color="#0a84ff", size=16))
            self.btn_show_token.setToolTip("Hide token")
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_show_token.setIcon(create_eye_icon(open_eye=True, color="#9c9ca4", size=16))
            self.btn_show_token.setToolTip("Show token")

    def _on_token_changed(self) -> None:
        self.status_lbl.setText("")

    def _do_verify_and_connect(self) -> None:
        """Verify token with GitHub, optionally create private repository, and save."""
        token = self.token_input.text().strip()
        if not token:
            self.status_lbl.setStyleSheet("color: #ff453a;")
            self.status_lbl.setText("Please enter your GitHub token.")
            self.adjustSize()
            return

        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("Verifying...")
        self.status_lbl.setStyleSheet("color: #9c9ca4;")
        self.status_lbl.setText("Connecting to GitHub API...")
        self.adjustSize()

        ok, user, msg = self.github_client.verify_token(token)
        if not ok or user is None:
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText("Connect")
            self.status_lbl.setStyleSheet("color: #ff453a;")
            if "expired" in msg.lower() or "invalid" in msg.lower() or "401" in msg.lower():
                self.status_lbl.setText("GitHub token is invalid or expired. Please generate a new token above.")
            else:
                self.status_lbl.setText(f"Error: {msg}")
            self.adjustSize()
            return

        self.authenticated_token = token
        self.authenticated_user = user
        repo_url = ""

        # Create private repo if requested
        if self.chk_create_repo.isChecked():
            self.status_lbl.setText(f"Signed in as @{user.login}. Setting up private repository...")
            ok_r, repo, r_msg = self.github_client.create_private_repo(
                token=token,
                repo_name="markup-notes",
                description="My Markup Notes vault backup",
            )
            if ok_r and repo is not None:
                repo_url = repo.clone_url
                self.created_repo_url = repo_url

        self.github_client.save_token(token=token, login=user.login, repo_url=repo_url)

        self.status_lbl.setStyleSheet("color: #30d158;")
        self.status_lbl.setText(f"Successfully connected as @{user.login}!")
        self.accept()

    @classmethod
    def execute(cls, parent: Optional[QWidget] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Launch GitHub connection dialog. Returns (accepted, token, repo_url)."""
        dlg = cls(parent=parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return (True, dlg.authenticated_token, dlg.created_repo_url)
        return (False, None, None)
