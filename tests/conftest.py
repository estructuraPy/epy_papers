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


@pytest.fixture(autouse=True, scope="session")
def _never_open_a_browser():
    """No test may open a browser tab, whatever it passes for display.

    Plotly's ``fig.show()`` outside a notebook does not draw anything locally:
    it starts an ephemeral HTTP server on 127.0.0.1, points the default
    browser at it, and blocks until that one request arrives. A test run that
    opens tabs is a test run nobody can leave unattended.

    Installed in EVERY repo rather than only where a scan found display calls.
    Going by scan is what let the tabs come back twice: a regex missed six
    repos because it could not cross a line end, and the AST scan that
    replaced it still only sees a display keyword passed as a literal ``True``
    -- one passed positionally, through a variable or from a parametrize list
    is invisible to both. The fixture is inert where nothing displays, so
    predicting which repos need it buys nothing and costs a recurrence.

    The branch under test still executes and still counts as covered; it just
    cannot reach a browser. This is the half the housekeeper's Rule 14 audits
    cannot see -- they read library ``src/``, and this lives in ``tests/``.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        yield
        return

    original = go.Figure.show
    go.Figure.show = lambda self, *args, **kwargs: None
    try:
        yield
    finally:
        go.Figure.show = original
