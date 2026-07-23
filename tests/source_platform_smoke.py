"""Source-platform smoke for macOS/Linux-friendly MailProcessor core paths."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config as cfg_module
import tool_manager as tm_module
from config import AppConfig
from tool_manager import TOOL_DEFINITIONS, ToolManager


def _write_tool(root: Path, folder_name: str, script_name: str) -> Path:
    tool_dir = root / folder_name
    tool_dir.mkdir(parents=True, exist_ok=True)
    (tool_dir / script_name).write_text("print('ok')\n", encoding="utf-8")
    return tool_dir


def _smoke_config(tmp_root: Path) -> None:
    with patch.dict(os.environ, {"LOCALAPPDATA": ""}, clear=False):
        assert cfg_module.app_data_dir() == Path.home() / "MailProcessor"

    config_dir = tmp_root / "config-home" / "MailProcessor"
    config_file = config_dir / "config.json"
    manual_tool = tmp_root / "manual-tools" / "UniversalMailCleaner"
    manual_tool.mkdir(parents=True)
    (manual_tool / "main.py").write_text("print('manual')\n", encoding="utf-8")

    with patch.object(cfg_module, "CONFIG_DIR", config_dir), patch.object(
        cfg_module, "CONFIG_FILE", config_file
    ):
        app_config = AppConfig(language="en", first_run=False)
        tool = app_config.get_tool("universal_mail_cleaner")
        tool.enabled = True
        tool.path = str(manual_tool)
        tool.main_script = "main.py"
        tool.installed_by = "manual"

        cfg_module.save(app_config)
        loaded = cfg_module.load()

    loaded_tool = loaded.tools["universal_mail_cleaner"]
    assert loaded.language == "en"
    assert loaded.first_run is False
    assert loaded_tool.enabled is True
    assert loaded_tool.path == str(manual_tool)
    assert loaded_tool.main_script == "main.py"
    assert loaded_tool.installed_by == "manual"


def _smoke_scan(tmp_root: Path) -> None:
    suite_root = tmp_root / "mail-suite"
    expected: dict[str, tuple[str, str]] = {}

    for tool_id, meta in TOOL_DEFINITIONS.items():
        folder_name = meta["folder_hints"][0]
        script_name = meta["main_scripts"][0]
        tool_dir = _write_tool(suite_root, folder_name, script_name)
        expected[tool_id] = (str(tool_dir), script_name)

    manager = ToolManager(AppConfig())
    with patch.object(tm_module, "_SCAN_ROOTS", [suite_root]), patch.object(
        tm_module, "_DOWNLOAD_DIR", tmp_root / "downloaded-tools"
    ):
        results = manager.scan()

    assert results == expected


def _smoke_manual_tool_path_and_launch(tmp_root: Path) -> None:
    manual_dir = _write_tool(
        tmp_root / "manual-tools",
        "UniversalDocsGrabber",
        "UniversalDocsGrabberV1.py",
    )
    script_path = manual_dir / "UniversalDocsGrabberV1.py"

    manager = ToolManager(AppConfig())
    assert manager.register_from_script_path(
        "universal_docs_grabber",
        str(script_path),
        installed_by="manual",
    )
    assert manager.is_path_valid("universal_docs_grabber")

    captured: dict[str, object] = {}

    def fake_popen(args, cwd=None, env=None):
        captured["args"] = args
        captured["cwd"] = cwd
        captured["env"] = env
        return object()

    with patch.object(tm_module.subprocess, "Popen", fake_popen):
        assert manager.launch("universal_docs_grabber") is None

    assert captured["args"] == [sys.executable, str(script_path)]
    assert captured["cwd"] == str(manual_dir)
    assert captured["env"]["PYTHONIOENCODING"] == "utf-8"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mailprocessor-source-smoke-") as tmp:
        tmp_root = Path(tmp)
        _smoke_config(tmp_root)
        _smoke_scan(tmp_root)
        _smoke_manual_tool_path_and_launch(tmp_root)

    print("MailProcessor source-platform smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

