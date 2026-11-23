"""Fail-closed Microsoft Store readiness audit for MailProcessor.

The audit is intentionally read-only.  It validates the existing release bundle,
Store metadata, capability contract, package, WACK evidence, and dependency
documentation.  It never builds, signs, uploads, or submits an artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

_RESCAP_NS = "http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "build",
        "dist",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "_archive",
        "_archiv",
        "node_modules",
    }
)


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


def _iter_project_files(project_root: Path) -> Iterable[Path]:
    for current_root, dirs, files in os.walk(project_root):
        dirs[:] = sorted(d for d in dirs if d not in _IGNORED_DIRS)
        base = Path(current_root)
        for filename in sorted(files):
            candidate = base / filename
            if candidate.is_file():
                yield candidate


def _extract_pyproject_project_version(text: str) -> str:
    if tomllib is not None:
        try:
            data = tomllib.loads(text)
        except Exception as exc:
            raise ValueError(f"pyproject.toml ungültig: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("project"), dict):
            raise ValueError("[project] fehlt in pyproject.toml")
        version = data["project"].get("version")
        if not isinstance(version, str) or not version.strip():
            raise ValueError("[project].version fehlt in pyproject.toml")
        return version.strip()

    found_project = False
    in_project = False
    bracket_depth = 0
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if bracket_depth == 0:
            header_match = re.match(r"^\[+\s*([^\[\]]+?)\s*\]+\s*(?:#.*)?$", stripped)
            if header_match:
                in_project = header_match.group(1).strip() == "project"
                if in_project:
                    found_project = True
                continue
            if in_project:
                ver_match = re.match(
                    r"""^version\s*=\s*(?:"([^"]+)"|'([^']+)')\s*(?:#.*)?$""",
                    stripped,
                )
                if ver_match:
                    value = (ver_match.group(1) or ver_match.group(2) or "").strip()
                    if value:
                        return value
        in_quote: str | None = None
        escaped = False
        for ch in stripped:
            if escaped:
                escaped = False
                continue
            if ch == "\\" and in_quote == '"':
                escaped = True
                continue
            if in_quote is not None:
                if ch == in_quote:
                    in_quote = None
                continue
            if ch in ('"', "'"):
                in_quote = ch
            elif ch == "#":
                break
            elif ch == "[":
                bracket_depth += 1
            elif ch == "]" and bracket_depth > 0:
                bracket_depth -= 1
    if not found_project:
        raise ValueError("[project] fehlt in pyproject.toml")
    raise ValueError("[project].version fehlt in pyproject.toml")


def _project_version(project_root: Path) -> str:
    if not project_root.is_dir():
        raise ValueError(f"Projektverzeichnis fehlt: {project_root}")
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        raise ValueError("pyproject.toml fehlt")
    text = pyproject.read_text(encoding="utf-8")
    return _extract_pyproject_project_version(text)


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
    resolved_release_dir = release_dir.resolve()
    for name, expected in entries.items():
        rel_path = Path(name)
        candidate = release_dir / name
        if (
            rel_path.is_absolute()
            or bool(rel_path.drive)
            or bool(rel_path.root)
            or ".." in rel_path.parts
            or candidate.is_symlink()
        ):
            mismatches.append(f"unsicherer Artefaktpfad: {name}")
            continue
        artifact = candidate.resolve(strict=False)
        if not artifact.is_relative_to(resolved_release_dir):
            mismatches.append(f"unsicherer Artefaktpfad: {name}")
            continue
        if not artifact.is_file():
            mismatches.append(f"fehlt: {name}")
        else:
            try:
                actual_hash = _sha256(artifact)
            except OSError as exc:
                mismatches.append(f"nicht lesbar ({name}): {exc}")
                continue
            if actual_hash != expected:
                mismatches.append(f"Hashabweichung: {name}")
    for suffix in missing_types:
        mismatches.append(f"kein gelistetes *{suffix}")

    version_pattern = re.compile(rf"(?<![0-9.]){re.escape(version)}(?![0-9.])")
    names_match_version = all(
        bool(version_pattern.search(name))
        for name in entries
        if name.endswith(required_suffixes)
    )
    if not names_match_version:
        mismatches.append(f"Artefaktname enthält nicht exakt Projektversion {version}")

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
    manifests = [path for path in _iter_project_files(project_root) if path.name == "AppxManifest.xml"]
    if len(manifests) != 1:
        return [Check("appx_manifest", "blocker", f"Erwartet genau ein AppxManifest.xml, gefunden: {len(manifests)}")]
    try:
        manifest_text = manifests[0].read_text(encoding="utf-8")
        root = ET.fromstring(manifest_text)
    except (OSError, UnicodeError, ET.ParseError) as exc:
        return [Check("appx_manifest", "blocker", f"AppxManifest.xml ungültig: {exc}")]

    identity = next((element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "Identity"), None)
    manifest_version = identity.attrib.get("Version") if identity is not None else None
    capabilities: set[str] = set()
    wrong_ns_fulltrust = False
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "Capability":
            continue
        cap_name = element.attrib.get("Name", "").strip()
        if not cap_name:
            continue
        if cap_name == "runFullTrust":
            if element.tag == f"{{{_RESCAP_NS}}}Capability":
                capabilities.add(cap_name)
            else:
                wrong_ns_fulltrust = True
        else:
            capabilities.add(cap_name)

    missing_caps = sorted(required_caps - capabilities)
    problems: list[str] = []
    if manifest_version != _four_part_version(version):
        problems.append(f"Manifest-Version {manifest_version!r}, erwartet {_four_part_version(version)}")
    if wrong_ns_fulltrust:
        problems.append("runFullTrust muss als rescap:Capability im restrictedcapabilities-Namespace deklariert sein")
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


def _normalize_pkg_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).casefold().strip("-")


def _extract_requirement_name(raw_line: str) -> str | None:
    line = raw_line.split("#", 1)[0].strip()
    if not line or line.startswith("-"):
        return None
    line = line.split(";", 1)[0].strip()
    line = line.split("@", 1)[0].strip()
    if not line:
        return None
    pkg = re.split(r"[<>=!~\[\s]", line, maxsplit=1)[0].strip()
    return pkg or None


def _dependency_check(project_root: Path) -> Check:
    requirements = project_root / "requirements.txt"
    licenses = project_root / "THIRD_PARTY_LICENSES.txt"
    if not requirements.is_file() or not licenses.is_file():
        return Check("dependency_licenses", "blocker", "requirements.txt oder THIRD_PARTY_LICENSES.txt fehlt")
    try:
        req_lines = requirements.read_text(encoding="utf-8").splitlines()
        license_raw = licenses.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return Check("dependency_licenses", "blocker", f"Lizenz-/Abhängigkeitsdatei ungültig: {exc}")

    package_names: list[str] = []
    for raw_line in req_lines:
        pkg_name = _extract_requirement_name(raw_line)
        if pkg_name:
            package_names.append(pkg_name)

    documented_tokens = {
        _normalize_pkg_name(tok)
        for tok in re.findall(r"[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*", license_raw)
        if _normalize_pkg_name(tok)
    }
    missing = [name for name in package_names if _normalize_pkg_name(name) not in documented_tokens]
    return _check(
        "dependency_licenses",
        not missing,
        f"{len(package_names)} direkte Runtime-Abhängigkeiten sind im Lizenzinventar abgedeckt",
        "Nicht im Lizenzinventar: " + ", ".join(missing),
    )


def _is_passing_wack_report(report_path: Path) -> bool:
    try:
        raw_text = report_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False

    suffix = report_path.suffix.casefold()
    if suffix == ".xml":
        try:
            root = ET.fromstring(raw_text)
        except ET.ParseError:
            return False
        overall_results: list[str] = []
        for elem in root.iter():
            for attr_key, attr_val in elem.attrib.items():
                key_lower = attr_key.rsplit("}", 1)[-1].casefold()
                val_lower = attr_val.strip().casefold()
                if key_lower == "overall_result":
                    overall_results.append(val_lower)
                elif key_lower == "result" and val_lower in {"fail", "failed"}:
                    return False
        return bool(overall_results) and all(val in {"pass", "passed"} for val in overall_results)

    if re.search(
        r"\b(?:fail|failed|failure|failures|pending(?:_[a-z0-9_]+)?|not\s+run|tbd|todo)\b",
        raw_text,
        flags=re.IGNORECASE,
    ):
        return False
    return bool(
        re.search(
            r"(?im)^\s*[-*#>\s]*(?:overall[_\s-]*)?(?:wack[_\s-]*)?(?:result|status|verdict|ergebnis)\s*[:=]\s*\*{0,2}(?:pass|passed|bestanden)\*{0,2}\s*$",
            raw_text,
        )
    )


def _distribution_checks(project_root: Path) -> list[Check]:
    docs = [name for name in ("PRIVACY_POLICY.md", "SUPPORT.md") if not (project_root / name).is_file()]
    all_files = list(_iter_project_files(project_root))
    packages = [path for path in all_files if path.suffix.casefold() == ".msix"]
    wack_reports = [
        path
        for path in all_files
        if "wack" in path.name.casefold() and path.suffix.casefold() in {".xml", ".txt", ".md"}
    ]
    valid_wack = any(_is_passing_wack_report(report) for report in wack_reports)
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
