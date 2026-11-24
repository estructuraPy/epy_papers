"""Tests for the custom-theme editor dialog and its helpers.

The dialog is built (never ``exec``'d) so its construction, the
form-value collection, the base-theme reload and the live-preview
restyle are all exercised headlessly. Mirrors
``epy_reports/tests/test_theme_editor_dialog.py`` against the
epy_papers API.
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QColorDialog, QMessageBox

from epy_papers._core import themes
from epy_papers._ui.theme_editor_dialog import (
    ThemeEditorDialog,
    _ColorButton,
    _contrast,
    _font_primary,
    _pt_value,
)

_app: QApplication | None = None


@pytest.fixture(scope="module")
def qapp():
    """Provide a module-scoped QApplication instance."""
    global _app
    if _app is None:
        _instance = QApplication.instance()
        _app = (
            _instance
            if isinstance(_instance, QApplication)
            else QApplication([])
        )
    return _app


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_contrast_dark_on_light():
    """Light backgrounds get black text."""
    assert _contrast("#FFFFFF") == "#000000"


def test_contrast_light_on_dark():
    """Dark backgrounds get white text."""
    assert _contrast("#000000") == "#FFFFFF"


def test_contrast_invalid_length_defaults_black():
    """A malformed hex string yields black."""
    assert _contrast("#FFF") == "#000000"


def test_font_primary_extracts_first_family():
    """The primary family is the first entry of the stack."""
    assert _font_primary('"Calibri", Arial, sans-serif') == "Calibri"
    assert _font_primary("'Georgia', serif") == "Georgia"


def test_font_primary_empty_defaults_calibri():
    """An empty stack falls back to Calibri."""
    assert _font_primary("") == "Calibri"


def test_pt_value_parses_points():
    """A ``"12pt"`` string parses to 12.0."""
    assert _pt_value("12pt") == 12.0
    assert _pt_value("12.5pt") == 12.5


def test_pt_value_empty_defaults_to_12():
    """Nothing numeric left after cleaning takes the ternary's else."""
    assert _pt_value("") == 12.0
    assert _pt_value("abc") == 12.0


def test_pt_value_malformed_number_defaults_to_12():
    """Digits/dots that survive cleaning but do not parse hit the except.

    ``"abc"`` above leaves an EMPTY cleaned string (the ternary's else
    branch); ``"1.2.3pt"`` strips to ``"1.2.3"`` -- non-empty, but not a
    valid float -- so this is the case that exercises ``except
    ValueError``.
    """
    assert _pt_value("1.2.3pt") == 12.0


# ---------------------------------------------------------------------------
# _ColorButton
# ---------------------------------------------------------------------------


def test_color_button_default(qapp):
    """A fresh button shows black and reports it."""
    btn = _ColorButton()
    assert btn.color() == "#000000"
    assert btn.text() == "#000000"


def test_color_button_set_color_uppercases_and_refreshes(qapp):
    """The colour button normalises hex to uppercase and repaints."""
    btn = _ColorButton("#abcdef")
    btn.set_color("#fedcba")
    assert btn.color() == "#FEDCBA"
    assert btn.text() == "#FEDCBA"
    assert "#FEDCBA" in btn.styleSheet()


def test_color_button_pick_applies_a_valid_choice(qapp, monkeypatch):
    """Picking a valid colour updates the button and emits changed."""
    monkeypatch.setattr(
        QColorDialog,
        "getColor",
        staticmethod(lambda *a, **k: QColor("#112233")),
    )
    btn = _ColorButton("#000000")
    fired = []
    btn.changed.connect(lambda: fired.append(1))
    btn._pick()
    assert btn.color() == "#112233"
    assert fired == [1]


def test_color_button_pick_cancelled_keeps_the_old_color(qapp, monkeypatch):
    """Cancelling the picker (an invalid QColor) changes nothing."""
    monkeypatch.setattr(
        QColorDialog,
        "getColor",
        staticmethod(lambda *a, **k: QColor()),  # invalid/default
    )
    btn = _ColorButton("#445566")
    fired = []
    btn.changed.connect(lambda: fired.append(1))
    btn._pick()
    assert btn.color() == "#445566"
    assert fired == []


# ---------------------------------------------------------------------------
# Dialog construction and payload
# ---------------------------------------------------------------------------


def test_dialog_lists_every_base_theme(qapp):
    """The base combo has one entry per registered theme."""
    dlg = ThemeEditorDialog()
    assert dlg.base_combo.count() == len(themes.THEMES)


def test_dialog_default_name_is_empty(qapp):
    """A fresh dialog has no name yet."""
    dlg = ThemeEditorDialog()
    assert dlg.theme_name() == ""


def test_dialog_name_is_stripped(qapp):
    """The reported name is whitespace-stripped."""
    dlg = ThemeEditorDialog()
    dlg.name_edit.setText("  My Theme  ")
    assert dlg.theme_name() == "My Theme"


def test_dialog_prefills_from_the_chosen_base_theme(qapp):
    """A known ``base_theme_id`` selects it and reloads its palette."""
    dlg = ThemeEditorDialog(base_theme_id="classic")
    classic = themes.get("classic")
    assert dlg.base_combo.currentData() == "classic"
    assert dlg._colors["page_bg"].color() == classic.css_vars.get(
        "bg", "#FFFFFF"
    ).upper()


def test_dialog_tolerates_an_unknown_base_theme_id(qapp):
    """A stale id is not found in the combo but still loads a fallback."""
    dlg = ThemeEditorDialog(base_theme_id="not-a-real-theme")
    assert dlg.base_combo.findData("not-a-real-theme") == -1
    fallback = themes.get("not-a-real-theme")
    assert dlg._colors["page_bg"].color() == fallback.css_vars.get(
        "bg", "#FFFFFF"
    ).upper()


def test_values_and_payload_round_trip(qapp):
    """The collected values build a coherent ``.epyson`` payload."""
    dlg = ThemeEditorDialog(base_theme_id="classic")
    dlg.name_edit.setText("Round Trip")
    values = dlg._values()
    assert values["display_name"] == "Round Trip"
    assert set(values) >= {
        "page_bg", "text", "heading", "primary", "secondary",
        "border", "code_bg", "mark", "text_font", "code_font",
        "scales", "callouts",
    }
    payload = dlg.epyson_payload()
    assert payload["display_name"] == "Round Trip"
    assert payload["typography"]["scales"]["h1"]["size"] > 0


def test_values_falls_back_to_default_fonts_when_blank(qapp):
    """Blank font fields become the documented Calibri/Consolas names."""
    dlg = ThemeEditorDialog()
    dlg._fonts["text"].setCurrentText("")
    dlg._fonts["code"].setCurrentText("")
    values = dlg._values()
    assert values["text_font"] == "Calibri"
    assert values["code_font"] == "Consolas"


def test_load_from_theme_uses_defaults_for_a_bare_theme(qapp, monkeypatch):
    """A theme whose ``css_vars`` is empty fills every field with defaults."""
    bare = themes.Theme(
        id="bare", display_name="Bare", qt_palette={}, css_vars={}
    )
    monkeypatch.setattr(themes, "get", lambda _tid: bare)
    dlg = ThemeEditorDialog()
    dlg._load_from_theme("bare")
    assert dlg._colors["page_bg"].color() == "#FFFFFF"
    assert dlg._colors["heading"].color() == "#00217E"
    assert dlg._colors["primary"].color() == "#00217E"
    assert dlg._colors["secondary"].color() == "#0969DA"
    assert dlg._colors["border"].color() == "#C8C8C8"
    assert dlg._colors["code_bg"].color() == "#F5F5F5"
    assert dlg._colors["mark"].color() == "#CA9A24"
    assert dlg._fonts["text"].currentText() == "Calibri"
    assert dlg._fonts["code"].currentText() == "Consolas"
    assert dlg._sizes["h1"].value() == 12.0
    assert dlg._weights["h1"].currentText() == "700"
    bg, border = dlg._callouts["note"]
    assert bg.color() == "#EAF2FB"
    assert border.color() == "#2F6FBF"


def test_changing_base_reloads_colors(qapp):
    """Selecting a different base reloads its palette into the form."""
    dlg = ThemeEditorDialog()
    first = dlg._colors["page_bg"].color()
    for theme in themes.THEMES.values():
        idx = dlg.base_combo.findData(theme.id)
        dlg.base_combo.setCurrentIndex(idx)
        if dlg._colors["page_bg"].color() != first:
            break
    chosen = themes.get(dlg.base_combo.currentData())
    assert dlg._colors["page_bg"].color() == chosen.css_vars.get(
        "bg", "#FFFFFF"
    ).upper()


def test_on_base_changed_reloads_the_selected_theme(qapp):
    """The slot itself reloads fields after a programmatic change."""
    dlg = ThemeEditorDialog(base_theme_id="classic")
    idx = dlg.base_combo.findData("minimal")
    assert idx >= 0, "minimal is bundled and must be selectable"
    dlg.base_combo.setCurrentIndex(idx)
    dlg._on_base_changed()
    minimal = themes.get("minimal")
    assert dlg._colors["page_bg"].color() == minimal.css_vars["bg"].upper()


def test_edit_id_prefills_the_existing_display_name(qapp):
    """Editing a registered theme pre-fills its saved display name."""
    theme_id = themes.DEFAULT_THEME_ID
    expected = themes.THEMES[theme_id].display_name
    dlg = ThemeEditorDialog(edit_id=theme_id)
    assert dlg.name_edit.text() == expected


def test_edit_id_unknown_leaves_name_blank(qapp):
    """An edit_id absent from the catalogue is not treated as a real
    edit -- a stale id must not invent a name.
    """
    dlg = ThemeEditorDialog(edit_id="not-a-real-theme")
    assert dlg.name_edit.text() == ""


# ---------------------------------------------------------------------------
# Live preview
# ---------------------------------------------------------------------------


def test_update_preview_sets_stylesheets(qapp):
    """Every preview widget is restyled from the current form values."""
    dlg = ThemeEditorDialog(base_theme_id="classic")
    dlg._update_preview()
    assert dlg.preview_box.styleSheet() != ""
    assert dlg._pv_heading.styleSheet() != ""
    assert dlg._pv_body.styleSheet() != ""
    assert dlg._pv_callout.styleSheet() != ""
    assert dlg._pv_code.styleSheet() != ""


def test_update_preview_uses_generic_fonts_when_blank(qapp):
    """Blank font fields degrade to ``sans-serif`` / ``monospace``."""
    dlg = ThemeEditorDialog()
    dlg._fonts["text"].setCurrentText("")
    dlg._fonts["code"].setCurrentText("")
    dlg._update_preview()
    assert "sans-serif" in dlg._pv_heading.styleSheet()
    assert "monospace" in dlg._pv_code.styleSheet()


# ---------------------------------------------------------------------------
# _on_save
# ---------------------------------------------------------------------------


def test_on_save_blank_name_warns_and_does_not_accept(qapp, monkeypatch):
    """An empty theme name is refused with a warning, dialog stays open."""
    warned = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        staticmethod(lambda *a, **k: warned.append(a)),
    )
    dlg = ThemeEditorDialog()
    accepted = []
    dlg.accepted.connect(lambda: accepted.append(1))
    dlg._on_save()
    assert warned, "expected a warning dialog for a blank name"
    assert accepted == []


def test_on_save_with_a_name_accepts(qapp, monkeypatch):
    """A non-blank theme name accepts the dialog without warning."""
    warned = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        staticmethod(lambda *a, **k: warned.append(a)),
    )
    dlg = ThemeEditorDialog()
    dlg.name_edit.setText("My Custom Theme")
    accepted = []
    dlg.accepted.connect(lambda: accepted.append(1))
    dlg._on_save()
    assert warned == []
    assert accepted == [1]
