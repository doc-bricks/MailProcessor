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
