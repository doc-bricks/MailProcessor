"""Configuration management for MailProcessor."""

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def app_data_dir() -> Path:
    """Return a stable per-user config directory, even with broken LOCALAPPDATA."""
    raw_local_appdata = os.environ.get("LOCALAPPDATA")
    base_dir = Path(raw_local_appdata) if raw_local_appdata else Path.home()
    if not base_dir.is_absolute():
        base_dir = Path.home()
    return base_dir / "MailProcessor"


CONFIG_DIR = app_data_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class ToolConfig:
    enabled: bool = False
    path: Optional[str] = None       # Ordner des Tools
    main_script: Optional[str] = None  # Dateiname des Einstiegsskripts
    installed_by: Optional[str] = None  # "scan" | "manual" | "installer"


@dataclass
class AppConfig:
    language: str = "de"
    first_run: bool = True
    start_with_windows: bool = False
    tools: dict[str, ToolConfig] = field(default_factory=dict)

    def get_tool(self, tool_id: str) -> ToolConfig:
        if tool_id not in self.tools:
            self.tools[tool_id] = ToolConfig()
        return self.tools[tool_id]


def load() -> AppConfig:
    if not CONFIG_FILE.exists():
        return AppConfig()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return AppConfig()
        raw_lang = data.get("language", "de")
        language = raw_lang if isinstance(raw_lang, str) and raw_lang in ("de", "en") else "de"
        raw_first_run = data.get("first_run", True)
        first_run = raw_first_run if isinstance(raw_first_run, bool) else True
        raw_autostart = data.get("start_with_windows", False)
        start_with_windows = raw_autostart if isinstance(raw_autostart, bool) else False
        cfg = AppConfig(
            language=language,
            first_run=first_run,
            start_with_windows=start_with_windows,
        )
        tools_data = data.get("tools", {})
        if not isinstance(tools_data, dict):
            tools_data = {}

        for tid, tdata in tools_data.items():
            if not isinstance(tid, str) or not isinstance(tdata, dict):
                continue
            cfg.tools[tid] = ToolConfig(
                enabled=tdata.get("enabled") if isinstance(tdata.get("enabled"), bool) else False,
                path=tdata.get("path") if isinstance(tdata.get("path"), str) else None,
                main_script=(
                    tdata.get("main_script") if isinstance(tdata.get("main_script"), str) else None
                ),
                installed_by=(
                    tdata.get("installed_by") if isinstance(tdata.get("installed_by"), str) else None
                ),
            )
        return cfg
    except Exception:
        return AppConfig()


def save(cfg: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "language": cfg.language,
        "first_run": cfg.first_run,
        "start_with_windows": cfg.start_with_windows,
        "tools": {
            tid: {
                "enabled": t.enabled,
                "path": t.path,
                "main_script": t.main_script,
                "installed_by": t.installed_by,
            }
            for tid, t in cfg.tools.items()
        },
    }
    serialized = json.dumps(data, indent=2, ensure_ascii=False)
    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CONFIG_DIR,
            prefix=".mp-",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temporary_path = Path(temp_file.name)
            temp_file.write(serialized)
        os.replace(temporary_path, CONFIG_FILE)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                # Cleanup is best-effort so the write or replace error is preserved.
                pass
