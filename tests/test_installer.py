"""Tests for installer.py - wizard state and download tracking."""

import os

import pytest
from PySide6.QtWidgets import QApplication

from config import AppConfig
from i18n import set_language
from installer import PathsPage, ToolsPage
from tool_manager import ToolManager


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def tm(monkeypatch):
    cfg = AppConfig()
    tool_manager = ToolManager(cfg)
    monkeypatch.setattr(
        tool_manager,
        "scan",
        lambda: {
            "universal_mail_cleaner": (r"C:\Tools\UniversalMailCleaner", "main.py"),
            "universal_docs_grabber": None,
            "universal_invoice_mail": None,
        },
    )
    return tool_manager


def test_tools_page_preserves_selection_on_rebuild(qapp, tm):
    set_language("de")
    page = ToolsPage(tm)

    page.initializePage()
    assert page._checkboxes["universal_mail_cleaner"].isChecked() is True

    page._checkboxes["universal_mail_cleaner"].setChecked(False)
    page.initializePage()

    assert page._checkboxes["universal_mail_cleaner"].isChecked() is False


def test_tools_page_blocks_completion_while_download_active(qapp):
    set_language("de")
    page = ToolsPage(ToolManager(AppConfig()))

    changes = []
    page.completeChanged.connect(lambda: changes.append(page.isComplete()))

    assert page.isComplete() is True

    page._set_download_active(True)
    assert page.isComplete() is False

    page._set_download_active(False)
    assert page.isComplete() is True
    assert changes == [False, True]


def test_paths_page_requires_manual_paths_before_completion(qapp, tm, tmp_path):
    set_language("de")
    tools_page = ToolsPage(tm)
    tools_page.initializePage()
    tools_page._checkboxes["universal_docs_grabber"].setChecked(True)

    page = PathsPage(tools_page, tm)
    changes = []
    page.completeChanged.connect(lambda: changes.append(page.isComplete()))

    page.initializePage()
    assert page.isComplete() is False
    assert "universal_docs_grabber" in page._path_edits

    script = tmp_path / "UniversalDocsGrabberV1.py"
    script.write_text("", encoding="utf-8")
    page._path_edits["universal_docs_grabber"].setText(str(script))

    assert page.isComplete() is True
    assert changes
    assert changes[-1] is True
