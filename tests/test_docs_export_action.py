"""The second rendering option, as a person meets it.

An action that exists, is offered when the engine can be reached, and
runs the render off the interface thread. The bridge and the dialog can
both be right while nothing in the window ever calls them.

Windows are built on an in-memory QSettings stand-in so no test touches
the real registry scope, and every modal is patched: headless, a modal
dialog does not fail, it hangs the run.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from epy_papers import app as app_module

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
    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        return instance
    if instance is None:
        return QApplication([])
    raise RuntimeError("these tests need a QApplication.")


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
    any_win: Any = win
    any_win._confirm_close = lambda _tab: True
    any_win.close()


def test_the_action_exists_and_is_in_the_export_menu(window) -> None:
    assert hasattr(window, "act_docs_export")
    titles = [action.text() for action in window.export_menu.actions()]
    assert "Export via epy_docs..." in titles


def test_it_sits_after_this_editors_own_exports(window) -> None:
    # ePy Papers builds a manuscript in a NAMED JOURNAL's shape; ePy
    # Docs builds the house document. A separator says they are not the
    # same kind of thing without a sentence.
    actions = list(window.export_menu.actions())
    docs = next(
        index
        for index, action in enumerate(actions)
        if action.text() == "Export via epy_docs..."
    )
    assert actions[docs - 1].isSeparator()


def test_it_is_offered_when_the_engine_can_be_reached(
    qapp, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Enablement is decided when the window is built, which is when ePy
    # Studio's hint is already in the environment.
    store: dict[str, Any] = {}
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    monkeypatch.setattr(app_module, "docs_available", lambda: True)
    win = app_module.PaperWindow()
    try:
        assert win.act_docs_export.isEnabled()
    finally:
        any_win: Any = win
        any_win._confirm_close = lambda _tab: True
        any_win.close()


def test_it_is_greyed_with_a_reason_when_it_cannot(
    qapp, monkeypatch: pytest.MonkeyPatch
) -> None:
    store: dict[str, Any] = {}
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    monkeypatch.setattr(app_module, "docs_available", lambda: False)
    win = app_module.PaperWindow()
    try:
        assert not win.act_docs_export.isEnabled()
        assert "epy-docs" in win.act_docs_export.toolTip()
    finally:
        any_win: Any = win
        any_win._confirm_close = lambda _tab: True
        any_win.close()


def test_an_unsaved_manuscript_is_asked_about_before_anything_opens(
    window, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The engine reads a FILE, so an unsaved buffer has nothing to give
    # it. Saving somebody's manuscript because they opened an export
    # dialog is not the export they asked for.
    from PySide6.QtWidgets import QMessageBox

    asked: list[str] = []

    def _decline(*args: object, **kwargs: object) -> object:
        asked.append("asked")
        return QMessageBox.StandardButton.Cancel

    monkeypatch.setattr(app_module.QMessageBox, "question", _decline)
    opened: list[str] = []
    from epy_papers._ui import docs_export_dialog as ded

    monkeypatch.setattr(
        ded.DocsExportDialog, "exec",
        lambda self: opened.append("opened") or QDialog.DialogCode.Rejected,
    )
    window._export_via_docs()
    assert asked == ["asked"]
    assert opened == []


def test_the_render_runs_off_the_interface_thread(
    window, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A render may take minutes and may start a child interpreter.
    # Doing it on the GUI thread freezes the window for the whole of it.
    from epy_papers._ui import docs_export_dialog as ded

    source = tmp_path / "articulo.md"
    source.write_text(SOURCE, encoding="utf-8")
    tab = window._create_tab()
    tab.load_file(source)
    window.tabs.setCurrentWidget(tab)

    monkeypatch.setattr(
        ded.DocsExportDialog, "exec",
        lambda self: QDialog.DialogCode.Accepted,
    )
    started: list[str] = []
    monkeypatch.setattr(
        ded._RenderWorker, "start", lambda self: started.append("started")
    )
    window._export_via_docs()
    assert started == ["started"]
    assert isinstance(window._docs_worker, ded._RenderWorker)


def test_the_engines_message_is_the_one_shown(
    window, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The library's own diagnosis is what a reader can act on; a generic
    # "export failed" sends them to the wrong place.
    shown: list[str] = []
    monkeypatch.setattr(
        app_module.QMessageBox,
        "critical",
        lambda *args, **kwargs: shown.append(args[2]),
    )
    window._on_docs_done_err("Quarto is not installed")
    assert shown
    assert "Quarto is not installed" in shown[0]


def test_success_says_where_the_documents_went(
    window, tmp_path: Path
) -> None:
    window._on_docs_done_ok(str(tmp_path / "out"))
    assert "out" in window.statusBar().currentMessage()
