"""Tests for journal-driven formatting, the user catalog and line numbers."""

from __future__ import annotations

import epy_papers as ep


def test_add_and_load_user_journal(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "EPY_PAPERS_USER_JOURNALS", str(tmp_path / "journals.json")
    )
    ep.add_journal(
        "xj",
        {"name": "X Journal", "columns": 2, "line_numbers": "continuous"},
    )
    catalog = ep.load_journals()
    assert "xj" in catalog
    assert catalog["xj"]["name"] == "X Journal"
    assert ("xj", "X Journal") in ep.available_journals()
    # leaf object stored inline (house data-file style)
    text = (tmp_path / "journals.json").read_text(encoding="utf-8")
    assert '"xj": {"name": "X Journal"' in text
    assert ep.remove_user_journal("xj") is True
    assert "xj" not in ep.load_journals()


def test_user_journal_overrides_bundled(tmp_path, monkeypatch):
    monkeypatch.setenv("EPY_PAPERS_USER_JOURNALS", str(tmp_path / "j.json"))
    bundled_id = ep.available_journals()[0][0]
    ep.add_journal(bundled_id, {"name": "OVERRIDDEN"})
    assert ep.load_journals()[bundled_id]["name"] == "OVERRIDDEN"


def test_add_journal_requires_id(tmp_path, monkeypatch):
    monkeypatch.setenv("EPY_PAPERS_USER_JOURNALS", str(tmp_path / "j.json"))
    try:
        ep.add_journal("  ", {"name": "x"})
    except ValueError:
        return
    raise AssertionError("expected ValueError for blank id")


def test_journal_css_reflects_profile():
    from epy_papers.tab import _journal_css

    css = _journal_css(
        {
            "columns": 2,
            "spacing": "double",
            "line_numbers": "continuous",
            "page_size": "a4",
            "font_size_pt": 11,
        }
    )
    assert "column-count: 2" in css
    assert "line-height: 2.0" in css
    assert "counter-increment: epyln" in css
    assert "210mm" in css
    assert "11pt" in css


def test_journal_css_single_column_no_line_numbers():
    from epy_papers.tab import _journal_css

    css = _journal_css(
        {"columns": 1, "spacing": "single", "line_numbers": "off"}
    )
    assert "column-count: 2" not in css
    assert "counter-increment: epyln" not in css
    assert "line-height: 1.15" in css


def test_preview_blinding_hides_authors():
    from epy_papers.tab import _build_preview_html

    src = (
        "---\ntitle: T\nauthors:\n  - name: Secret Author\n"
        "abstract: A\n---\n\nBody paragraph.\n"
    )
    html = _build_preview_html(src, {"name": "J", "blinding": "double"})
    assert "Secret Author" not in html
    assert "withheld" in html
    assert 'class="page"' in html
    assert "fmt-bar" in html


def test_preview_shows_authors_when_not_blinded():
    from epy_papers.tab import _build_preview_html

    src = (
        "---\ntitle: T\nauthors:\n  - name: Jane Doe\n"
        "abstract: A\n---\n\nBody.\n"
    )
    html = _build_preview_html(src, {"name": "J", "blinding": "none"})
    assert "Jane Doe" in html


def test_render_line_number_flag():
    from epy_papers._authoring import Manuscript
    from epy_papers._render import Renderer

    src = "---\ntitle: T\nabstract: A\n---\n\nBody.\n"
    on = Renderer(Manuscript.from_source(src), {"line_numbers": "continuous"})
    off = Renderer(Manuscript.from_source(src), {"line_numbers": "off"})
    assert on._has_line_numbers() is True
    assert off._has_line_numbers() is False
