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

    def fake_popen(args, cwd=None, env=None):
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


def test_scan_finds_downloaded_tool_inside_github_extract_dir(tm, tmp_path, monkeypatch):
    """scan() rediscovers tools from the GitHub installer extract layout."""
    import tool_manager

    download_root = tmp_path / "downloads"
    extracted = (
        download_root
        / "universal_mail_cleaner"
        / "extracted"
        / "doc-bricks-UniversalMailCleaner-abc123"
    )
    extracted.mkdir(parents=True)
    (extracted / "mail_imap_cleaner_v1.py").write_text("# demo", encoding="utf-8")

    monkeypatch.setattr(tool_manager, "_DOWNLOAD_DIR", download_root)
    monkeypatch.setattr(tool_manager, "_SCAN_ROOTS", [download_root])

    results = tm.scan()

    assert results["universal_mail_cleaner"] == (
        str(extracted),
        "mail_imap_cleaner_v1.py",
    )


def test_download_dir_falls_back_to_home_when_localappdata_is_relative(monkeypatch):
    import importlib
    import tool_manager

    monkeypatch.setenv("LOCALAPPDATA", "relative-localappdata")
    reloaded = importlib.reload(tool_manager)

    assert reloaded._DOWNLOAD_DIR == Path.home() / "MailProcessor" / "tools"


def test_scan_handles_permission_error_in_download_dir(tm, tmp_path, monkeypatch):
    """scan() gibt None zurück wenn iterdir() im Download-Ordner PermissionError wirft."""
    import tool_manager

    download_root = tmp_path / "downloads"
    download_root.mkdir()

    monkeypatch.setattr(tool_manager, "_DOWNLOAD_DIR", download_root)
    monkeypatch.setattr(tool_manager, "_SCAN_ROOTS", [download_root])

    original_iterdir = Path.iterdir

    def patched_iterdir(self):
        if self.resolve(strict=False) == download_root.resolve(strict=False):
            raise PermissionError("Zugriff verweigert (simuliert)")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", patched_iterdir)

    # Vor dem Fix: PermissionError propagiert → scan() stürzt ab.
    # Nach dem Fix: scan() fängt den Fehler ab und liefert None für alle Tools.
    results = tm.scan()
    assert all(v is None for v in results.values())


def test_launch_sets_pythonioencoding_in_subprocess_env(tmp_path, tm, monkeypatch):
    """launch() übergibt PYTHONIOENCODING=utf-8 an die Subprozess-Umgebung."""
    folder = tmp_path / "MyTool"
    folder.mkdir()
    script = folder / "main.py"
    script.write_text("", encoding="utf-8")

    tm.register("universal_mail_cleaner", str(folder), "main.py")

    captured = {}

    def fake_popen(args, cwd=None, env=None):
        captured["env"] = env

    monkeypatch.setattr("tool_manager.subprocess.Popen", fake_popen)

    result = tm.launch("universal_mail_cleaner")
    assert result is None
    assert captured.get("env") is not None, "env wurde nicht an Popen übergeben"
    assert captured["env"].get("PYTHONIOENCODING") == "utf-8"


def test_download_tool_prevents_zip_slip(tm, tmp_path, monkeypatch):
    """download_tool() detects and rejects zip entries attempting path traversal."""
    import io
    import json
    import zipfile
    import tool_manager

    download_root = tmp_path / "downloads"
    monkeypatch.setattr(tool_manager, "_DOWNLOAD_DIR", download_root)

    # Create in-memory zip with traversal member
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("../evil.txt", "malicious content")
    zip_bytes = zip_buffer.getvalue()

    fake_release = {
        "tag_name": "v1.0.0",
        "zipball_url": "https://example.com/fake.zip",
    }

    class FakeResponse:
        def __init__(self, data, headers=None):
            self.data = io.BytesIO(data)
            self.headers = headers or {}
        def read(self, size=-1):
            return self.data.read(size)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def fake_urlopen(req, timeout=None):
        from urllib.parse import urlparse
        url = req.full_url if hasattr(req, "full_url") else req
        if urlparse(url).hostname == "api.github.com":
            return FakeResponse(json.dumps(fake_release).encode("utf-8"))
        return FakeResponse(zip_bytes, {"Content-Length": str(len(zip_bytes))})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    err = tm.download_tool("universal_mail_cleaner")
    assert err is not None
    assert "unsafe archive entry" in err


def test_download_tool_extracts_safe_archive(tm, tmp_path, monkeypatch):
    """download_tool() safely extracts a valid archive and registers the tool."""
    import io
    import json
    import zipfile
    import tool_manager

    download_root = tmp_path / "downloads"
    monkeypatch.setattr(tool_manager, "_DOWNLOAD_DIR", download_root)

    # Create in-memory zip with valid structure
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("UniversalMailCleaner-1.0.0/mail_imap_cleaner_v1.py", "# cleaner script")
    zip_bytes = zip_buffer.getvalue()

    fake_release = {
        "tag_name": "v1.0.0",
        "zipball_url": "https://example.com/fake.zip",
    }

    class FakeResponse:
        def __init__(self, data, headers=None):
            self.data = io.BytesIO(data)
            self.headers = headers or {}
        def read(self, size=-1):
            return self.data.read(size)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def fake_urlopen(req, timeout=None):
        from urllib.parse import urlparse
        url = req.full_url if hasattr(req, "full_url") else req
        if urlparse(url).hostname == "api.github.com":
            return FakeResponse(json.dumps(fake_release).encode("utf-8"))
        return FakeResponse(zip_bytes, {"Content-Length": str(len(zip_bytes))})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    err = tm.download_tool("universal_mail_cleaner")
    assert err is None
    assert tm.is_path_valid("universal_mail_cleaner")

