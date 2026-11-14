"""Built-in Git & GitHub backup source control side panel with non-tech visual interface."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QModelIndex, QRectF, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from core.config import ConfigManager
from core.git_manager import GitCommit, GitManager, GitStatus
from core.github_client import GitHubClient
from core.storage import StorageManager
from ui.github_auth_dialog import ModernGitHubAuthDialog
from utils.icons import (
    create_backup_icon,
    create_close_icon,
    create_github_icon,
    create_markdown_icon,
    create_sync_icon,
)


class ToggleSwitch(QCheckBox):
    """Modern iOS / macOS style pill toggle switch."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(34, 18)
        self.setText("")

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_on = self.isChecked()
        track_color = QColor("#30d158") if is_on else QColor("#3a3a40")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(0, 1, 34, 16, 8, 8)

        thumb_x = 19 if is_on else 3
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(thumb_x, 3, 12, 12)
        painter.end()


class ChangeItemDelegate(QStyledItemDelegate):
    """Custom painter for changed note items with clean badge pills and hover states."""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), 36)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect.adjusted(2, 2, -2, -2)
        is_hover = bool(option.state & option.state.State_MouseOver)
        is_selected = bool(option.state & option.state.State_Selected)

        if is_selected:
            painter.setBrush(QColor("#2a2a2e"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
        elif is_hover:
            painter.setBrush(QColor("#242428"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)

        # Title text
        title = index.data(Qt.ItemDataRole.DisplayRole) or ""
        badge = index.data(Qt.ItemDataRole.UserRole + 1) or "Edited"

        if badge == "Clean":
            painter.setPen(QColor("#7a7a82"))
            f = QFont(option.font)
            f.setPointSize(10)
            painter.setFont(f)
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), title)
            painter.restore()
            return

        # Markdown icon
        icon_pix = create_markdown_icon("#8e8e93", size=13).pixmap(13, 13)
        painter.drawPixmap(rect.left() + 8, rect.top() + (rect.height() - 13) // 2, icon_pix)

        painter.setPen(QColor("#ececec"))
        f = QFont(option.font)
        f.setPointSize(10)
        f.setBold(False)
        painter.setFont(f)

        # Truncate title if needed to prevent overlap with badge
        avail_w = rect.width() - 85
        fm = painter.fontMetrics()
        elided = fm.elidedText(title, Qt.TextElideMode.ElideMiddle, avail_w)
        painter.drawText(rect.left() + 28, rect.top() + (rect.height() + fm.ascent() - fm.descent()) // 2, elided)

        # Badge Pill
        b_w, b_h = 44, 18
        bx = rect.right() - b_w - 6
        by = rect.top() + (rect.height() - b_h) // 2
        b_rect = QRectF(float(bx), float(by), float(b_w), float(b_h))

        if badge == "New":
            bg_col, txt_col = QColor("#14321d"), QColor("#56d364")
        elif badge == "Deleted":
            bg_col, txt_col = QColor("#381a1f"), QColor("#f85149")
        else:
            bg_col, txt_col = QColor("#14283c"), QColor("#58a6ff")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_col)
        painter.drawRoundedRect(b_rect, 4, 4)

        bf = QFont(option.font)
        bf.setPointSize(9)
        bf.setBold(True)
        painter.setFont(bf)
        painter.setPen(txt_col)
        painter.drawText(b_rect, int(Qt.AlignmentFlag.AlignCenter), badge)

        painter.restore()


class HistoryItemDelegate(QStyledItemDelegate):
    """Custom painter for recent backup commit rows."""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), 46)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect.adjusted(2, 2, -2, -2)
        is_hover = bool(option.state & option.state.State_MouseOver)
        is_selected = bool(option.state & option.state.State_Selected)

        if is_selected:
            painter.setBrush(QColor("#2a2a2e"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
        elif is_hover:
            painter.setBrush(QColor("#242428"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)

        msg = index.data(Qt.ItemDataRole.DisplayRole) or ""
        sub = index.data(Qt.ItemDataRole.UserRole + 1) or ""

        # Line 1: Message
        painter.setPen(QColor("#ececec"))
        f = QFont(option.font)
        f.setPointSize(10)
        f.setBold(False)
        painter.setFont(f)
        fm = painter.fontMetrics()
        elided_msg = fm.elidedText(msg, Qt.TextElideMode.ElideRight, rect.width() - 16)
        painter.drawText(rect.left() + 8, rect.top() + 18, elided_msg)

        # Line 2: Subtitle
        painter.setPen(QColor("#7a7a82"))
        sf = QFont(option.font)
        sf.setPointSize(9)
        painter.setFont(sf)
        painter.drawText(rect.left() + 8, rect.top() + 34, sub)

        painter.restore()


class SyncWorker(QThread):
    """Background worker thread executing Git synchronization without blocking the GUI."""

    finished = pyqtSignal(bool, str)

    def __init__(self, git_manager: GitManager, message: Optional[str] = None) -> None:
        super().__init__()
        self.git_manager = git_manager
        self.message = message

    def run(self) -> None:
        ok, msg = self.git_manager.sync(message=self.message)
        self.finished.emit(ok, msg)


class BackupPanel(QWidget):
    """Collapsible right-side drawer panel providing non-technical Git backup and versioning."""

    close_requested = pyqtSignal()
    changes_updated = pyqtSignal(int)  # Emits total pending unbacked changes count
    note_reverted = pyqtSignal(str)   # Emits relative path of note when reverted
    sync_completed = pyqtSignal(bool, str)  # Emits (success, message) on sync completion

    def __init__(
        self,
        storage_manager: StorageManager,
        config_manager: Optional[ConfigManager] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)
        self.storage = storage_manager
        self.config_manager = config_manager
        self.git_manager = GitManager(self.storage.root_dir)
        self.github_client = GitHubClient()
        self._sync_thread: Optional[SyncWorker] = None

        self._auto_backup_timer = QTimer(self)
        self._auto_backup_timer.setSingleShot(True)
        self._auto_backup_timer.setInterval(2500)
        self._auto_backup_timer.timeout.connect(self._on_auto_backup_timer_fired)

        self.setObjectName("BackupPanel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)

        self._init_ui()

        if self.config_manager:
            self.toggle_auto_backup.setChecked(self.config_manager.get_auto_backup())
        self.toggle_auto_backup.toggled.connect(self._on_auto_backup_toggled)

        self.refresh_status()

    def _init_ui(self) -> None:
        self.setStyleSheet("""
            QWidget#BackupPanel {
                background-color: #1e1e1e;
                border-left: 1px solid #2b2b2b;
            }
            QLabel {
                background: transparent;
                border: none;
            }
            QLabel#PanelHeaderTitle {
                font-size: 11px;
                font-weight: 600;
                color: #888888;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            QLabel#SectionHeader {
                font-size: 11px;
                font-weight: 600;
                color: #888888;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            QPushButton#SyncBtn {
                background-color: #2c2c30;
                color: #f3f3f3;
                border: 1px solid #3c3c44;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton#SyncBtn:hover {
                background-color: #383840;
                border-color: #0a84ff;
                color: #ffffff;
            }
            QPushButton#SyncBtn:pressed {
                background-color: #242428;
            }
            QPushButton#SyncBtn:disabled {
                background-color: #222226;
                border-color: #2a2a30;
                color: #606068;
            }
            QPushButton#LinkBtn {
                background: transparent;
                border: none;
                color: #7a7a82;
                font-size: 11px;
                padding: 2px 4px;
            }
            QPushButton#LinkBtn:hover {
                color: #ff6961;
            }
            QPushButton#LinkBtnAccent {
                background: transparent;
                border: none;
                color: #0a84ff;
                font-size: 10px;
                font-weight: 500;
                padding: 2px 4px;
            }
            QPushButton#LinkBtnAccent:hover {
                color: #409cff;
            }
            QPushButton#LinkBtnAccent:disabled {
                color: #484850;
            }
            QPushButton#PillBtn {
                background-color: #2c2c30;
                border: 1px solid #3c3c44;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 10px;
                font-weight: 500;
                padding: 3px 8px;
            }
            QPushButton#PillBtn:hover {
                background-color: #383840;
                color: #ffffff;
            }
            QPushButton#IconButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 3px;
            }
            QPushButton#IconButton:hover {
                background-color: #2c2c30;
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)

        # 1. Top Panel Header
        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 0)
        header.setSpacing(6)

        title_lbl = QLabel("BACKUP & SYNC", parent=self)
        title_lbl.setObjectName("PanelHeaderTitle")
        header.addWidget(title_lbl)

        header.addStretch()

        self.btn_refresh = QPushButton(parent=self)
        self.btn_refresh.setObjectName("IconButton")
        self.btn_refresh.setIcon(create_sync_icon("#8e8e93", size=13))
        self.btn_refresh.setToolTip("Refresh status and changes")
        self.btn_refresh.setFixedSize(24, 24)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_status)
        header.addWidget(self.btn_refresh)

        self.btn_close = QPushButton(parent=self)
        self.btn_close.setObjectName("IconButton")
        self.btn_close.setIcon(create_close_icon("#8e8e93", size=13))
        self.btn_close.setToolTip("Close backup panel")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_requested.emit)
        header.addWidget(self.btn_close)

        layout.addLayout(header)

        # 2. Account & Connection Row (Persistent widgets, zero overlap risk)
        self.account_row = QHBoxLayout()
        self.account_row.setContentsMargins(4, 2, 4, 2)
        self.account_row.setSpacing(10)

        self.account_icon = QLabel(parent=self)
        self.account_icon.setFixedSize(20, 20)
        self.account_row.addWidget(self.account_icon)

        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(1)
        self.account_title = QLabel("Checking...", parent=self)
        self.account_title.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600;")
        info_vbox.addWidget(self.account_title)

        self.account_subtitle = QLabel("Local vault", parent=self)
        self.account_subtitle.setStyleSheet("color: #7a7a82; font-size: 10px;")
        info_vbox.addWidget(self.account_subtitle)
        self.account_row.addLayout(info_vbox)

        self.account_row.addStretch()

        self.account_action_btn = QPushButton("Connect", parent=self)
        self.account_action_btn.setObjectName("PillBtn")
        self.account_action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.account_action_btn.clicked.connect(self._on_account_action_clicked)
        self.account_row.addWidget(self.account_action_btn)

        layout.addLayout(self.account_row)

        # 3. Primary Sync Button & Status Indicator
        sync_vbox = QVBoxLayout()
        sync_vbox.setSpacing(4)

        self.btn_sync = QPushButton("☁  Sync Notes", parent=self)
        self.btn_sync.setObjectName("SyncBtn")
        self.btn_sync.setToolTip("Synchronize notes with GitHub (Ctrl+Shift+S)")
        self.btn_sync.setFixedHeight(30)
        self.btn_sync.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync.clicked.connect(self.trigger_sync)
        sync_vbox.addWidget(self.btn_sync)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(5)
        status_row.addStretch()

        self.sync_dot = QLabel("●", parent=self)
        self.sync_dot.setStyleSheet("color: #30d158; font-size: 8px;")
        status_row.addWidget(self.sync_dot)

        self.lbl_sync_status = QLabel("Ready", parent=self)
        self.lbl_sync_status.setStyleSheet("color: #7a7a82; font-size: 10px;")
        status_row.addWidget(self.lbl_sync_status)

        status_row.addStretch()
        sync_vbox.addLayout(status_row)
        layout.addLayout(sync_vbox)

        # 3b. Auto-Backup Toggle Card
        auto_card = QWidget(parent=self)
        auto_card.setObjectName("AutoBackupCard")
        auto_card.setStyleSheet("""
            QWidget#AutoBackupCard {
                background-color: #242428;
                border: 1px solid #2e2e34;
                border-radius: 8px;
            }
        """)
        auto_layout = QHBoxLayout(auto_card)
        auto_layout.setContentsMargins(10, 7, 10, 7)
        auto_layout.setSpacing(8)

        auto_vbox = QVBoxLayout()
        auto_vbox.setSpacing(1)
        self.lbl_auto_title = QLabel("Automatic Backup", parent=auto_card)
        self.lbl_auto_title.setStyleSheet("color: #ececec; font-size: 11px; font-weight: 600;")
        auto_vbox.addWidget(self.lbl_auto_title)

        self.lbl_auto_subtitle = QLabel("Auto-sync to GitHub on edit", parent=auto_card)
        self.lbl_auto_subtitle.setStyleSheet("color: #7a7a82; font-size: 10px;")
        auto_vbox.addWidget(self.lbl_auto_subtitle)
        auto_layout.addLayout(auto_vbox)

        auto_layout.addStretch()

        self.toggle_auto_backup = ToggleSwitch(parent=auto_card)
        self.toggle_auto_backup.setToolTip("Automatically sync and push changes to GitHub when notes are edited")
        self.toggle_auto_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        auto_layout.addWidget(self.toggle_auto_backup)

        layout.addWidget(auto_card)

        # Separator line 1
        div1 = QLabel(parent=self)
        div1.setFixedHeight(1)
        div1.setStyleSheet("background-color: #2b2b2b;")
        layout.addWidget(div1)

        # 4. Changes Section
        changes_header = QHBoxLayout()
        changes_header.setContentsMargins(2, 2, 2, 0)
        self.lbl_changes_title = QLabel("CHANGES", parent=self)
        self.lbl_changes_title.setObjectName("SectionHeader")
        changes_header.addWidget(self.lbl_changes_title)

        self.changes_badge = QLabel("0", parent=self)
        self.changes_badge.setStyleSheet(
            "background-color: #2a2a2e; color: #a0a0a8; border-radius: 7px; "
            "padding: 1px 6px; font-size: 9px; font-weight: 600;"
        )
        changes_header.addWidget(self.changes_badge)

        changes_header.addStretch()

        self.btn_backup_all = QPushButton("Backup All", parent=self)
        self.btn_backup_all.setObjectName("LinkBtnAccent")
        self.btn_backup_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_backup_all.clicked.connect(self.trigger_sync)
        changes_header.addWidget(self.btn_backup_all)
        layout.addLayout(changes_header)

        self.changes_list = QListWidget(parent=self)
        self.changes_list.setObjectName("ChangesList")
        self.changes_list.setItemDelegate(ChangeItemDelegate(self))
        self.changes_list.setFixedHeight(110)
        self.changes_list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.changes_list.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.changes_list)

        # Separator line 2
        div2 = QLabel(parent=self)
        div2.setFixedHeight(1)
        div2.setStyleSheet("background-color: #2b2b2b;")
        layout.addWidget(div2)

        # 5. Version History Section
        history_header = QHBoxLayout()
        history_header.setContentsMargins(2, 2, 2, 0)
        lbl_history = QLabel("RECENT BACKUPS", parent=self)
        lbl_history.setObjectName("SectionHeader")
        history_header.addWidget(lbl_history)
        history_header.addStretch()
        layout.addLayout(history_header)

        self.history_list = QListWidget(parent=self)
        self.history_list.setObjectName("HistoryList")
        self.history_list.setItemDelegate(HistoryItemDelegate(self))
        self.history_list.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.history_list)

    def refresh_status(self) -> None:
        """Poll Git repository state, refresh changes, commit history, and GitHub account info."""
        # 1. Update Account Row
        token = self.github_client.get_token()
        login, repo_url = self.github_client.get_stored_profile()

        if not self.git_manager.is_repo():
            self.account_icon.setPixmap(create_backup_icon("#8e8e93", size=18).pixmap(18, 18))
            self.account_title.setText("Vault Not Initialized")
            self.account_subtitle.setText("Git versioning disabled")
            self.account_action_btn.setObjectName("PillBtn")
            self.account_action_btn.setText("Initialize")
            self.account_action_btn.setStyleSheet("")
        elif not token or not login:
            self.account_icon.setPixmap(create_github_icon("#8e8e93", size=18).pixmap(18, 18))
            self.account_title.setText("Local Vault Only")
            self.account_subtitle.setText("No remote backup connected")
            self.account_action_btn.setObjectName("PillBtn")
            self.account_action_btn.setText("Connect")
            self.account_action_btn.setStyleSheet("")
        else:
            self.account_icon.setPixmap(create_github_icon("#30d158", size=18).pixmap(18, 18))
            self.account_title.setText(f"@{login}")

            remote_status = self.git_manager.get_remote()
            clean_repo = repo_url or (remote_status if remote_status else "Local vault")
            if "github.com" in clean_repo:
                parts = clean_repo.split("github.com/")[-1].replace(".git", "")
                display_repo = f"Vault: {parts}"
            else:
                display_repo = "Private vault • main"

            self.account_subtitle.setText(display_repo)
            self.account_action_btn.setObjectName("LinkBtn")
            self.account_action_btn.setText("Disconnect")
            self.account_action_btn.setStyleSheet("color: #7a7a82; font-size: 10px; background: transparent; border: none;")

        # 2. Update Changes List
        status: GitStatus = self.git_manager.get_status()
        self.changes_list.clear()

        total = status.total_changes
        self.changes_badge.setText(str(total))
        self.btn_backup_all.setEnabled(total > 0)
        self.changes_updated.emit(total)

        if total == 0:
            item = QListWidgetItem("No unbacked changes ✓")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setData(Qt.ItemDataRole.UserRole + 1, "Clean")
            item.setForeground(QColor("#7a7a82"))
            self.changes_list.addItem(item)
        else:
            for p in status.modified:
                self._add_change_item(p, "Edited")
            for p in status.added:
                self._add_change_item(p, "New")
            for p in status.untracked:
                self._add_change_item(p, "New")
            for p in status.deleted:
                self._add_change_item(p, "Deleted")

        # 3. Update Sync Status text & dot
        if status.ahead > 0:
            self.sync_dot.setStyleSheet("color: #0a84ff; font-size: 8px;")
            self.lbl_sync_status.setText(f"{status.ahead} commit(s) ready to push")
            self.lbl_sync_status.setStyleSheet("color: #0a84ff; font-size: 10px;")
        elif total > 0:
            self.sync_dot.setStyleSheet("color: #e5a93c; font-size: 8px;")
            self.lbl_sync_status.setText(f"{total} unbacked change(s)")
            self.lbl_sync_status.setStyleSheet("color: #e5a93c; font-size: 10px;")
        else:
            self.sync_dot.setStyleSheet("color: #30d158; font-size: 8px;")
            self.lbl_sync_status.setText("All notes synced with GitHub")
            self.lbl_sync_status.setStyleSheet("color: #7a7a82; font-size: 10px;")

        # 4. Update History List
        self.history_list.clear()
        commits = self.git_manager.get_history(limit=20)
        if not commits:
            item = QListWidgetItem("No backups yet")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setData(Qt.ItemDataRole.UserRole + 1, "Initialize backup to create history")
            item.setForeground(QColor("#7a7a82"))
            self.history_list.addItem(item)
        else:
            for c in commits:
                self._add_history_item(c)

    def _add_change_item(self, rel_path: str, badge: str) -> None:
        item = QListWidgetItem(Path(rel_path).name)
        item.setData(Qt.ItemDataRole.UserRole, rel_path)
        item.setData(Qt.ItemDataRole.UserRole + 1, badge)
        self.changes_list.addItem(item)

    def _add_history_item(self, commit: GitCommit) -> None:
        item = QListWidgetItem(commit.message)
        item.setData(Qt.ItemDataRole.UserRole, commit.hash)
        item.setData(Qt.ItemDataRole.UserRole + 1, f"{commit.relative_date} • {commit.short_hash}")
        self.history_list.addItem(item)

    def _on_account_action_clicked(self) -> None:
        """Handle click on Connect / Initialize / Disconnect button."""
        action_text = self.account_action_btn.text().lower()
        if "initialize" in action_text:
            self.git_manager.init_repo()
            self.refresh_status()
        elif "disconnect" in action_text:
            self.github_client.clear_token()
            self.refresh_status()
        else:
            accepted, token, repo_url = ModernGitHubAuthDialog.execute(parent=self)
            if accepted and token:
                if repo_url:
                    auth_url = self.github_client.build_authenticated_remote_url(repo_url, token)
                    self.git_manager.set_remote(auth_url)
                self.refresh_status()
                self.trigger_sync()

    def trigger_sync(self) -> None:
        """Trigger background asynchronous sync without freezing GUI."""
        if self._sync_thread and self._sync_thread.isRunning():
            return

        self.btn_sync.setEnabled(False)
        self.btn_sync.setText("Syncing with GitHub...")
        self.sync_dot.setStyleSheet("color: #0a84ff; font-size: 8px;")
        self.lbl_sync_status.setText("Uploading changes...")
        self.lbl_sync_status.setStyleSheet("color: #0a84ff; font-size: 10px;")

        self._sync_thread = SyncWorker(self.git_manager)
        self._sync_thread.finished.connect(self._on_sync_finished)
        self._sync_thread.start()

    def _on_sync_finished(self, success: bool, message: str) -> None:
        self.btn_sync.setEnabled(True)
        self.btn_sync.setText("☁  Sync Notes")
        self.refresh_status()
        self.sync_completed.emit(success, message)

        if success:
            self.sync_dot.setStyleSheet("color: #30d158; font-size: 8px;")
            self.lbl_sync_status.setText("All notes synced with GitHub")
            self.lbl_sync_status.setStyleSheet("color: #7a7a82; font-size: 10px;")
        else:
            self.sync_dot.setStyleSheet("color: #ff453a; font-size: 8px;")
            self.lbl_sync_status.setText(f"Sync failed: {message}")
            self.lbl_sync_status.setStyleSheet("color: #ff453a; font-size: 10px;")

    def is_auto_backup_enabled(self) -> bool:
        """Check if automatic backup on edit is active."""
        return self.toggle_auto_backup.isChecked()

    def _on_auto_backup_toggled(self, enabled: bool) -> None:
        """Handle user toggling automatic backup."""
        if self.config_manager:
            self.config_manager.set_auto_backup(enabled)
        if enabled:
            status = self.git_manager.get_status()
            if not status.is_clean or status.ahead > 0:
                self.schedule_auto_backup()
        else:
            self._auto_backup_timer.stop()

    def schedule_auto_backup(self) -> None:
        """Schedule debounced background sync (2.5s) if automatic backup is enabled."""
        if not self.toggle_auto_backup.isChecked():
            return
        if not self.git_manager.is_repo():
            return
        self._auto_backup_timer.start(2500)

    def _on_auto_backup_timer_fired(self) -> None:
        """Debounced auto-backup timer expired; trigger sync if dirty or ahead."""
        if not self.toggle_auto_backup.isChecked():
            return
        if not self.git_manager.is_repo():
            return
        status = self.git_manager.get_status()
        if not status.is_clean or status.ahead > 0:
            self.trigger_sync()
