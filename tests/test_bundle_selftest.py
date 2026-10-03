"""The frozen-bundle self-test must not touch a real user profile or host state."""

import builtins
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

import config as cfg_module
import main as main_module


@pytest.fixture
def isolated_qapp(monkeypatch, tmp_path):
    profile = tmp_path / "profile"
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LOCALAPPDATA", str(profile / "localappdata"))
    monkeypatch.setenv("APPDATA", str(profile / "appdata"))
    monkeypatch.setenv("USERPROFILE", str(profile / "user"))
    monkeypatch.setenv("TEMP", str(profile / "temp"))
    monkeypatch.setenv("TMP", str(profile / "temp"))

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app, profile


def test_self_test_checks_frozen_ui_without_loading_or_saving_profile(
    isolated_qapp, monkeypatch
):
    _, profile = isolated_qapp
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(repo_root), raising=False)

    def unexpected_call(*_args, **_kwargs):
        pytest.fail("self-test reached a forbidden profile or host-state path")

    monkeypatch.setattr(cfg_module, "load", unexpected_call)
    monkeypatch.setattr(cfg_module, "save", unexpected_call)

    import settings_dialog
    import tool_manager
    import urllib.request

    monkeypatch.setattr(settings_dialog, "ensure_autostart_entry", unexpected_call)
    monkeypatch.setattr(tool_manager.ToolManager, "scan", unexpected_call)
    monkeypatch.setattr(tool_manager.ToolManager, "download_tool", unexpected_call)
    monkeypatch.setattr(tool_manager.ToolManager, "launch", unexpected_call)
    monkeypatch.setattr(urllib.request, "urlopen", unexpected_call)

    real_import = builtins.__import__

    def block_installer(name, *args, **kwargs):
        if name == "installer":
            pytest.fail("self-test imported the first-run installer")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", block_installer)
    monkeypatch.setattr(sys, "argv", ["MailProcessor", "--self-test"])

    assert main_module.main() == 0
    assert not (profile / "localappdata" / "MailProcessor").exists()


def test_self_test_reports_missing_asset(isolated_qapp, monkeypatch, tmp_path):
    _, profile = isolated_qapp
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(sys, "argv", ["MailProcessor", "--self-test"])

    assert main_module.main() == 11
    assert not (profile / "localappdata" / "MailProcessor").exists()


def test_self_test_reports_unreadable_asset(isolated_qapp, monkeypatch, tmp_path):
    _, profile = isolated_qapp
    bad_resource = tmp_path / "resources" / "icon.ico"
    bad_resource.parent.mkdir()
    bad_resource.write_text("not an icon", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(sys, "argv", ["MailProcessor", "--self-test"])

    assert main_module.main() == 12
    assert not (profile / "localappdata" / "MailProcessor").exists()


def test_self_test_reports_ui_that_never_paints(isolated_qapp, monkeypatch):
    _, profile = isolated_qapp
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(repo_root), raising=False)
    monkeypatch.setattr(sys, "argv", ["MailProcessor", "--self-test"])

    from PySide6.QtCore import QEventLoop
    from settings_dialog import SettingsDialog

    monkeypatch.setattr(SettingsDialog, "show", lambda _self: None)
    monkeypatch.setattr(QEventLoop, "exec", lambda _self: 0)

    assert main_module.main() == 14
    assert not (profile / "localappdata" / "MailProcessor").exists()
