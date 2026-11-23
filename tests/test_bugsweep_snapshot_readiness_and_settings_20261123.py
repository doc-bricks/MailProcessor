"""Regression tests for the 2026-11-23 bugsweep iteration.

Covers:
- BS-01: tray.py Cancel must not persist config/language to disk; settings_dialog.py
  autostart comparison rejects extra trailing flags/unbalanced quotes and renders
  platform-native script paths.
- BS-02: snapshot_export.py preserves HOME label when LOCALAPPDATA is unset/empty,
  normalizes '..' segments before tail redaction, scopes pyproject version lookup
  to [project], rejects directory/blank targets, and writes atomically without
  leaving temp files on failure.
- BS-03: store_readiness.py enforces exact version boundaries in SHA256SUMS.txt,
  rejects drive-relative / symlink-escaping artifact paths, and parses [project]
  with multiline arrays via TOML parser.
- BS-04: store_readiness.py checks dependencies with PEP-508/503 token boundaries
  (no substring false-positives), requires rescap namespace for runFullTrust in
  AppxManifest.xml, distinguishes real WACK XML/protocol PASS from prose templates,
  ignores archived/venv trees, and degrades UnicodeDecodeError to blocker checks.
- BS-05: update_files.py cleans up temporary files when os.replace fails and turns
  invalid UTF-8 targets into MaintenanceError (exit code 2).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QDialog

import config as cfg_module
from config import AppConfig
from i18n import get_language, set_language
import settings_dialog
from snapshot_export import _read_app_version, _redact_path_hint, write_snapshot
from store_readiness import audit_store_readiness
from tray import MailProcessorTray
import update_files


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_utf8(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _base_ready_fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "project"
    release = tmp_path / "release"
    root.mkdir()
    release.mkdir()

    _write_utf8(
        root / "pyproject.toml",
        '[project]\nname = "mailprocessor"\nclassifiers = [\n"Topic :: Utilities",\n]\nversion = "0.1.0"\n',
    )
    _write_utf8(root / "requirements.txt", "PySide6>=6.6.0\n")
    _write_utf8(root / "THIRD_PARTY_LICENSES.txt", "PySide6 | LGPL-3.0\n")
    _write_utf8(root / "PRIVACY_POLICY.md", "# Privacy\n")
    _write_utf8(root / "SUPPORT.md", "# Support\n")
    _write_utf8(root / "tool_manager.py", "import urllib.request\nimport subprocess\nsubprocess.Popen\n")
    _write_utf8(root / "settings_dialog.py", "import winreg\n")
    _write_utf8(
        root / "store_package.json",
        json.dumps(
            {
                "app_name": "MailProcessor",
                "publisher": "CN=publisher",
                "identity_name": "Publisher.MailProcessor",
                "version": "0.1.0.0",
                "executable": "MailProcessor.exe",
                "capabilities": "runFullTrust,internetClient",
                "privacy_url": "https://example.test/privacy",
                "support_url": "https://example.test/support",
            }
        ),
    )
    _write_utf8(
        root / "store_package" / "MailProcessor" / "AppxManifest.xml",
        '''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
 xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
 <Identity Name="Publisher.MailProcessor" Publisher="CN=publisher" Version="0.1.0.0" />
 <Capabilities><Capability Name="internetClient"/><rescap:Capability Name="runFullTrust"/></Capabilities>
</Package>''',
    )
    _write_utf8(root / "releases" / "windowsstore" / "MailProcessor-0.1.0.msix", "package")
    _write_utf8(root / "releases" / "windowsstore" / "WACK_PROTOCOL.md", "Result: PASS\n")

    exe = release / "MailProcessor-0.1.0-desktop.exe"
    source = release / "MailProcessor-0.1.0-source.zip"
    exe.write_bytes(b"exe")
    source.write_bytes(b"source")
    _write_utf8(
        release / "SHA256SUMS.txt",
        f"{_sha256(exe)}  {exe.name}\n{_sha256(source)}  {source.name}\n",
    )
    return root, release


def test_bs01_tray_cancel_settings_does_not_save_or_mutate_config(qapp, tmp_path, monkeypatch):
    set_language("de")
    cfg = AppConfig(language="de", first_run=False, start_with_windows=False)
    cfg.get_tool("universal_mail_cleaner").enabled = True
    cfg.get_tool("universal_mail_cleaner").path = str(tmp_path)
    cfg.get_tool("universal_mail_cleaner").main_script = "main.py"

    save_calls: list[AppConfig] = []
    monkeypatch.setattr(cfg_module, "save", lambda c: save_calls.append(c))

    class FakeRejectedDialog:
        def __init__(self, app_cfg, parent=None):
            # Simulate in-dialog mutations before user clicks Cancel
            app_cfg.tools.clear()
            app_cfg.start_with_windows = True
            set_language("en")

        def exec(self):
            return QDialog.DialogCode.Rejected

    monkeypatch.setattr(settings_dialog, "SettingsDialog", FakeRejectedDialog)

    tray_icon = MailProcessorTray(cfg, parent=qapp)
    try:
        tray_icon._open_settings()
        assert save_calls == [], "Clicking Cancel in SettingsDialog must not write config.json"
        assert cfg.language == "de"
        assert cfg.start_with_windows is False
        assert get_language() == "de"
        assert cfg.tools["universal_mail_cleaner"].enabled is True
    finally:
        tray_icon.hide()
        tray_icon.setContextMenu(None)
        tray_icon.deleteLater()


def test_bs01_autostart_command_rejects_extra_flags_and_unbalanced_quotes(monkeypatch, tmp_path):
    monkeypatch.setattr(sys := settings_dialog.sys, "frozen", True, raising=False)
    fake_exe = tmp_path / "MailProcessor.exe"
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    assert settings_dialog._is_current_autostart_command(f'"{fake_exe}"') is True
    # Extra --self-test or stale CLI argument must NOT be accepted as current!
    assert settings_dialog._is_current_autostart_command(f'"{fake_exe}" --self-test') is False
    # Unbalanced quote must NOT be accepted as current!
    assert settings_dialog._is_current_autostart_command(f'"{fake_exe}') is False


def test_bs02_snapshot_redaction_preserves_home_when_localappdata_falls_back_and_strips_dotdot(
    tmp_path, monkeypatch
):
    fake_home = tmp_path / "HomeUser"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    # Simulate unset LOCALAPPDATA where LOCALAPPDATA_ROOT fell back to Path.home()
    monkeypatch.setattr("snapshot_export.LOCALAPPDATA_ROOT", fake_home)

    home_tool = fake_home / "Tools" / "UniversalMailCleaner"
    assert _redact_path_hint(str(home_tool)) == "HOME/Tools/UniversalMailCleaner"

    # Whitespace-only path must return None
    assert _redact_path_hint("   ") is None

    # Relative path must never expand against CWD even when CWD is inside HOME
    monkeypatch.chdir(fake_home)
    assert _redact_path_hint("./tools/universal_mail_cleaner") == ".../tools/universal_mail_cleaner"

    # Parent traversal outside HOME/LOCALAPPDATA must not leak discarded segment names or '..'
    escaped = tmp_path / "OtherSecretUser" / "Sub" / ".."
    hint = _redact_path_hint(str(escaped))
    assert hint == f".../{tmp_path.name}/OtherSecretUser"
    assert "Sub" not in hint
    assert ".." not in hint.split("/")[1:]
    assert _redact_path_hint("../..") is None


def test_bs02_read_app_version_scopes_pyproject_to_project_table_and_write_snapshot_is_atomic(
    tmp_path, monkeypatch
):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    _write_utf8(
        app_dir / "pyproject.toml",
        '[tool.other]\nversion = "9.9.9"\n\n[project]\nname = "doc-bricks-mailprocessor"\nversion = "0.1.0"\n',
    )
    monkeypatch.setattr("snapshot_export.APP_ROOT", app_dir)
    assert _read_app_version() == "0.1.0"
    # Verify Python 3.10 fallback scanner (when tomllib is None) produces identical result
    monkeypatch.setattr("snapshot_export.tomllib", None)
    assert _read_app_version() == "0.1.0"

    # Directory target must fail cleanly without corrupting directory
    out_dir = tmp_path / "existing_dir"
    out_dir.mkdir()
    with pytest.raises((IsADirectoryError, ValueError, OSError)):
        write_snapshot(out_dir, AppConfig(first_run=False))

    # Failed os.replace must preserve existing snapshot file and leave no .tmp file behind
    target = tmp_path / "snap" / "mailprocessor-suite-v1.json"
    _write_utf8(target, '{"preserved": true}\n')

    def boom_replace(src, dst):
        raise PermissionError("simulated replace failure")

    monkeypatch.setattr(os, "replace", boom_replace)
    with pytest.raises(PermissionError):
        write_snapshot(target, AppConfig(first_run=False))

    assert target.read_text(encoding="utf-8") == '{"preserved": true}\n'
    leftovers = [p.name for p in target.parent.iterdir() if p.name != target.name]
    assert leftovers == []


def test_bs03_store_readiness_enforces_exact_version_boundary_in_release_artifacts(tmp_path, monkeypatch):
    root, release = _base_ready_fixture(tmp_path)
    # Verify Python 3.10 fallback TOML parser handles multiline arrays inside [project]
    import store_readiness
    with monkeypatch.context() as mp:
        mp.setattr(store_readiness, "tomllib", None)
        assert audit_store_readiness(root, release)["status"] == "ready"
    # Replace 0.1.0-desktop.exe with 10.1.0-desktop.exe (contains substring '0.1.0'!)
    (release / "MailProcessor-0.1.0-desktop.exe").unlink()
    wrong_ver_exe = release / "MailProcessor-10.1.0-desktop.exe"
    wrong_ver_exe.write_bytes(b"exe")
    source = release / "MailProcessor-0.1.0-source.zip"
    _write_utf8(
        release / "SHA256SUMS.txt",
        f"{_sha256(wrong_ver_exe)}  {wrong_ver_exe.name}\n{_sha256(source)}  {source.name}\n",
    )

    report = audit_store_readiness(root, release)
    checks = {item["check_id"]: item for item in report["checks"]}
    assert report["status"] == "blocked"
    assert checks["release_integrity"]["status"] == "blocker"


def test_bs04_store_readiness_dependency_word_boundary_rescap_and_wack_parsing(tmp_path):
    root, release = _base_ready_fixture(tmp_path)

    # 1. Substring false-positive: requirement 'ring' must NOT match 'keyring' in licenses!
    _write_utf8(root / "requirements.txt", "PySide6>=6.6.0,!=6.12.0; sys_platform == 'win32'\nring>=1.0\n")
    _write_utf8(root / "THIRD_PARTY_LICENSES.txt", "PySide6 | LGPL-3.0\nkeyring | MIT\n")
    report1 = audit_store_readiness(root, release)
    checks1 = {item["check_id"]: item for item in report1["checks"]}
    assert checks1["dependency_licenses"]["status"] == "blocker"
    assert "ring" in checks1["dependency_licenses"]["detail"]
    assert "PySide6" not in checks1["dependency_licenses"]["detail"]

    # Fix license inventory (also testing hyphen/underscore PEP-503 normalization)
    _write_utf8(root / "requirements.txt", "python_multipart>=0.0.9; sys_platform == 'win32' # form parser\n")
    _write_utf8(root / "THIRD_PARTY_LICENSES.txt", "python-multipart | Apache-2.0\n")

    # 2. runFullTrust in default namespace (without rescap) must be a blocker!
    _write_utf8(
        root / "store_package" / "MailProcessor" / "AppxManifest.xml",
        '''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10">
 <Identity Name="Publisher.MailProcessor" Publisher="CN=publisher" Version="0.1.0.0" />
 <Capabilities><Capability Name="internetClient"/><Capability Name="runFullTrust"/></Capabilities>
</Package>''',
    )
    report2 = audit_store_readiness(root, release)
    checks2 = {item["check_id"]: item for item in report2["checks"]}
    assert checks2["dependency_licenses"]["status"] == "pass"
    assert checks2["appx_manifest"]["status"] == "blocker"

    # Restore valid rescap manifest
    _write_utf8(
        root / "store_package" / "MailProcessor" / "AppxManifest.xml",
        '''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
 xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
 <Identity Name="Publisher.MailProcessor" Publisher="CN=publisher" Version="0.1.0.0" />
 <Capabilities><Capability Name="internetClient"/><rescap:Capability Name="runFullTrust"/></Capabilities>
</Package>''',
    )

    # 3a. Prose template ("All WACK tests must pass before submission", status PENDING) must NOT pass!
    _write_utf8(
        root / "releases" / "windowsstore" / "WACK_PROTOCOL.md",
        "# WACK Protocol\nStatus: PENDING_MSIX_BUILD\nAll WACK checks must pass before Store submission.\n",
    )
    report3 = audit_store_readiness(root, release)
    checks3 = {item["check_id"]: item for item in report3["checks"]}
    assert checks3["wack_report"]["status"] == "blocker"

    # 3b. Real appcert XML report with OVERALL_RESULT="PASS" and description mentioning "failures" MUST pass!
    (root / "releases" / "windowsstore" / "WACK_PROTOCOL.md").unlink()
    _write_utf8(
        root / "releases" / "windowsstore" / "wack_report.xml",
        '''<?xml version="1.0" encoding="utf-8"?>
<REPORT OVERALL_RESULT="PASS">
  <REQUIREMENT TITLE="Crashes and hangs" RATIONALE="Checks for app launch failures." RESULT="PASS" />
</REPORT>''',
    )
    # Also place an archived AppxManifest under _archive/ to verify ignored directories don't break count
    _write_utf8(root / "_archive" / "old" / "AppxManifest.xml", "<Package/>")

    report4 = audit_store_readiness(root, release)
    assert report4["status"] == "ready", report4["checks"]


def test_bs04_store_readiness_handles_non_utf8_license_file_without_crashing(tmp_path):
    root, release = _base_ready_fixture(tmp_path)
    (root / "THIRD_PARTY_LICENSES.txt").write_bytes(b"PySide6 \xff\xfe invalid utf8")

    report = audit_store_readiness(root, release)
    checks = {item["check_id"]: item for item in report["checks"]}
    assert report["status"] == "blocked"
    assert checks["dependency_licenses"]["status"] == "blocker"


def test_bs05_update_files_cleans_temp_on_replace_failure_and_catches_invalid_utf8(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(update_files, "PROJECT_DIR", tmp_path)
    _write_utf8(
        tmp_path / "build_exe.bat",
        '  --name MailProcessor ^\n  --icon "%ICON_PATH%" ^\n  --distpath "dist" ^',
    )
    _write_utf8(tmp_path / "tray.py", "self.setIcon(_load_tray_icon())\n")
    _write_utf8(tmp_path / "settings_dialog.py", "ensure_autostart_entry(enable)\n")
    _write_utf8(tmp_path / "main.py", "ensure_autostart_entry(cfg.start_with_windows)\n")

    def fail_replace(src, dst):
        raise PermissionError("locked target")

    monkeypatch.setattr(os, "replace", fail_replace)
    assert update_files.main(["--project-dir", str(tmp_path), "--apply"]) == 2
    # No leftover temporary files may remain in tmp_path
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == sorted(update_files.TARGET_FILES)

    # Corrupt UTF-8 in main.py must return exit code 2 (MaintenanceError), not crash with UnicodeDecodeError
    (tmp_path / "main.py").write_bytes(b"\xff\xfe\x00bad")
    assert update_files.main(["--project-dir", str(tmp_path)]) == 2
