"""Runtime behaviour of ``epy_papers._core._i18n``: tr / set_language /
translate_widget.

``test_i18n.py`` and ``test_i18n_coverage.py`` are static gates over the
``_ES`` dictionary's completeness; neither one calls ``tr()``,
``set_language()`` or ``translate_widget()``. This file exercises the
actual runtime switch.

``_lang`` and ``_observers`` are module globals shared with the rest of
the test session (every ``PaperWindow`` built anywhere registers a
``_retranslate_ui`` callback that is never unregistered). Every test here
swaps both out via ``monkeypatch`` so it neither leaks state into later
tests nor gets tripped by callbacks earlier tests left behind.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from epy_papers._core import _i18n


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _isolated_i18n_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run every test in this file on a private ``_lang``/``_observers``.

    Without this, calling ``set_language`` here would also fire every
    ``_retranslate_ui`` callback any earlier test's ``PaperWindow`` left
    registered, and a later test module would inherit whatever language
    this file leaves active.
    """
    monkeypatch.setattr(_i18n, "_lang", "en")
    monkeypatch.setattr(_i18n, "_observers", [])


def test_tr_is_the_identity_in_english():
    """English is the source language: tr() never looks at _ES."""
    assert _i18n.tr("Save") == "Save"
    assert _i18n.tr("some string not in the dict at all") == (
        "some string not in the dict at all"
    )


def test_tr_returns_the_spanish_entry_once_switched():
    """The whole point of _ES: a known key comes back translated."""
    _i18n.set_language("es")
    assert _i18n.tr("Save") == "Guardar"


def test_tr_falls_back_to_english_for_an_unmapped_key():
    """A key with no Spanish entry is not an error: it shows English.

    Counter-example to the translated-lookup test above: switching
    languages must not turn every UNKNOWN string into a KeyError or an
    empty string.
    """
    _i18n.set_language("es")
    assert _i18n.tr("nobody translated this literal") == (
        "nobody translated this literal"
    )


def test_set_language_rejects_an_unknown_code():
    """An unrecognized code is refused, not silently adopted.

    If this guard did not fire, a typo'd language code would leave the
    UI's ``current_language()`` reporting something nothing in
    ``LANGUAGES`` recognizes, and every future retranslation would be a
    silent no-op (``_ES`` is keyed by English source strings only).
    """
    _i18n.set_language("fr")
    assert _i18n.current_language() == "en"


def test_set_language_is_a_noop_when_already_active():
    """Setting the current language again must not re-fire observers.

    The guard is ``lang == _lang``, not just membership: a callback fired
    twice on select would double-apply anything non-idempotent.
    """
    calls: list[str] = []
    _i18n.on_language_changed(lambda: calls.append("fired"))
    _i18n.set_language("en")  # already active
    assert calls == []


def test_set_language_fires_every_registered_observer():
    """The mechanism PaperWindow relies on to relabel live, with no restart."""
    calls: list[str] = []
    _i18n.on_language_changed(lambda: calls.append("a"))
    _i18n.on_language_changed(lambda: calls.append("b"))
    _i18n.set_language("es")
    assert calls == ["a", "b"]
    assert _i18n.current_language() == "es"


def test_translate_widget_is_a_noop_in_english():
    """English never runs the widget walk -- there is nothing to translate."""
    label = QLabel("Save")
    translated: list[str] = []
    # A translate that ran here would call setText; watch for that.
    label.setText = lambda *_a, **_k: translated.append("called")  # type: ignore[method-assign]
    _i18n.translate_widget(label)
    assert translated == []


def test_translate_widget_relabels_every_supported_child(qapp):
    """Every widget kind the manual dialogs use gets its text swapped.

    ``Save`` / ``OK`` / ``Cancel`` are real ``_ES`` keys, so this is a
    genuine translation, not a check that some setter merely got called.
    """
    _i18n.set_language("es")
    root = QWidget()
    root.setWindowTitle("Save")
    label = QLabel("OK", root)
    button = QPushButton("Cancel", root)
    box = QGroupBox("Save", root)
    line = QLineEdit(root)
    line.setPlaceholderText("OK")
    area = QPlainTextEdit(root)
    area.setPlaceholderText("Cancel")

    _i18n.translate_widget(root)

    assert root.windowTitle() == "Guardar"
    assert label.text() == "Aceptar"
    assert button.text() == "Cancelar"
    assert box.title() == "Guardar"
    assert line.placeholderText() == "Aceptar"
    assert area.placeholderText() == "Cancelar"


def test_translate_widget_leaves_untranslated_text_and_empty_fields_alone(
    qapp,
):
    """Counter-example: user data and blank fields must survive untouched.

    A widget walk that blindly called ``tr()`` on empty strings or on a
    reader's own text (e.g. a typed journal name) would corrupt it; both
    must pass through unchanged.
    """
    _i18n.set_language("es")
    root = QWidget()
    root.setWindowTitle("")  # falsy: must be skipped, not translated to ""
    label = QLabel("My Custom Journal Name", root)
    line = QLineEdit(root)
    line.setPlaceholderText("")

    _i18n.translate_widget(root)

    assert root.windowTitle() == ""
    assert label.text() == "My Custom Journal Name"
    assert line.placeholderText() == ""
