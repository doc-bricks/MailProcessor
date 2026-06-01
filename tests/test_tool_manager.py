"""Tests for tool_manager.py — scan, register/unregister, version, path validation."""
from pathlib import Path

import pytest

from config import AppConfig
from tool_manager import ToolManager


@pytest.fixture
def cfg():
    return AppConfig()


@pytest.fixture
def tm(cfg):
    return ToolManager(cfg)


def test_scan_finds_nothing(tm, tmp_path, monkeypatch):
    """scan() returns None for all tools when directories are empty."""
    import tool_manager
    monkeypatch.setattr(tool_manager, "_SCAN_ROOTS", [tmp_path])
    results = tm.scan()
    assert all(v is None for v in results.values())
    assert set(results.keys()) == {"universal_mail_cleaner", "universal_docs_grabber", "universal_invoice_mail"}


def test_register_success(tmp_path, tm):
    """register() sets ToolConfig and is_path_valid returns True."""
    folder = tmp_path / "MyTool"
    folder.mkdir()
    script = folder / "main.py"
    script.write_text("# dummy", encoding="utf-8")

    result = tm.register("universal_mail_cleaner", str(folder), "main.py", "test")
    assert result is True
    assert tm.is_path_valid("universal_mail_cleaner")


def test_register_missing_script(tmp_path, tm):
    """register() returns False when the script does not exist."""
    folder = tmp_path / "MyTool"
    folder.mkdir()
    result = tm.register("universal_mail_cleaner", str(folder), "nonexistent.py")
    assert result is False


def test_launch_uses_python_interpreter_when_frozen(tmp_path, tm, monkeypatch):
    """launch() falls back to a real Python interpreter in frozen builds."""
    folder = tmp_path / "MyTool"
    folder.mkdir()
    script = folder / "main.py"
    script.write_text("", encoding="utf-8")

    tm.register("universal_mail_cleaner", str(folder), "main.py")
    monkeypatch.setattr("tool_manager.sys.frozen", True, raising=False)
    monkeypatch.setattr(
        "tool_manager.shutil.which",
        lambda name: r"C:\\Python311\\pythonw.exe" if name == "pythonw" else None,
    )

    captured = {}

    def fake_popen(args, cwd=None):
        captured["args"] = args
        captured["cwd"] = cwd

    monkeypatch.setattr("tool_manager.subprocess.Popen", fake_popen)

    assert tm.launch("universal_mail_cleaner") is None
    assert captured["args"] == [r"C:\\Python311\\pythonw.exe", str(script)]
    assert captured["cwd"] == str(script.parent)


def test_launch_reports_missing_python_when_frozen(tmp_path, tm, monkeypatch):
    """launch() refuses to use the frozen EXE when no interpreter is available."""
    folder = tmp_path / "MyTool"
    folder.mkdir()
    script = folder / "main.py"
    script.write_text("", encoding="utf-8")

    tm.register("universal_mail_cleaner", str(folder), "main.py")
    monkeypatch.setattr("tool_manager.sys.frozen", True, raising=False)
    monkeypatch.setattr("tool_manager.shutil.which", lambda name: None)

    assert tm.launch("universal_mail_cleaner") == "Python interpreter not found"


def test_unregister_clears_tool(tmp_path, tm):
    """unregister() removes the tool from active_tools."""
    folder = tmp_path / "MyTool"
    folder.mkdir()
    (folder / "main.py").write_text("", encoding="utf-8")
    tm.register("universal_mail_cleaner", str(folder), "main.py")
    assert "universal_mail_cleaner" in tm.active_tools()

    tm.unregister("universal_mail_cleaner")
    assert "universal_mail_cleaner" not in tm.active_tools()


def test_is_path_valid_no_config(tm):
    """is_path_valid returns False when tool is not configured."""
    assert tm.is_path_valid("universal_mail_cleaner") is False


def test_tool_version_no_path(tm):
    """tool_version returns '' when tool has no path."""
    assert tm.tool_version("universal_mail_cleaner") == ""


def test_tool_version_from_changelog(tmp_path, tm):
    """tool_version reads version from CHANGELOG.md."""
    folder = tmp_path / "MyTool"
    folder.mkdir()
    script = folder / "main.py"
    script.write_text("", encoding="utf-8")
    changelog = folder / "CHANGELOG.md"
    changelog.write_text("## [1.3.5] - 2026-05-01\n\n- feature x\n", encoding="utf-8")

    tm.register("universal_mail_cleaner", str(folder), "main.py")
    assert tm.tool_version("universal_mail_cleaner") == "v1.3.5"


def test_tool_version_no_changelog(tmp_path, tm):
    """tool_version returns '' when CHANGELOG.md is missing."""
    folder = tmp_path / "MyTool"
    folder.mkdir()
    (folder / "main.py").write_text("", encoding="utf-8")
    tm.register("universal_mail_cleaner", str(folder), "main.py")
    assert tm.tool_version("universal_mail_cleaner") == ""


def test_find_script_in_folder(tmp_path):
    """find_script_in_folder locates the correct main script."""
    folder = tmp_path / "ToolFolder"
    folder.mkdir()
    (folder / "UniversalDocsGrabberV1.py").write_text("", encoding="utf-8")
    result = ToolManager.find_script_in_folder(str(folder), "universal_docs_grabber")
    assert result == "UniversalDocsGrabberV1.py"
