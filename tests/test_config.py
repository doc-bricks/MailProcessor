"""Tests for config.py — load/save roundtrip, defaults, corrupt file."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import config as cfg_module
from config import AppConfig, ToolConfig


@pytest.fixture(autouse=True)
def _patch_config_path(tmp_path):
    """Redirect CONFIG_FILE to a temp directory for every test."""
    config_dir = tmp_path / "MailProcessor"
    config_file = config_dir / "config.json"
    with patch.object(cfg_module, "CONFIG_DIR", config_dir), \
         patch.object(cfg_module, "CONFIG_FILE", config_file):
        yield config_file


def test_default_config():
    cfg = cfg_module.load()
    assert cfg.language == "de"
    assert cfg.first_run is True
    assert cfg.start_with_windows is False
    assert cfg.tools == {}


def test_save_load_roundtrip():
    cfg = AppConfig(language="en", first_run=False, start_with_windows=True)
    cfg.get_tool("universal_mail_cleaner").enabled = True
    cfg.get_tool("universal_mail_cleaner").path = "/some/path"
    cfg.get_tool("universal_mail_cleaner").main_script = "main.py"
    cfg.get_tool("universal_mail_cleaner").installed_by = "scan"

    cfg_module.save(cfg)
    loaded = cfg_module.load()

    assert loaded.language == "en"
    assert loaded.first_run is False
    assert loaded.start_with_windows is True
    t = loaded.tools.get("universal_mail_cleaner")
    assert t is not None
    assert t.enabled is True
    assert t.path == "/some/path"
    assert t.main_script == "main.py"
    assert t.installed_by == "scan"


def test_save_temp_write_failure_preserves_previous_config(monkeypatch):
    config_file = cfg_module.CONFIG_FILE
    previous = AppConfig(language="en", first_run=False, start_with_windows=True)
    previous.tools["synthetic"] = ToolConfig(
        enabled=True,
        path="/synthetic/tool",
        main_script="main.py",
        installed_by="manual",
    )
    cfg_module.save(previous)
    previous_bytes = config_file.read_bytes()

    replacement = AppConfig(language="de", first_run=True)
    real_named_temp_file = cfg_module.tempfile.NamedTemporaryFile
    temporary_paths = []

    class PartialWriter:
        def __init__(self, wrapped):
            self._wrapped = wrapped
            self.name = wrapped.name

        def __enter__(self):
            self._wrapped.__enter__()
            return self

        def __exit__(self, *args):
            return self._wrapped.__exit__(*args)

        def write(self, value):
            self._wrapped.write(value[:16])
            self._wrapped.flush()
            raise OSError("synthetic interrupted temp write")

    def fail_during_temp_write(*args, **kwargs):
        wrapped = real_named_temp_file(*args, **kwargs)
        temporary_paths.append(Path(wrapped.name))
        return PartialWriter(wrapped)

    monkeypatch.setattr(cfg_module.tempfile, "NamedTemporaryFile", fail_during_temp_write)

    with pytest.raises(OSError, match="synthetic interrupted temp write"):
        cfg_module.save(replacement)

    assert config_file.read_bytes() == previous_bytes
    loaded = cfg_module.load()
    assert loaded.language == "en"
    assert loaded.first_run is False
    assert loaded.start_with_windows is True
    assert loaded.tools["synthetic"].main_script == "main.py"
    assert len(temporary_paths) == 1
    assert not temporary_paths[0].exists()


def test_save_replace_failure_preserves_original_error_and_config(monkeypatch):
    config_file = cfg_module.CONFIG_FILE
    previous = AppConfig(language="en", first_run=False, start_with_windows=True)
    previous.tools["synthetic"] = ToolConfig(
        enabled=True,
        path="/synthetic/tool",
        main_script="main.py",
        installed_by="manual",
    )
    cfg_module.save(previous)
    previous_bytes = config_file.read_bytes()

    class FailingOS:
        @staticmethod
        def replace(source, destination):
            raise OSError("synthetic atomic replace failure")

    real_unlink = Path.unlink

    def fail_temp_cleanup(path, *args, **kwargs):
        if path.parent == config_file.parent and path.name.startswith(".mp-"):
            raise OSError("synthetic temp cleanup failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(cfg_module, "os", FailingOS)
    monkeypatch.setattr(Path, "unlink", fail_temp_cleanup)

    with pytest.raises(OSError, match="synthetic atomic replace failure"):
        cfg_module.save(AppConfig(language="de", first_run=True))

    assert config_file.read_bytes() == previous_bytes
    loaded = cfg_module.load()
    assert loaded.language == "en"
    assert loaded.first_run is False
    assert loaded.start_with_windows is True
    assert loaded.tools["synthetic"].main_script == "main.py"
    # The injected cleanup failure may leave only this test's unique temp file.
    leftovers = list(config_file.parent.glob(".mp-*.tmp"))
    assert len(leftovers) == 1


def test_load_corrupt_file(tmp_path):
    config_dir = Path(str(cfg_module.CONFIG_DIR))
    config_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = Path(str(cfg_module.CONFIG_FILE))
    cfg_file.write_text("{ not valid json }", encoding="utf-8")
    cfg = cfg_module.load()
    # Must not raise; returns defaults
    assert cfg.language == "de"
    assert cfg.first_run is True


def test_load_keeps_valid_top_level_settings_when_tool_entry_is_invalid(tmp_path):
    config_dir = Path(str(cfg_module.CONFIG_DIR))
    config_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = Path(str(cfg_module.CONFIG_FILE))
    cfg_file.write_text(
        json.dumps(
            {
                "language": "en",
                "first_run": False,
                "start_with_windows": True,
                "tools": {
                    "broken_tool": ["not-a-dict"],
                },
            }
        ),
        encoding="utf-8",
    )

    cfg = cfg_module.load()

    assert cfg.language == "en"
    assert cfg.first_run is False
    assert cfg.start_with_windows is True
    assert cfg.tools == {}


def test_load_ignores_non_mapping_tools_block_but_keeps_global_settings(tmp_path):
    config_dir = Path(str(cfg_module.CONFIG_DIR))
    config_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = Path(str(cfg_module.CONFIG_FILE))
    cfg_file.write_text(
        json.dumps(
            {
                "language": "en",
                "first_run": False,
                "start_with_windows": True,
                "tools": ["unexpected-list"],
            }
        ),
        encoding="utf-8",
    )

    cfg = cfg_module.load()

    assert cfg.language == "en"
    assert cfg.first_run is False
    assert cfg.start_with_windows is True
    assert cfg.tools == {}


def test_get_tool_auto_creates():
    cfg = AppConfig()
    t = cfg.get_tool("new_tool")
    assert isinstance(t, ToolConfig)
    assert t.enabled is False
    # Second call returns same object
    assert cfg.get_tool("new_tool") is t


def test_app_data_dir_falls_back_to_home_when_localappdata_is_empty(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", "")

    assert cfg_module.app_data_dir() == Path.home() / "MailProcessor"


def test_app_data_dir_falls_back_to_home_when_localappdata_is_relative(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", "relative-localappdata")

    assert cfg_module.app_data_dir() == Path.home() / "MailProcessor"
