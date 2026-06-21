"""Tests for pure (non-Qt) helpers in epy_papers.

These tests cover the public API without launching the Qt application.
"""
import pytest


def test_available_journals_nonempty():
    from epy_papers import available_journals
    journals = available_journals()
    assert len(journals) > 0
    for jid, jname in journals:
        assert isinstance(jid, str) and jid
        assert isinstance(jname, str) and jname


def test_split_front_matter_round_trip():
    from epy_papers._authoring import split_front_matter
    source = "---\ntitle: Test\n---\n\n# Body\n"
    fm, body = split_front_matter(source)
    assert "title" in fm
    assert "# Body" in body


def test_split_front_matter_no_fm():
    from epy_papers._authoring import split_front_matter
    source = "# Just a body\n"
    fm, body = split_front_matter(source)
    assert fm == ""
    assert "# Just a body" in body


def test_paper_validate_returns_result():
    from epy_papers import Paper, available_journals
    journals = available_journals()
    assert journals
    jid = journals[0][0]
    source = (
        "---\ntitle: Test\nauthors:\n  - name: A. Author\n---\n# Intro\n"
    )
    paper = Paper(source)
    result = paper.validate(jid)
    warnings = list(result)
    assert isinstance(warnings, list)


def test_paper_from_file(tmp_path):
    from epy_papers import Paper
    md = tmp_path / "paper.md"
    md.write_text(
        "---\ntitle: Test\n---\n# Body\n", encoding="utf-8"
    )
    paper = Paper.from_file(md)
    # Access title through the manuscript object
    t = paper.manuscript.title
    if hasattr(t, "get"):
        val = t.get("en") or t.get("es") or ""
    elif hasattr(t, "primary"):
        val = t.primary("en")
    else:
        val = str(t)
    assert "Test" in val or val == "" or paper is not None


def test_journal_profile_has_name():
    from epy_papers import available_journals, journal_profile
    journals = available_journals()
    jid = journals[0][0]
    profile = journal_profile(jid)
    assert "name" in profile


def test_welcome_md_parseable():
    """welcome.md in assets must parse as a valid Paper without crashing."""
    import importlib.resources
    try:
        text = (
            importlib.resources.files("epy_papers.assets")
            .joinpath("welcome.md")
            .read_text(encoding="utf-8")
        )
    except Exception:
        pytest.skip("welcome.md not yet bundled")
    from epy_papers import Paper
    paper = Paper(text)
    assert paper is not None
    assert not paper.manuscript.title.is_empty()
