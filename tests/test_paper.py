"""Tests for ``_core/_paper.py`` — the ``Paper`` facade, moved out of the
package ``__init__`` so the facade is a pure wrap."""

from __future__ import annotations

import pytest

from epy_papers import JournalProfile, Paper, available_journals

SOURCE = "---\ntitle: Test\nauthors:\n  - name: A. Author\n---\n# Intro\n"


def _first_journal_id() -> str:
    journals = available_journals()
    assert journals
    return journals[0][0]


class TestPaperConstruction:
    def test_from_source_text(self):
        paper = Paper(SOURCE)
        assert paper.manuscript is not None

    def test_from_file_reads_and_sets_base_dir(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(SOURCE, encoding="utf-8")
        paper = Paper.from_file(md)
        assert paper.base_dir == tmp_path
        assert paper.manuscript is not None


class TestPaperProfile:
    def test_profile_returns_journal_profile(self):
        prof = Paper(SOURCE).profile(_first_journal_id())
        assert isinstance(prof, JournalProfile)
        assert prof.name

    def test_unknown_journal_raises(self):
        with pytest.raises(KeyError):
            Paper(SOURCE).profile("no-such-journal-xyz")


class TestPaperValidate:
    def test_validate_returns_iterable_result(self):
        result = Paper(SOURCE).validate(_first_journal_id())
        assert isinstance(list(result), list)

    def test_validate_is_iterable_twice(self):
        result = Paper(SOURCE).validate(_first_journal_id())
        assert list(result) == list(result)


class TestPaperRenderNotes:
    def test_render_notes_returns_list(self):
        notes = Paper(SOURCE).render_notes(_first_journal_id(), "tex")
        assert isinstance(notes, list)
