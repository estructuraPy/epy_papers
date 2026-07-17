"""Formal API compliance tests for epy_papers.

Verifies that the public exports are importable, have the expected interface,
and conform to the declared __all__ contract. Complements test_public_api.py
(behavioural smoke tests) with a stricter, exhaustive surface check.
"""

from __future__ import annotations

import re

import epy_papers as ep

# ---------------------------------------------------------------------------
# Importability
# ---------------------------------------------------------------------------


class TestImportability:
    def test_package_importable(self):
        assert ep is not None

    def test_paper_importable(self):
        from epy_papers import Paper

        assert isinstance(Paper, type)

    def test_journal_profile_importable(self):
        from epy_papers import JournalProfile

        assert isinstance(JournalProfile, type)

    def test_manuscript_importable(self):
        from epy_papers import Manuscript

        assert isinstance(Manuscript, type)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


class TestVersion:
    def test_version_attribute_exists(self):
        assert hasattr(ep, "__version__")

    def test_version_is_string(self):
        assert isinstance(ep.__version__, str)

    def test_version_semver_format(self):
        parts = ep.__version__.split(".")
        assert len(parts) == 3, f"Expected 3 version parts, got {parts}"

    def test_version_parts_are_numeric(self):
        for part in ep.__version__.split("."):
            assert re.match(r"^\d+", part), f"Non-numeric version part: {part!r}"


# ---------------------------------------------------------------------------
# __all__ contract
# ---------------------------------------------------------------------------


class TestAllContract:
    _EXPECTED = [
        "Paper",
        "JournalProfile",
        "Manuscript",
        "Author",
        "Bilingual",
        "BilingualList",
        "ValidationResult",
        "Warning",
        "Severity",
        "PandocMissingError",
        "available_journals",
        "journal_profile",
        "load_journals",
        "load_user_journals",
        "user_journals_path",
        "add_journal",
        "remove_user_journal",
    ]

    def test_all_exists(self):
        assert hasattr(ep, "__all__")

    def test_all_matches_declared_contract(self):
        assert sorted(ep.__all__) == sorted(self._EXPECTED)

    def test_all_symbols_importable(self):
        for name in ep.__all__:
            assert hasattr(ep, name), f"__all__ member {name!r} not found on module"


# ---------------------------------------------------------------------------
# Paper facade required methods
# ---------------------------------------------------------------------------


class TestPaperMethods:
    _REQUIRED_METHODS = ["profile", "validate", "to_draft", "render_notes"]
    _REQUIRED_CLASSMETHODS = ["from_file"]

    def test_required_methods_present(self):
        from epy_papers import Paper

        for method in self._REQUIRED_METHODS:
            assert hasattr(Paper, method), f"Paper missing: {method!r}"

    def test_required_classmethods_present(self):
        from epy_papers import Paper

        for method in self._REQUIRED_CLASSMETHODS:
            assert callable(getattr(Paper, method)), f"Paper.{method!r} is not callable"

    def test_all_required_methods_callable(self):
        from epy_papers import Paper

        for method in self._REQUIRED_METHODS:
            assert callable(getattr(Paper, method)), f"{method!r} is not callable"


# ---------------------------------------------------------------------------
# JournalProfile view
# ---------------------------------------------------------------------------


class TestJournalProfile:
    def test_get_method_present(self):
        from epy_papers import JournalProfile

        assert hasattr(JournalProfile, "get")

    def test_name_property_present(self):
        from epy_papers import JournalProfile

        assert isinstance(JournalProfile.name, property)


# ---------------------------------------------------------------------------
# Journal catalog functions
# ---------------------------------------------------------------------------


class TestJournalCatalog:
    def test_available_journals_returns_list(self):
        journals = ep.available_journals()
        assert isinstance(journals, list)
        assert len(journals) > 0

    def test_available_journals_entries_are_id_name_tuples(self):
        journals = ep.available_journals()
        for entry in journals:
            assert isinstance(entry, tuple)
            assert len(entry) == 2

    def test_load_journals_returns_dict(self):
        catalog = ep.load_journals()
        assert isinstance(catalog, dict)
        assert len(catalog) > 0

    def test_journal_profile_returns_dict(self):
        catalog = ep.load_journals()
        first_id = next(iter(catalog))
        prof = ep.journal_profile(first_id)
        assert isinstance(prof, dict)

    def test_journal_profile_unknown_raises_key_error(self):
        import pytest

        with pytest.raises(KeyError):
            ep.journal_profile("__definitely_not_a_real_journal_id__")

    def test_user_journals_path_returns_path(self):
        from pathlib import Path

        assert isinstance(ep.user_journals_path(), Path)
