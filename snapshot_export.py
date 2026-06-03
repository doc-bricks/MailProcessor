"""Read-only snapshot export for MailProcessor."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from config import AppConfig
from tool_manager import TOOL_DEFINITIONS, ToolManager

SNAPSHOT_SCHEMA = "mailprocessor-suite-v1"
APP_NAME = "MailProcessor"
LOCALAPPDATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home()))
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
    destination = Path(target_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_snapshot_payload(cfg, exported_at=exported_at)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
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


def _read_app_version() -> str:
    changelog_path = APP_ROOT / "CHANGELOG.md"
    if not changelog_path.exists():
        return ""
    try:
        text = changelog_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

    match = re.search(r"##\s*\[?(\d+\.\d+\.\d+)\]?", text)
    return match.group(1) if match else ""


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
    if not path_value:
        return None

    local_hint = _path_hint_relative_to(path_value, LOCALAPPDATA_ROOT, "LOCALAPPDATA")
    if local_hint:
        return local_hint

    home_hint = _path_hint_relative_to(path_value, Path.home(), "HOME")
    if home_hint:
        return home_hint

    path = Path(path_value)
    parts = [part for part in path.parts if part not in {path.anchor, "\\", "/"}]
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
    if not relative_text:
        return label
    return f"{label}/{relative_text}"
