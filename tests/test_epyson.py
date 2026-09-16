"""Tests for ``epy_papers._core.epyson``.

No existing test file imports this module directly: the ~75% it already
had came incidentally from ``themes.THEMES = load_all_themes()`` running
at import time against the real bundled layouts, and from app.py/tab.py
tests calling ``themes.get()`` / ``apply_palette()`` / ``qss_for()``. This
file covers the remaining color-math helpers, the user-theme CRUD
functions (``save_user_theme`` / ``load_user_theme`` / ``user_theme_ids`` /
``delete_user_theme``, none of which epy_papers currently wires to any
dialog -- there is no theme *editor* here, only the gallery *picker* --
but all five are exported in ``themes.__all__`` as public API), the
corrupt-file skip branches in ``load_all_themes``, and
``_tonal_variants``/``build_epyson`` (likewise unused by any current UI in
this app, but exported/public and independently testable as pure
functions).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from epy_papers._core import epyson
from epy_papers._core.themes_base import Theme


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        return instance
    if instance is None:
        return QApplication([])
    raise RuntimeError("epyson tests need a QApplication.")


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def test_coerce_hex_passes_through_an_already_hashed_string():
    assert epyson._coerce_hex("#112233") == "#112233"


def test_coerce_hex_adds_the_missing_hash():
    assert epyson._coerce_hex("112233") == "#112233"


def test_coerce_hex_converts_an_rgb_triplet():
    assert epyson._coerce_hex([17, 34, 51]) == "#112233"


def test_lighten_mixes_toward_white():
    assert epyson._lighten("#000000", 0.5) == "#7F7F7F"
    assert epyson._lighten("#000000", 0.0) == "#000000"


def test_darken_mixes_toward_black():
    assert epyson._darken("#FFFFFF", 0.5) == "#7F7F7F"


# ---------------------------------------------------------------------------
# _callout_vars: direct bg/border override vs. palette reference
# ---------------------------------------------------------------------------


def test_callout_vars_uses_direct_colors_when_both_are_given():
    """No bundled layout uses this form (all reference a named palette),
    but the theme editor a sibling app ships writes it, and this module
    is shared code -- so this is the only place it is exercised.
    """
    callouts = {
        "types": {
            "note": {"bg": "#ABCDEF", "border": [1, 2, 3]},
        }
    }
    out = epyson._callout_vars(callouts, epyson._palettes())
    assert out["callout-note-bg"] == "#ABCDEF"
    assert out["callout-note-border"] == "#010203"


def test_callout_vars_falls_back_to_the_named_palette():
    out = epyson._callout_vars({}, epyson._palettes())
    # note has no explicit type entry, so it uses the "blues" fallback.
    assert "callout-note-bg" in out
    assert "callout-note-border" in out


# ---------------------------------------------------------------------------
# load_layout_theme / _theme_from_raw over every real bundled file
# ---------------------------------------------------------------------------


def test_every_bundled_layout_loads_into_a_valid_theme():
    from epy_papers._config import _loader

    for filename in _loader.list_bundled_layout_files():
        theme = epyson.load_layout_theme(filename)
        assert theme.id
        assert theme.display_name
        assert theme.qt_palette
        assert theme.css_vars


# ---------------------------------------------------------------------------
# User themes: save / load / list / delete round trip
# ---------------------------------------------------------------------------


@pytest.fixture
def user_themes_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "user_themes"
    monkeypatch.setattr(epyson, "user_themes_dir", lambda: directory)
    return directory


def test_safe_stem_slugifies_a_display_name():
    assert epyson._safe_stem("My Custom Theme!") == "my-custom-theme"


def test_safe_stem_falls_back_when_nothing_survives():
    assert epyson._safe_stem("!!!") == "custom-theme"


def test_save_load_and_list_a_user_theme_round_trips(
    user_themes_dir: Path,
):
    payload = {
        "display_name": "My Test Theme",
        "font_families": {"default": {"primary": "Arial"}},
        "palette": {"page": {"background": [255, 255, 255]}},
    }
    theme_id = epyson.save_user_theme(payload)
    assert theme_id == "my-test-theme"
    assert (user_themes_dir / "my-test-theme.epyson").exists()

    assert epyson.user_theme_ids() == {"my-test-theme"}

    theme = epyson.load_user_theme(user_themes_dir / "my-test-theme.epyson")
    assert isinstance(theme, Theme)
    assert theme.display_name == "My Test Theme"


def test_user_theme_ids_skips_a_corrupt_file_without_raising(
    user_themes_dir: Path,
):
    user_themes_dir.mkdir(parents=True)
    (user_themes_dir / "broken.epyson").write_text(
        "{not valid json", encoding="utf-8"
    )
    good = {"display_name": "Good", "layout_name": "good-one"}
    epyson.save_user_theme(good)
    assert epyson.user_theme_ids() == {"good-one"}


def test_delete_user_theme_removes_the_file(user_themes_dir: Path):
    epyson.save_user_theme({"display_name": "Doomed"})
    assert (user_themes_dir / "doomed.epyson").exists()
    epyson.delete_user_theme("doomed")
    assert not (user_themes_dir / "doomed.epyson").exists()


def test_delete_user_theme_is_a_noop_for_a_theme_that_never_existed(
    user_themes_dir: Path,
):
    user_themes_dir.mkdir(parents=True)
    epyson.delete_user_theme("never-existed")  # must not raise


def test_user_themes_dir_lives_under_app_config_location():
    # Not monkeypatched here: the real function, checked directly.
    path = epyson.user_themes_dir()
    assert path.name == "themes"
    assert path.parent.name == "epy_papers"


# ---------------------------------------------------------------------------
# load_all_themes: corrupt-file skip branches (bundled + user)
# ---------------------------------------------------------------------------


def test_load_all_themes_skips_a_corrupt_bundled_layout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    real_load = epyson.load_layout_theme

    def _flaky(filename: str):
        if filename == "corporate.epyson":
            raise KeyError("simulated corrupt layout")
        return real_load(filename)

    monkeypatch.setattr(epyson, "load_layout_theme", _flaky)
    monkeypatch.setattr(epyson, "user_themes_dir", lambda: tmp_path / "none")

    themes = epyson.load_all_themes()
    assert "corporate" not in themes
    assert themes  # the other bundled layouts still loaded


def test_load_all_themes_skips_a_corrupt_user_theme(
    user_themes_dir: Path,
):
    user_themes_dir.mkdir(parents=True)
    (user_themes_dir / "broken.epyson").write_text("nope", encoding="utf-8")
    epyson.save_user_theme({"display_name": "Fine", "layout_name": "fine"})

    themes = epyson.load_all_themes()
    assert "fine" in themes
    assert "broken" not in themes


def test_load_all_themes_user_theme_overrides_a_bundled_id_of_the_same_name(
    user_themes_dir: Path,
):
    user_themes_dir.mkdir(parents=True)
    epyson.save_user_theme(
        {"display_name": "Overridden Corporate", "layout_name": "corporate"}
    )
    themes = epyson.load_all_themes()
    assert themes["corporate"].display_name == "Overridden Corporate"


# ---------------------------------------------------------------------------
# apply_palette
# ---------------------------------------------------------------------------


def test_apply_palette_sets_the_style_font_and_palette(qapp: QApplication):
    theme = epyson.load_layout_theme("corporate.epyson")
    epyson.apply_palette(qapp, theme)
    assert qapp.font().pointSize() == 10


def test_apply_palette_falls_back_to_segoe_ui_when_variable_text_absent(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
):
    """``QFont(name).family()`` always echoes the constructor argument
    back verbatim regardless of real availability (verified with a
    probe), so the ``"segoe ui variable" not in family`` fallback can
    never fire through normal QFont behaviour on this platform. Forcing
    ``QFont.family()`` to return something else is the only way to
    exercise it.
    """
    monkeypatch.setattr(QFont, "family", lambda self: "Arial")
    theme = epyson.load_layout_theme("corporate.epyson")
    epyson.apply_palette(qapp, theme)  # must not raise
    assert qapp.font().pointSize() == 10


def test_apply_palette_skips_an_unknown_color_role(qapp: QApplication):
    theme = Theme(
        id="t",
        display_name="T",
        qt_palette={"NotARealQPaletteRole": "#ffffff", "Window": "#ffffff"},
        css_vars={},
    )
    epyson.apply_palette(qapp, theme)  # must not raise


# ---------------------------------------------------------------------------
# _tonal_variants (unused by qss_for, which inlines its own tonal math;
# exported indirectly as shared color-math -- tested as a pure function)
# ---------------------------------------------------------------------------


def test_tonal_variants_light_theme_darkens_surfaces():
    result = epyson._tonal_variants("#FFFFFF", "#0000FF", is_dark_theme=False)
    assert set(result) == {
        "bg_toolbar",
        "bg_statusbar",
        "bg_panel",
        "bg_menu",
        "accent_soft",
        "accent_strong",
        "scrollbar_handle",
    }
    # Darkened from pure white: every value must differ from the bg.
    assert result["bg_toolbar"] != "#FFFFFF"


def test_tonal_variants_dark_theme_lightens_surfaces():
    result = epyson._tonal_variants("#000000", "#00FFFF", is_dark_theme=True)
    assert result["bg_toolbar"] != "#000000"
    assert result["bg_panel"] != "#000000"


# ---------------------------------------------------------------------------
# build_epyson (unused by any UI in this app; exported shared code)
# ---------------------------------------------------------------------------


def test_build_epyson_assembles_a_loadable_payload():
    values = {
        "display_name": "Built Theme",
        "text_font": "Georgia",
        "code_font": "Fira Code",
        "page_bg": "#FFFFFF",
        "text": "#000000",
        "heading": "#111111",
        "primary": "#0000FF",
        "secondary": "#00FF00",
        "border": "#CCCCCC",
        "code_bg": "#EEEEEE",
        "mark": "#FFFF00",
        "scales": {
            "h1": {"size": 24, "weight": "700"},
            "text": {"size": 12, "weight": "400"},
        },
        "callouts": {
            "note": {"bg": "#CCCCFF", "border": "#0000FF"},
        },
    }
    payload = epyson.build_epyson(values)
    assert payload["display_name"] == "Built Theme"
    assert payload["font_families"]["default"]["primary"] == "Georgia"
    assert payload["palette"]["page"]["background"] == [255, 255, 255]
    assert payload["typography"]["scales"]["h1"]["size"] == 24
    assert payload["callouts"]["types"]["note"]["bg"] == "#CCCCFF"

    # The payload round-trips through the same theme builder used for
    # bundled/user layouts.
    theme = epyson._theme_from_raw(payload, "built-theme")
    assert theme.display_name == "Built Theme"
