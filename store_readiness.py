"""Fail-closed Microsoft Store readiness audit for MailProcessor.

The audit is intentionally read-only.  It validates the existing release bundle,
Store metadata, capability contract, package, WACK evidence, and dependency
documentation.  It never builds, signs, uploads, or submits an artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    detail: str


def _check(check_id: str, ok: bool, success: str, failure: str) -> Check:
    return Check(check_id, "pass" if ok else "blocker", success if ok else failure)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_version(project_root: Path) -> str:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        raise ValueError("pyproject.toml fehlt")
    text = pyproject.read_text(encoding="utf-8")
    project_match = re.search(r"(?ms)^\[project\]\s*$\n(.*?)(?=^\[|\Z)", text)
    if project_match is None:
        raise ValueError("[project] fehlt in pyproject.toml")
    version_match = re.search(
        r'''(?m)^\s*version\s*=\s*["']([^"']+)["']\s*$''',
        project_match.group(1),
    )
    if version_match is None or not version_match.group(1).strip():
        raise ValueError("[project].version fehlt in pyproject.toml")
    return version_match.group(1).strip()


def _four_part_version(version: str) -> str:
    parts = version.split(".")
    if not all(part.isdigit() for part in parts) or not 1 <= len(parts) <= 4:
        raise ValueError(f"Nicht unterstützte numerische Version: {version}")
    return ".".join(parts + ["0"] * (4 - len(parts)))


def _parse_sums(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+[*]?(.+)", line.strip())
        if not match:
            raise ValueError(f"Ungültige SHA256SUMS-Zeile: {line}")
        entries[match.group(2)] = match.group(1).lower()
    return entries


def _release_checks(release_dir: Path, version: str) -> list[Check]:
    sums_path = release_dir / "SHA256SUMS.txt"
    if not sums_path.is_file():
        return [Check("release_integrity", "blocker", f"SHA256SUMS.txt fehlt in {release_dir}")]
    try:
        entries = _parse_sums(sums_path)
    except (OSError, UnicodeError, ValueError) as exc:
        return [Check("release_integrity", "blocker", str(exc))]

    required_suffixes = ("-desktop.exe", "-source.zip")
    missing_types = [suffix for suffix in required_suffixes if not any(name.endswith(suffix) for name in entries)]
    mismatches: list[str] = []
    for name, expected in entries.items():
        artifact = (release_dir / name).resolve(strict=False)
        if not artifact.is_relative_to(release_dir.resolve()) or Path(name).is_absolute():
            mismatches.append(f"unsicherer Artefaktpfad: {name}")
            continue
        if not artifact.is_file():
            mismatches.append(f"fehlt: {name}")
        elif _sha256(artifact) != expected:
            mismatches.append(f"Hashabweichung: {name}")
    for suffix in missing_types:
        mismatches.append(f"kein gelistetes *{suffix}")

    names_match_version = all(version in name for name in entries if name.endswith(required_suffixes))
    if not names_match_version:
        mismatches.append(f"Artefaktname enthält nicht Projektversion {version}")

    return [
        _check(
            "release_integrity",
            not mismatches,
            f"{len(entries)} gelistete Release-Artefakte stimmen mit SHA256SUMS.txt überein",
            "; ".join(mismatches),
        )
    ]


def _https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _capability_set(value: object) -> set[str]:
    if isinstance(value, str):
        return {item.strip() for item in value.split(",") if item.strip()}
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()


def _required_capabilities(project_root: Path) -> set[str]:
    required: set[str] = set()
    source = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in project_root.glob("*.py")
        if path.is_file() and path.name != Path(__file__).name
    )
    if "subprocess.Popen" in source or "import winreg" in source:
        required.add("runFullTrust")
    if "urllib.request" in source:
        required.add("internetClient")
    return required


def _store_config_checks(project_root: Path, version: str, required_caps: set[str]) -> tuple[list[Check], dict]:
    config_path = project_root / "store_package.json"
    if not config_path.is_file():
        return [Check("store_config", "blocker", "store_package.json fehlt")], {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [Check("store_config", "blocker", f"store_package.json ungültig: {exc}")], {}
    if not isinstance(data, dict):
        return [Check("store_config", "blocker", "store_package.json muss ein JSON-Objekt sein")], {}

    required_text = ("app_name", "publisher", "identity_name", "executable")
    missing = [key for key in required_text if not isinstance(data.get(key), str) or not data[key].strip()]
    publisher = str(data.get("publisher", ""))
    if "YourPublisher" in publisher:
        missing.append("publisher (Platzhalter)")
    if data.get("version") != _four_part_version(version):
        missing.append(f"version (erwartet {_four_part_version(version)})")
    if not _https_url(data.get("privacy_url")):
        missing.append("privacy_url (HTTPS)")
    if not _https_url(data.get("support_url")):
        missing.append("support_url (HTTPS)")

    capabilities = _capability_set(data.get("capabilities"))
    missing_caps = sorted(required_caps - capabilities)
    if missing_caps:
        missing.append("capabilities: " + ", ".join(missing_caps))

    checks = [
        _check(
            "store_config",
            not missing,
            "Store-Metadaten, HTTPS-URLs, Version und Capability-Vertrag sind vollständig",
            "Fehlend oder inkonsistent: " + "; ".join(missing),
        )
    ]
    return checks, data


def _manifest_checks(project_root: Path, version: str, required_caps: set[str]) -> list[Check]:
    manifests = list(project_root.glob("**/AppxManifest.xml"))
    if len(manifests) != 1:
        return [Check("appx_manifest", "blocker", f"Erwartet genau ein AppxManifest.xml, gefunden: {len(manifests)}")]
    try:
        root = ET.parse(manifests[0]).getroot()
    except (OSError, ET.ParseError) as exc:
        return [Check("appx_manifest", "blocker", f"AppxManifest.xml ungültig: {exc}")]

    identity = next((element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "Identity"), None)
    manifest_version = identity.attrib.get("Version") if identity is not None else None
    capabilities = {
        element.attrib.get("Name", "")
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "Capability"
    }
    missing_caps = sorted(required_caps - capabilities)
    problems: list[str] = []
    if manifest_version != _four_part_version(version):
        problems.append(f"Manifest-Version {manifest_version!r}, erwartet {_four_part_version(version)}")
    if missing_caps:
        problems.append("fehlende Capabilities: " + ", ".join(missing_caps))
    return [
        _check(
            "appx_manifest",
            not problems,
            "Manifest-Version und erforderliche Capabilities stimmen",
            "; ".join(problems),
        )
    ]


def _dependency_check(project_root: Path) -> Check:
    requirements = project_root / "requirements.txt"
    licenses = project_root / "THIRD_PARTY_LICENSES.txt"
    if not requirements.is_file() or not licenses.is_file():
        return Check("dependency_licenses", "blocker", "requirements.txt oder THIRD_PARTY_LICENSES.txt fehlt")
    package_names = []
    for line in requirements.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            package_names.append(re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip())
    license_text = licenses.read_text(encoding="utf-8").casefold()
    missing = [name for name in package_names if name.casefold() not in license_text]
    return _check(
        "dependency_licenses",
        not missing,
        f"{len(package_names)} direkte Runtime-Abhängigkeiten sind im Lizenzinventar abgedeckt",
        "Nicht im Lizenzinventar: " + ", ".join(missing),
    )


def _distribution_checks(project_root: Path) -> list[Check]:
    docs = [name for name in ("PRIVACY_POLICY.md", "SUPPORT.md") if not (project_root / name).is_file()]
    packages = list(project_root.glob("**/*.msix"))
    wack_reports = [
        path
        for path in project_root.glob("**/*")
        if path.is_file() and "wack" in path.name.casefold() and path.suffix.casefold() in {".xml", ".txt", ".md"}
    ]
    valid_wack = False
    for report in wack_reports:
        text = report.read_text(encoding="utf-8", errors="replace").casefold()
        if "pass" in text and "fail" not in text:
            valid_wack = True
            break
    return [
        _check(
            "privacy_support_docs",
            not docs,
            "Datenschutz- und Supportdokumente sind vorhanden",
            "Fehlende Dokumente: " + ", ".join(docs),
        ),
        _check(
            "msix_package",
            bool(packages),
            f"MSIX-Paket vorhanden: {packages[0].relative_to(project_root)}" if packages else "",
            "Kein MSIX-Paket vorhanden",
        ),
        _check(
            "wack_report",
            valid_wack,
            "WACK-Bericht enthält PASS ohne FAIL",
            "Kein bestandener WACK-Bericht vorhanden",
        ),
    ]


def audit_store_readiness(project_root: Path, release_dir: Path | None = None) -> dict:
    project_root = project_root.resolve()
    try:
        version = _project_version(project_root)
        expected_store_version = _four_part_version(version)
    except (OSError, UnicodeError, ValueError) as exc:
        check = Check("project_version", "blocker", str(exc))
        return {"schema_version": "mailprocessor-store-readiness-v1", "status": "blocked", "checks": [asdict(check)]}

    if release_dir is None:
        release_dir = project_root / "releases" / f"v{version}"
    else:
        release_dir = release_dir.resolve()

    required_caps = _required_capabilities(project_root)
    checks: list[Check] = [
        Check("project_version", "pass", f"Projektversion {version}; Store-Version {expected_store_version}"),
        Check(
            "capability_contract",
            "pass",
            "Erforderlich aus dem Quellvertrag: " + (", ".join(sorted(required_caps)) or "keine"),
        ),
    ]
    checks.extend(_release_checks(release_dir, version))
    config_checks, _ = _store_config_checks(project_root, version, required_caps)
    checks.extend(config_checks)
    checks.extend(_manifest_checks(project_root, version, required_caps))
    checks.append(_dependency_check(project_root))
    checks.extend(_distribution_checks(project_root))

    status = "ready" if all(check.status == "pass" for check in checks) else "blocked"
    return {
        "schema_version": "mailprocessor-store-readiness-v1",
        "status": status,
        "project": "MailProcessor",
        "version": version,
        "release_dir": str(release_dir),
        "checks": [asdict(check) for check in checks],
    }


def _render_text(report: dict) -> str:
    lines = [f"MailProcessor Windows Store readiness: {report['status'].upper()}"]
    for item in report["checks"]:
        marker = "PASS" if item["status"] == "pass" else "BLOCKER"
        lines.append(f"[{marker}] {item['check_id']}: {item['detail']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only MailProcessor Windows Store readiness audit")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--release-dir", type=Path, help="Existing vX.Y.Z release bundle to hash-check")
    parser.add_argument("--json", action="store_true", help="Emit stable JSON for LLMs and automation")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    report = audit_store_readiness(args.project_root, args.release_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_render_text(report))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    sys.exit(main())
