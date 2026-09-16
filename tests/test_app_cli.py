"""CLI entry-point coverage for ``epy_papers.app``: ``main()`` and its
``--register`` / ``--set-default`` / `--unregister`` / ``--version`` /
bare-GUI branches not already exercised by ``test_winreg_assoc.py``
(which covers the plain ``--register`` / ``--unregister`` HKCU round
trip).

Every ``winreg_assoc`` call here is monkeypatched: these tests target
``app.py``'s own wiring (error handling, ``--as-default`` follow-up,
``--set-default``), not the registry helpers themselves, and a couple of
paths (``--as-default``'s Settings launch) would otherwise pop a real
Windows Settings window on the machine running the suite.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

from epy_papers import app as app_module


class _ScratchSettings:
    """In-memory stand-in for ``QSettings`` sharing one dict per test."""

    def __init__(self, store: dict[str, Any]) -> None:
        self._store = store

    def value(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def setValue(self, key: str, value: Any) -> None:  # noqa: N802 - Qt API
        self._store[key] = value


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        return instance
    if instance is None:
        return QApplication([])
    raise RuntimeError("these tests need a QApplication.")


@pytest.fixture(autouse=True)
def _scratch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every ``main()`` call in this file that reaches ``PaperWindow()``
    must use scratch settings, never the real "ANM Ingeniería" registry
    scope.
    """
    store: dict[str, Any] = {}
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )


# ---------------------------------------------------------------------------
# --register
# ---------------------------------------------------------------------------


def test_register_reports_a_runtime_error_from_winreg_assoc(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    from epy_papers._core import winreg_assoc

    monkeypatch.setattr(
        winreg_assoc,
        "register",
        lambda **_k: (_ for _ in ()).throw(RuntimeError("locked key")),
    )
    assert app_module.main(["--register"]) == 2
    assert "locked key" in capsys.readouterr().err


def test_register_as_default_prints_the_settings_hint_and_opens_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """``--as-default`` must print the extra hint AND call the Settings
    launcher exactly once -- mocked, so no real Settings window opens on
    the machine running the suite.
    """
    from epy_papers._core import winreg_assoc

    monkeypatch.setattr(
        winreg_assoc, "register", lambda **_k: ["registered: X"]
    )
    opened: list[str] = []
    monkeypatch.setattr(
        winreg_assoc,
        "open_default_apps_settings",
        lambda: opened.append("opened") or True,
    )
    assert app_module.main(["--register", "--as-default"]) == 0
    out = capsys.readouterr().out
    assert "Default apps" in out
    assert opened == ["opened"]


def test_register_without_as_default_never_opens_settings(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """Counter-example: plain ``--register`` must not touch Settings at
    all -- the hint and the launch are both gated on ``--as-default``.
    """
    from epy_papers._core import winreg_assoc

    monkeypatch.setattr(
        winreg_assoc, "register", lambda **_k: ["registered: X"]
    )
    opened: list[str] = []
    monkeypatch.setattr(
        winreg_assoc,
        "open_default_apps_settings",
        lambda: opened.append("opened") or True,
    )
    assert app_module.main(["--register"]) == 0
    assert opened == []


# ---------------------------------------------------------------------------
# --set-default
# ---------------------------------------------------------------------------


def test_set_default_success(monkeypatch: pytest.MonkeyPatch):
    from epy_papers._core import winreg_assoc

    monkeypatch.setattr(
        winreg_assoc, "open_default_apps_settings", lambda: True
    )
    assert app_module.main(["--set-default"]) == 0


def test_set_default_failure_reports_manual_instructions(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    from epy_papers._core import winreg_assoc

    monkeypatch.setattr(
        winreg_assoc, "open_default_apps_settings", lambda: False
    )
    assert app_module.main(["--set-default"]) == 2
    assert "Settings -> Apps" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# --unregister
# ---------------------------------------------------------------------------


def test_unregister_reports_a_runtime_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    from epy_papers._core import winreg_assoc

    monkeypatch.setattr(
        winreg_assoc,
        "unregister",
        lambda: (_ for _ in ()).throw(RuntimeError("no such key")),
    )
    assert app_module.main(["--unregister"]) == 2
    assert "no such key" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# --version
# ---------------------------------------------------------------------------


def test_version_prints_the_installed_version(
    capsys: pytest.CaptureFixture[str],
):
    import epy_papers

    assert app_module.main(["--version"]) == 0
    assert epy_papers.__version__ in capsys.readouterr().out


def test_version_falls_back_when_the_import_is_broken(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """Defensive fallback: if the version symbol itself cannot be read,
    ``--version`` still exits 0 with a placeholder rather than crashing
    the one command a broken install still needs to answer.
    """
    import epy_papers

    monkeypatch.delattr(epy_papers, "__version__")
    assert app_module.main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Bare GUI launch (no flags): reuses whatever QApplication this session
# already created. The "no QApplication yet" / "bare QCoreApplication"
# branches in main() are a first-process-only concern -- see the report
# for why they are not exercised here.
# ---------------------------------------------------------------------------


def test_main_with_no_flags_builds_a_window_and_opens_given_files(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    opened: list[Any] = []
    monkeypatch.setattr(
        app_module.PaperWindow, "open_path", lambda self, p: opened.append(p)
    )
    monkeypatch.setattr(app_module.PaperWindow, "show", lambda self: None)
    paper = tmp_path / "existing.md"
    paper.write_text("# Body\n", encoding="utf-8")
    missing = tmp_path / "missing.md"
    assert app_module.main([str(paper), str(missing)]) == 0
    assert opened == [paper]


def test_main_with_no_flags_reuses_the_existing_qapplication(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
):
    calls: list[str] = []
    monkeypatch.setattr(
        QApplication, "exec", lambda self: calls.append("exec") or 0
    )
    monkeypatch.setattr(app_module.PaperWindow, "show", lambda self: None)
    assert app_module.main([]) == 0
    assert calls == ["exec"]


def test_dunder_main_guard_runs_main_and_exits_with_its_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """Covers ``if __name__ == "__main__": main()`` at the bottom of
    app.py -- the one line a plain import can never reach.

    ``runpy.run_module(..., run_name="__main__")`` re-executes the module
    body in-process (unlike a subprocess, which coverage would not
    attribute to this run at all) with ``__name__`` set to
    ``"__main__"``, so the guard's body genuinely runs and is traced.
    ``--version`` is used so the run exits immediately after printing,
    never reaching the GUI bootstrap.
    """
    import runpy

    monkeypatch.setattr(sys, "argv", ["epy_papers", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("epy_papers.app", run_name="__main__")
    assert exc_info.value.code == 0
    assert "epy_papers" in capsys.readouterr().out
