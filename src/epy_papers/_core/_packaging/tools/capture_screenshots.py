"""Capture the epy_papers user-manual screenshots.

Renders the real Fluent-styled UI (main window + the dialogs the manual
walks through) to PNGs under
``src/epy_papers/_config/_assets/screenshots/`` so the bundled
``welcome.md`` / ``welcome_es.md`` manuals show the actual program.

Run it headlessly::

    QT_QPA_PLATFORM=offscreen python \
        src/epy_papers/_core/_packaging/tools/capture_screenshots.py

It writes both the English files (``editor.png`` …) and the Spanish
variants (``editor_es.png`` …) by toggling the live UI language.
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

# The native Windows platform is used on purpose: the ``offscreen`` plugin
# ships an empty font database on Windows and renders every Qt-native glyph
# as .notdef tofu. ``WA_DontShowOnScreen`` (set in ``grab_widget``) keeps the
# windows off the desktop while still laying them out for ``grab()``.
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu"
)

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))

from PySide6.QtCore import (  # noqa: E402
    QElapsedTimer,
    QEventLoop,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402

from epy_papers._core import _i18n as i18n  # noqa: E402
from epy_papers._ui import themes  # noqa: E402
from epy_papers.app import PaperWindow  # noqa: E402
from epy_papers._ui.design_block_dialog import DesignBlockDialog  # noqa: E402
from epy_papers._ui.theme_gallery_dialog import ThemeGalleryDialog  # noqa: E402

OUT = (
    REPO_ROOT / "src" / "epy_papers" / "_config" / "_assets" / "screenshots"
)

# A compact manuscript that exercises the front matter, a citation, an
# equation and a table so the editor screenshot shows representative
# journal Markdown next to its live preview.
DEMO_PAPER = """\
---
title:
  en: "Wind-Induced Response of Slender Towers"
  es: "Respuesta al viento de torres esbeltas"
authors:
  - name: Angel Navarro-Mora
    affiliation: ANM Ingeniería, Cartago, Costa Rica
    email: ahnavarro@anmingenieria.com
    orcid: 0000-0002-0539-7014
    corresponding: true
abstract:
  en: "For a slender tower the wind, not gravity, governs the lateral
    design. This note summarizes the dynamic-pressure argument and its
    consequences for the bracing system."
  es: "En una torre esbelta el viento, no la gravedad, gobierna el diseño
    lateral. Esta nota resume el argumento de la presión dinámica y sus
    consecuencias para el sistema de arriostramiento."
keywords:
  en: [wind, slender towers, lateral design, bracing]
  es: [viento, torres esbeltas, diseño lateral, arriostramiento]
bibliography: refs.bib
---

# Introduction

Tall, slender towers are governed by wind rather than gravity
[@newmark1982]. The dynamic pressure the wind exerts on the facade scales
with the square of its speed,

$$ q = \\tfrac{1}{2}\\,\\rho\\,V^{2} $$

so gusts, not self-weight, size the lateral system.

| Property      | Value   |
| ------------- | ------- |
| Height        | 443 m   |
| Floors        | 102     |
| Steel frame   | 57,000 t|
"""


def pump(app: QApplication, ms: int) -> None:
    """Spin the event loop for ``ms`` so async painting/rendering settles."""
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < ms:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)


def grab_widget(app: QApplication, widget, path: Path, settle: int) -> None:
    """Lay a widget out offscreen, let it settle, then save a grab."""
    widget.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    widget.show()
    pump(app, settle)
    pix = widget.grab()
    path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(path))
    size = path.stat().st_size if path.exists() else 0
    print(f"  {path.name:32s} {pix.width()}x{pix.height()}  {size:,} B")


def capture_dialogs(app: QApplication, win: PaperWindow, suffix: str) -> None:
    """Capture every manual dialog for the active language."""
    specs = [
        ("dlg_design_block", lambda: DesignBlockDialog(win), None),
        (
            "dlg_theme_gallery",
            lambda: ThemeGalleryDialog(win, current_id="corporate"),
            (640, 460),
        ),
    ]
    for stem, factory, size in specs:
        dlg: QDialog = factory()
        dlg.setModal(False)
        if size is not None:
            dlg.resize(*size)
        grab_widget(app, dlg, OUT / f"{stem}{suffix}.png", settle=250)
        dlg.close()
        dlg.deleteLater()
        pump(app, 50)


def capture_language(app: QApplication, win: PaperWindow, suffix: str) -> None:
    """Capture the editor and dialogs for whichever language is active."""
    # Refresh the validation dock so it reflects the loaded demo paper
    # (and the active language) rather than the empty initial state.
    with contextlib.suppress(Exception):
        win._run_validation()
    pump(app, 500)
    grab_widget(app, win, OUT / f"editor{suffix}.png", settle=1500)
    capture_dialogs(app, win, suffix)


def main() -> int:
    """Boot the app offscreen and capture every manual screenshot."""
    app = QApplication.instance() or QApplication(sys.argv)
    theme = themes.get("corporate")
    themes.apply_palette(app, theme)
    app.setStyleSheet(themes.qss_for(theme))

    win = PaperWindow()
    win.resize(1280, 800)
    win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    tab = win._current_tab()
    if tab is not None:
        tab.set_initial_text(DEMO_PAPER, path=None)
    win.show()
    # Let the Pandoc-driven preview paint before the first grab.
    pump(app, 3500)

    print("English:")
    capture_language(app, win, "")

    print("Spanish:")
    i18n.set_language("es")
    pump(app, 300)
    capture_language(app, win, "_es")

    QTimer.singleShot(0, app.quit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
