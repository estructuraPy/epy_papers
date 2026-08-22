"""Shared pytest fixtures.

``epy_papers`` is imported here -- before any test module -- so its
``_pin_system_icu()`` bootstrap runs ahead of every ``PySide6`` import.
Test files that import ``PySide6.QtWidgets`` at module level before
importing the package die with a DLL load error in conda environments
otherwise (conda's ``Library\\bin`` ICU shadows the Windows system ICU
that Qt links against); this mirrors epy_reports' conftest.py fix.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Force headless Qt before any QApplication is built (dialog/preview tests).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import epy_papers  # noqa: E402, F401 — must precede any PySide6 import (ICU pin)

_HERE = Path(__file__).parent

@pytest.fixture
def fixtures_dir() -> Path:
    """Return the test fixtures directory.

    The replication fixtures (``navarro_*.md`` / ``.bib``) live directly in
    ``tests/`` as siblings of ``test_replication.py``, their sole consumer
    (no ``tests/fixtures/`` folder — forbidden non-mirror layout).
    """
    return _HERE
