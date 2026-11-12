"""Modern, sleek dialogs matching the Apple Notes aesthetic."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
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


class ModernLinkDialog(QDialog):
    """A sleek, modern dark-themed modal dialog for inserting or editing markdown links."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        initial_text: str = "",
        initial_url: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Insert Link")
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
            QLabel#FieldLabel {
                font-size: 12px;
                font-weight: 500;
                color: #9c9ca4;
            }
            QLineEdit#ModernInput {
                background-color: #161619;
                border: 1px solid #383840;
                border-radius: 7px;
                padding: 8px 12px;
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
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #0071e3;
            }
            QPushButton#SecondaryBtn {
                background-color: #2c2c32;
                color: #d6d6dc;
                border: 1px solid #3a3a42;
                border-radius: 7px;
                padding: 8px 18px;
                font-size: 13px;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #383840;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(12)

        # Title
        title_lbl = QLabel("Insert Link", parent=self)
        title_lbl.setObjectName("TitleLabel")
        layout.addWidget(title_lbl)

        # Field 1: Text
        text_lbl = QLabel("Text", parent=self)
        text_lbl.setObjectName("FieldLabel")
        layout.addWidget(text_lbl)

        self.text_input = QLineEdit(parent=self)
        self.text_input.setObjectName("ModernInput")
        self.text_input.setPlaceholderText("Link title or label")
        self.text_input.setText(initial_text)
        self.text_input.returnPressed.connect(self._on_enter_pressed)
        layout.addWidget(self.text_input)

        # Field 2: Link URL
        url_lbl = QLabel("Link", parent=self)
        url_lbl.setObjectName("FieldLabel")
        layout.addWidget(url_lbl)

        self.url_input = QLineEdit(parent=self)
        self.url_input.setObjectName("ModernInput")
        self.url_input.setPlaceholderText("https://example.com")
        self.url_input.setText(initial_url)
        self.url_input.returnPressed.connect(self._on_enter_pressed)
        layout.addWidget(self.url_input)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel", parent=self)
        self.cancel_btn.setObjectName("SecondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("Insert", parent=self)
        self.ok_btn.setObjectName("PrimaryBtn")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)

        layout.addLayout(btn_layout)

        # Smart focus management
        if initial_text:
            self.url_input.setFocus()
            if initial_url:
                self.url_input.selectAll()
        else:
            self.text_input.setFocus()

    def _on_enter_pressed(self) -> None:
        """Advance to URL field if text was filled on enter, otherwise accept."""
        if self.sender() is self.text_input and not self.url_input.text().strip():
            self.url_input.setFocus()
        else:
            self.accept()

    @classmethod
    def get_link_data(
        cls,
        parent: Optional[QWidget],
        initial_text: str = "",
        initial_url: str = "",
    ) -> Tuple[str, str, bool]:
        """Launch modern link modal and return (text, url, accepted)."""
        dlg = cls(parent=parent, initial_text=initial_text, initial_url=initial_url)
        accepted = dlg.exec() == QDialog.DialogCode.Accepted
        if not accepted:
            return ("", "", False)
        return dlg.text_input.text().strip(), dlg.url_input.text().strip(), True


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


class ModernColorDialog(QColorDialog):
    """Sleek, modernized color picker dialog matching Apple Notes dark theme."""

    def __init__(
        self,
        initial: Optional[QColor] = None,
        parent: Optional[QWidget] = None,
        title: str = "Select Color",
    ) -> None:
        super().__init__(initial if initial is not None else QColor("#0a84ff"), parent)
        self.setWindowTitle(title)
        self.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        self._modernize_ui()

    def _modernize_ui(self) -> None:
        """Strip legacy Qt icons and apply sleek dark theme styling."""
        # Modernize OK and Cancel buttons
        btn_box = self.findChild(QDialogButtonBox)
        if btn_box is not None:
            for btn in btn_box.buttons():
                btn.setIcon(QIcon())
                btn.setIconSize(QSize(0, 0))
                role = btn_box.buttonRole(btn)
                if role in (
                    QDialogButtonBox.ButtonRole.AcceptRole,
                    QDialogButtonBox.ButtonRole.YesRole,
                ):
                    btn.setText("Apply")
                    btn.setObjectName("ModernPrimaryBtn")
                else:
                    btn.setText("Cancel")
                    btn.setObjectName("ModernCancelBtn")

        # Modernize remaining buttons (e.g. 'Add to Custom Colors', 'Pick Screen Color')
        for btn in self.findChildren(QPushButton):
            btn.setIcon(QIcon())
            btn.setIconSize(QSize(0, 0))
            txt = btn.text().replace("&", "")
            btn.setText(txt)
            if btn.objectName() not in ("ModernPrimaryBtn", "ModernCancelBtn"):
                btn.setObjectName("ModernSecondaryBtn")

        # Strip mnemonic '&' from all labels
        for lbl in self.findChildren(QLabel):
            if "&" in lbl.text():
                lbl.setText(lbl.text().replace("&", ""))

        self.setStyleSheet("""
            QColorDialog {
                background-color: #242426;
                border: 1px solid #38383a;
                border-radius: 12px;
            }
            QLabel {
                color: #d1d1d6;
                background: transparent !important;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit, QSpinBox {
                background-color: #1a1a1c;
                color: #ffffff;
                border: 1px solid #3a3a3c;
                border-radius: 6px;
                padding: 4px 6px;
                font-size: 12px;
                selection-background-color: #0a84ff;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #0a84ff;
                background-color: #141416;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #2c2c30;
                border: none;
                width: 14px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #3a3a40;
            }
            QPushButton#ModernPrimaryBtn {
                background-color: #0a84ff;
                color: #ffffff;
                border: 1px solid #0071e3;
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton#ModernPrimaryBtn:hover {
                background-color: #0071e3;
            }
            QPushButton#ModernPrimaryBtn:pressed {
                background-color: #005bb5;
            }
            QPushButton#ModernCancelBtn, QPushButton#ModernSecondaryBtn {
                background-color: #323236;
                color: #f2f2f7;
                border: 1px solid #444448;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 13px;
                font-weight: 500;
                min-width: 70px;
            }
            QPushButton#ModernCancelBtn:hover, QPushButton#ModernSecondaryBtn:hover {
                background-color: #3e3e44;
                border: 1px solid #55555c;
            }
        """)

    @classmethod
    def get_color(
        cls,
        initial: Optional[QColor] = None,
        parent: Optional[QWidget] = None,
        title: str = "Select Color",
    ) -> QColor:
        """Static convenience method matching QColorDialog.getColor with modern styling."""
        dialog = cls(initial=initial, parent=parent, title=title)
        if dialog.exec() == QColorDialog.DialogCode.Accepted:
            return dialog.selectedColor()
        return QColor()


class ModernMessageDialog(QDialog):
    """Sleek dark-themed message / alert / confirmation dialog."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "Alert",
        message: str = "",
        confirm_text: str = "OK",
        cancel_text: Optional[str] = None,
        is_error: bool = False,
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
                background: transparent;
                border: none;
            }
            QLabel#TitleLabel {
                font-size: 16px;
                font-weight: 600;
                color: #ffffff;
            }
            QLabel#MessageLabel {
                font-size: 13px;
                color: #a0a0a8;
                line-height: 1.4;
            }
            QPushButton#PrimaryBtn {
                background-color: #0a84ff;
                color: #ffffff;
                font-weight: 600;
                border: none;
                border-radius: 7px;
                padding: 9px 22px;
                font-size: 13px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #0071e3;
            }
            QPushButton#ErrorPrimaryBtn {
                background-color: #e03e3e;
                color: #ffffff;
                font-weight: 600;
                border: none;
                border-radius: 7px;
                padding: 9px 22px;
                font-size: 13px;
            }
            QPushButton#ErrorPrimaryBtn:hover {
                background-color: #c93434;
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

        title_lbl = QLabel(title, parent=self)
        title_lbl.setObjectName("TitleLabel")
        layout.addWidget(title_lbl)

        msg_lbl = QLabel(message, parent=self)
        msg_lbl.setObjectName("MessageLabel")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        if cancel_text:
            cancel_btn = QPushButton(cancel_text, parent=self)
            cancel_btn.setObjectName("SecondaryBtn")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_text, parent=self)
        confirm_btn.setObjectName("ErrorPrimaryBtn" if is_error and not cancel_text else "PrimaryBtn")
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    @classmethod
    def show_error(cls, parent: Optional[QWidget], title: str, message: str) -> None:
        """Display an error alert modal."""
        dlg = cls(parent=parent, title=title, message=message, confirm_text="OK", is_error=True)
        dlg.exec()

    @classmethod
    def show_info(cls, parent: Optional[QWidget], title: str, message: str) -> None:
        """Display an informational modal."""
        dlg = cls(parent=parent, title=title, message=message, confirm_text="OK", is_error=False)
        dlg.exec()

    @classmethod
    def confirm(
        cls,
        parent: Optional[QWidget],
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
    ) -> bool:
        """Display a confirmation modal and return True if accepted."""
        dlg = cls(
            parent=parent,
            title=title,
            message=message,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            is_error=False,
        )
        return dlg.exec() == QDialog.DialogCode.Accepted


class ModernExportDialog(QDialog):
    """Sleek, dark-mode export dialog for generating PDF, HTML, or Markdown."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        note_title: str = "Untitled",
        markdown_content: str = "",
    ) -> None:
        super().__init__(parent)
        from pathlib import Path
        from utils.exporter import export_note_to_html, export_note_to_pdf

        self.note_title = note_title
        self.markdown_content = markdown_content
        self.exported_path: Optional[Path] = None

        self.setWindowTitle("Export Note")
        self.setFixedWidth(520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Default export directory: ~/Documents or ~/
        doc_dir = Path.home() / "Documents"
        self._target_dir: Path = doc_dir if doc_dir.exists() else Path.home()
        self._format_mode: str = "pdf"  # "pdf", "html_dark", "html_light", "md"

        safe_title = "".join(c for c in note_title if c.isalnum() or c in (" ", "-", "_")).strip() or "Untitled"
        self._base_name = safe_title

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
            QLabel#DialogTitle {
                font-size: 17px;
                font-weight: 600;
                color: #ffffff;
            }
            QLabel#FieldLabel {
                font-size: 12px;
                font-weight: 600;
                color: #8e8e96;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QLineEdit#ExportInput {
                background-color: #161619;
                border: 1px solid #383840;
                border-radius: 7px;
                padding: 9px 12px;
                color: #ffffff;
                font-size: 13px;
                selection-background-color: #0a84ff;
            }
            QLineEdit#ExportInput:focus {
                border: 1px solid #0a84ff;
                background-color: #1a1a1e;
            }
            QPushButton#FormatTabBtn {
                background-color: #2c2c32;
                color: #b0b0b8;
                border: 1px solid #3a3a42;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton#FormatTabBtn:hover {
                background-color: #383840;
                color: #ffffff;
            }
            QPushButton#FormatTabBtn:checked {
                background-color: #0a84ff;
                color: #ffffff;
                border-color: #0a84ff;
                font-weight: 600;
            }
            QPushButton#FolderChipBtn {
                background-color: #24242a;
                color: #c4c4cc;
                border: 1px solid #383840;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton#FolderChipBtn:hover {
                background-color: #32323a;
                color: #ffffff;
            }
            QPushButton#FolderChipBtn:checked {
                background-color: #363640;
                color: #ffffff;
                border-color: #0a84ff;
            }
            QPushButton#PrimaryExportBtn {
                background-color: #0a84ff;
                color: #ffffff;
                font-weight: 600;
                border: none;
                border-radius: 7px;
                padding: 9px 22px;
                font-size: 13px;
            }
            QPushButton#PrimaryExportBtn:hover {
                background-color: #0071e3;
            }
            QPushButton#CancelExportBtn {
                background-color: #2c2c32;
                color: #d6d6dc;
                border: 1px solid #3a3a42;
                border-radius: 7px;
                padding: 9px 18px;
                font-size: 13px;
            }
            QPushButton#CancelExportBtn:hover {
                background-color: #383840;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(14)

        # 1. Title
        title_lbl = QLabel("Export Note", parent=self)
        title_lbl.setObjectName("DialogTitle")
        layout.addWidget(title_lbl)

        # 2. Format Selector
        fmt_lbl = QLabel("Export Format", parent=self)
        fmt_lbl.setObjectName("FieldLabel")
        layout.addWidget(fmt_lbl)

        fmt_layout = QHBoxLayout()
        fmt_layout.setSpacing(6)

        self.btn_pdf = QPushButton("PDF Document", parent=self)
        self.btn_pdf.setObjectName("FormatTabBtn")
        self.btn_pdf.setCheckable(True)
        self.btn_pdf.setChecked(True)
        self.btn_pdf.clicked.connect(lambda: self._set_format("pdf"))
        fmt_layout.addWidget(self.btn_pdf)

        self.btn_html_dark = QPushButton("HTML (Dark)", parent=self)
        self.btn_html_dark.setObjectName("FormatTabBtn")
        self.btn_html_dark.setCheckable(True)
        self.btn_html_dark.clicked.connect(lambda: self._set_format("html_dark"))
        fmt_layout.addWidget(self.btn_html_dark)

        self.btn_html_light = QPushButton("HTML (Light)", parent=self)
        self.btn_html_light.setObjectName("FormatTabBtn")
        self.btn_html_light.setCheckable(True)
        self.btn_html_light.clicked.connect(lambda: self._set_format("html_light"))
        fmt_layout.addWidget(self.btn_html_light)

        self.btn_md = QPushButton("Markdown", parent=self)
        self.btn_md.setObjectName("FormatTabBtn")
        self.btn_md.setCheckable(True)
        self.btn_md.clicked.connect(lambda: self._set_format("md"))
        fmt_layout.addWidget(self.btn_md)

        layout.addLayout(fmt_layout)

        # 3. File Name Input
        name_lbl = QLabel("File Name", parent=self)
        name_lbl.setObjectName("FieldLabel")
        layout.addWidget(name_lbl)

        self.filename_input = QLineEdit(f"{self._base_name}.pdf", parent=self)
        self.filename_input.setObjectName("ExportInput")
        layout.addWidget(self.filename_input)

        # 4. Save Location
        loc_lbl = QLabel("Save Destination", parent=self)
        loc_lbl.setObjectName("FieldLabel")
        layout.addWidget(loc_lbl)

        # Folder location row
        loc_row = QHBoxLayout()
        loc_row.setSpacing(6)

        self.btn_chip_docs = QPushButton("Documents", parent=self)
        self.btn_chip_docs.setObjectName("FolderChipBtn")
        self.btn_chip_docs.setCheckable(True)
        self.btn_chip_docs.clicked.connect(lambda: self._set_dest_dir(Path.home() / "Documents"))
        loc_row.addWidget(self.btn_chip_docs)

        self.btn_chip_down = QPushButton("Downloads", parent=self)
        self.btn_chip_down.setObjectName("FolderChipBtn")
        self.btn_chip_down.setCheckable(True)
        self.btn_chip_down.clicked.connect(lambda: self._set_dest_dir(Path.home() / "Downloads"))
        loc_row.addWidget(self.btn_chip_down)

        self.btn_chip_desk = QPushButton("Desktop", parent=self)
        self.btn_chip_desk.setObjectName("FolderChipBtn")
        self.btn_chip_desk.setCheckable(True)
        self.btn_chip_desk.clicked.connect(lambda: self._set_dest_dir(Path.home() / "Desktop"))
        loc_row.addWidget(self.btn_chip_desk)

        self.btn_browse = QPushButton("Browse Other...", parent=self)
        self.btn_browse.setObjectName("FolderChipBtn")
        self.btn_browse.setCheckable(True)
        self.btn_browse.clicked.connect(self._browse_custom_dir)
        loc_row.addWidget(self.btn_browse)

        layout.addLayout(loc_row)

        self.path_display = QLabel(str(self._target_dir), parent=self)
        self.path_display.setStyleSheet("font-size: 11px; color: #787882; padding-left: 2px;")
        layout.addWidget(self.path_display)

        self._update_chip_styles()

        # 5. Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel", parent=self)
        cancel_btn.setObjectName("CancelExportBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.export_action_btn = QPushButton("Export Note", parent=self)
        self.export_action_btn.setObjectName("PrimaryExportBtn")
        self.export_action_btn.clicked.connect(self._do_export)
        btn_layout.addWidget(self.export_action_btn)

        layout.addLayout(btn_layout)

    def _set_format(self, fmt: str) -> None:
        self._format_mode = fmt
        self.btn_pdf.setChecked(fmt == "pdf")
        self.btn_html_dark.setChecked(fmt == "html_dark")
        self.btn_html_light.setChecked(fmt == "html_light")
        self.btn_md.setChecked(fmt == "md")

        ext = ".pdf" if fmt == "pdf" else (".html" if "html" in fmt else ".md")
        cur_text = self.filename_input.text().strip()
        from pathlib import Path
        stem = Path(cur_text).stem if cur_text else self._base_name
        self.filename_input.setText(f"{stem}{ext}")

    def _set_dest_dir(self, directory: Path) -> None:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            self._target_dir = directory
            self.path_display.setText(str(directory))
            self._update_chip_styles()
        except OSError:
            pass

    def _update_chip_styles(self) -> None:
        from pathlib import Path
        home = Path.home()
        self.btn_chip_docs.setChecked(self._target_dir == home / "Documents")
        self.btn_chip_down.setChecked(self._target_dir == home / "Downloads")
        self.btn_chip_desk.setChecked(self._target_dir == home / "Desktop")
        self.btn_browse.setChecked(
            self._target_dir not in (home / "Documents", home / "Downloads", home / "Desktop")
        )

    def _browse_custom_dir(self) -> None:
        from PyQt6.QtWidgets import QFileDialog
        chosen = QFileDialog.getExistingDirectory(self, "Choose Export Directory", str(self._target_dir))
        if chosen:
            self._set_dest_dir(Path(chosen))

    def _do_export(self) -> None:
        from pathlib import Path
        from utils.exporter import export_note_to_html, export_note_to_pdf

        filename = self.filename_input.text().strip()
        if not filename:
            ModernMessageDialog.show_error(self, "Invalid File Name", "Please enter a valid file name.")
            return

        target_file = self._target_dir / filename
        if target_file.exists():
            overwrite = ModernMessageDialog.confirm(
                self,
                "File Exists",
                f"A file named '{filename}' already exists in this folder.\nDo you want to overwrite it?",
                confirm_text="Overwrite",
                cancel_text="Cancel",
            )
            if not overwrite:
                return

        ok = False
        if self._format_mode == "pdf":
            ok = export_note_to_pdf(self.note_title, self.markdown_content, target_file)
        elif self._format_mode == "html_dark":
            ok = export_note_to_html(self.note_title, self.markdown_content, target_file, dark_theme=True)
        elif self._format_mode == "html_light":
            ok = export_note_to_html(self.note_title, self.markdown_content, target_file, dark_theme=False)
        else:
            try:
                target_file.write_text(self.markdown_content, encoding="utf-8")
                ok = True
            except Exception:
                ok = False

        if ok:
            self.exported_path = target_file
            self.accept()
        else:
            ModernMessageDialog.show_error(self, "Export Failed", "An error occurred while saving the exported file.")

    @classmethod
    def execute_export(
        cls, parent: Optional[QWidget], note_title: str, markdown_content: str
    ) -> Optional[Path]:
        """Launch the modern export modal and return the exported file Path on success."""
        dlg = cls(parent=parent, note_title=note_title, markdown_content=markdown_content)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.exported_path
        return None

