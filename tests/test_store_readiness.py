from __future__ import annotations

import hashlib
import json
from pathlib import Path

from store_readiness import _required_capabilities, audit_store_readiness


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ready_fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "project"
    release = tmp_path / "release"
    root.mkdir()
    release.mkdir()

    _write(
        root / "pyproject.toml",
        '[project]\nname = "mailprocessor"\nversion = "0.1.0"\n',
    )
    _write(root / "requirements.txt", "PySide6>=6.6.0\n")
    _write(root / "THIRD_PARTY_LICENSES.txt", "PySide6 | LGPL\n")
    _write(root / "PRIVACY_POLICY.md", "# Privacy\n")
    _write(root / "SUPPORT.md", "# Support\n")
    _write(root / "tool_manager.py", "import urllib.request\nimport subprocess\nsubprocess.Popen\n")
    _write(root / "settings_dialog.py", "import winreg\n")
    _write(
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
    _write(
        root / "store_package" / "MailProcessor" / "AppxManifest.xml",
        '''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
 xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
 <Identity Name="Publisher.MailProcessor" Publisher="CN=publisher" Version="0.1.0.0" />
 <Capabilities><Capability Name="internetClient"/><rescap:Capability Name="runFullTrust"/></Capabilities>
</Package>''',
    )
    _write(root / "releases" / "windowsstore" / "MailProcessor-0.1.0.msix", "package")
    _write(root / "releases" / "windowsstore" / "WACK_PROTOCOL.md", "Result: PASS\n")

    exe = release / "MailProcessor-0.1.0-desktop.exe"
    source = release / "MailProcessor-0.1.0-source.zip"
    exe.write_bytes(b"exe")
    source.write_bytes(b"source")
    _write(
        release / "SHA256SUMS.txt",
        f"{_sha256(exe)}  {exe.name}\n{_sha256(source)}  {source.name}\n",
    )
    return root, release


def _by_id(report: dict) -> dict[str, dict]:
    return {item["check_id"]: item for item in report["checks"]}


def test_ready_fixture_passes_all_gates(tmp_path):
    root, release = _ready_fixture(tmp_path)

    report = audit_store_readiness(root, release)

    assert report["status"] == "ready"
    assert all(item["status"] == "pass" for item in report["checks"])


def test_tampered_release_is_a_blocker(tmp_path):
    root, release = _ready_fixture(tmp_path)
    (release / "MailProcessor-0.1.0-desktop.exe").write_bytes(b"tampered")

    report = audit_store_readiness(root, release)

    check = _by_id(report)["release_integrity"]
    assert report["status"] == "blocked"
    assert check["status"] == "blocker"
    assert "Hashabweichung" in check["detail"]


def test_missing_fulltrust_capability_is_a_blocker(tmp_path):
    root, release = _ready_fixture(tmp_path)
    config_path = root / "store_package.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["capabilities"] = "internetClient"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    report = audit_store_readiness(root, release)

    check = _by_id(report)["store_config"]
    assert check["status"] == "blocker"
    assert "runFullTrust" in check["detail"]


def test_missing_privacy_and_support_material_is_a_blocker(tmp_path):
    root, release = _ready_fixture(tmp_path)
    (root / "PRIVACY_POLICY.md").unlink()
    (root / "SUPPORT.md").unlink()

    report = audit_store_readiness(root, release)

    check = _by_id(report)["privacy_support_docs"]
    assert check["status"] == "blocker"
    assert "PRIVACY_POLICY.md" in check["detail"]
    assert "SUPPORT.md" in check["detail"]


def test_release_checksum_cannot_escape_release_directory(tmp_path):
    root, release = _ready_fixture(tmp_path)
    outside = tmp_path / "MailProcessor-0.1.0-desktop.exe"
    outside.write_bytes(b"outside")
    source = release / "MailProcessor-0.1.0-source.zip"
    _write(
        release / "SHA256SUMS.txt",
        f"{_sha256(outside)}  ../{outside.name}\n{_sha256(source)}  {source.name}\n",
    )

    report = audit_store_readiness(root, release)

    check = _by_id(report)["release_integrity"]
    assert check["status"] == "blocker"
    assert "unsicherer Artefaktpfad" in check["detail"]


def test_auditor_does_not_create_its_own_capability_requirements(tmp_path):
    _write(tmp_path / "store_readiness.py", "subprocess.Popen\nimport winreg\nimport urllib.request\n")

    assert _required_capabilities(tmp_path) == set()
