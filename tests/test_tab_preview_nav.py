"""Tests for preview link navigation (anchors under <base>, popups, Back).

Mirrors the epy_reports preview-navigation contract: the Pandoc preview
carries a ``<base href>`` (so relative figures resolve) which would
capture every ``href="#id"``; the injected interceptor keeps citation,
footnote and section links jumping in-page and records each jump so
Back returns to the exact previous position. ``target="_blank"`` links
are handed to the system browser instead of being swallowed.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from epy_papers._ui import tab as tab_mod

_app: QApplication | None = None


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a module-scoped QApplication instance."""
    global _app
    if _app is not None:
        return _app
    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        app = instance
    elif instance is None:
        app = QApplication([])
    else:
        raise RuntimeError(
            "Preview tests need a QApplication, not a QCoreApplication."
        )
    _app = app
    return app


def test_anchor_nav_script_contract():
    """The injected script records scroll state for Back restoration."""
    js = tab_mod._ANCHOR_NAV_JS
    assert "history.pushState" in js
    assert "epyScroll" in js
    assert "popstate" in js
    assert "preventDefault" in js


def test_fast_preview_has_no_base_and_no_interceptor():
    """The fast preview carries no <base>, so anchors work natively."""
    html = tab_mod._build_preview_html("# Title\n\nBody\n")
    assert "<base href=" not in html
    assert "epyScroll" not in html


def test_popup_links_open_in_system_browser(qapp, monkeypatch):
    """target=_blank navigation is handed to the OS browser."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWebEngineCore import QWebEnginePage

    opened: list[str] = []
    monkeypatch.setattr(
        QDesktopServices, "openUrl", lambda url: opened.append(url.toString())
    )
    page = tab_mod._ExternalOpenPage(None)
    accepted = page.acceptNavigationRequest(
        QUrl("https://example.test/paper"),
        QWebEnginePage.NavigationType.NavigationTypeLinkClicked,
        True,
    )
    assert accepted is False
    assert opened == ["https://example.test/paper"]


def test_preview_view_creates_external_page(qapp):
    """createWindow returns the throwaway external-open page."""
    from PySide6.QtWebEngineCore import QWebEnginePage

    view = tab_mod._PreviewView()
    page = view.createWindow(QWebEnginePage.WebWindowType.WebBrowserTab)
    assert isinstance(page, tab_mod._ExternalOpenPage)
    view.deleteLater()


def test_render_load_clears_history_flagged(qapp):
    """A flagged (render) load clears history; unflagged keeps it."""
    widget = tab_mod.PaperTab()
    try:
        calls: list[str] = []

        class _FakeHistory:
            def clear(self):
                calls.append("clear")

        class _FakeView:
            def history(self):
                return _FakeHistory()

        widget.view = _FakeView()  # type: ignore[assignment] — behavioral stub
        widget._expect_render_load = True
        widget._on_preview_load_finished(True)
        assert calls == ["clear"]
        assert widget._expect_render_load is False

        widget._on_preview_load_finished(True)
        assert calls == ["clear"]
    finally:
        widget.cleanup_preview_tmp()
        widget.deleteLater()
        from PySide6.QtCore import QEvent

        qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
