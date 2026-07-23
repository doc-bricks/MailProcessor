"""Contract tests for the safe, portable update_files maintenance script."""

import importlib.util
import sys
from pathlib import Path

import pytest


PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_DIR / "update_files.py"


def load_module():
    spec = importlib.util.spec_from_file_location("update_files_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


@pytest.fixture
def historic_fixture(tmp_path):
    (tmp_path / "build_exe.bat").write_text(
        '  --name MailProcessor ^\n  --icon "%ICON_PATH%" ^\n  --distpath "dist" ^',
        encoding="utf-8",
    )
    (tmp_path / "tray.py").write_text(
        """def _make_tray_icon():
    pixmap = object()
    return QIcon(pixmap)

class MailProcessorTray:
    def __init__(self):
        self.setIcon(_make_tray_icon())
""",
        encoding="utf-8",
    )
    (tmp_path / "settings_dialog.py").write_text(
        '''    @staticmethod
    def _apply_autostart(enable: bool):
        import winreg
        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        app_name = "MailProcessor"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enable:
                import sys
                from pathlib import Path
                script = str(Path(__file__).parent / "main.py")
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{sys.executable}" "{script}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass''',
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        "def start(cfg):\n    from tray import MailProcessorTray\n", encoding="utf-8"
    )
    return tmp_path


def test_dry_run_lists_exactly_four_targets_without_writing(historic_fixture, monkeypatch):
    module = load_module()
    monkeypatch.setattr(module, "PROJECT_DIR", historic_fixture)
    original = {path.name: path.read_text(encoding="utf-8") for path in historic_fixture.iterdir()}

    assert module.main(["--project-dir", str(historic_fixture)]) == 0

    assert {path.name: path.read_text(encoding="utf-8") for path in historic_fixture.iterdir()} == original
    plan = module.plan_updates(historic_fixture)
    assert [update.relative_path for update in plan] == list(module.TARGET_FILES)
    assert {update.status for update in plan} == {"would update"}


def test_apply_changes_only_the_four_documented_targets(historic_fixture, monkeypatch):
    module = load_module()
    monkeypatch.setattr(module, "PROJECT_DIR", historic_fixture)
    untouched = historic_fixture / "unrelated.txt"
    untouched.write_text("do not touch", encoding="utf-8")

    assert module.main(["--project-dir", str(historic_fixture), "--apply"]) == 0

    assert untouched.read_text(encoding="utf-8") == "do not touch"
    assert "--add-data" in (historic_fixture / "build_exe.bat").read_text(encoding="utf-8")
    assert "resources" in (historic_fixture / "tray.py").read_text(encoding="utf-8")
    assert "getattr(sys, \"frozen\", False)" in (
        historic_fixture / "settings_dialog.py"
    ).read_text(encoding="utf-8")
    assert "SettingsDialog._apply_autostart(True)" in (
        historic_fixture / "main.py"
    ).read_text(encoding="utf-8")


def test_rejects_relative_or_external_project_paths(historic_fixture, monkeypatch):
    module = load_module()
    monkeypatch.setattr(module, "PROJECT_DIR", historic_fixture)

    with pytest.raises(module.MaintenanceError, match="absolute path"):
        module.resolve_project_dir(".")
    with pytest.raises(module.MaintenanceError, match="must resolve"):
        module.resolve_project_dir(str(historic_fixture.parent))


def test_current_project_is_an_idempotent_four_file_dry_run():
    module = load_module()

    plan = module.plan_updates(PROJECT_DIR)

    assert [update.relative_path for update in plan] == list(module.TARGET_FILES)
    assert {update.status for update in plan} == {"already current"}
