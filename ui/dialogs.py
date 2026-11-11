"""Modern, sleek dialogs matching the Apple Notes aesthetic."""

from typing import Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ModernInputDialog(QDialog):
    """A sleek, modern dark-themed input dialog replacing dinosaur QInputDialog."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "New Folder",
        prompt: str = "Enter folder name:",
        default_text: str = "",
        confirm_text: str = "Create",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.setStyleSheet("""
            QDialog {
                background-color: #202024;
                color: #f0f0f0;
                border: 1px solid #36363c;
                border-radius: 12px;
            }
            QLabel {
                background-color: transparent !important;
                background: transparent !important;
                border: none !important;
            }
            QLabel#TitleLabel {
                font-size: 16px;
                font-weight: 600;
                color: #ffffff;
            }
            QLabel#PromptLabel {
                font-size: 13px;
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
                padding: 9px 20px;
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
                padding: 9px 18px;
                font-size: 13px;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #383840;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(14)

        # Title
        title_lbl = QLabel(title, parent=self)
        title_lbl.setObjectName("TitleLabel")
        layout.addWidget(title_lbl)

        # Prompt
        if prompt:
            prompt_lbl = QLabel(prompt, parent=self)
            prompt_lbl.setObjectName("PromptLabel")
            layout.addWidget(prompt_lbl)

        # Input field
        self.input_field = QLineEdit(parent=self)
        self.input_field.setObjectName("ModernInput")
        self.input_field.setText(default_text)
        self.input_field.returnPressed.connect(self.accept)
        layout.addWidget(self.input_field)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel", parent=self)
        self.cancel_btn.setObjectName("SecondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton(confirm_text, parent=self)
        self.ok_btn.setObjectName("PrimaryBtn")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)

        layout.addLayout(btn_layout)

    @classmethod
    def get_text(
        cls,
        parent: Optional[QWidget],
        title: str,
        prompt: str = "",
        default: str = "",
        confirm_text: str = "Create",
    ) -> Tuple[str, bool]:
        """Show modern input dialog and return (text, accepted)."""
        dlg = cls(
            parent=parent,
            title=title,
            prompt=prompt,
            default_text=default,
            confirm_text=confirm_text,
        )
        dlg.input_field.setFocus()
        accepted = dlg.exec() == QDialog.DialogCode.Accepted
        return dlg.input_field.text().strip(), accepted


class ModernConfirmDialog(QDialog):
    """A sleek, modern dark-themed confirmation dialog replacing QMessageBox."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_text: str = "Delete",
        is_destructive: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        confirm_btn_bg = "#e03e3e" if is_destructive else "#0a84ff"
        confirm_btn_hover = "#f04848" if is_destructive else "#0071e3"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #202024;
                color: #f0f0f0;
                border: 1px solid #36363c;
                border-radius: 12px;
            }}
            QLabel {{
                background-color: transparent !important;
                background: transparent !important;
                border: none !important;
            }}
            QLabel#TitleLabel {{
                font-size: 16px;
                font-weight: 600;
                color: #ffffff;
            }}
            QLabel#MessageLabel {{
                font-size: 13px;
                color: #9c9ca4;
                line-height: 1.45;
            }}
            QPushButton#ConfirmBtn {{
                background-color: {confirm_btn_bg};
                color: #ffffff;
                font-weight: 600;
                border: none;
                border-radius: 7px;
                padding: 9px 20px;
                font-size: 13px;
            }}
            QPushButton#ConfirmBtn:hover {{
                background-color: {confirm_btn_hover};
            }}
            QPushButton#SecondaryBtn {{
                background-color: #2c2c32;
                color: #d6d6dc;
                border: 1px solid #3a3a42;
                border-radius: 7px;
                padding: 9px 18px;
                font-size: 13px;
            }}
            QPushButton#SecondaryBtn:hover {{
                background-color: #383840;
                color: #ffffff;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(14)

        # Title
        title_lbl = QLabel(title, parent=self)
        title_lbl.setObjectName("TitleLabel")
        layout.addWidget(title_lbl)

        # Message
        msg_lbl = QLabel(message, parent=self)
        msg_lbl.setObjectName("MessageLabel")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel", parent=self)
        self.cancel_btn.setObjectName("SecondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.confirm_btn = QPushButton(confirm_text, parent=self)
        self.confirm_btn.setObjectName("ConfirmBtn")
        self.confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_btn)

        layout.addLayout(btn_layout)

    @classmethod
    def ask(
        cls,
        parent: Optional[QWidget],
        title: str,
        message: str,
        confirm_text: str = "Delete",
        is_destructive: bool = True,
    ) -> bool:
        """Show modern confirmation dialog and return True if confirmed."""
        dlg = cls(
            parent=parent,
            title=title,
            message=message,
            confirm_text=confirm_text,
            is_destructive=is_destructive,
        )
        return dlg.exec() == QDialog.DialogCode.Accepted
