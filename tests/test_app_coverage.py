"""Coverage of ``epy_papers.app`` behaviour not already exercised.

``test_app_helpers.py``, ``test_app_autosave.py`` and
``test_app_export_async.py`` cover the public API, the autosave contract
and the threaded-export contract. This file covers everything else that
was still missed at ~61% statement coverage: the manual-text placeholder
resolver, the journal combo/catalog wiring, the "Add Journal" dialog, the
validation dock's own branches, theme application, the About/manual/
design-block/theme-gallery dialog openers, tab lifecycle (create, close,
reload, drag & drop, closeEvent), Save/Save As, and the
``_run_off_thread`` worker body itself.

Windows are always built on an in-memory ``QSettings`` stand-in (never the
real "ANM Ingeniería" registry scope) and every modal is patched: headless,
a modal dialog does not fail, it hangs the run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QMessageBox,
    QWidget,
)

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
    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        return instance
    if instance is None:
        return QApplication([])
    raise RuntimeError("these tests need a QApplication.")


@pytest.fixture
def store() -> dict[str, Any]:
    return {}


@pytest.fixture
def window(qapp: QApplication, store, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    win = app_module.PaperWindow()
    yield win
    any_win: Any = win
    any_win._confirm_close = lambda _tab: True
    any_win.close()


def _no_modals(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Record every modal instead of opening one; return (kind, text)."""
    seen: list[tuple[str, str]] = []
    for name in ("critical", "warning", "information"):
        monkeypatch.setattr(
            app_module.QMessageBox,
            name,
            staticmethod(
                lambda *args, _n=name, **_k: seen.append((_n, str(args[2])))
                or QMessageBox.StandardButton.Ok
            ),
        )
    return seen


def _sync_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every QThread run its ``run()`` synchronously, still traced.

    ``QThread.start()`` hands ``run()`` to a native OS thread that Qt spins
    up outside Python's ``threading`` module -- coverage.py only
    auto-installs its line tracer on frames entered through that module's
    own bootstrap, so statements inside ``run()`` are invisible to it no
    matter how thoroughly a test exercises them (proven with a standalone
    probe: a trivial ``QThread.run()`` body never appears in
    ``coverage.get_data()`` even though it demonstrably executes).

    Deferring the call by one tick with ``QTimer.singleShot`` (rather than
    calling ``run()`` immediately) matters too: ``_run_off_thread`` shows a
    ``QProgressDialog`` and relies on the worker's ``done`` signal to close
    it from *inside* that dialog's ``exec()`` loop. Calling ``run()``
    synchronously before ``exec()`` starts fires ``done`` -> ``close()`` on
    a dialog that is not shown yet and is not running a loop, so nothing
    ever ends it and ``exec()`` hangs (reproduced while building this
    fixture). Posting it instead lets ``exec()``'s own loop pick up the
    timer and close itself correctly.
    """
    monkeypatch.setattr(
        QThread,
        "start",
        lambda self, *_a, **_k: QTimer.singleShot(0, self.run),
    )


# ---------------------------------------------------------------------------
# _load_manual_text
# ---------------------------------------------------------------------------


class _FakeTraversable:
    """Minimal ``importlib.resources`` Traversable double.

    Tracks the joined path parts so ``is_file()``/``read_text()`` can be
    driven per (subdir, name) pair -- the real bundled assets always
    resolve, so hitting the "missing image" / "resolution failed" branches
    in ``_load_manual_text`` requires a fake resource tree instead of
    deleting real files under ``src/``.
    """

    def __init__(
        self, base: dict[str, Any], parts: tuple[str, ...] = ()
    ) -> None:
        self._base = base
        self._parts = parts

    def joinpath(self, part: str) -> _FakeTraversable:
        return _FakeTraversable(self._base, (*self._parts, part))

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._base["text"]

    def is_file(self) -> bool:
        path = "/".join(self._parts)
        raiser = self._base["raise_on"].get(path)
        if raiser is not None:
            raise raiser
        return path not in self._base["missing"]

    def __str__(self) -> str:
        return "C:/fake_assets/" + "/".join(self._parts)


def test_load_manual_text_returns_empty_string_on_read_failure():
    """A filename with no real bundled resource is reported as "", not a
    crash: the caller (``_open_manual``) turns "" into a warning dialog.
    """
    text = app_module._load_manual_text("this_file_does_not_exist.md")
    assert text == ""


def test_load_manual_text_prefers_the_spanish_screenshot_when_present(
    monkeypatch: pytest.MonkeyPatch,
):
    """``*_es.md`` swaps every screenshot placeholder for its ``_es`` twin.

    Real assets always ship both variants, so exercising the "found"
    branch of that lookup needs the fake resource tree.
    """
    base = {
        "text": "__SHOT_EDITOR__ __EPY_LOGO__",
        "missing": set(),
        "raise_on": {},
    }
    monkeypatch.setattr(
        app_module.importlib.resources,
        "files",
        lambda _pkg: _FakeTraversable(base),
    )
    text = app_module._load_manual_text("welcome_es.md")
    assert "editor_es.png" in text
    assert "__SHOT_EDITOR__" not in text
    assert "branding/epy_papers.png" in text


def test_load_manual_text_falls_back_when_spanish_screenshot_is_absent(
    monkeypatch: pytest.MonkeyPatch,
):
    """Counter-example: no ``_es`` variant on disk keeps the English name."""
    base = {
        "text": "__SHOT_EDITOR__",
        "missing": {"screenshots/editor_es.png"},
        "raise_on": {},
    }
    monkeypatch.setattr(
        app_module.importlib.resources,
        "files",
        lambda _pkg: _FakeTraversable(base),
    )
    text = app_module._load_manual_text("welcome_es.md")
    assert "screenshots/editor.png" in text
    assert "editor_es.png" not in text


def test_load_manual_text_swallows_oserror_probing_the_spanish_variant(
    monkeypatch: pytest.MonkeyPatch,
):
    """A resource backend that raises OSError on the *_es probe itself
    (not on the final resolution) must not abort the whole manual load.
    """
    base = {
        "text": "__SHOT_EDITOR__",
        "missing": set(),
        "raise_on": {"screenshots/editor_es.png": OSError("no such resource")},
    }
    monkeypatch.setattr(
        app_module.importlib.resources,
        "files",
        lambda _pkg: _FakeTraversable(base),
    )
    text = app_module._load_manual_text("welcome_es.md")
    # The probe failed, so the base (English) name is kept and resolves.
    assert "screenshots/editor.png" in text


def test_load_manual_text_drops_a_missing_image_placeholder_entirely(
    monkeypatch: pytest.MonkeyPatch,
):
    """A placeholder whose image cannot be found is removed, image and all.

    Pandoc aborts on a src that does not exist, so leaving the
    placeholder (or a broken ``![]()`` around it) in the text would break
    every export of a manual tab that hit this path for real.
    """
    base = {
        "text": "before ![caption](__SHOT_EDITOR__){.figure} after "
        "__SHOT_EDITOR__ tail",
        "missing": {"screenshots/editor.png"},
        "raise_on": {},
    }
    monkeypatch.setattr(
        app_module.importlib.resources,
        "files",
        lambda _pkg: _FakeTraversable(base),
    )
    text = app_module._load_manual_text("welcome.md")
    assert "__SHOT_EDITOR__" not in text
    assert "![caption]" not in text
    assert text == "before  after  tail"


def test_load_manual_text_treats_a_resolution_error_as_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    """``is_file()`` raising while resolving the final URI is caught too,
    not just the ``_es`` probe -- both try/excepts guard the same failure
    mode against a different call site.
    """
    base = {
        "text": "__EPY_LOGO__",
        "missing": set(),
        "raise_on": {"branding/epy_papers.png": ValueError("bad path")},
    }
    monkeypatch.setattr(
        app_module.importlib.resources,
        "files",
        lambda _pkg: _FakeTraversable(base),
    )
    text = app_module._load_manual_text("welcome.md")
    assert "__EPY_LOGO__" not in text
    assert text == ""


# ---------------------------------------------------------------------------
# __init__: saved language restore
# ---------------------------------------------------------------------------


def test_a_saved_non_english_language_is_restored_on_launch(
    qapp: QApplication, store: dict[str, Any], monkeypatch: pytest.MonkeyPatch
):
    """A window built with ``language=es`` already saved switches live.

    If this regresses, every user who chose Spanish sees English again on
    the next launch, silently.
    """
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    from epy_papers._core import _i18n

    monkeypatch.setattr(_i18n, "_lang", "en")
    monkeypatch.setattr(_i18n, "_observers", [])
    store["language"] = "es"
    win = app_module.PaperWindow()
    try:
        assert _i18n.current_language() == "es"
        assert win.lang_actions["es"].isChecked()
    finally:
        any_win: Any = win
        any_win._confirm_close = lambda _tab: True
        any_win.close()


# ---------------------------------------------------------------------------
# Theme actions / menu guards
# ---------------------------------------------------------------------------


def test_build_theme_actions_is_a_noop_when_themes_are_unavailable(
    window, monkeypatch: pytest.MonkeyPatch
):
    """The guard other tests can never see: no epy_reports themes present.

    Counter-example lives in every other test in this suite -- they all
    build with themes available and get a populated ``theme_group``.
    """
    monkeypatch.setattr(app_module, "_THEMES_AVAILABLE", False)
    before = window.theme_group
    window._build_theme_actions()
    assert window.theme_group is before  # untouched: returned immediately


def test_populate_theme_menu_is_a_noop_without_a_theme_submenu():
    """A window that never built ``theme_sub`` (themes disabled at
    construction) must not crash when asked to repopulate it.
    """
    from types import SimpleNamespace

    fake = SimpleNamespace(theme_group=None)
    # Must not raise AttributeError reaching for `.theme_sub`.
    app_module.PaperWindow._populate_theme_menu(fake)


# ---------------------------------------------------------------------------
# Journal combo / catalog
# ---------------------------------------------------------------------------


def test_journal_combo_survives_a_broken_catalog(
    qapp: QApplication, store: dict[str, Any], monkeypatch: pytest.MonkeyPatch
):
    """``available_journals()`` raising must not stop the window opening.

    A corrupted user catalog (see ``load_user_journals``'s own warning
    path) must degrade to an empty combo, not an unhandled exception in
    the constructor.
    """
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    import epy_papers

    monkeypatch.setattr(
        epy_papers,
        "available_journals",
        lambda: (_ for _ in ()).throw(RuntimeError("catalog corrupted")),
    )
    win = app_module.PaperWindow()
    try:
        assert win._journal_combo.count() == 0
    finally:
        any_win: Any = win
        any_win._confirm_close = lambda _tab: True
        any_win.close()


def test_journal_combo_restores_the_saved_selection(
    qapp: QApplication, store: dict[str, Any], monkeypatch: pytest.MonkeyPatch
):
    """A previously chosen journal is pre-selected, not reset to the first."""
    from epy_papers import available_journals

    journals = available_journals()
    target_id = journals[-1][0]
    monkeypatch.setattr(
        app_module, "QSettings", lambda *_a: _ScratchSettings(store)
    )
    store["journal_id"] = target_id
    win = app_module.PaperWindow()
    try:
        assert win._current_journal_id() == target_id
    finally:
        any_win: Any = win
        any_win._confirm_close = lambda _tab: True
        any_win.close()


def test_current_profile_is_none_with_no_journal_selected(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(window, "_current_journal_id", lambda: "")
    assert window._current_profile() is None


def test_current_profile_is_none_when_the_lookup_raises(
    window, monkeypatch: pytest.MonkeyPatch
):
    """An id present in the combo but gone from the catalog degrades to
    None rather than propagating a KeyError into the constructor/UI code.
    """
    import epy_papers

    monkeypatch.setattr(window, "_current_journal_id", lambda: "ghost-id")
    monkeypatch.setattr(
        epy_papers,
        "journal_profile",
        lambda _jid: (_ for _ in ()).throw(KeyError("ghost-id")),
    )
    assert window._current_profile() is None


def test_apply_journal_to_tabs_pushes_the_profile_to_every_open_tab(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab_a = window._create_tab()
    tab_a.load_file(_write(tmp_path / "a.md"))
    tab_b = window._create_tab()
    tab_b.load_file(_write(tmp_path / "b.md"))

    seen: list[Any] = []
    monkeypatch.setattr(
        tab_a, "set_journal", lambda profile: seen.append(("a", profile))
    )
    monkeypatch.setattr(
        tab_b, "set_journal", lambda profile: seen.append(("b", profile))
    )
    profile = {"name": "Test Journal"}
    monkeypatch.setattr(window, "_current_profile", lambda: profile)
    window._apply_journal_to_tabs()
    assert ("a", profile) in seen
    assert ("b", profile) in seen


def test_on_journal_changed_persists_reformats_and_revalidates(
    window, store: dict[str, Any], monkeypatch: pytest.MonkeyPatch
):
    calls: list[str] = []
    monkeypatch.setattr(
        window, "_apply_journal_to_tabs", lambda: calls.append("apply")
    )
    monkeypatch.setattr(window, "_run_validation", lambda: calls.append("run"))
    monkeypatch.setattr(window, "_current_journal_id", lambda: "some-id")
    window._on_journal_changed()
    assert store["journal_id"] == "some-id"
    assert calls == ["apply", "run"]


def test_refresh_journal_combo_rebuilds_and_keeps_the_selection(
    window,
):
    from epy_papers import available_journals

    journals = available_journals()
    target_id = journals[-1][0]
    window._refresh_journal_combo(select_id=target_id)
    assert window._current_journal_id() == target_id


def test_refresh_journal_combo_survives_a_broken_catalog_mid_session(
    window, monkeypatch: pytest.MonkeyPatch
):
    """Rebuilding after a catalog-write failure must not crash the app."""
    import epy_papers

    monkeypatch.setattr(
        epy_papers,
        "available_journals",
        lambda: (_ for _ in ()).throw(RuntimeError("disk full")),
    )
    window._refresh_journal_combo()
    assert window._journal_combo.count() == 0


def _write(path: Path, text: str = SOURCE) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# "Add Journal" dialog
# ---------------------------------------------------------------------------


def _mock_new_journal_exec(
    monkeypatch: pytest.MonkeyPatch,
    *,
    accept: bool,
    jid: str = "",
    name: str = "",
) -> None:
    def _fake_exec(self: QDialog) -> QDialog.DialogCode:
        if accept:
            fields = self.findChildren(QLineEdit)
            fields[0].setText(jid)
            fields[1].setText(name)
            return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(QDialog, "exec", _fake_exec)


def test_new_journal_rejected_dialog_adds_nothing(
    window, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv(
        "EPY_PAPERS_USER_JOURNALS", str(tmp_path / "journals.json")
    )
    before = window._journal_combo.count()
    _mock_new_journal_exec(monkeypatch, accept=False)
    window._new_journal()
    assert window._journal_combo.count() == before
    assert not (tmp_path / "journals.json").exists()


def test_new_journal_requires_id_and_name(
    window, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv(
        "EPY_PAPERS_USER_JOURNALS", str(tmp_path / "journals.json")
    )
    seen = _no_modals(monkeypatch)
    _mock_new_journal_exec(monkeypatch, accept=True)  # empty id/name
    window._new_journal()
    assert seen and "required" in seen[0][1]
    assert not (tmp_path / "journals.json").exists()


def test_new_journal_success_adds_selects_and_reports(
    window, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """The happy path: catalog gains the entry, combo selects it, and the
    status bar names it -- the counter-example to the two guards above.
    """
    catalog = tmp_path / "journals.json"
    monkeypatch.setenv("EPY_PAPERS_USER_JOURNALS", str(catalog))
    _mock_new_journal_exec(
        monkeypatch, accept=True, jid="my-new-journal", name="My New Journal"
    )
    window._new_journal()
    assert catalog.exists()
    assert window._current_journal_id() == "my-new-journal"
    assert "My New Journal" in window.statusBar().currentMessage()


def test_new_journal_reports_a_write_failure(
    window, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """A catalog that cannot be written shows the error, not a crash."""
    import epy_papers

    monkeypatch.setenv(
        "EPY_PAPERS_USER_JOURNALS", str(tmp_path / "journals.json")
    )
    seen = _no_modals(monkeypatch)
    monkeypatch.setattr(
        epy_papers,
        "add_journal",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("disk full")),
    )
    _mock_new_journal_exec(
        monkeypatch, accept=True, jid="x", name="X Journal"
    )
    window._new_journal()
    assert any("disk full" in text for _kind, text in seen)


# ---------------------------------------------------------------------------
# Validation dock
# ---------------------------------------------------------------------------


def test_run_validation_reports_no_issues_found(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import epy_papers

    class _Clean:
        def __init__(self, *_a):
            pass

        def validate(self, _jid):
            return []

    monkeypatch.setattr(epy_papers, "Paper", _Clean)
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "clean.md"))
    window.tabs.setCurrentWidget(tab)
    window._run_validation()
    assert window._validation_list.count() == 1
    assert "No issues found" in window._validation_list.item(0).text()


def test_run_validation_reports_a_raised_exception(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A validator that blows up (bad profile, bad manuscript) shows the
    error in the dock rather than crashing tab-switch/journal-change.
    """
    import epy_papers

    monkeypatch.setattr(
        epy_papers,
        "Paper",
        lambda *_a: (_ for _ in ()).throw(RuntimeError("bad manuscript")),
    )
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "broken.md"))
    window.tabs.setCurrentWidget(tab)
    window._run_validation()
    assert window._validation_list.count() == 1
    assert "bad manuscript" in window._validation_list.item(0).text()


def test_run_validation_skips_with_no_journal_selected(window, tmp_path: Path):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    window._journal_combo.setCurrentIndex(-1)
    window._run_validation()
    assert window._validation_list.count() == 0


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------


def test_apply_theme_is_a_noop_when_themes_are_unavailable(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(app_module, "_THEMES_AVAILABLE", False)
    window._apply_theme("corporate")  # must not raise


def test_apply_theme_swallows_an_unknown_theme_id(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        app_module._themes,
        "get",
        lambda _tid: (_ for _ in ()).throw(KeyError("no such theme")),
    )
    window._apply_theme("not-a-real-theme")  # must not raise


def test_apply_theme_swallows_a_palette_application_failure(
    window, monkeypatch: pytest.MonkeyPatch
):
    """A theme that fails to apply (bad QSS) must still mark the radio
    action checked rather than leave the menu out of sync.
    """
    monkeypatch.setattr(
        app_module._themes,
        "apply_palette",
        lambda *_a: (_ for _ in ()).throw(RuntimeError("bad palette")),
    )
    theme_id = next(iter(app_module._themes.THEMES))
    window._apply_theme(theme_id)
    assert window.theme_actions[theme_id].isChecked()


def test_apply_theme_without_persist_does_not_touch_settings(
    window, store: dict[str, Any]
):
    store.pop("theme", None)
    theme_id = next(iter(app_module._themes.THEMES))
    window._apply_theme(theme_id, persist=False)
    assert "theme" not in store


def test_open_theme_gallery_is_a_noop_when_themes_are_unavailable(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(app_module, "_THEMES_AVAILABLE", False)
    window._open_theme_gallery()  # must not raise / open anything


def test_open_theme_gallery_rejected_leaves_the_theme_unchanged(
    window, store: dict[str, Any], monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._ui.theme_gallery_dialog import ThemeGalleryDialog

    before = store.get("theme")
    monkeypatch.setattr(
        ThemeGalleryDialog, "exec", lambda self: QDialog.DialogCode.Rejected
    )
    window._open_theme_gallery()
    assert store.get("theme") == before


def test_open_theme_gallery_accepted_applies_the_chosen_theme(
    window, monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._ui.theme_gallery_dialog import ThemeGalleryDialog

    theme_id = next(iter(app_module._themes.THEMES))
    monkeypatch.setattr(
        ThemeGalleryDialog, "exec", lambda self: QDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(
        ThemeGalleryDialog, "selected_theme_id", lambda self: theme_id
    )
    window._open_theme_gallery()
    assert window.theme_actions[theme_id].isChecked()


def test_open_design_block_picker_rejected_inserts_nothing(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._ui.design_block_dialog import DesignBlockDialog

    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    before = tab.text()
    monkeypatch.setattr(
        DesignBlockDialog, "exec", lambda self: QDialog.DialogCode.Rejected
    )
    window._open_design_block_picker()
    assert tab.text() == before


def test_open_design_block_picker_accepted_inserts_the_chosen_block(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._ui.design_block_dialog import DesignBlockDialog

    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    monkeypatch.setattr(
        DesignBlockDialog, "exec", lambda self: QDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(
        DesignBlockDialog, "selected_kind", lambda self: "stat"
    )
    window._open_design_block_picker()
    assert tab.text() != SOURCE  # something was inserted


# ---------------------------------------------------------------------------
# i18n retranslation
# ---------------------------------------------------------------------------


def test_retranslate_ui_relabels_captured_actions_and_menus(
    window, monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._core import _i18n

    monkeypatch.setattr(_i18n, "_lang", "en")
    monkeypatch.setattr(_i18n, "_observers", [window._retranslate_ui])
    try:
        _i18n.set_language("es")
        assert window.act_save.text() == "Guardar"
        assert window.file_menu.title() == "&Archivo"
        assert window._journal_label.text().startswith("Revista:")
        assert window._validate_btn.text() == "Validar"
        assert window.lang_actions["es"].isChecked()
    finally:
        _i18n.set_language("en")


def test_set_language_persists_and_switches_live(
    window, store: dict[str, Any], monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._core import _i18n

    monkeypatch.setattr(_i18n, "_lang", "en")
    monkeypatch.setattr(_i18n, "_observers", [])
    window._set_language("es")
    assert store["language"] == "es"
    assert _i18n.current_language() == "es"


# ---------------------------------------------------------------------------
# _on_active_tab
# ---------------------------------------------------------------------------


def test_on_active_tab_is_a_noop_with_no_current_tab(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(window, "_current_tab", lambda: None)
    window._on_active_tab("toggle_bold")  # must not raise


def test_on_active_tab_forwards_to_the_named_method_with_args(
    window, tmp_path: Path
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    calls: list[tuple[str, ...]] = []
    tab.insert_disclosure = lambda kind: calls.append(
        ("insert_disclosure", kind)
    )
    window._on_active_tab("insert_disclosure", "ai")
    assert calls == [("insert_disclosure", "ai")]


def test_on_active_tab_ignores_an_unknown_method_name(window, tmp_path: Path):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    window._on_active_tab("this_method_does_not_exist")  # must not raise


# ---------------------------------------------------------------------------
# Export menu handlers (dialog wiring, as opposed to the export machinery
# already covered by test_app_export_async.py)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "opener,fmt",
    [
        ("_export_docx", "docx"),
        ("_export_latex", "tex"),
        ("_export_pdf", "pdf"),
        ("_export_html", "html"),
    ],
)
def test_export_action_is_a_noop_with_no_current_tab(
    window, monkeypatch: pytest.MonkeyPatch, opener: str, fmt: str
):
    monkeypatch.setattr(window, "_current_tab", lambda: None)
    called: list[Any] = []
    monkeypatch.setattr(window, "_do_export", lambda *a: called.append(a))
    getattr(window, opener)()
    assert called == []


@pytest.mark.parametrize(
    "opener,fmt",
    [
        ("_export_docx", "docx"),
        ("_export_latex", "tex"),
        ("_export_pdf", "pdf"),
    ],
)
def test_export_action_cancelled_dialog_does_not_export(
    window,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    opener: str,
    fmt: str,
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        lambda *_a, **_k: ("", ""),
    )
    called: list[Any] = []
    monkeypatch.setattr(window, "_do_export", lambda *a: called.append(a))
    getattr(window, opener)()
    assert called == []


@pytest.mark.parametrize(
    "opener,fmt,suffix",
    [
        ("_export_docx", "docx", ".docx"),
        ("_export_latex", "tex", ".tex"),
        ("_export_pdf", "pdf", ".pdf"),
    ],
)
def test_export_action_adds_the_missing_suffix_and_delegates(
    window,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    opener: str,
    fmt: str,
    suffix: str,
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    target = tmp_path / "draft"  # no suffix on purpose
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        lambda *_a, **_k: (str(target), ""),
    )
    called: list[Any] = []
    monkeypatch.setattr(
        window, "_do_export", lambda t, path, f: called.append((t, path, f))
    )
    getattr(window, opener)()
    assert len(called) == 1
    _tab, path, got_fmt = called[0]
    assert path == target.with_suffix(suffix)
    assert got_fmt == fmt


def test_export_html_cancelled_dialog_does_not_export(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        lambda *_a, **_k: ("", ""),
    )
    window._export_html()  # must not raise / must not write anything


def test_export_html_adds_the_missing_suffix(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    target = tmp_path / "draft_no_suffix"
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        lambda *_a, **_k: (str(target), ""),
    )
    window._export_html()
    assert target.with_suffix(".html").exists()


def test_export_html_reports_a_write_failure(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    out = tmp_path / "sub" / "out.html"  # parent dir absent -> write fails
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        lambda *_a, **_k: (str(out), ""),
    )
    seen = _no_modals(monkeypatch)
    window._export_html()
    assert seen and seen[0][0] == "critical"
    assert not out.exists()
    assert window._exports_in_flight == 0


# ---------------------------------------------------------------------------
# _run_off_thread's worker body, _do_export's _write closure, and
# _offer_install_latex's _install closure -- all run inside QThread.run()
# and are only traceable with QThread.start patched (see _sync_thread).
# ---------------------------------------------------------------------------


def test_run_off_thread_worker_succeeds_and_fails_on_the_traced_thread(
    window, monkeypatch: pytest.MonkeyPatch
):
    _sync_thread(monkeypatch)
    calls: list[int] = []
    assert window._run_off_thread("T", "L", lambda: calls.append(1)) is None
    assert calls == [1]

    boom = ValueError("boom")

    def _work() -> None:
        raise boom

    assert window._run_off_thread("T", "L", _work) is boom


def test_do_export_write_closure_runs_on_the_traced_thread(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import epy_papers

    _sync_thread(monkeypatch)
    calls: list[tuple[Any, ...]] = []

    class _Recording:
        def __init__(self, *a):
            calls.append(("init", a))

        def to_draft(self, *a, **k):
            calls.append(("to_draft", a, k))

    monkeypatch.setattr(epy_papers, "Paper", _Recording)
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    _no_modals(monkeypatch)
    window._do_export(tab, tmp_path / "out.docx", "docx")
    assert any(c[0] == "to_draft" for c in calls)


def test_offer_install_latex_declined_returns_false_without_installing(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.No,
    )
    assert window._offer_install_latex() is False


def test_offer_install_latex_accepted_runs_the_installer_and_succeeds(
    window, monkeypatch: pytest.MonkeyPatch
):
    """The success path: the ``_install`` closure -- running on the same
    traced/native-thread boundary as ``_write`` above -- actually calls
    ``install_tinytex``.
    """
    from epy_papers._core import _latex

    _sync_thread(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(_latex, "install_tinytex", lambda: calls.append("ran"))
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )
    assert window._offer_install_latex() is True
    assert calls == ["ran"]


def test_offer_install_latex_accepted_but_install_fails(
    window, monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._core import _latex

    _sync_thread(monkeypatch)

    def _boom():
        raise RuntimeError("network unreachable")

    monkeypatch.setattr(_latex, "install_tinytex", _boom)
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )
    seen = _no_modals(monkeypatch)
    assert window._offer_install_latex() is False
    assert any(
        kind == "critical" and "network unreachable" in text
        for kind, text in seen
    )


# ---------------------------------------------------------------------------
# About / manual dialogs
# ---------------------------------------------------------------------------


def test_show_about_opens_and_closes_the_about_dialog(
    window, monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._ui.about_dialog import AboutDialog

    opened: list[str] = []
    monkeypatch.setattr(
        AboutDialog,
        "exec",
        lambda self: opened.append("opened") or QDialog.DialogCode.Accepted,
    )
    window._show_about()
    assert opened == ["opened"]


def test_open_manual_creates_a_tab_with_the_manual_text(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        app_module, "_load_manual_text", lambda _f: "# Manual body\n"
    )
    before = window.tabs.count()
    window._open_manual("welcome.md")
    assert window.tabs.count() == before + 1
    assert window._current_tab().text() == "# Manual body\n"


def test_open_manual_warns_when_the_manual_cannot_be_loaded(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(app_module, "_load_manual_text", lambda _f: "")
    seen = _no_modals(monkeypatch)
    before = window.tabs.count()
    window._open_manual("missing.md")
    assert window.tabs.count() == before  # no tab created
    assert seen


# ---------------------------------------------------------------------------
# Tab title / window title bookkeeping
# ---------------------------------------------------------------------------


def test_refresh_tab_title_ignores_a_tab_no_longer_in_the_bar(
    window, tmp_path: Path
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    index = window.tabs.indexOf(tab)
    window.tabs.removeTab(index)
    window._refresh_tab_title(tab)  # must not raise (indexOf is now -1)


def test_update_window_title_falls_back_to_app_name_with_no_tabs(window):
    while window.tabs.count():
        window.tabs.removeTab(0)
    window._update_window_title()
    assert window.windowTitle() == app_module.APP_NAME


# ---------------------------------------------------------------------------
# _export_via_docs guards not already covered by test_docs_export_action.py
# ---------------------------------------------------------------------------


def test_export_via_docs_is_a_noop_with_no_current_tab(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(window, "_current_tab", lambda: None)
    window._export_via_docs()  # must not raise


def test_export_via_docs_stops_if_save_fails(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab = window._create_tab()
    tab.set_initial_text("dirty content", path=None)
    window.tabs.setCurrentWidget(tab)
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Save,
    )
    monkeypatch.setattr(window, "_save_current", lambda: False)
    from epy_papers._ui import docs_export_dialog as ded

    opened: list[str] = []
    monkeypatch.setattr(
        ded.DocsExportDialog,
        "exec",
        lambda self: opened.append("opened"),
    )
    window._export_via_docs()
    assert opened == []


def test_export_via_docs_defensive_guard_when_save_leaves_no_path(
    window, monkeypatch: pytest.MonkeyPatch
):
    """Defensive line: even if ``_save_current`` claims success, exporting
    without a resulting path must still be refused rather than handed to
    the dialog with ``tab.path is None``.
    """
    tab = window._create_tab()
    tab.set_initial_text("dirty content", path=None)
    window.tabs.setCurrentWidget(tab)
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Save,
    )
    # _save_current lies here on purpose: path stays None either way.
    monkeypatch.setattr(window, "_save_current", lambda: True)
    from epy_papers._ui import docs_export_dialog as ded

    opened: list[str] = []
    monkeypatch.setattr(
        ded.DocsExportDialog, "exec", lambda self: opened.append("opened")
    )
    window._export_via_docs()
    assert opened == []


def test_export_via_docs_rejected_dialog_starts_no_worker(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from epy_papers._ui import docs_export_dialog as ded

    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    monkeypatch.setattr(
        ded.DocsExportDialog, "exec", lambda self: QDialog.DialogCode.Rejected
    )
    window._export_via_docs()
    assert not hasattr(window, "_docs_worker") or window._docs_worker is None


# ---------------------------------------------------------------------------
# File actions: new / open / save / save-as / reload
# ---------------------------------------------------------------------------


def test_new_tab_creates_an_empty_untitled_tab(window):
    before = window.tabs.count()
    tab = window._new_tab()
    assert window.tabs.count() == before + 1
    assert tab.text() == ""
    assert tab.path is None


def test_open_dialog_starts_in_the_current_tabs_directory(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    window.tabs.setCurrentWidget(tab)
    seen_start: list[str] = []

    def _fake_open(_self, _title, start, _filt):
        seen_start.append(start)
        return [], ""

    monkeypatch.setattr(
        app_module.QFileDialog, "getOpenFileNames", _fake_open
    )
    window._open_dialog()
    assert seen_start == [str(tmp_path)]


def test_open_dialog_opens_every_selected_file(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    f1 = _write(tmp_path / "one.md")
    f2 = _write(tmp_path / "two.md")
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getOpenFileNames",
        lambda *_a, **_k: ([str(f1), str(f2)], ""),
    )
    opened: list[Path] = []
    monkeypatch.setattr(window, "open_path", lambda p: opened.append(p))
    window._open_dialog()
    assert opened == [f1, f2]


def test_open_path_warns_when_the_target_is_not_a_file(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    seen = _no_modals(monkeypatch)
    window.open_path(tmp_path / "does_not_exist.md")
    assert seen


def test_open_path_focuses_an_already_open_file_instead_of_reopening(
    window, tmp_path: Path
):
    path = _write(tmp_path / "shared.md")
    tab = window._create_tab()
    tab.load_file(path)
    window._new_tab()  # make it not-current
    before = window.tabs.count()
    window.open_path(path)
    assert window.tabs.count() == before  # no new tab
    assert window.tabs.currentWidget() is tab


def test_open_path_reuses_an_empty_untitled_current_tab(
    window, tmp_path: Path
):
    path = _write(tmp_path / "reuse.md")
    empty_tab = window._new_tab()
    before = window.tabs.count()
    window.open_path(path)
    assert window.tabs.count() == before  # reused, not appended
    assert window.tabs.currentWidget() is empty_tab
    assert empty_tab.path == path.resolve()


def test_open_path_opens_a_new_tab_when_current_has_content(
    window, tmp_path: Path
):
    busy = window._new_tab()
    busy.editor.appendPlainText("already writing something")
    path = _write(tmp_path / "other.md")
    before = window.tabs.count()
    window.open_path(path)
    assert window.tabs.count() == before + 1


def test_save_current_with_no_tab_returns_false(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(window, "_current_tab", lambda: None)
    assert window._save_current() is False


def test_save_current_with_no_path_falls_back_to_save_as(
    window, monkeypatch: pytest.MonkeyPatch
):
    window._new_tab()  # current tab now has no path
    calls: list[str] = []
    monkeypatch.setattr(
        window, "_save_current_as", lambda: calls.append("as") or True
    )
    assert window._save_current() is True
    assert calls == ["as"]


def test_save_current_writes_and_reports(window, tmp_path: Path):
    path = _write(tmp_path / "p.md")
    tab = window._create_tab()
    tab.load_file(path)
    window.tabs.setCurrentWidget(tab)
    tab.editor.appendPlainText("more")
    assert window._save_current() is True
    assert "more" in path.read_text(encoding="utf-8")
    assert not tab.dirty
    assert str(path) in window.statusBar().currentMessage()


def test_save_current_as_cancelled_returns_false(
    window, monkeypatch: pytest.MonkeyPatch
):
    tab = window._new_tab()
    monkeypatch.setattr(
        app_module.QFileDialog, "getSaveFileName", lambda *_a, **_k: ("", "")
    )
    assert window._save_current_as() is False
    assert tab.path is None


def test_save_current_as_appends_md_suffix_and_saves(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab = window._new_tab()
    tab.editor.appendPlainText("hello")
    target = tmp_path / "no_suffix"
    monkeypatch.setattr(
        app_module.QFileDialog,
        "getSaveFileName",
        lambda *_a, **_k: (str(target), ""),
    )
    assert window._save_current_as() is True
    assert tab.path == target.with_suffix(".md")
    assert target.with_suffix(".md").exists()


def test_save_current_as_with_no_current_tab_returns_false(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(window, "_current_tab", lambda: None)
    assert window._save_current_as() is False


def test_reload_current_is_a_noop_with_no_tab_or_no_path(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(window, "_current_tab", lambda: None)
    window._reload_current()  # no tab: must not raise
    tab = window._new_tab()  # no path
    window._reload_current()
    assert tab.text() == ""


def test_reload_current_declined_keeps_the_dirty_buffer(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = _write(tmp_path / "p.md")
    tab = window._create_tab()
    tab.load_file(path)
    window.tabs.setCurrentWidget(tab)
    tab.editor.appendPlainText("unsaved edit")
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.No,
    )
    window._reload_current()
    assert "unsaved edit" in tab.text()


def test_reload_current_confirmed_reloads_from_disk(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = _write(tmp_path / "p.md")
    tab = window._create_tab()
    tab.load_file(path)
    window.tabs.setCurrentWidget(tab)
    tab.editor.appendPlainText("unsaved edit")
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )
    window._reload_current()
    assert "unsaved edit" not in tab.text()
    assert str(path) in window.statusBar().currentMessage()


# ---------------------------------------------------------------------------
# Closing: _confirm_close, _close_tab_at, _close_current_tab, closeEvent
# ---------------------------------------------------------------------------


def test_confirm_close_is_true_for_a_clean_tab(window):
    tab = window._new_tab()
    assert window._confirm_close(tab) is True


def test_confirm_close_save_path_saves_and_returns_its_result(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = _write(tmp_path / "p.md")
    tab = window._create_tab()
    tab.load_file(path)
    window._new_tab()  # make `tab` not current
    tab.editor.appendPlainText("edit")
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Save,
    )
    assert window._confirm_close(tab) is True
    assert window.tabs.currentWidget() is tab  # switched to it to save
    assert "edit" in path.read_text(encoding="utf-8")


def test_confirm_close_discard_returns_true_without_saving(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = _write(tmp_path / "p.md")
    tab = window._create_tab()
    tab.load_file(path)
    tab.editor.appendPlainText("edit")
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Discard,
    )
    assert window._confirm_close(tab) is True
    assert "edit" not in path.read_text(encoding="utf-8")


def test_confirm_close_cancel_returns_false(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    tab.editor.appendPlainText("edit")
    monkeypatch.setattr(
        app_module.QMessageBox,
        "question",
        lambda *_a, **_k: QMessageBox.StandardButton.Cancel,
    )
    assert window._confirm_close(tab) is False


def test_close_tab_at_ignores_a_non_papertab_widget(window):
    index = window.tabs.addTab(QWidget(), "not a paper tab")
    before = window.tabs.count()
    window._close_tab_at(index)
    assert window.tabs.count() == before  # untouched


def test_close_tab_at_aborts_when_confirm_close_declines(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    tab = window._create_tab()
    tab.load_file(_write(tmp_path / "p.md"))
    index = window.tabs.indexOf(tab)
    monkeypatch.setattr(window, "_confirm_close", lambda _t: False)
    before = window.tabs.count()
    window._close_tab_at(index)
    assert window.tabs.count() == before


def test_close_tab_at_removes_the_tab_and_reopens_welcome_if_last(
    window, monkeypatch: pytest.MonkeyPatch
):
    """The window fixture starts with exactly one (welcome) tab open.

    Closing it must not leave zero tabs: a fresh welcome tab reopens so
    the window is never left with an empty tab bar.
    """
    monkeypatch.setattr(window, "_confirm_close", lambda _t: True)
    assert window.tabs.count() == 1
    original = window.tabs.widget(0)
    window._close_tab_at(0)
    assert window.tabs.count() == 1  # the welcome tab reopened, not zero
    assert window.tabs.widget(0) is not original
    assert window.tabs.widget(0).path is None


def test_close_current_tab_closes_the_active_index(
    window, monkeypatch: pytest.MonkeyPatch
):
    calls: list[int] = []
    monkeypatch.setattr(window, "_close_tab_at", lambda i: calls.append(i))
    window.tabs.setCurrentIndex(window.tabs.count() - 1)
    window._close_current_tab()
    assert calls == [window.tabs.count() - 1]


def test_close_current_tab_is_a_noop_with_no_tabs(
    window, monkeypatch: pytest.MonkeyPatch
):
    calls: list[int] = []
    monkeypatch.setattr(window, "_close_tab_at", lambda i: calls.append(i))
    while window.tabs.count():
        window.tabs.removeTab(0)
    window._close_current_tab()
    assert calls == []


class _FakeCloseEvent:
    def __init__(self) -> None:
        self.accepted = False
        self.ignored = False

    def accept(self) -> None:
        self.accepted = True

    def ignore(self) -> None:
        self.ignored = True


def test_close_event_ignored_when_a_tab_declines(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(window, "_confirm_close", lambda _t: False)
    event = _FakeCloseEvent()
    window.closeEvent(event)
    assert event.ignored is True
    assert event.accepted is False


def test_close_event_accepted_when_every_tab_agrees(
    window, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(window, "_confirm_close", lambda _t: True)
    event = _FakeCloseEvent()
    window.closeEvent(event)
    assert event.accepted is True
    assert event.ignored is False


# ---------------------------------------------------------------------------
# Drag & drop
# ---------------------------------------------------------------------------


class _FakeMimeData:
    def __init__(self, urls: list[Any], has_urls: bool = True) -> None:
        self._urls = urls
        self._has = has_urls

    def hasUrls(self) -> bool:  # noqa: N802 - Qt API name
        return self._has

    def urls(self) -> list[Any]:
        return self._urls


class _FakeDragEvent:
    def __init__(self, mime: _FakeMimeData) -> None:
        self._mime = mime
        self.accepted = False

    def mimeData(self) -> _FakeMimeData:  # noqa: N802 - Qt API name
        return self._mime

    def acceptProposedAction(self) -> None:  # noqa: N802 - Qt API name
        self.accepted = True


def test_drag_enter_event_accepts_file_urls(window):
    event = _FakeDragEvent(_FakeMimeData([object()]))
    window.dragEnterEvent(event)
    assert event.accepted is True


def test_drag_enter_event_ignores_non_url_drags(window):
    event = _FakeDragEvent(_FakeMimeData([], has_urls=False))
    window.dragEnterEvent(event)
    assert event.accepted is False


def test_drop_event_opens_only_supported_extensions(
    window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from PySide6.QtCore import QUrl

    md = _write(tmp_path / "one.md")
    other = tmp_path / "notes.txt"
    other.write_text("irrelevant", encoding="utf-8")
    urls = [QUrl.fromLocalFile(str(md)), QUrl.fromLocalFile(str(other))]
    event = _FakeDragEvent(_FakeMimeData(urls))
    opened: list[Path] = []
    monkeypatch.setattr(window, "open_path", lambda p: opened.append(p))
    window.dropEvent(event)
    assert opened == [md]
