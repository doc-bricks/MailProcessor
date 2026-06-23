"""Tests for the read-only desktop snapshot export."""

from datetime import datetime
from pathlib import Path

from config import AppConfig
from snapshot_export import (
    SNAPSHOT_SCHEMA,
    _safe_localappdata_root,
    build_snapshot_payload,
    write_snapshot,
)


def test_build_snapshot_payload_redacts_private_paths_and_reports_statuses(
    tmp_path,
    monkeypatch,
):
    localappdata = tmp_path / "LocalAppData"
    tool_root = localappdata / "MailProcessor" / "tools" / "universal_mail_cleaner"
    tool_root.mkdir(parents=True)
    (tool_root / "main.py").write_text("", encoding="utf-8")
    (tool_root / "CHANGELOG.md").write_text("## [1.2.3] - 2026-06-01\n", encoding="utf-8")

    missing_root = Path("D:/MailTools/UniversalDocsGrabber")

    cfg = AppConfig(language="de", first_run=False, start_with_windows=True)
    cfg.get_tool("universal_mail_cleaner").enabled = True
    cfg.get_tool("universal_mail_cleaner").path = str(tool_root)
    cfg.get_tool("universal_mail_cleaner").main_script = "main.py"
    cfg.get_tool("universal_mail_cleaner").installed_by = "github"

    cfg.get_tool("universal_docs_grabber").enabled = True
    cfg.get_tool("universal_docs_grabber").path = str(missing_root)
    cfg.get_tool("universal_docs_grabber").main_script = "main.py"
    cfg.get_tool("universal_docs_grabber").installed_by = "manual"

    monkeypatch.setattr("snapshot_export.LOCALAPPDATA_ROOT", localappdata)

    payload = build_snapshot_payload(
        cfg,
        exported_at=datetime.fromisoformat("2026-06-02T12:34:56+02:00"),
    )

    assert payload["schema"] == SNAPSHOT_SCHEMA
    assert payload["exported_at"] == "2026-06-02T12:34:56+02:00"
    assert payload["app"]["name"] == "MailProcessor"
    assert payload["app"]["version"] == "0.1.0"
    assert payload["app"]["platform"] == "windows"

    tools = {tool["id"]: tool for tool in payload["tools"]}

    cleaner = tools["universal_mail_cleaner"]
    assert cleaner["display_name"] == "Universal Mail Cleaner"
    assert cleaner["enabled"] is True
    assert cleaner["installed_by"] == "github"
    assert cleaner["version"] == "v1.2.3"
    assert cleaner["status"] == "available"
    assert cleaner["path_hint"] == "LOCALAPPDATA/MailProcessor/tools/universal_mail_cleaner"

    docs_grabber = tools["universal_docs_grabber"]
    assert docs_grabber["status"] == "missing"
    assert docs_grabber["path_hint"] == ".../MailTools/UniversalDocsGrabber"
    assert "Lukas" not in docs_grabber["path_hint"]

    invoice_mail = tools["universal_invoice_mail"]
    assert invoice_mail["enabled"] is False
    assert invoice_mail["status"] == "not_configured"
    assert "path_hint" not in invoice_mail


def test_write_snapshot_writes_utf8_json_without_private_absolute_paths(
    tmp_path,
    monkeypatch,
):
    localappdata = tmp_path / "Users" / "Lukas" / "AppData" / "Local"
    tool_root = localappdata / "MailProcessor" / "tools" / "universal_invoice_mail"
    tool_root.mkdir(parents=True)
    (tool_root / "main.py").write_text("", encoding="utf-8")

    cfg = AppConfig(first_run=False)
    cfg.get_tool("universal_invoice_mail").enabled = True
    cfg.get_tool("universal_invoice_mail").path = str(tool_root)
    cfg.get_tool("universal_invoice_mail").main_script = "main.py"

    monkeypatch.setattr("snapshot_export.LOCALAPPDATA_ROOT", localappdata)

    output_path = tmp_path / "exports" / "mailprocessor-suite-v1.json"
    written_path = write_snapshot(
        output_path,
        cfg,
        exported_at=datetime.fromisoformat("2026-06-02T08:00:00+02:00"),
    )

    text = written_path.read_text(encoding="utf-8")
    assert written_path == output_path
    assert '"schema": "mailprocessor-suite-v1"' in text
    assert "Lukas" not in text
    assert str(tool_root) not in text
    assert "LOCALAPPDATA/MailProcessor/tools/universal_invoice_mail" in text


def test_safe_localappdata_root_falls_back_to_home_when_env_is_empty(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", "")

    assert _safe_localappdata_root() == Path.home()


def test_safe_localappdata_root_falls_back_to_home_when_env_is_relative(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", "relative-localappdata")

    assert _safe_localappdata_root() == Path.home()
