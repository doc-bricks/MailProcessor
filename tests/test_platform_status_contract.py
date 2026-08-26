from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_active_platform_status_documents_match_removed_companion_scope():
    for removed_path in (
        "PORTIERUNGSPLAN.md",
        "PORTING_STATUS.md",
        "MOBILE_PWA_SMOKE.md",
        "web_companion/PORTING_STATUS.md",
        "web_companion/MOBILE_PWA_SMOKE.md",
    ):
        assert not (ROOT / removed_path).exists()

    readme = _read("README.md")
    readme_de = _read("README-DE.md")
    releases = _read("RELEASES.md")
    llms = _read("llms.txt")

    assert "73 Pytest tests" in readme
    assert "73 Pytest-Tests" in readme_de
    assert "73/73 Pytest tests" in llms
    assert "Last-checked: 2026-08-26" in llms

    assert "former web/PWA companion" in readme
    assert "macOS and Linux" in readme
    assert "frühere Web-/PWA" in readme_de
    assert "macOS und Linux" in readme_de
    assert "web/PWA" in releases
    assert "macOS/Linux" in releases
    assert "web/PWA" in llms
    assert "macOS/Linux" in llms
    assert "not a synchronization interface or a mobile product" in readme
    assert "keine aktive Produktfläche" in readme_de
    assert "MACOS_LINUX_SOURCE_SMOKE.md" in readme
    assert "MACOS_LINUX_SOURCE_SMOKE.md" in readme_de
    assert "device/emulator" in releases
    assert "acceptance record" in releases
    assert "MSIX" in releases
    assert "WACK" in releases
