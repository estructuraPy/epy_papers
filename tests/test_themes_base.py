"""Tests for ``epy_papers._core.themes_base.Theme``."""

from __future__ import annotations

from epy_papers._core.themes_base import Theme


def test_to_css_renders_a_root_block_with_every_variable():
    theme = Theme(
        id="t",
        display_name="T",
        qt_palette={},
        css_vars={"primary": "#123456", "spacing": "8px"},
    )
    css = theme.to_css()
    assert css == (
        ":root {\n    --primary: #123456;\n    --spacing: 8px;\n}"
    )


def test_to_css_is_empty_string_with_no_variables():
    theme = Theme(id="t", display_name="T", qt_palette={}, css_vars={})
    assert theme.to_css() == ""
