"""Tests for settings_dialog.py — rescan feedback and tool management."""
import os

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from config import AppConfig, ToolConfig
from i18n import set_language


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_rescan_shows_rescan_done_when_tools_added(qapp, tmp_path, monkeypatch):
    """_on_rescan() shows 'rescan_done' message when new tools are detected."""
    set_language("de")
    from settings_dialog import SettingsDialog

    cfg = AppConfig()
    dlg = SettingsDialog(cfg)

    tool_dir = tmp_path / "UniversalMailCleaner"
    tool_dir.mkdir()
    (tool_dir / "main.py").write_text("", encoding="utf-8")

    import tool_manager as tm_module
    monkeypatch.setattr(tm_module, "_SCAN_ROOTS", [tmp_path])

    shown_texts: list[str] = []

    def _fake_info(parent, title, text, *a, **kw):
        shown_texts.append(text)

    monkeypatch.setattr(QMessageBox, "information", staticmethod(_fake_info))

    dlg._on_rescan()

    assert shown_texts, "QMessageBox.information must be called"
    assert "Keine neuen Tools" not in shown_texts[0], (
        "When tools were added, 'rescan_done' message must be shown"
    )
    assert "hinzugefügt" in shown_texts[0] or "added" in shown_texts[0]


def test_rescan_shows_rescan_none_when_no_tools_found(qapp, tmp_path, monkeypatch):
    """_on_rescan() shows 'rescan_none' message when scan finds nothing new."""
    set_language("de")
    from settings_dialog import SettingsDialog

    cfg = AppConfig()
    dlg = SettingsDialog(cfg)

    import tool_manager as tm_module
    monkeypatch.setattr(tm_module, "_SCAN_ROOTS", [tmp_path])

    shown_texts: list[str] = []

    def _fake_info(parent, title, text, *a, **kw):
        shown_texts.append(text)

    monkeypatch.setattr(QMessageBox, "information", staticmethod(_fake_info))

    dlg._on_rescan()

    assert shown_texts, "QMessageBox.information must be called"
    assert "Keine neuen Tools gefunden" in shown_texts[0], (
        "When no new tools found, 'rescan_none' message must be shown, "
        f"got: {shown_texts[0]!r}"
    )


def test_rescan_shows_rescan_none_when_tool_already_registered(qapp, tmp_path, monkeypatch):
    """_on_rescan() shows 'rescan_none' when the found tool is already enabled."""
    set_language("de")
    from settings_dialog import SettingsDialog

    cfg = AppConfig()
    cfg.get_tool("universal_mail_cleaner").enabled = True
    cfg.get_tool("universal_mail_cleaner").path = str(tmp_path / "UniversalMailCleaner")
    cfg.get_tool("universal_mail_cleaner").main_script = "main.py"

    tool_dir = tmp_path / "UniversalMailCleaner"
    tool_dir.mkdir()
    (tool_dir / "main.py").write_text("", encoding="utf-8")

    dlg = SettingsDialog(cfg)

    import tool_manager as tm_module
    monkeypatch.setattr(tm_module, "_SCAN_ROOTS", [tmp_path])

    shown_texts: list[str] = []

    def _fake_info(parent, title, text, *a, **kw):
        shown_texts.append(text)

    monkeypatch.setattr(QMessageBox, "information", staticmethod(_fake_info))

    dlg._on_rescan()

    assert shown_texts, "QMessageBox.information must be called"
    assert "Keine neuen Tools gefunden" in shown_texts[0], (
        "When tool is already registered, scan adds nothing — 'rescan_none' must be shown, "
        f"got: {shown_texts[0]!r}"
    )


def test_tool_action_buttons_require_selection_and_expose_tool_context(qapp, tmp_path):
    """Change/remove buttons stay disabled without selection and expose the selected tool."""
    set_language("de")
    from settings_dialog import SettingsDialog

    cfg = AppConfig()
    tool_cfg = ToolConfig(enabled=True, path=str(tmp_path), main_script="main.py")
    cfg.tools["universal_mail_cleaner"] = tool_cfg

    dlg = SettingsDialog(cfg)

    assert not dlg._change_btn.isEnabled()
    assert not dlg._remove_btn.isEnabled()
    assert dlg._change_btn.accessibleName() == "Pfad ändern"
    assert dlg._remove_btn.accessibleName() == "Entfernen"

    dlg._table.selectRow(0)
    qapp.processEvents()

    assert dlg._change_btn.isEnabled()
    assert dlg._remove_btn.isEnabled()
    assert dlg._change_btn.accessibleName() == "Pfad ändern: Universal Mail Cleaner"
    assert dlg._remove_btn.accessibleName() == "Entfernen: Universal Mail Cleaner"
    assert dlg._change_btn.toolTip() == "Pfad ändern: Universal Mail Cleaner"
    assert dlg._remove_btn.toolTip() == "Entfernen: Universal Mail Cleaner"
    assert "IMAP-Postfach nach Regeln bereinigen" in dlg._change_btn.accessibleDescription()
