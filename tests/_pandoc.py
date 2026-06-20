"""Pandoc availability guard shared by render-dependent tests."""

from __future__ import annotations

import pytest

try:
    import pypandoc
except ImportError:  # pragma: no cover - env guard
    pypandoc = None


def pandoc_available() -> bool:
    """Whether a usable Pandoc binary is reachable via pypandoc."""
    if pypandoc is None:
        return False
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        return False
    return True


needs_pandoc = pytest.mark.skipif(
    not pandoc_available(), reason="Pandoc is not installed"
)
