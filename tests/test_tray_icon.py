from __future__ import annotations

import hashlib
import os
import struct
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import tray


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ICON = PROJECT_ROOT / "resources" / "icon.ico"
BUILD_ICON = PROJECT_ROOT / "MailProcessor.ico"


def _read_ico_sizes(path: Path) -> set[tuple[int, int]]:
    data = path.read_bytes()
    if len(data) < 6:
        raise AssertionError(f"ICO-Datei zu kurz: {path}")
    reserved, icon_type, count = struct.unpack_from("<HHH", data, 0)
    if reserved != 0 or icon_type != 1 or count <= 0:
        raise AssertionError(f"Ungültiger ICO-Header: {path}")

    sizes: set[tuple[int, int]] = set()
    for index in range(count):
        offset = 6 + index * 16
        width = data[offset] or 256
        height = data[offset + 1] or 256
        sizes.add((width, height))
    return sizes


def test_runtime_icon_loads_from_file_instead_of_fallback():
    app = QApplication.instance() or QApplication([])

    icon = tray._load_tray_icon()
    fallback = tray._make_tray_icon()

    assert app is not None
    assert not icon.isNull()
    assert icon.cacheKey() != fallback.cacheKey()


def test_build_and_runtime_icons_are_kept_in_sync():
    resource_hash = hashlib.sha256(RESOURCE_ICON.read_bytes()).hexdigest()
    build_hash = hashlib.sha256(BUILD_ICON.read_bytes()).hexdigest()

    assert resource_hash == build_hash


def test_runtime_icon_contains_expected_sizes():
    sizes = _read_ico_sizes(RESOURCE_ICON)

    assert {(16, 16), (32, 32), (48, 48), (256, 256)}.issubset(sizes)


def test_pyside6_keeps_context_menu_alive_after_gc():
    """Dokumentiert: PySide6 hält QMenu intern am Leben nach setContextMenu().

    Auch ohne Python-Instanzvariable (lokale Variable) überlebt das QMenu gc.collect().
    self._context_menu in _build_menu() ist dennoch best practice (defensives Hardening),
    da das interne C++-Verhalten implementierungsabhängig ist.
    """
    import gc

    from PySide6.QtWidgets import QMenu, QSystemTrayIcon

    app = QApplication.instance() or QApplication([])
    icon = QSystemTrayIcon()
    local_menu = QMenu()
    local_menu.addAction("MarkAction")
    icon.setContextMenu(local_menu)
    del local_menu
    gc.collect()

    result = icon.contextMenu()
    assert result is not None, "PySide6 hält QMenu nach GC am Leben"
    assert len(result.actions()) > 0, "Aktionen bleiben nach GC erhalten"


def test_build_menu_stores_menu_as_instance_variable():
    """_build_menu muss self._context_menu setzen damit Python-GC das QMenu nicht löscht."""
    from config import AppConfig
    from tray import MailProcessorTray

    app = QApplication.instance() or QApplication([])
    cfg = AppConfig()
    tray_icon = MailProcessorTray(cfg)

    assert hasattr(tray_icon, "_context_menu"), "_context_menu muss als Instanzvariable gehalten werden"
    assert tray_icon._context_menu is not None
    assert tray_icon._context_menu is tray_icon.contextMenu()
