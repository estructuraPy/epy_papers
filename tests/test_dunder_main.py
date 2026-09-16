"""Tests for ``epy_papers.__main__`` (``python -m epy_papers``)."""

from __future__ import annotations

import runpy
import sys

import pytest


def test_import_reaches_the_guard_without_running_main():
    """A plain import must not launch anything: ``__name__`` is the
    module's dotted path here, never ``"__main__"``.
    """
    import epy_papers.__main__ as m

    assert hasattr(m, "main")


def test_run_as_main_invokes_app_main_and_exits_with_its_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """``runpy.run_module(..., run_name="__main__")`` re-executes the
    module in-process with ``__name__ == "__main__"``, so the guarded
    ``raise SystemExit(main())`` genuinely runs (and is traced) without
    spawning a subprocess or launching the real GUI.
    """
    monkeypatch.setattr(sys, "argv", ["epy_papers", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("epy_papers.__main__", run_name="__main__")
    assert exc_info.value.code == 0
    assert "epy_papers" in capsys.readouterr().out
