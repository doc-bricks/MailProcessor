from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LICENSES_FILE = PROJECT_ROOT / "THIRD_PARTY_LICENSES.txt"


def test_third_party_licenses_lists_runtime_dependencies():
    text = LICENSES_FILE.read_text(encoding="utf-8")

    expected_packages = [
        "PySide6",
        "PySide6_Addons",
        "PySide6_Essentials",
        "shiboken6",
    ]

    for package in expected_packages:
        assert package in text

    # Ensure removed legacy web_companion packages are not present
    for legacy_pkg in ["react-dom", "@capacitor/core", "@capacitor/android", "@capacitor/ios"]:
        assert legacy_pkg not in text

    assert "Checked: 2026-08-14" in text
