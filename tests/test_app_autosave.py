"""Autosave contract of the epy_papers window.

Every test says what breaks in the application if it fails. Windows are
built against an in-memory ``QSettings`` stand-in so no test touches the
real "ANM Ingeniería" registry scope, and ``closeEvent``'s modal save
prompt is bypassed at teardown because a modal dialog does not fail under
a headless run -- it hangs it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

from epy_papers import app as app_module
from epy_papers._core._latex import LatexMissingError

ORIGINAL = "# Draft\n\nBody.\n"


class _ScratchSettings:
    """In-memory stand-in for ``QSettings`` sharing one dict per test."""

    def __init__(self, store: dict[str, Any]) -> None:
        self._store = store

    def value(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def setValue(self, key: str, value: Any) -> None:  # noqa: N802 - Qt API name
        self._store[key] = value


class _NoEngine:
    """``Paper`` stand-in whose export always lacks a LaTeX engine."""

    def __init__(self, *_args: Any) -> None:
        pass

    def to_draft(self, *_args: Any, **_kwargs: Any) -> None:
        raise LatexMissingError("no engine")


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a module-scoped QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def store() -> dict[str, Any]:
    """The settings dict shared by every window of one test."""
    return {}


@pytest.fixture
def make_window(
    qapp: QApplication,
    store: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Callable[[], app_module.PaperWindow]]:
    """Build windows on the scratch settings; close them without prompts."""
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_args: _ScratchSettings(store)
    )
    windows: list[app_module.PaperWindow] = []

    def _make() -> app_module.PaperWindow:
        win = app_module.PaperWindow()
        windows.append(win)
        return win

    yield _make
    for win in windows:
        win._confirm_close = lambda _tab: True
        win.close()


def _open(win: app_module.PaperWindow, path: Path) -> Any:
    """Open ``path`` in a new tab, make it current and return the tab."""
    if not path.exists():
        path.write_text(ORIGINAL, encoding="utf-8")
    tab = win._create_tab()
    tab.load_file(path)
    win.tabs.setCurrentWidget(tab)
    return tab


def _edited(win: app_module.PaperWindow, path: Path) -> Any:
    """Open ``path`` with ``ORIGINAL`` on disk and a dirty edit on top."""
    path.write_text(ORIGINAL, encoding="utf-8")
    tab = _open(win, path)
    tab.editor.appendPlainText("edited")
    assert tab.dirty, "precondition: an edit marks the tab dirty"
    return tab


def test_autosave_off_by_default_writes_nothing(
    make_window: Callable[[], app_module.PaperWindow], tmp_path: Path
) -> None:
    """Off is the default and off means the timer never writes.

    If this fails a fresh install rewrites files the person never asked to
    save.
    """
    win = make_window()
    path = tmp_path / "paper.md"
    tab = _edited(win, path)
    assert not win.act_autosave.isChecked()
    assert not win._autosave_timer.isActive()
    win._autosave_current()
    assert path.read_text(encoding="utf-8") == ORIGINAL
    assert tab.dirty


def test_autosave_on_writes_dirty_tab_with_path(
    make_window: Callable[[], app_module.PaperWindow], tmp_path: Path
) -> None:
    """On, with a path and dirty: disk changes and the flag clears.

    If this fails the option is inert.
    """
    win = make_window()
    path = tmp_path / "paper.md"
    tab = _edited(win, path)
    win.act_autosave.setChecked(True)
    win._autosave_current()
    written = path.read_text(encoding="utf-8")
    assert written != ORIGINAL and written.endswith("edited")
    assert not tab.dirty


def test_autosave_untitled_never_opens_dialog(
    make_window: Callable[[], app_module.PaperWindow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A buffer without a path is skipped and no dialog opens.

    A fallback through ``_save_current`` raises here; in the app it would
    block the person typing behind a modal Save As every 30 s.
    """
    win = make_window()
    tab = win._create_tab()
    win.tabs.setCurrentWidget(tab)
    tab.editor.appendPlainText("edited")
    assert tab.dirty and tab.path is None

    def _no_dialog(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("a dialog opened")

    monkeypatch.setattr(app_module.QFileDialog, "getSaveFileName", _no_dialog)
    win.act_autosave.setChecked(True)
    win._autosave_current()
    assert tab.dirty


def test_autosave_skips_when_export_in_flight(
    make_window: Callable[[], app_module.PaperWindow], tmp_path: Path
) -> None:
    """With an export in flight the timer does not write; after, it does.

    If this fails a timer tick rewrites the paper while an export reads it.
    """
    win = make_window()
    path = tmp_path / "paper.md"
    _edited(win, path)
    win.act_autosave.setChecked(True)
    win._exports_in_flight = 1
    win._autosave_current()
    assert path.read_text(encoding="utf-8") == ORIGINAL
    win._exports_in_flight = 0
    win._autosave_current()
    written = path.read_text(encoding="utf-8")
    assert written != ORIGINAL and written.endswith("edited")


def test_exports_in_flight_covers_the_tinytex_offer(
    make_window: Callable[[], app_module.PaperWindow],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The counter is raised while the TinyTeX offer runs and 0 afterwards.

    The offer's progress dialog runs a nested event loop where the timer
    can fire: 0 there means a write mid-export; stuck at 1 after a declined
    or failed install means autosave silently dead for the session.
    """
    import epy_papers

    win = make_window()
    tab = _open(win, tmp_path / "paper.md")
    seen: list[int] = []

    def _decline() -> bool:
        seen.append(win._exports_in_flight)
        return False

    monkeypatch.setattr(epy_papers, "Paper", _NoEngine)
    monkeypatch.setattr(win, "_offer_install_latex", _decline)
    win._do_export(tab, tmp_path / "out.pdf", "pdf")
    assert seen == [1]
    assert win._exports_in_flight == 0


def test_exports_in_flight_returns_to_zero_after_failed_retry(
    make_window: Callable[[], app_module.PaperWindow],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Install accepted, retry fails: the error shows and the counter is 0.

    This is the error path only a ``finally`` covers; a decrement placed on
    the success path leaves autosave disabled after every failed export.
    """
    import epy_papers

    win = make_window()
    tab = _open(win, tmp_path / "paper.md")
    errors: list[str] = []
    monkeypatch.setattr(
        app_module.QMessageBox,
        "critical",
        lambda *args, **_kwargs: errors.append(str(args[1])),
    )
    monkeypatch.setattr(epy_papers, "Paper", _NoEngine)
    monkeypatch.setattr(win, "_offer_install_latex", lambda: True)
    win._do_export(tab, tmp_path / "out.pdf", "pdf")
    assert errors == ["Export PDF failed"]
    assert win._exports_in_flight == 0


def test_export_html_lowers_the_counter(
    make_window: Callable[[], app_module.PaperWindow],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The synchronous HTML export raises and lowers the counter too.

    Every export must take part: one that does not lets the timer write
    while it runs.
    """
    win = make_window()
    _open(win, tmp_path / "paper.md")
    out = tmp_path / "out.html"
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(out), "HTML (*.html)"),
    )
    win._export_html()
    assert out.exists()
    assert win._exports_in_flight == 0


def test_autosave_preference_persists(
    make_window: Callable[[], app_module.PaperWindow],
    store: dict[str, Any],
) -> None:
    """The choice survives reopening: a second window starts checked.

    ``trigger()`` is the user's click; it flips the box, persists the
    string and starts or stops the timer.
    """
    first = make_window()
    assert first._autosave_timer.interval() == app_module.AUTOSAVE_INTERVAL_MS
    first.act_autosave.trigger()
    assert store["autosave"] == "true"
    assert first._autosave_timer.isActive()

    second = make_window()
    assert second.act_autosave.isChecked()
    assert second._autosave_timer.isActive()

    first.act_autosave.trigger()
    assert store["autosave"] == "false"
    assert not first._autosave_timer.isActive()


def test_spanish_strings_exist() -> None:
    """Both new labels translate; a missing key shows English in Spanish."""
    from epy_papers._core._i18n import _ES

    assert _ES["Autosave"] == "Guardado automático"
    assert "{path}" in _ES["Autosaved: {path}"]
