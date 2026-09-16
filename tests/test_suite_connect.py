"""Tests for ``epy_papers.epy_suite_connect.get_suite_info``."""

from __future__ import annotations

import epy_papers
from epy_papers.epy_suite_connect import get_suite_info


def test_get_suite_info_reports_the_real_package_identity():
    info = get_suite_info()
    assert info["pkg"] == "epy_papers"
    assert info["version"] == epy_papers.__version__


def test_get_suite_info_author_defaults_to_empty_string():
    """epy_papers carries no ``__author__`` attribute (verified: the
    package only ever sets ``__version__``), so this is always the
    ``getattr`` default path -- exercised for real, not mocked.
    """
    assert not hasattr(epy_papers, "__author__")
    info = get_suite_info()
    assert info["author"] == ""
