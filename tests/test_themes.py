"""Tests for ``epy_papers._core.themes``: the catalogue's ``get()``
fallback chain and ``reload()``.

No existing test file covers this module directly; the app.py tests
exercise ``_apply_theme``/``_build_theme_actions`` around it, but never
``themes.get()``'s own degrade-gracefully fallbacks or ``reload()``.
"""

from __future__ import annotations

import pytest

from epy_papers._core import themes


def test_get_returns_the_requested_theme_when_present():
    theme_id = next(iter(themes.THEMES))
    assert themes.get(theme_id).id == theme_id


def test_get_falls_back_to_default_for_an_unknown_id():
    assert themes.DEFAULT_THEME_ID in themes.THEMES  # precondition
    result = themes.get("not-a-real-theme-id")
    assert result.id == themes.DEFAULT_THEME_ID


def test_get_falls_back_to_default_for_a_falsy_id():
    result = themes.get(None)
    assert result.id == themes.DEFAULT_THEME_ID
    assert themes.get("").id == themes.DEFAULT_THEME_ID


def test_get_falls_back_to_any_registered_theme_when_default_is_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    """Counter-example to the two tests above: the default id itself can
    go missing (a corrupt/edited bundle) and the app must still boot with
    whatever theme IS registered, rather than crashing.
    """
    trimmed = {
        k: v for k, v in themes.THEMES.items() if k != themes.DEFAULT_THEME_ID
    }
    assert trimmed  # precondition: at least one non-default theme exists
    monkeypatch.setattr(themes, "THEMES", trimmed)
    result = themes.get("also-not-real")
    assert result.id in trimmed


def test_get_returns_a_last_resort_empty_theme_when_nothing_is_registered(
    monkeypatch: pytest.MonkeyPatch,
):
    """The ultimate fallback: every layout file is corrupt/missing. The
    app must still boot (with no colours) rather than raise out of the
    window constructor.
    """
    monkeypatch.setattr(themes, "THEMES", {})
    result = themes.get("anything")
    assert result.id == "fallback"
    assert result.qt_palette == {}
    assert result.css_vars == {}


def test_reload_rescans_and_mutates_the_existing_dict_in_place():
    """``reload()`` must mutate THEMES, not rebind it: app.py and other
    modules hold direct references to the original dict object.
    """
    original_dict = themes.THEMES
    result = themes.reload()
    assert result is original_dict  # same object, refreshed in place
    assert themes.DEFAULT_THEME_ID in themes.THEMES
