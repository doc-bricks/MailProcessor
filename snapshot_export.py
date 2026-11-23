"""Read-only snapshot export for MailProcessor."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

from config import AppConfig
from tool_manager import TOOL_DEFINITIONS, ToolManager


def _safe_localappdata_root() -> Path:
    raw_local_appdata = os.environ.get("LOCALAPPDATA")
    base_dir = Path(raw_local_appdata) if raw_local_appdata else Path.home()
    if not base_dir.is_absolute():
        base_dir = Path.home()
    return base_dir


SNAPSHOT_SCHEMA = "mailprocessor-suite-v1"
APP_NAME = "MailProcessor"
LOCALAPPDATA_ROOT = _safe_localappdata_root()
APP_ROOT = Path(__file__).parent


def build_snapshot_payload(
    cfg: AppConfig,
    exported_at: datetime | None = None,
) -> dict:
    timestamp = exported_at or datetime.now().astimezone()
    tool_manager = ToolManager(cfg)

    return {
        "schema": SNAPSHOT_SCHEMA,
        "exported_at": timestamp.isoformat(timespec="seconds"),
        "app": {
            "name": APP_NAME,
            "version": _read_app_version(),
            "platform": _platform_name(),
        },
        "tools": [
            _build_tool_entry(tool_manager, tool_id)
            for tool_id in TOOL_DEFINITIONS
        ],
        "notes": [
            "Snapshot enthält keine Maildaten und keine Zugangsdaten.",
            "Pfade sind redigiert und nur als Hinweis für den Desktop-Abgleich gedacht.",
        ],
    }


def write_snapshot(
    target_path: str | Path,
    cfg: AppConfig,
    exported_at: datetime | None = None,
) -> Path:
    if isinstance(target_path, str) and not target_path.strip():
        raise ValueError("Snapshot target path must not be empty.")
    destination = Path(target_path)
    if not str(destination).strip():
        raise ValueError("Snapshot target path must not be empty.")
    if destination.is_symlink():
        raise ValueError(f"Refusing to overwrite symlink snapshot target: {destination}")
    if destination.exists() and destination.is_dir():
        raise IsADirectoryError(f"Snapshot destination is a directory: {destination}")

    has_explicit_parent = bool(destination.parent) and str(destination.parent) not in ("", ".")
    if has_explicit_parent:
        destination.parent.mkdir(parents=True, exist_ok=True)
    parent_dir = destination.parent if has_explicit_parent else Path(".")

    payload = build_snapshot_payload(cfg, exported_at=exported_at)
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=parent_dir,
            prefix=".mailprocessor-snapshot-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(serialized)
        os.replace(temp_path, destination)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
    return destination


def _build_tool_entry(tool_manager: ToolManager, tool_id: str) -> dict:
    meta = TOOL_DEFINITIONS[tool_id]
    tool_cfg = tool_manager.cfg.tools.get(tool_id)
    version = tool_manager.tool_version(tool_id)
    status = _tool_status(tool_manager, tool_id)

    entry = {
        "id": tool_id,
        "display_name": meta["display_name"],
        "enabled": bool(tool_cfg.enabled) if tool_cfg else False,
        "installed_by": tool_cfg.installed_by if tool_cfg and tool_cfg.installed_by else None,
        "version": version,
        "status": status,
    }

    path_hint = _redact_path_hint(tool_cfg.path if tool_cfg else None)
    if path_hint:
        entry["path_hint"] = path_hint

    return entry


def _tool_status(tool_manager: ToolManager, tool_id: str) -> str:
    tool_cfg = tool_manager.cfg.tools.get(tool_id)
    if not tool_cfg or not tool_cfg.enabled:
        return "not_configured"
    if not tool_cfg.path or not tool_cfg.main_script:
        return "not_configured"
    if tool_manager.is_path_valid(tool_id):
        return "available"
    return "missing"


def _extract_pyproject_version(text: str) -> str:
    if tomllib is not None:
        data = tomllib.loads(text)
        if isinstance(data, dict):
            project = data.get("project")
            if isinstance(project, dict):
                version = project.get("version")
                if isinstance(version, str) and version.strip():
                    return version.strip()
        return ""

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
    return ""


def _read_app_version() -> str:
    changelog_path = APP_ROOT / "CHANGELOG.md"
    if changelog_path.is_file():
        try:
            text = changelog_path.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r"##\s*\[?v?(\d+\.\d+\.\d+)\]?", text)
            if match:
                return match.group(1)
        except Exception:
            pass

    pyproject_path = APP_ROOT / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            text = pyproject_path.read_text(encoding="utf-8", errors="ignore")
            version = _extract_pyproject_version(text)
            if version:
                return version
        except Exception:
            pass

    try:
        import importlib.metadata

        return importlib.metadata.version("doc-bricks-mailprocessor")
    except Exception:
        pass

    return ""


def _platform_name() -> str:
    if os.name == "nt":
        return "windows"
    if os.name == "posix" and sys_platform_startswith("darwin"):
        return "macos"
    if os.name == "posix":
        return "linux"
    return "unknown"


def sys_platform_startswith(prefix: str) -> bool:
    import sys

    return sys.platform.startswith(prefix)


def _redact_path_hint(path_value: str | None) -> str | None:
    if not isinstance(path_value, str) or not path_value.strip():
        return None
    cleaned = path_value.strip()

    home_root = Path.home()
    try:
        same_base = LOCALAPPDATA_ROOT.resolve(strict=False) == home_root.resolve(strict=False)
    except Exception:
        same_base = LOCALAPPDATA_ROOT == home_root

    if Path(cleaned).is_absolute():
        bases = (
            ((home_root, "HOME"),)
            if same_base
            else ((LOCALAPPDATA_ROOT, "LOCALAPPDATA"), (home_root, "HOME"))
        )
        for base_path, label in bases:
            hint = _path_hint_relative_to(cleaned, base_path, label)
            if hint:
                return hint

    normalized = Path(os.path.normpath(cleaned))
    parts = [
        part
        for part in normalized.parts
        if part not in {normalized.anchor, "\\", "/", ".", ".."}
    ]
    if not parts:
        return None
    tail = parts[-2:] if len(parts) >= 2 else parts
    return "/".join(["...", *tail])


def _path_hint_relative_to(path_value: str, base: Path, label: str) -> str | None:
    try:
        relative = Path(path_value).resolve(strict=False).relative_to(base.resolve(strict=False))
    except Exception:
        return None

    relative_text = relative.as_posix()
    if not relative_text or relative_text == ".":
        return label
    return f"{label}/{relative_text}"
