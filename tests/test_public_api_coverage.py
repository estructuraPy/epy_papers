"""Coverage of ``epy_papers.__init__`` behaviour not already exercised.

``test_journal_format.py``, ``test_api_formal.py`` and ``test_render.py``
cover the journal catalog, the API surface contract and the DOCX/LaTeX
export paths. This file covers what they leave out: ``to_draft``'s
``pdf``/``html`` branches, ``render_notes`` (checked only for
*existence* elsewhere, never called), ``remove_user_journal``'s two
early-return guards, and ``_dumps_compact``'s list-handling branches
(only its dict side is exercised by the journal-catalog tests, since
every journal profile written there has scalar-only fields).

A real TinyTeX engine is installed on this machine (verified via
``epy_papers._core._latex.find_engine()`` before writing this file), so
the PDF-export test compiles for real rather than mocking the engine
away -- consistent with ``test_api_formal.py``'s pandoc-backed DOCX/TeX
tests.
"""

from __future__ import annotations

import epy_papers as ep

SIMPLE = (
    "---\ntitle: {en: A test manuscript}\n"
    "abstract: {en: A short abstract.}\nkeywords: {en: [test]}\n"
    "---\n\n# Introduction\n\nBody text.\n"
)


# ---------------------------------------------------------------------------
# Paper.to_draft: pdf / html branches (docx / tex covered by test_api_formal)
# ---------------------------------------------------------------------------


def test_to_draft_pdf_produces_a_real_pdf_file(tmp_path):
    out = ep.Paper(SIMPLE).to_draft(
        "eng-structures", tmp_path / "draft.pdf", fmt="pdf"
    )
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF-")


def test_to_draft_html_produces_a_real_html_file(tmp_path):
    out = ep.Paper(SIMPLE).to_draft(
        "generic-manuscript", tmp_path / "draft.html", fmt="html"
    )
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "<html" in text.lower()
    assert "Introduction" in text


def test_to_draft_defaults_to_the_journals_first_declared_format(tmp_path):
    """No ``fmt`` given: the journal's own ``formats`` list picks it, not
    a hardcoded ``docx`` -- the guard this is a counter-example for is
    ``fmt = fmt or (prof.get("formats") or ["docx"])[0]``.

    ``eng-structures`` declares ``["tex", "docx"]`` (verified directly
    against the catalog below), so a plain call with no ``fmt`` must
    produce LaTeX source, not a Word document -- checked by content
    signature since ``to_draft`` writes to the exact path given and never
    renames its extension.
    """
    prof = ep.journal_profile("eng-structures")
    assert prof.get("formats")[0] == "tex"
    out = ep.Paper(SIMPLE).to_draft(
        "eng-structures", tmp_path / "draft_default"
    )
    assert out.exists()
    assert "\\documentclass" in out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Paper.render_notes
# ---------------------------------------------------------------------------


def test_render_notes_reports_an_unbundled_latex_class(tmp_path):
    """``bee`` resolves to ``svjour3``, which is not bundled (see
    ``test_api_formal.test_latex_class_fallback_records_note``) -- the
    same fact surfaced through the public ``render_notes`` API instead of
    reaching into the ``Renderer`` directly.
    """
    notes = ep.Paper(SIMPLE).render_notes("bee", "tex")
    assert any("not bundled" in n for n in notes)


def test_render_notes_html_never_touches_the_latex_class():
    """``fmt="html"`` must not probe for a LaTeX class at all -- only
    ``tex``/``pdf`` do. A profile with no bundled class would otherwise
    add a spurious note to a format that never uses LaTeX.
    """
    notes = ep.Paper(SIMPLE).render_notes("bee", "html")
    assert not any("not bundled" in n for n in notes)


# ---------------------------------------------------------------------------
# remove_user_journal: both early-return guards
# ---------------------------------------------------------------------------


def test_remove_user_journal_with_no_catalog_file_returns_false(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(
        "EPY_PAPERS_USER_JOURNALS", str(tmp_path / "never_created.json")
    )
    assert ep.remove_user_journal("anything") is False


def test_remove_user_journal_absent_from_an_existing_catalog_returns_false(
    tmp_path, monkeypatch
):
    catalog = tmp_path / "journals.json"
    monkeypatch.setenv("EPY_PAPERS_USER_JOURNALS", str(catalog))
    ep.add_journal("present", {"name": "Present Journal"})
    assert ep.remove_user_journal("not-present") is False
    # Counter-example: the journal that IS there is unaffected.
    assert "present" in ep.load_user_journals()


# ---------------------------------------------------------------------------
# _dumps_compact: list-handling branches (dict side covered by the
# leaf-object-on-one-line assertion in test_journal_format.py)
# ---------------------------------------------------------------------------


def test_dumps_compact_leaf_list_stays_on_one_line():
    assert ep._dumps_compact([1, 2, "three"]) == '[1, 2, "three"]'


def test_dumps_compact_empty_list_is_bracket_pair():
    assert ep._dumps_compact([]) == "[]"


def test_dumps_compact_list_of_dicts_expands_multiline():
    result = ep._dumps_compact([{"a": 1}, {"b": 2}])
    assert result == '[\n  {"a": 1},\n  {"b": 2}\n]'


def test_dumps_compact_round_trips_through_add_journal_with_a_list_field(
    tmp_path, monkeypatch
):
    """The real caller: a journal profile whose own field is a list of
    mappings must still parse back to the same structure.
    """
    import json

    monkeypatch.setenv(
        "EPY_PAPERS_USER_JOURNALS", str(tmp_path / "journals.json")
    )
    ep.add_journal(
        "list-field-journal",
        {"name": "N", "reviewers": [{"name": "R1"}, {"name": "R2"}]},
    )
    written = json.loads(
        (tmp_path / "journals.json").read_text(encoding="utf-8")
    )
    assert written["list-field-journal"]["reviewers"] == [
        {"name": "R1"},
        {"name": "R2"},
    ]
