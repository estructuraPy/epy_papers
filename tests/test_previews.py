"""Tests for the QPainter preview thumbnails and the visual pickers."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_theme_preview_for_every_theme(qapp):
    from epy_papers._core import themes
    from epy_papers._ui._previews import THEME_THUMB, theme_preview

    assert themes.THEMES, "the theme catalogue must not be empty"
    for theme in themes.THEMES.values():
        pix = theme_preview(theme)
        assert not pix.isNull()
        assert pix.size() == THEME_THUMB


def test_layout_preview_for_every_design_block(qapp):
    from epy_papers._core._design import DESIGN_BLOCKS
    from epy_papers._ui._previews import LAYOUT_THUMB, layout_preview

    for kind in DESIGN_BLOCKS:
        pix = layout_preview(kind)
        assert not pix.isNull(), kind
        assert pix.size() == LAYOUT_THUMB


# ``DESIGN_BLOCKS`` (epy_papers's own insertable blocks) covers only
# lead/badge/card/cards/stat/stats/timeline/agenda. ``_draw_layout_body``
# also draws schematics for slide-layout kinds this app never inserts
# itself (shared code with the family's slide-layout pickers), plus the
# "unknown id" fallback -- none of which the test above ever reaches.
_OTHER_LAYOUT_IDS = (
    "section",
    "two-column",
    "comparison",
    "image-caption",
    "image-fullbleed",
    "quote",
    "code",
    "blank",
    "image-left",
    "image-right",
    "quote-portrait",
    "some-unknown-layout-id",  # exercises the else fallback
)


def test_layout_preview_for_every_other_schematic(qapp):
    from epy_papers._ui._previews import LAYOUT_THUMB, layout_preview

    for kind in _OTHER_LAYOUT_IDS:
        pix = layout_preview(kind)
        assert not pix.isNull(), kind
        assert pix.size() == LAYOUT_THUMB


def test_color_falls_back_when_the_value_is_absent_or_invalid(qapp):
    from PySide6.QtGui import QColor

    from epy_papers._ui._previews import _color

    assert _color(None, "#123456") == QColor("#123456")
    assert _color("not-a-real-color", "#654321") == QColor("#654321")
    assert _color(None, QColor("#abcdef")) == QColor("#abcdef")


def test_color_uses_the_value_when_it_is_a_valid_hex(qapp):
    from PySide6.QtGui import QColor

    from epy_papers._ui._previews import _color

    assert _color("#00ff00", "#ffffff") == QColor("#00ff00")


def test_primary_family_is_empty_string_with_no_stack():
    from epy_papers._ui._previews import _primary_family

    assert _primary_family(None) == ""
    assert _primary_family("") == ""


def test_primary_family_extracts_the_first_quoted_family():
    from epy_papers._ui._previews import _primary_family

    assert _primary_family('"Times New Roman", serif') == "Times New Roman"


def test_design_block_dialog_lists_all_blocks(qapp):
    from epy_papers._core._design import DESIGN_BLOCKS
    from epy_papers._ui.design_block_dialog import DesignBlockDialog

    dlg = DesignBlockDialog()
    assert dlg._list.count() == len(DESIGN_BLOCKS)
    assert dlg.selected_kind() in DESIGN_BLOCKS


def test_theme_gallery_lists_all_themes(qapp):
    from epy_papers._core import themes
    from epy_papers._ui.theme_gallery_dialog import ThemeGalleryDialog

    dlg = ThemeGalleryDialog(current_id=themes.DEFAULT_THEME_ID)
    assert dlg._list.count() == len(themes.THEMES)
    assert dlg.selected_theme_id()
