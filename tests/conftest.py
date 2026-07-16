"""Shared pytest fixtures.

``conftest.py`` is auto-loaded by pytest and makes the tests directory
importable, so test modules can ``import _pandoc`` for the Pandoc guard.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Force headless Qt before any QApplication is built (dialog/preview tests).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

@pytest.fixture
def fixtures_dir() -> Path:
    """Return the test fixtures directory.

    The replication fixtures (``navarro_*.md`` / ``.bib``) live directly in
    ``tests/`` as siblings of ``test_replication.py``, their sole consumer
    (no ``tests/fixtures/`` folder — forbidden non-mirror layout).
    """
    return _HERE
