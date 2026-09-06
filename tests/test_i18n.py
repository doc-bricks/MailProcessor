"""Tests for i18n.py — key coverage, formatting, language switching."""
from i18n import _STRINGS, get_language, set_language, tr


def test_all_keys_have_de_and_en():
    """Every translation key must have both 'de' and 'en' variants."""
    missing = [
        f"{key}: missing '{lang}'"
        for key, variants in _STRINGS.items()
        for lang in ("de", "en")
        if lang not in variants or not variants[lang]
    ]
    assert missing == [], "\n".join(missing)


def test_tr_returns_key_for_unknown():
    """tr() returns the raw key when it's not in _STRINGS."""
    set_language("de")
    assert tr("__nonexistent_key__") == "__nonexistent_key__"


def test_tr_format_args_de():
    set_language("de")
    result = tr("launch_error", "some error")
    assert "some error" in result


def test_tr_format_args_en():
    set_language("en")
    result = tr("launch_error", "some error")
    assert "some error" in result


def test_set_get_language_de():
    set_language("de")
    assert get_language() == "de"
    assert tr("menu_quit") == "Beenden"


def test_set_get_language_en():
    set_language("en")
    assert get_language() == "en"
    assert tr("menu_quit") == "Quit"


def test_invalid_language_falls_back_to_de():
    set_language("xx")
    assert get_language() == "de"


def test_tr_de_differs_from_en_for_most_keys():
    """Sanity: at least half of keys have different DE and EN text."""
    different = sum(
        1 for v in _STRINGS.values()
        if v.get("de") != v.get("en")
    )
    assert different > len(_STRINGS) // 2
