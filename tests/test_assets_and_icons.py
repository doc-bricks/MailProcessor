# -*- coding: utf-8 -*-
"""Vertragstests für Anwendungs-Icons, Multi-Resolution-ICOs, PWA- und Store-Assets."""

import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def get_ico_sizes(ico_path: Path) -> list[tuple[int, int]]:
    """Liest alle Frame-Größen aus einer ICO-Datei aus (via struct & PIL Fallback)."""
    data = ico_path.read_bytes()
    if len(data) < 6:
        return []
    reserved, icon_type, count = struct.unpack_from("<HHH", data, 0)
    if reserved != 0 or icon_type != 1:
        return []
    sizes = []
    for idx in range(count):
        offset = 6 + idx * 16
        w = data[offset] or 256
        h = data[offset + 1] or 256
        sizes.append((w, h))
    return sorted(sizes)


class TestMailProcessorIconsAndAssets(unittest.TestCase):
    """Testet Existenz, Dimensionen und Layer-Vollständigkeit aller Icons."""

    EXPECTED_7_LAYERS = [
        (16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)
    ]
    EXPECTED_FAV_LAYERS = [
        (16, 16), (24, 24), (32, 32), (48, 48)
    ]

    def test_root_icons_exist_and_have_required_layers(self):
        """Root-Icons für Desktop-Shortcuts, Dateimanager und Windows Explorer."""
        root_icos = [
            ROOT / "MailProcessor.ico",
            ROOT / "icon.ico",
            ROOT / "DesktopIcon.ico",
        ]
        for ico in root_icos:
            with self.subTest(ico=ico.name):
                self.assertTrue(ico.exists(), f"Datei fehlt: {ico}")
                sizes = get_ico_sizes(ico)
                self.assertEqual(
                    sizes, self.EXPECTED_7_LAYERS,
                    f"Ungültige Layer in {ico.name}: {sizes}"
                )

        # Root Favicon
        fav_ico = ROOT / "favicon.ico"
        self.assertTrue(fav_ico.exists(), "Root favicon.ico fehlt")
        self.assertEqual(get_ico_sizes(fav_ico), self.EXPECTED_FAV_LAYERS)

        root_pngs = [
            ROOT / "MailProcessor.png",
            ROOT / "icon.png",
            ROOT / "DesktopIcon.png",
        ]
        for png in root_pngs:
            with self.subTest(png=png.name):
                self.assertTrue(png.exists(), f"Datei fehlt: {png}")
                with Image.open(png) as img:
                    self.assertEqual(img.size, (1024, 1024))
                    self.assertEqual(img.mode, "RGBA")

    def test_build_and_resources_icons_parity(self):
        """Build-Icon und Runtime-Icon müssen byte-identisch synchronisiert sein."""
        build_ico = ROOT / "MailProcessor.ico"
        resource_ico = ROOT / "resources" / "icon.ico"
        self.assertTrue(build_ico.exists())
        self.assertTrue(resource_ico.exists())
        self.assertEqual(
            hashlib.sha256(build_ico.read_bytes()).hexdigest(),
            hashlib.sha256(resource_ico.read_bytes()).hexdigest(),
            "MailProcessor.ico und resources/icon.ico weichen voneinander ab"
        )

    def test_assets_folder_integrity(self):
        """Das assets/-Verzeichnis enthält standardisierte Icons und Favicons."""
        assets_dir = ROOT / "assets"
        self.assertTrue(assets_dir.is_dir(), "assets/ Ordner existiert nicht")

        # 7-layer ICOs
        for name in ["icon.ico", "MailProcessor.ico", "DesktopIcon.ico", "app_icon.ico"]:
            ico = assets_dir / name
            self.assertTrue(ico.exists(), f"Fehlt in assets/: {name}")
            self.assertEqual(get_ico_sizes(ico), self.EXPECTED_7_LAYERS)

        # Favicon ICO
        fav_ico = assets_dir / "favicon.ico"
        self.assertTrue(fav_ico.exists(), "assets/favicon.ico fehlt")
        self.assertEqual(get_ico_sizes(fav_ico), self.EXPECTED_FAV_LAYERS)

        # High-res PNGs
        for name in ["icon.png", "MailProcessor.png", "DesktopIcon.png"]:
            png = assets_dir / name
            self.assertTrue(png.exists(), f"Fehlt in assets/: {name}")
            with Image.open(png) as img:
                self.assertEqual(img.size, (1024, 1024))
                self.assertEqual(img.mode, "RGBA")

        # Web / Touch Icons
        touch_png = assets_dir / "apple-touch-icon.png"
        self.assertTrue(touch_png.exists())
        with Image.open(touch_png) as img:
            self.assertEqual(img.size, (180, 180))
            self.assertEqual(img.mode, "RGBA")

        for fname, expected_dim in [("favicon.png", (32, 32)), ("favicon-16.png", (16, 16)), ("favicon-32.png", (32, 32))]:
            p = assets_dir / fname
            self.assertTrue(p.exists(), f"Fehlt: {fname}")
            with Image.open(p) as img:
                self.assertEqual(img.size, expected_dim)
                self.assertEqual(img.mode, "RGBA")

        # Preserve existing banner assets
        self.assertTrue((assets_dir / "banner.png").exists(), "assets/banner.png fehlt")
        self.assertTrue((assets_dir / "banner.svg").exists(), "assets/banner.svg fehlt")

    def test_store_assets_integrity(self):
        """store_assets/ enthält alle erforderlichen Microsoft Store Kachelgrößen."""
        store_dir = ROOT / "store_assets"
        self.assertTrue(store_dir.is_dir(), "store_assets/ Ordner existiert nicht")

        expected_specs = {
            "icon_44x44.png": (44, 44),
            "Square44x44Logo.png": (44, 44),
            "icon_50x50.png": (50, 50),
            "StoreLogo.png": (50, 50),
            "Square50x50Logo.png": (50, 50),
            "icon_150x150.png": (150, 150),
            "Square150x150Logo.png": (150, 150),
            "icon_310x310.png": (310, 310),
            "Square310x310Logo.png": (310, 310),
            "icon_310x150.png": (310, 150),
            "Wide310x150Logo.png": (310, 150),
        }

        for filename, expected_size in expected_specs.items():
            path = store_dir / filename
            self.assertTrue(path.exists(), f"Store-Asset fehlt: {filename}")
            with Image.open(path) as img:
                self.assertEqual(img.size, expected_size, f"Größe für {filename} abweichend")
                self.assertEqual(img.mode, "RGBA")

        self.assertTrue((store_dir / "README.md").exists(), "store_assets/README.md fehlt")

    def test_mobile_and_pwa_icons_integrity(self):
        """mobile_icons/ enthält Manifest und standardisierte Bildgrößen."""
        mobile_dir = ROOT / "mobile_icons"
        self.assertTrue(mobile_dir.is_dir(), "mobile_icons/ Ordner existiert nicht")

        manifest_file = mobile_dir / "manifest.json"
        self.assertTrue(manifest_file.exists(), "mobile_icons/manifest.json fehlt")
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        self.assertIn("icons", manifest_data)
        self.assertGreaterEqual(len(manifest_data["icons"]), 4)

        for name in ["icon-192.png", "icon-maskable-192.png"]:
            path = mobile_dir / name
            self.assertTrue(path.exists(), f"Fehlt: {name}")
            with Image.open(path) as img:
                self.assertEqual(img.size, (192, 192))
                self.assertEqual(img.mode, "RGBA")

        for name in ["icon-512.png", "icon-maskable-512.png"]:
            path = mobile_dir / name
            self.assertTrue(path.exists(), f"Fehlt: {name}")
            with Image.open(path) as img:
                self.assertEqual(img.size, (512, 512))
                self.assertEqual(img.mode, "RGBA")

        for name in ["apple-touch-icon.png", "apple-touch-icon-180.png"]:
            path = mobile_dir / name
            self.assertTrue(path.exists(), f"Fehlt: {name}")
            with Image.open(path) as img:
                self.assertEqual(img.size, (180, 180))
                self.assertEqual(img.mode, "RGBA")

        self.assertTrue((mobile_dir / "favicon.ico").exists(), "mobile_icons/favicon.ico fehlt")
        self.assertEqual(get_ico_sizes(mobile_dir / "favicon.ico"), self.EXPECTED_FAV_LAYERS)
        self.assertTrue((mobile_dir / "favicon.png").exists(), "mobile_icons/favicon.png fehlt")
        self.assertTrue((mobile_dir / "icon.png").exists(), "mobile_icons/icon.png fehlt")

    def test_runtime_get_app_icon(self):
        """get_app_icon() liefert ein valides Icon ohne Fehler."""
        from PySide6.QtWidgets import QApplication
        from tray import get_app_icon

        _ = QApplication.instance() or QApplication(["test"])
        icon = get_app_icon()
        self.assertFalse(icon.isNull(), "get_app_icon() lieferte ein leeres Icon zurück")


if __name__ == "__main__":
    unittest.main()
