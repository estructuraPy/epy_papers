"""The export runs off the GUI thread, and says so when it fails.

A LaTeX compile takes seconds to minutes. Run on the GUI thread it stops
the window repainting for that whole time: the application looks hung,
and a person who clicks it gets Windows offering to close it. These
tests pin that the work happens on another thread, that the counter
keeping autosave off an export returns to zero on every path including
the failing ones, and that a failed export is reported rather than
silent.

Windows are built on an in-memory QSettings stand-in so no test touches
the real "ANM Ingeniería" registry scope, and every modal is patched:
headless, a modal dialog does not fail, it hangs the run.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

import epy_papers
from epy_papers import app as app_module
from epy_papers._core._latex import LatexMissingError

SOURCE = "---\ntitle: A paper\n---\n\nBody.\n"


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
    """Provide a module-scoped QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> Iterator[app_module.PaperWindow]:
    """Build a window on scratch settings and close it without prompts."""
    store: dict[str, Any] = {}
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    win = app_module.PaperWindow()
    yield win
    win._confirm_close = lambda _tab: True
    win.close()


@pytest.fixture
def tab(window: app_module.PaperWindow, tmp_path: Path) -> Any:
    """Open one saved paper and make it the current tab."""
    path = tmp_path / "paper.md"
    path.write_text(SOURCE, encoding="utf-8")
    opened = window._create_tab()
    opened.load_file(path)
    window.tabs.setCurrentWidget(opened)
    return opened


def _no_modals(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record every modal instead of opening one; return the titles."""
    seen: list[str] = []
    for name in ("critical", "warning", "information"):
        monkeypatch.setattr(
            app_module.QMessageBox,
            name,
            staticmethod(lambda *args, **_k: seen.append(str(args[1]))),
        )
    return seen


class _RecordingPaper:
    """``Paper`` stand-in recording the thread its export ran on."""

    threads: list[int] = []
    raises: Exception | None = None
    calls = 0

    def __init__(self, *_args: Any) -> None:
        pass

    def to_draft(self, *_args: Any, **_kwargs: Any) -> None:
        type(self).threads.append(threading.get_ident())
        type(self).calls += 1
        if type(self).raises is not None:
            raise type(self).raises


@pytest.fixture
def paper(monkeypatch: pytest.MonkeyPatch) -> type[_RecordingPaper]:
    """Replace the exporter with one that records and can fail."""

    class _Paper(_RecordingPaper):
        threads: list[int] = []
        raises: Exception | None = None
        calls = 0

    monkeypatch.setattr(epy_papers, "Paper", _Paper)
    return _Paper


def test_the_export_does_not_run_on_the_gui_thread(
    window: app_module.PaperWindow,
    tab: Any,
    tmp_path: Path,
    paper: type[_RecordingPaper],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The whole point: a LaTeX compile on the GUI thread freezes the
    # window for its entire duration, and the application looks hung.
    _no_modals(monkeypatch)
    window._do_export(tab, tmp_path / "out.pdf", "pdf")
    assert paper.calls == 1
    assert paper.threads[0] != threading.get_ident()


def test_the_counter_is_raised_during_the_work_and_zero_after(
    window: app_module.PaperWindow,
    tab: Any,
    tmp_path: Path,
    paper: type[_RecordingPaper],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Autosave reads this counter before writing. Zero while an export
    # runs means a timer tick rewrites the file the export is reading.
    seen: list[int] = []
    original = window._run_off_thread

    def _watch(title: str, label: str, work: Callable[[], None]) -> Any:
        seen.append(window._exports_in_flight)
        return original(title, label, work)

    monkeypatch.setattr(window, "_run_off_thread", _watch)
    _no_modals(monkeypatch)
    window._do_export(tab, tmp_path / "out.pdf", "pdf")
    assert seen == [1]
    assert window._exports_in_flight == 0


def test_a_failed_export_reports_and_releases_the_counter(
    window: app_module.PaperWindow,
    tab: Any,
    tmp_path: Path,
    paper: type[_RecordingPaper],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An exception raised on a worker thread reaches no Qt slot on its
    # own: without this it is swallowed and the export looks successful.
    # A counter left at one silently disables autosave for the session.
    paper.raises = RuntimeError("pdflatex not happy")
    seen = _no_modals(monkeypatch)
    window._do_export(tab, tmp_path / "out.pdf", "pdf")
    assert seen == ["Export PDF failed"]
    assert "Export failed" in window.statusBar().currentMessage()
    assert window._exports_in_flight == 0


def test_a_missing_engine_offers_once_and_retries_once(
    window: app_module.PaperWindow,
    tab: Any,
    tmp_path: Path,
    paper: type[_RecordingPaper],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Retrying in a loop would reinstall TinyTeX on every failure and
    # never stop; not retrying at all would waste the install the person
    # just agreed to.
    paper.raises = LatexMissingError("no engine")
    offers: list[int] = []

    def _offer() -> bool:
        # Raises rather than returning, so a retry LOOP fails here
        # instead of reinstalling for ever and hanging the run.
        assert not offers, "TinyTeX was offered twice for one export"
        offers.append(1)
        return True

    monkeypatch.setattr(window, "_offer_install_latex", _offer)
    _no_modals(monkeypatch)
    window._do_export(tab, tmp_path / "out.pdf", "pdf")
    assert len(offers) == 1
    assert paper.calls == 2
    assert window._exports_in_flight == 0


def test_a_declined_install_stops_and_releases_the_counter(
    window: app_module.PaperWindow,
    tab: Any,
    tmp_path: Path,
    paper: type[_RecordingPaper],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # CONTROL for the path that returns early: saying no must not leave
    # the counter raised, which is the shape a `finally` protects.
    paper.raises = LatexMissingError("no engine")
    monkeypatch.setattr(window, "_offer_install_latex", lambda: False)
    _no_modals(monkeypatch)
    window._do_export(tab, tmp_path / "out.pdf", "pdf")
    assert paper.calls == 1
    assert window._exports_in_flight == 0


def test_a_second_export_is_refused_while_one_is_running(
    window: app_module.PaperWindow,
    tab: Any,
    tmp_path: Path,
    paper: type[_RecordingPaper],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The progress dialog runs a nested event loop, so the menu is still
    # reachable. Two compiles writing the same file is the failure.
    _no_modals(monkeypatch)
    window._exports_in_flight = 1
    window._do_export(tab, tmp_path / "out.pdf", "pdf")
    assert paper.calls == 0
    assert "already running" in window.statusBar().currentMessage()
    window._exports_in_flight = 0


def test_the_worker_callable_never_touches_a_widget(
    window: app_module.PaperWindow, qapp: QApplication
) -> None:
    # Qt objects belong to the thread that made them; calling into one
    # from a worker is undefined behaviour, not an error message.
    from PySide6.QtCore import QThread

    inside: list[bool] = []

    def _work() -> None:
        inside.append(QThread.currentThread() is not qapp.thread())

    assert window._run_off_thread("T", "L", _work) is None
    assert inside == [True]


def test_the_worker_returns_the_exception_it_caught(
    window: app_module.PaperWindow
) -> None:
    # CONTROL: a helper that swallowed the failure would make every
    # test above pass while every export reported success.
    boom = ValueError("no")

    def _work() -> None:
        raise boom

    assert window._run_off_thread("T", "L", _work) is boom
