"""System tray icon and context menu."""

import copy
import sys
from pathlib import Path

from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QSystemTrayIcon

import config as cfg_module
from config import AppConfig
from i18n import tr
from tool_manager import ToolManager


def _make_tray_icon(size: int = 22) -> QIcon:
    """Create a simple envelope icon for the tray (no external file needed)."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    painter.setBrush(QColor(30, 120, 200))
    painter.setPen(QColor(0, 0, 0, 0))
    painter.drawEllipse(1, 1, size - 2, size - 2)

    # Envelope body
    margin = size // 5
    env_rect = pixmap.rect().adjusted(margin, margin + 2, -margin, -margin)
    painter.setBrush(QColor(255, 255, 255))
    painter.setPen(QColor(200, 200, 200))
    painter.drawRect(env_rect)

    # Envelope flap (V line)
    cx = env_rect.center().x()
    painter.setPen(QColor(150, 150, 150))
    painter.drawLine(env_rect.left(), env_rect.top(), cx, env_rect.center().y())
    painter.drawLine(cx, env_rect.center().y(), env_rect.right(), env_rect.top())

    painter.end()
    return QIcon(pixmap)


def _resource_path(relative_path: str) -> Path:
    """Return an absolute path to a resource inside source or packaged app."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / relative_path


def _load_tray_icon() -> QIcon:
    icon_path = _resource_path("resources/icon.ico")
    icon = QIcon(str(icon_path))
    if icon.isNull():
        return _make_tray_icon()
    return icon


class MailProcessorTray(QSystemTrayIcon):
    def __init__(self, app_cfg: AppConfig, parent=None):
        super().__init__(parent)
        self._cfg = app_cfg
        self._tm = ToolManager(app_cfg)
        self.setIcon(_load_tray_icon())
        self.setToolTip(tr("tray_tooltip"))
        self._build_menu()
        self.activated.connect(self._on_activated)

    def _build_menu(self):
        menu = QMenu()

        active = self._tm.active_tools()
        if active:
            for tid in active:
                name = self._tm.tool_display_name(tid)
                version = self._tm.tool_version(tid)
                if version:
                    name = f"{name} {version}"
                action = QAction(name, self)
                valid = self._tm.is_path_valid(tid)
                action.setEnabled(valid)
                action.setToolTip(self._tm.tool_description(tid))
                # Capture tid in closure
                action.triggered.connect(lambda checked=False, t=tid: self._launch(t))
                menu.addAction(action)
        else:
            no_tools = QAction(tr("no_tools"), self)
            no_tools.setEnabled(False)
            menu.addAction(no_tools)

        menu.addSeparator()
        settings_action = QAction(tr("menu_settings"), self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        export_action = QAction(tr("menu_export_snapshot"), self)
        export_action.triggered.connect(self._export_snapshot)
        menu.addAction(export_action)

        menu.addSeparator()
        quit_action = QAction(tr("menu_quit"), self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _launch(self, tool_id: str):
        err = self._tm.launch(tool_id)
        if err:
            self.showMessage(
                tr("error"),
                tr("launch_error", err),
                QSystemTrayIcon.MessageIcon.Critical,
                3000,
            )

    def _open_settings(self):
        from PySide6.QtWidgets import QDialog
        from settings_dialog import SettingsDialog
        # Snapshot tools so Cancel can restore them: ToolManager holds a reference
        # to the same AppConfig, so mutations from remove/rescan happen immediately.
        tools_snapshot = copy.deepcopy(self._cfg.tools)
        dlg = SettingsDialog(self._cfg)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            self._cfg.tools = tools_snapshot
        # Rebuild menu in case tools changed
        self._build_menu()
        # Persist language change
        from i18n import get_language
        if self._cfg.language != get_language():
            self._cfg.language = get_language()
        cfg_module.save(self._cfg)
        self.setToolTip(tr("tray_tooltip"))

    def _export_snapshot(self):
        from snapshot_export import SNAPSHOT_SCHEMA, write_snapshot

        suggested_path = Path.home() / f"{SNAPSHOT_SCHEMA}.json"
        selected_path, _ = QFileDialog.getSaveFileName(
            None,
            tr("export_dialog_title"),
            str(suggested_path),
            tr("export_file_filter"),
        )
        if not selected_path:
            return
        if not selected_path.lower().endswith(".json"):
            selected_path = f"{selected_path}.json"

        try:
            written_path = write_snapshot(selected_path, self._cfg)
        except Exception as exc:
            self.showMessage(
                tr("error"),
                tr("export_error", str(exc)),
                QSystemTrayIcon.MessageIcon.Critical,
                4000,
            )
            return

        self.showMessage(
            tr("app_name"),
            tr("export_ok", str(written_path)),
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._open_settings()
