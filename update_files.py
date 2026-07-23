"""Preview and, on request, apply the historic MailProcessor maintenance patch.

The script is deliberately scoped to the project directory containing this file.
It previews by default; use ``--apply`` only after reviewing the four-file plan.
"""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


PROJECT_DIR = Path(__file__).resolve().parent
TARGET_FILES = ("build_exe.bat", "tray.py", "settings_dialog.py", "main.py")


class MaintenanceError(RuntimeError):
    """Raised when the requested maintenance run is unsafe or incomplete."""


@dataclass(frozen=True)
class PlannedUpdate:
    relative_path: str
    status: str
    content: str


def _replace_or_confirm(
    content: str,
    old: str,
    new: str,
    is_current: Callable[[str], bool],
    relative_path: str,
) -> tuple[str, str]:
    if old in content:
        return content.replace(old, new, 1), "would update"
    if is_current(content):
        return content, "already current"
    raise MaintenanceError(
        f"{relative_path}: expected historic marker is missing; refusing to guess a change."
    )


def _update_build_script(content: str) -> tuple[str, str]:
    old = '  --icon "%ICON_PATH%" ^\n  --distpath "dist" ^'
    new = '  --icon "%ICON_PATH%" ^\n  --add-data "resources;resources" ^\n  --distpath "dist" ^'
    return _replace_or_confirm(
        content,
        old,
        new,
        lambda text: "--add-data" in text and "resources" in text,
        "build_exe.bat",
    )


def _update_tray(content: str) -> tuple[str, str]:
    old_call = "        self.setIcon(_make_tray_icon())"
    new_call = '''        import sys
        from pathlib import Path
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent
        self.setIcon(QIcon(str(base_dir / "resources" / "icon.ico")))'''
    without_factory = re.sub(
        r"def _make_tray_icon.*?return QIcon\(pixmap\)\n\n", "", content, flags=re.DOTALL
    )
    if without_factory != content and old_call in without_factory:
        return without_factory.replace(old_call, new_call, 1), "would update"
    if "self.setIcon(_load_tray_icon())" in content or "resources/icon.ico" in content:
        return content, "already current"
    raise MaintenanceError(
        "tray.py: expected historic tray-icon marker is missing; refusing to guess a change."
    )


def _update_settings_dialog(content: str) -> tuple[str, str]:
    old = '''    @staticmethod
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
            pass'''
    new = '''    @staticmethod
    def _apply_autostart(enable: bool):
        import winreg
        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        app_name = "MailProcessor"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enable:
                import sys
                from pathlib import Path
                if getattr(sys, "frozen", False):
                    cmd = f'"{sys.executable}"'
                else:
                    script = str(Path(__file__).parent / "main.py")
                    cmd = f'"{sys.executable}" "{script}"'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass'''
    return _replace_or_confirm(
        content,
        old,
        new,
        lambda text: "ensure_autostart_entry(enable)" in text
        or 'if getattr(sys, "frozen", False):' in text,
        "settings_dialog.py",
    )


def _update_main(content: str) -> tuple[str, str]:
    old = "    from tray import MailProcessorTray"
    new = '''    if cfg.start_with_windows:
        from settings_dialog import SettingsDialog
        SettingsDialog._apply_autostart(True)

    from tray import MailProcessorTray'''
    if "ensure_autostart_entry(cfg.start_with_windows)" in content:
        return content, "already current"
    return _replace_or_confirm(
        content,
        old,
        new,
        lambda text: "ensure_autostart_entry(cfg.start_with_windows)" in text,
        "main.py",
    )


TRANSFORMS: dict[str, Callable[[str], tuple[str, str]]] = {
    "build_exe.bat": _update_build_script,
    "tray.py": _update_tray,
    "settings_dialog.py": _update_settings_dialog,
    "main.py": _update_main,
}


def resolve_project_dir(raw_path: str | None) -> Path:
    """Return the script project root, rejecting every path outside that scope."""
    expected = PROJECT_DIR.resolve()
    if raw_path is None:
        return expected

    supplied = Path(raw_path).expanduser()
    if not supplied.is_absolute():
        raise MaintenanceError("--project-dir must be an absolute path.")
    resolved = supplied.resolve()
    if resolved != expected:
        raise MaintenanceError(
            f"--project-dir must resolve to this script's project directory: {expected}"
        )
    return resolved


def plan_updates(project_dir: Path) -> list[PlannedUpdate]:
    """Read and validate every target before any write is attempted."""
    updates: list[PlannedUpdate] = []
    for relative_path in TARGET_FILES:
        target = project_dir / relative_path
        if not target.is_file():
            raise MaintenanceError(f"Required target is missing or not a file: {target}")
        try:
            content = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise MaintenanceError(f"Could not read required target {target}: {exc}") from exc
        updated, status = TRANSFORMS[relative_path](content)
        updates.append(PlannedUpdate(relative_path, status, updated))
    return updates


def _atomic_write(target: Path, content: str) -> None:
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="", delete=False, dir=target.parent
        ) as handle:
            handle.write(content)
            temporary_path = Path(handle.name)
        os.replace(temporary_path, target)
    except OSError as exc:
        raise MaintenanceError(f"Could not write {target}: {exc}") from exc


def run(project_dir: Path, *, apply: bool) -> list[PlannedUpdate]:
    updates = plan_updates(project_dir)
    if apply:
        for update in updates:
            if update.status == "would update":
                _atomic_write(project_dir / update.relative_path, update.content)
    return updates


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-dir",
        help="absolute project directory; it must resolve to this script's directory",
    )
    parser.add_argument(
        "--apply", action="store_true", help="write the reviewed changes (default: dry run)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        project_dir = resolve_project_dir(args.project_dir)
        updates = run(project_dir, apply=args.apply)
    except MaintenanceError as exc:
        print(f"update_files: ERROR: {exc}")
        return 2

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"update_files: {mode}; project={project_dir}")
    for update in updates:
        print(f" - {update.relative_path}: {update.status}")
    print(f"update_files: {len(updates)} intended files checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
