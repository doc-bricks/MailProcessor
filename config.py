"""Configuration management for MailProcessor."""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MailProcessor"
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
        cfg = AppConfig(
            language=data.get("language", "de"),
            first_run=data.get("first_run", True),
            start_with_windows=data.get("start_with_windows", False),
        )
        tools_data = data.get("tools", {})
        if not isinstance(tools_data, dict):
            tools_data = {}

        for tid, tdata in tools_data.items():
            if not isinstance(tid, str) or not isinstance(tdata, dict):
                continue
            cfg.tools[tid] = ToolConfig(
                enabled=tdata.get("enabled", False),
                path=tdata.get("path"),
                main_script=tdata.get("main_script"),
                installed_by=tdata.get("installed_by"),
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
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
