"""Two lines that were covered by luck rather than on purpose.

The debounced re-render and autosave's clean-buffer early-return were being
reached only because some other test happened to let a QTimer fire before the
session ended. That is not coverage, it is timing: add a slow test anywhere in
the suite and they go dark, which is exactly what happened. Both are called
directly here.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def window(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])

    from epy_papers import app as app_module

    monkeypatch.setattr(
        app_module, "QSettings",
        lambda *_a, **_k: QSettings(str(tmp_path / "s.ini"),
                                    QSettings.Format.IniFormat))
    built = app_module.PaperWindow()
    # Accept the close unconditionally. A test that marks a tab dirty would
    # otherwise hit the window's "save changes?" prompt during teardown --
    # a modal dialog with nobody to answer it, which hangs the run. Measured:
    # both dirty-tab tests below hung until this was added.
    monkeypatch.setattr(type(built), "closeEvent",
                        lambda self, event: event.accept())
    yield built
    built.close()


class TestTheDebouncedRender:
    """``_render`` exists only to forward the debounce timer's tick. Leaving
    it to a real timer means the line is covered on a fast machine and dark on
    a loaded one."""

    def test_the_tick_forwards_to_a_render_that_preserves_position(
            self, window, monkeypatch):
        tab = window._current_tab()
        assert tab is not None

        seen: list[bool] = []

        def _render_now(self, *, preserve: bool = False) -> None:
            seen.append(preserve)

        monkeypatch.setattr(type(tab), "_render_now", _render_now)

        tab._render()

        assert seen == [True], (
            "the debounced tick must preserve the scroll position; a plain "
            "re-render jumps the reader back to the top on every keystroke"
        )


class TestAutosaveOnACleanBuffer:
    """Autosave must do nothing when there is nothing to save. Rewriting a
    clean buffer touches the file's mtime for no reason, and on a watched
    directory that is a change notification nobody made."""

    @staticmethod
    def _armed(window, monkeypatch, *, dirty: bool,
               save_succeeds: bool = False):
        """Autosave is OFF by default, so a test that forgets to arm it
        returns at the very first guard and proves nothing about the rest.
        That is exactly how this line stayed dark."""
        window.act_autosave.setChecked(True)
        window._exports_in_flight = 0
        tab = window._current_tab()
        assert tab is not None
        monkeypatch.setattr(type(tab), "dirty", property(lambda self: dirty))

        saved: list[bool] = []

        def _save(self) -> bool:
            saved.append(True)
            # Answering False stops _autosave_current at its next guard,
            # before the status-bar message. Letting it through instead hangs
            # the test: the window is never given an event loop in which to
            # retire the 3 s message timer.
            return save_succeeds

        monkeypatch.setattr(type(tab), "save", _save)
        return tab, saved

    def test_a_clean_tab_is_not_written(self, window, monkeypatch):
        _tab, saved = self._armed(window, monkeypatch, dirty=False)

        window._autosave_current()

        assert saved == [], "autosave wrote a buffer that had no changes"

    def test_a_dirty_tab_is_written(self, window, monkeypatch):
        """The counter-example: the early return is about the BUFFER, not
        about autosave being on. With it armed and real edits present, the
        save must happen."""
        _tab, saved = self._armed(window, monkeypatch, dirty=True)

        window._autosave_current()

        assert saved == [True]

    def test_autosave_switched_off_writes_nothing_however_dirty(
            self, window, monkeypatch):
        """And the guard that hid this line in the first place."""
        _tab, saved = self._armed(window, monkeypatch, dirty=True)
        window.act_autosave.setChecked(False)

        window._autosave_current()

        assert saved == []
