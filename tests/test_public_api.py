"""Tests that the single public API surface stays stable."""

from __future__ import annotations

import pytest

import epy_paper as ep


def test_public_names_present():
    """The documented public names are importable."""
    for name in (
        "Paper",
        "JournalProfile",
        "Manuscript",
        "Author",
        "Bilingual",
        "ValidationResult",
        "Warning",
        "Severity",
        "available_journals",
        "journal_profile",
        "load_journals",
    ):
        assert hasattr(ep, name), name


def test_available_journals_shape():
    """available_journals returns (id, name) tuples."""
    items = ep.available_journals()
    assert all(
        isinstance(t, tuple) and len(t) == 2 for t in items
    )


def test_journal_profile_lookup():
    """journal_profile returns a dict and raises on unknown ids."""
    prof = ep.journal_profile("eng-structures")
    assert prof["publisher"] == "Elsevier"
    with pytest.raises(KeyError):
        ep.journal_profile("does-not-exist")


def test_paper_from_string_and_profile_view():
    """Paper builds from a string and exposes JournalProfile views."""
    paper = ep.Paper("---\ntitle: {en: T}\n---\n# Body")
    view = paper.profile("eng-structures")
    assert view.name == "Engineering Structures"
    assert view.get("page_size") == "a4"
    assert view.columns == "single"
