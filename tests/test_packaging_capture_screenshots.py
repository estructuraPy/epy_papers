"""Tests for ``epy_papers._core._packaging.capture_screenshots``.

Dev-only release tooling; nothing exercised it before. ``OUT`` is always
monkeypatched to a ``tmp_path``: the real one resolves to
``src/epy_papers/_config/_assets/screenshots`` -- INSIDE ``src/`` -- where
the real bundled manual screenshots live. A real capture would overwrite
them, which the task's "tests only, never touch src/" rule forbids.

``main()`` also builds a real ``PaperWindow``; ``QSettings`` is
monkeypatched the same way every app.py test does it, so this never
touches the real "ANM Ingeniería" registry scope, and the language is
always restored to English afterward -- ``i18n.set_language`` is global,
shared-process state every other test file assumes starts in English.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from epy_papers import app as app_module
from epy_papers._core import _i18n
from epy_papers._core._packaging import capture_screenshots as cs


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
    raise RuntimeError("capture_screenshots tests need a QApplication.")


@pytest.fixture(autouse=True)
def _restore_language():
    """``main()`` calls the real ``i18n.set_language("es")``; every other
    test file in the suite assumes English is the default, so this file
    always puts it back regardless of how the test finished.
    """
    yield
    _i18n.set_language("en")


# ---------------------------------------------------------------------------
# pump
# ---------------------------------------------------------------------------


def test_pump_spins_the_event_loop_for_at_least_the_requested_time(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
):
    calls: list[int] = []
    real_process_events = qapp.processEvents

    def _counting(*args, **kwargs):
        calls.append(1)
        return real_process_events(*args, **kwargs)

    monkeypatch.setattr(qapp, "processEvents", _counting)
    cs.pump(qapp, 30)
    assert calls  # processEvents was actually driven at least once


# ---------------------------------------------------------------------------
# grab_widget
# ---------------------------------------------------------------------------


def test_grab_widget_saves_a_nonempty_png(
    qapp: QApplication, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    widget = QWidget()
    widget.resize(120, 80)
    label = QLabel("hello", widget)
    label.resize(120, 80)
    path = tmp_path / "shot.png"

    cs.grab_widget(qapp, widget, path, settle=10)

    assert path.exists()
    assert path.stat().st_size > 0
    out = capsys.readouterr().out
    assert "shot.png" in out
    widget.deleteLater()


# ---------------------------------------------------------------------------
# capture_dialogs / capture_language / main -- full integration
# ---------------------------------------------------------------------------


@pytest.fixture
def window(qapp: QApplication, monkeypatch: pytest.MonkeyPatch):
    store: dict[str, Any] = {}
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    win = app_module.PaperWindow()
    yield win
    any_win: Any = win
    any_win._confirm_close = lambda _tab: True
    any_win.close()


def test_capture_dialogs_writes_both_dialog_screenshots(
    qapp: QApplication, window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cs, "OUT", tmp_path)
    cs.capture_dialogs(qapp, window, "")
    assert (tmp_path / "dlg_design_block.png").exists()
    assert (tmp_path / "dlg_theme_gallery.png").exists()


def test_capture_dialogs_suffix_names_the_language_variant(
    qapp: QApplication, window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cs, "OUT", tmp_path)
    cs.capture_dialogs(qapp, window, "_es")
    assert (tmp_path / "dlg_design_block_es.png").exists()
    assert (tmp_path / "dlg_theme_gallery_es.png").exists()


def test_capture_language_writes_the_editor_and_both_dialogs(
    qapp: QApplication, window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cs, "OUT", tmp_path)
    tab = window._current_tab()
    tab.set_initial_text("# A heading\n\nBody.\n", path=None)
    cs.capture_language(qapp, window, "")
    assert (tmp_path / "editor.png").exists()
    assert (tmp_path / "dlg_design_block.png").exists()


def test_capture_language_survives_a_validation_failure(
    qapp: QApplication,
    window,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """``_run_validation`` is wrapped in ``contextlib.suppress(Exception)``:
    a broken validator must not stop the manual's screenshots from being
    captured, since the manual is regenerated far more often than the
    validation pipeline changes.
    """
    monkeypatch.setattr(cs, "OUT", tmp_path)
    monkeypatch.setattr(
        window,
        "_run_validation",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    cs.capture_language(qapp, window, "")
    assert (tmp_path / "editor.png").exists()


def test_main_captures_screenshots_for_both_languages(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    store: dict[str, Any] = {}
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    monkeypatch.setattr(cs, "OUT", tmp_path)

    result = cs.main()

    assert result == 0
    assert (tmp_path / "editor.png").exists()
    assert (tmp_path / "editor_es.png").exists()
    assert (tmp_path / "dlg_design_block.png").exists()
    assert (tmp_path / "dlg_design_block_es.png").exists()
    assert (tmp_path / "dlg_theme_gallery.png").exists()
    assert (tmp_path / "dlg_theme_gallery_es.png").exists()
