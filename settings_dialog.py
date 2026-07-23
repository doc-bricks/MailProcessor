"""Settings dialog: manage tools and general preferences."""

import os
import shlex
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QLabel, QComboBox, QCheckBox, QMessageBox, QFileDialog,
    QAbstractItemView, QSizePolicy,
)

import config as cfg_module
from config import AppConfig
from i18n import tr, set_language, get_language
from tool_manager import ToolManager, TOOL_DEFINITIONS

_AUTOSTART_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_AUTOSTART_APP_NAME = "MailProcessor"


def _expected_autostart_command() -> str:
    exe = Path(sys.executable)
    if getattr(sys, "frozen", False):
        return f'"{exe}"'
    script = Path(__file__).parent / "main.py"
    return f'"{exe}" "{script}"'


def _normalize_cmd_token(token: str) -> str:
    value = token.strip().strip("'").strip('"')
    if not value:
        return ""
    try:
        return os.path.normcase(os.path.normpath(os.path.expandvars(value)))
    except Exception:
        return os.path.normcase(value)


def _command_tokens(command: str) -> list[str]:
    if not command:
        return []
    try:
        tokens = shlex.split(command, posix=False)
    except Exception:
        tokens = command.split()
    return [token.strip() for token in tokens if token]


def _read_autostart_command() -> str | None:
    if os.name != "nt":
        return None
    import winreg

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_REG_PATH, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, _AUTOSTART_APP_NAME)
            return value if isinstance(value, str) else None
        finally:
            winreg.CloseKey(key)
    except Exception:
        return None


def _is_current_autostart_command(stored_command: str) -> bool:
    expected = _command_tokens(_expected_autostart_command())
    current = _command_tokens(stored_command)
    if len(current) < len(expected):
        return False

    for idx, expected_token in enumerate(expected):
        if _normalize_cmd_token(current[idx]) != _normalize_cmd_token(expected_token):
            return False
    return True


def ensure_autostart_entry(enable: bool) -> None:
    """Ensure registry autostart entry points to the current executable path."""
    if os.name != "nt":
        return
    import winreg

    if not enable:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_REG_PATH, 0, winreg.KEY_SET_VALUE)
            try:
                try:
                    winreg.DeleteValue(key, _AUTOSTART_APP_NAME)
                except FileNotFoundError:
                    pass
            finally:
                winreg.CloseKey(key)
        except Exception:
            pass
        return

    expected = _expected_autostart_command()
    current = _read_autostart_command()
    if current and _is_current_autostart_command(current):
        return

    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_REG_PATH)
        try:
            winreg.SetValueEx(key, _AUTOSTART_APP_NAME, 0, winreg.REG_SZ, expected)
        finally:
            winreg.CloseKey(key)
    except Exception:
        pass


class SettingsDialog(QDialog):
    def __init__(self, app_cfg: AppConfig, parent=None):
        super().__init__(parent)
        self._cfg = app_cfg
        self._tm = ToolManager(app_cfg)

        self.setWindowTitle(tr("settings_title"))
        self.resize(680, 460)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._tabs.addTab(self._build_tools_tab(), tr("tab_tools"))
        self._tabs.addTab(self._build_general_tab(), tr("tab_general"))

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton(tr("save"))
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Tools tab
    # ------------------------------------------------------------------

    def _build_tools_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels([tr("col_tool"), tr("col_status"), tr("col_path")])
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.itemSelectionChanged.connect(self._update_tool_action_state)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        rescan_btn = QPushButton(tr("btn_rescan"))
        rescan_btn.clicked.connect(self._on_rescan)
        self._change_btn = QPushButton(tr("btn_change_path"))
        self._change_btn.clicked.connect(self._on_change_path)
        self._remove_btn = QPushButton(tr("btn_remove_tool"))
        self._remove_btn.clicked.connect(self._on_remove_tool)
        btn_row.addWidget(rescan_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._change_btn)
        btn_row.addWidget(self._remove_btn)
        layout.addLayout(btn_row)

        self._refresh_table()
        self._update_tool_action_state()
        return w

    def _refresh_table(self):
        self._table.setRowCount(0)
        for tid in TOOL_DEFINITIONS:
            t = self._cfg.tools.get(tid)
            row = self._table.rowCount()
            self._table.insertRow(row)

            name_item = QTableWidgetItem(self._tm.tool_display_name(tid))
            name_item.setData(Qt.ItemDataRole.UserRole, tid)
            self._table.setItem(row, 0, name_item)

            if not t or not t.enabled:
                status = tr("status_inactive")
                path_text = ""
            elif not self._tm.is_path_valid(tid):
                status = tr("status_missing")
                path_text = t.path or ""
            else:
                status = tr("status_active")
                path_text = f"{t.path}\\{t.main_script}"

            status_item = QTableWidgetItem(status)
            path_item = QTableWidgetItem(path_text)
            self._table.setItem(row, 1, status_item)
            self._table.setItem(row, 2, path_item)

        self._table.resizeColumnToContents(0)
        self._table.resizeColumnToContents(1)
        self._update_tool_action_state()

    def _selected_tool_id(self) -> str | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_tool_action_state(self):
        tid = self._selected_tool_id()
        if tid:
            tool_name = self._tm.tool_display_name(tid)
            tool_desc = self._tm.tool_description(tid)
            change_name = f"{tr('btn_change_path')}: {tool_name}"
            remove_name = f"{tr('btn_remove_tool')}: {tool_name}"
            self._change_btn.setEnabled(True)
            self._change_btn.setToolTip(change_name)
            self._change_btn.setAccessibleName(change_name)
            self._change_btn.setAccessibleDescription(tool_desc)
            self._remove_btn.setEnabled(True)
            self._remove_btn.setToolTip(remove_name)
            self._remove_btn.setAccessibleName(remove_name)
            self._remove_btn.setAccessibleDescription(tool_desc)
            return

        self._change_btn.setEnabled(False)
        self._change_btn.setToolTip("")
        self._change_btn.setAccessibleName(tr("btn_change_path"))
        self._change_btn.setAccessibleDescription("")
        self._remove_btn.setEnabled(False)
        self._remove_btn.setToolTip("")
        self._remove_btn.setAccessibleName(tr("btn_remove_tool"))
        self._remove_btn.setAccessibleDescription("")

    def _on_rescan(self):
        results = self._tm.scan()
        added = self._tm.apply_scan_results(results)
        self._refresh_table()
        msg_key = "rescan_done" if added else "rescan_none"
        QMessageBox.information(self, tr("app_name"), tr(msg_key))

    def _on_change_path(self):
        tid = self._selected_tool_id()
        if not tid:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr("select_script"), "",
            "Python Scripts (*.py)"
        )
        if not path:
            return
        ok = self._tm.register_from_script_path(tid, path, "manual")
        if not ok:
            QMessageBox.warning(self, tr("warning"), tr("path_not_found"))
            return
        self._refresh_table()

    def _on_remove_tool(self):
        tid = self._selected_tool_id()
        if not tid:
            return
        reply = QMessageBox.question(
            self, tr("warning"), tr("remove_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._tm.unregister(tid)
            self._refresh_table()

    # ------------------------------------------------------------------
    # General tab
    # ------------------------------------------------------------------

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(tr("label_language")))
        self._lang_combo = QComboBox()
        self._lang_combo.addItem(tr("lang_de"), "de")
        self._lang_combo.addItem(tr("lang_en"), "en")
        self._lang_combo.setCurrentIndex(0 if get_language() == "de" else 1)
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()
        layout.addLayout(lang_row)

        self._autostart_cb = QCheckBox(tr("label_autostart"))
        self._autostart_cb.setChecked(self._cfg.start_with_windows)
        note = QLabel(tr("autostart_note"))
        note.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self._autostart_cb)
        layout.addWidget(note)

        layout.addStretch()
        return w

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _on_save(self):
        lang = self._lang_combo.currentData()
        set_language(lang)
        self._cfg.language = lang
        self._cfg.start_with_windows = self._autostart_cb.isChecked()
        self._apply_autostart(self._cfg.start_with_windows)
        cfg_module.save(self._cfg)
        self.accept()

    @staticmethod
    def _apply_autostart(enable: bool):
        ensure_autostart_entry(enable)
