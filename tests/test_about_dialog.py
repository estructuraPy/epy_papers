"""Tests for epy_papers._ui.about_dialog.AboutDialog.

Mirrors ``src/epy_papers/_ui/about_dialog.py`` per housekeeper.py's
``audit_module_mirror`` (module-level tests-mirror DNA).
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_window_title_and_modality(qapp):
    from epy_papers._ui.about_dialog import AboutDialog

    dlg = AboutDialog()
    assert dlg.windowTitle() == "About epy_papers"
    from PySide6.QtCore import Qt

    assert dlg.windowModality() == Qt.WindowModality.ApplicationModal


def test_version_label_shows_package_version(qapp):
    from PySide6.QtWidgets import QLabel

    import epy_papers
    from epy_papers._ui.about_dialog import AboutDialog

    dlg = AboutDialog()
    labels = dlg.findChildren(QLabel)
    texts = " ".join(lbl.text() for lbl in labels)
    assert epy_papers.__version__ in texts


def test_author_email_link_present(qapp):
    from PySide6.QtWidgets import QLabel

    from epy_papers._ui.about_dialog import AboutDialog

    dlg = AboutDialog()
    labels = dlg.findChildren(QLabel)
    texts = " ".join(lbl.text() for lbl in labels)
    assert "ahnavarro@anmingenieria.com" in texts


def test_close_button_rejects_dialog(qapp):
    from PySide6.QtWidgets import QDialogButtonBox

    from epy_papers._ui.about_dialog import AboutDialog

    dlg = AboutDialog()
    buttons = dlg.findChild(QDialogButtonBox)
    assert buttons is not None
    closed: list[bool] = []
    dlg.rejected.connect(lambda: closed.append(True))
    buttons.rejected.emit()
    assert closed == [True]


def test_branding_pixmap_missing_resource_returns_empty(qapp, monkeypatch):
    from epy_papers._ui import about_dialog

    def _boom(_pkg):
        raise ModuleNotFoundError("no such package")

    monkeypatch.setattr(about_dialog.importlib.resources, "files", _boom)
    pix = about_dialog._load_branding_pixmap("does_not_exist.png")
    assert pix.isNull()
