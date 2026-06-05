"""Tests for installer.py - wizard state and download tracking."""

import copy
import os

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from config import AppConfig, ToolConfig
from i18n import set_language
from installer import PathsPage, ToolsPage, WelcomePage
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


def test_settings_cancel_restores_tool_registrations(qapp, monkeypatch):
    """Regression: SettingsDialog mutations (remove/rescan) must be rolled back when
    the user clicks Cancel. Before the fix, _open_settings() saved the mutated cfg
    unconditionally regardless of whether exec() returned Accepted or Rejected."""
    from tray import MailProcessorTray
    from settings_dialog import SettingsDialog

    cfg = AppConfig()
    cfg.tools["universal_mail_cleaner"] = ToolConfig(
        enabled=True, path="/tools/umc", main_script="main.py"
    )

    def _fake_exec(self):
        # Simulate the user removing a tool and then clicking Cancel
        self._tm.unregister("universal_mail_cleaner")
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(SettingsDialog, "exec", _fake_exec)

    tray = MailProcessorTray(cfg)
    tray._open_settings()

    assert cfg.tools["universal_mail_cleaner"].enabled is True, (
        "Tool removal must be rolled back when Settings dialog is cancelled"
    )
    assert cfg.tools["universal_mail_cleaner"].path == "/tools/umc"


def test_welcome_page_rebuild_replaces_layout_on_revisit(qapp):
    """Regression: WelcomePage.initializePage() must discard the old layout via
    QWidget().setLayout(old) before calling _rebuild(). Without it, Qt silently
    ignores the new QVBoxLayout(self) and the page renders blank on revisit."""
    set_language("de")
    page = WelcomePage()
    page.initializePage()
    assert page.layout() is not None
    assert page.layout().count() > 0, "Layout should have widgets after first build"

    # Simulate going back to this page (second call to initializePage)
    page.initializePage()
    assert page.layout() is not None
    assert page.layout().count() > 0, "Layout must still have widgets after rebuild"


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


def test_rescan_blocked_while_download_active(qapp, tm):
    """Regression: _on_rescan() darf die UI nicht neu aufbauen, wenn noch Download-Threads
    laufen. Ein Rebuild löscht die Widgets per deleteLater(); die _on_done-Closures der
    Threads referenzieren diese alten Widgets und würden bei Abschluss RuntimeError auslösen."""
    set_language("de")
    page = ToolsPage(tm)
    page.initializePage()

    # Merke den aktuellen Layout-Stand (Adresse des Layout-Objekts)
    layout_before = page.layout()

    # Simuliere einen aktiven Download
    page._set_download_active(True)
    assert page._active_downloads == 1

    # Rescan soll ohne Wirkung bleiben
    page._on_rescan()

    # Layout darf nicht ersetzt worden sein
    assert page.layout() is layout_before, (
        "_on_rescan() darf während aktiver Downloads keine UI-Neuerstellung auslösen"
    )

    # Cleanup
    page._set_download_active(False)


def test_download_callback_survives_page_rebuild(qapp, tm, monkeypatch):
    """Regression (zwei Aspekte):
    1. _on_done/_on_progress dürfen keine unkontrollierten Fehler auslösen wenn Widgets
       nach Download-Start zerstört wurden (shiboken6.delete = deterministisch tot).
    2. _scan_results muss auch dann aktualisiert werden wenn der Widget-Zugriff danach
       RuntimeError wirft — das Update liegt außerhalb des try/except-Blocks.
       Ohne die Umordnung (Fix): except feuert vor dem Update → assert_in schlägt fehl.
    """
    from installer import _DownloadThread
    from PySide6.QtWidgets import QLabel, QPushButton, QCheckBox
    from config import ToolConfig
    import shiboken6

    set_language("de")
    page = ToolsPage(tm)
    page.initializePage()

    monkeypatch.setattr(_DownloadThread, "start", lambda self: None)

    # Echte Widgets (benötigt: _start_download greift sofort auf sie zu)
    label = QLabel()
    btn = QPushButton()
    cb = QCheckBox()

    # Tool mit path+main_script eintragen damit der _scan_results-Zweig in _on_done läuft
    tool_id = "universal_docs_grabber"
    tm.cfg.tools[tool_id] = ToolConfig(enabled=False, path="/fake/path", main_script="main.py")

    page._start_download(tool_id, label, btn, cb)
    thread = page._threads[-1]

    # C++-Objekte deterministisch zerstören (kein DeferredDelete/Event-Loop nötig)
    shiboken6.delete(label)
    shiboken6.delete(btn)
    shiboken6.delete(cb)

    # Callbacks auf zerstörten Widgets — darf nicht crashen
    thread.progress.emit(50)
    thread.finished_signal.emit("")

    # Kernaussage: _scan_results muss befüllt sein trotz RuntimeError beim Widget-Zugriff.
    # Ohne die Umordnung (Update im try-Block) überspringt der except-Guard das Update.
    assert tool_id in page._scan_results, (
        "_scan_results muss unabhängig vom Widget-Zustand befüllt werden"
    )
    assert page._scan_results[tool_id] == ("/fake/path", "main.py")


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
