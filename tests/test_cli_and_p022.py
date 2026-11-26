"""Tests for MailProcessor headless CLI and Policy P-022 artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import config as cfg_module
import mailprocessor_cli
import main as main_module
import tool_manager as tm_module


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "MailProcessor"
    cfg_file = cfg_dir / "config.json"
    monkeypatch.setattr(cfg_module, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(cfg_module, "CONFIG_FILE", cfg_file)
    return cfg_file


def test_version_and_help_via_main_without_qapp(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["MailProcessor", "--version", "--json"])
    assert main_module.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"app": "MailProcessor", "version": "0.1.0"}

    monkeypatch.setattr(sys, "argv", ["MailProcessor", "--help"])
    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 0
    assert "MailProcessor headless CLI" in capsys.readouterr().out


def test_cli_status_scan_register_snapshot_launch_and_unregister(tmp_path, monkeypatch, capsys):
    suite_root = tmp_path / "suite"
    cleaner_dir = suite_root / "REL-PUB_UniversalMailCleaner"
    cleaner_dir.mkdir(parents=True)
    cleaner_script = cleaner_dir / "mail_imap_cleaner_v1.py"
    cleaner_script.write_text("# cleaner\n", encoding="utf-8")

    grabber_dir = tmp_path / "manual_grabber"
    grabber_dir.mkdir(parents=True)
    grabber_script = grabber_dir / "UniversalDocsGrabberV1.py"
    grabber_script.write_text("# grabber\n", encoding="utf-8")

    monkeypatch.setattr(tm_module, "_SCAN_ROOTS", [suite_root])
    monkeypatch.setattr(tm_module, "_DOWNLOAD_DIR", tmp_path / "downloads")

    # 1. Dry-run scan leaves config untouched
    assert mailprocessor_cli.main(["scan", "--json"]) == 0
    scan_dry = json.loads(capsys.readouterr().out)
    assert scan_dry["dry_run"] is True
    assert scan_dry["detected"]["universal_mail_cleaner"]["found"] is True
    assert not cfg_module.CONFIG_FILE.exists()

    # 2. Apply scan persists discovered tool
    assert mailprocessor_cli.main(["scan", "--apply", "--json"]) == 0
    scan_apply = json.loads(capsys.readouterr().out)
    assert scan_apply["applied"] is True
    assert scan_apply["updated_tools"] == ["universal_mail_cleaner"]
    assert cfg_module.CONFIG_FILE.is_file()

    # 3. Register second tool manually
    assert mailprocessor_cli.main(["register", "universal_docs_grabber", str(grabber_script), "--json"]) == 0
    reg_payload = json.loads(capsys.readouterr().out)
    assert reg_payload["ok"] is True
    assert reg_payload["tool"]["status"] == "available"

    # 4. Status reflects both configured tools with redacted path hints
    assert mailprocessor_cli.main(["status", "--json"]) == 0
    status_payload = json.loads(capsys.readouterr().out)
    by_id = {item["id"]: item for item in status_payload["tools"]}
    assert by_id["universal_mail_cleaner"]["status"] == "available"
    assert by_id["universal_docs_grabber"]["status"] == "available"
    assert by_id["universal_invoice_mail"]["status"] == "not_configured"
    assert str(tmp_path) not in (by_id["universal_mail_cleaner"]["path_hint"] or "")

    # 5. Snapshot exports to file atomically
    snap_path = tmp_path / "out" / "suite.json"
    assert mailprocessor_cli.main(["snapshot", "--out", str(snap_path), "--json"]) == 0
    snap_res = json.loads(capsys.readouterr().out)
    assert snap_res["ok"] is True
    snap_data = json.loads(snap_path.read_text(encoding="utf-8"))
    assert snap_data["schema"] == "mailprocessor-suite-v1"
    assert len(snap_data["tools"]) == 3

    # 6. Launch dry-run validates script and interpreter without spawning
    assert mailprocessor_cli.main(["launch", "universal_mail_cleaner", "--dry-run", "--json"]) == 0
    launch_dry = json.loads(capsys.readouterr().out)
    assert launch_dry["ok"] is True
    assert launch_dry["dry_run"] is True

    # 7. Unregister requires --yes unless --dry-run
    assert mailprocessor_cli.main(["unregister", "universal_docs_grabber", "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False

    assert mailprocessor_cli.main(["unregister", "universal_docs_grabber", "--yes", "--json"]) == 0
    unreg_ok = json.loads(capsys.readouterr().out)
    assert unreg_ok["ok"] is True
    assert unreg_ok["dry_run"] is False
    assert cfg_module.load().tools["universal_docs_grabber"].enabled is False


def test_cli_fail_closed_for_unknown_tool_and_missing_path(tmp_path, capsys):
    assert mailprocessor_cli.main(["register", "unknown_tool", str(tmp_path), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False

    assert mailprocessor_cli.main(["register", "universal_mail_cleaner", str(tmp_path / "missing"), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_cli_store_readiness_delegation(capsys):
    rc = mailprocessor_cli.main(["store-readiness", "--json"])
    assert rc == 2
    report = json.loads(capsys.readouterr().out)
    assert report["schema_version"] == "mailprocessor-store-readiness-v1"
    assert report["status"] == "blocked"


def test_p022_skill_and_llm_entrypoint_files():
    root = Path(__file__).resolve().parents[1]
    skill_md = (root / "SKILL.md").read_text(encoding="utf-8")
    llm_txt = (root / "llm.txt").read_text(encoding="utf-8")
    llms_txt = (root / "llms.txt").read_text(encoding="utf-8")

    assert "mailprocessor" in skill_md.lower()
    assert "status --json" in skill_md
    assert "snapshot" in skill_md
    assert "C:\\Users\\" not in skill_md
    assert "OneDrive" not in skill_md

    assert "llms.txt" in llm_txt
    assert "SKILL.md" in llm_txt
    assert "SKILL.md" in llms_txt
    assert "llm.txt" in llms_txt
