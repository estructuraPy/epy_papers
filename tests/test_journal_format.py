"""Tests for journal-driven formatting, the user catalog and line numbers."""

from __future__ import annotations

import json
import warnings

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
    # Line numbering is no longer a per-paragraph CSS counter: a journal
    # numbers typeset rows, so the preview paints a per-visual-row gutter.
    assert "counter-increment: epyln" not in css
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


# --- corrupt catalog tests (Finding 1/2/3 from DeepSeek audit) -------------


def test_load_user_journals_corrupt_file_warns(tmp_path, monkeypatch):
    """load_user_journals emits UserWarning when the catalog is corrupt."""
    catalog_path = tmp_path / "journals.json"
    catalog_path.write_text("NOT VALID JSON", encoding="utf-8")
    monkeypatch.setenv("EPY_PAPERS_USER_JOURNALS", str(catalog_path))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = ep.load_user_journals()
    assert result == {}
    user_warns = [w for w in caught if issubclass(w.category, UserWarning)]
    assert user_warns, "expected a UserWarning for a corrupt catalog"
    assert str(catalog_path) in str(user_warns[0].message)


def test_add_journal_corrupt_existing_warns(tmp_path, monkeypatch):
    """add_journal warns when the existing catalog cannot be parsed."""
    catalog_path = tmp_path / "journals.json"
    catalog_path.write_text("{bad json", encoding="utf-8")
    monkeypatch.setenv("EPY_PAPERS_USER_JOURNALS", str(catalog_path))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ep.add_journal("new-j", {"name": "New Journal"})
    user_warns = [w for w in caught if issubclass(w.category, UserWarning)]
    assert user_warns, "expected a UserWarning for a corrupt existing catalog"
    # The new journal is still written (replacing the corrupt file).
    written = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert "new-j" in written


def test_remove_user_journal_corrupt_raises(tmp_path, monkeypatch):
    """remove_user_journal propagates the parse error on a corrupt catalog."""
    catalog_path = tmp_path / "journals.json"
    catalog_path.write_text("NOT VALID JSON", encoding="utf-8")
    monkeypatch.setenv("EPY_PAPERS_USER_JOURNALS", str(catalog_path))
    try:
        ep.remove_user_journal("any-id")
    except (json.JSONDecodeError, OSError):
        pass  # expected — catalog is unreadable
    else:
        raise AssertionError(
            "expected JSONDecodeError/OSError for a corrupt catalog"
        )
