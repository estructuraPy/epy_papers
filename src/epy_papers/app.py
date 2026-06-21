"""epy_papers GUI: multi-tab paper authoring editor."""

from __future__ import annotations

import argparse
import importlib.resources
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QIcon,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDockWidget,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from epy_papers import _i18n as i18n

# epy_papers bundles its own copy of the suite theme system, so the app keeps
# the same Fluent/WinUI appearance as epy_reports / epy_slides regardless of
# whether the sibling apps are installed alongside it.
from epy_papers import themes as _themes
from epy_papers.about_dialog import _load_branding_pixmap

APP_NAME = "epy_papers"

SUPPORTED_EXTENSIONS = {".md", ".markdown"}

FILE_FILTER = "Markdown paper (*.md *.markdown);;All files (*)"

_THEMES_AVAILABLE = True


def _load_welcome_text() -> str:
    """Load the bundled welcome.md, returning empty string on failure."""
    try:
        return (
            importlib.resources.files("epy_papers.assets")
            .joinpath("welcome.md")
            .read_text(encoding="utf-8")
        )
    except Exception:
        return ""


WELCOME_TEXT = _load_welcome_text()


class PaperWindow(QMainWindow):
    """Main window: holds a tab bar with one PaperTab per file."""

    def __init__(self) -> None:
        """Build the tab widget, toolbar, validation dock, welcome tab."""
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1300, 840)

        logo_pix = _load_branding_pixmap("epy_papers.png")
        if not logo_pix.isNull():
            self.setWindowIcon(QIcon(logo_pix))

        self._settings = QSettings("ANM Ingeniería", "epy_papers")

        # Lazy import to avoid Qt initialisation order issues.
        from epy_papers.tab import PaperTab  # noqa: PLC0415

        self._PaperTab = PaperTab

        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self._close_tab_at)
        self.tabs.currentChanged.connect(self._on_current_changed)
        self.setCentralWidget(self.tabs)
        self.setStatusBar(QStatusBar(self))

        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self.menuBar().hide()

        self._build_validation_dock()

        self.setAcceptDrops(True)

        # Optionally apply epy_reports theme
        if _THEMES_AVAILABLE and _themes is not None:
            saved_theme = str(
                self._settings.value(
                    "theme", _themes.DEFAULT_THEME_ID
                )
            )
            self._apply_theme(saved_theme, persist=False)

        # Internationalization
        self._capture_i18n()
        i18n.on_language_changed(self._retranslate_ui)
        saved_lang = str(self._settings.value("language", "en"))
        if saved_lang in i18n.LANGUAGES and saved_lang != "en":
            i18n.set_language(saved_lang)
        self._sync_language_menu()

        self._open_welcome_tab()

    # -------------------------------------------- actions / menus

    def _build_actions(self) -> None:
        """Create all QActions used by the menus and toolbar."""
        self.act_new = QAction("New", self)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)
        self.act_new.triggered.connect(self._new_tab)

        self.act_open = QAction("Open...", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self._open_dialog)

        self.act_save = QAction("Save", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.triggered.connect(self._save_current)

        self.act_save_as = QAction("Save As...", self)
        self.act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.act_save_as.triggered.connect(self._save_current_as)

        self.act_reload = QAction("Reload", self)
        self.act_reload.setShortcut("F5")
        self.act_reload.triggered.connect(self._reload_current)

        self.act_close = QAction("Close Tab", self)
        self.act_close.setShortcut(QKeySequence.StandardKey.Close)
        self.act_close.triggered.connect(self._close_current_tab)

        self.act_quit = QAction("Quit", self)
        self.act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.act_quit.triggered.connect(self.close)

        self.act_bold = QAction("Bold", self)
        self.act_bold.setShortcut(QKeySequence("Ctrl+B"))
        self.act_bold.triggered.connect(
            lambda: self._on_active_tab("toggle_bold")
        )

        self.act_italic = QAction("Italic", self)
        self.act_italic.setShortcut(QKeySequence("Ctrl+I"))
        self.act_italic.triggered.connect(
            lambda: self._on_active_tab("toggle_italic")
        )

        self.act_link = QAction("Insert Link...", self)
        self.act_link.setShortcut(QKeySequence("Ctrl+K"))
        self.act_link.triggered.connect(
            lambda: self._on_active_tab("insert_link")
        )

        self.act_ins_title = QAction("Insert Title Block", self)
        self.act_ins_title.setShortcut(QKeySequence("Ctrl+Shift+Y"))
        self.act_ins_title.triggered.connect(
            lambda: self._on_active_tab("insert_title_block")
        )

        self.act_ins_authors = QAction("Insert Authors", self)
        self.act_ins_authors.triggered.connect(
            lambda: self._on_active_tab("insert_authors")
        )

        self.act_ins_abstract = QAction("Insert Abstract", self)
        self.act_ins_abstract.triggered.connect(
            lambda: self._on_active_tab("insert_abstract")
        )

        self.act_ins_keywords = QAction("Insert Keywords", self)
        self.act_ins_keywords.triggered.connect(
            lambda: self._on_active_tab("insert_keywords")
        )

        self.act_ins_highlights = QAction("Insert Highlights", self)
        self.act_ins_highlights.triggered.connect(
            lambda: self._on_active_tab("insert_highlights")
        )

        self.act_ins_declarations = QAction(
            "Insert Declarations", self
        )
        self.act_ins_declarations.triggered.connect(
            lambda: self._on_active_tab("insert_declarations")
        )

        self.act_ins_figure = QAction("Insert Figure", self)
        self.act_ins_figure.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.act_ins_figure.triggered.connect(
            lambda: self._on_active_tab("insert_figure")
        )

        self.act_ins_table = QAction("Insert Table", self)
        self.act_ins_table.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.act_ins_table.triggered.connect(
            lambda: self._on_active_tab("insert_table")
        )

        self.act_ins_equation = QAction("Insert Equation", self)
        self.act_ins_equation.setShortcut(QKeySequence("Ctrl+Shift+Q"))
        self.act_ins_equation.triggered.connect(
            lambda: self._on_active_tab("insert_equation")
        )

        self.act_ins_citation = QAction("Insert Citation", self)
        self.act_ins_citation.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.act_ins_citation.triggered.connect(
            lambda: self._on_active_tab("insert_citation")
        )

        self.act_ins_code = QAction("Insert Code Block", self)
        self.act_ins_code.setShortcut(QKeySequence("Ctrl+Shift+K"))
        self.act_ins_code.triggered.connect(
            lambda: self._on_active_tab("insert_code_block")
        )

        # Shared design blocks (cards, big stats, timelines, agendas) — the
        # same insert options epy_reports and epy_slides expose, one engine.
        from epy_papers._design import (  # noqa: PLC0415
            DESIGN_BLOCK_LABELS,
            DESIGN_BLOCKS,
        )

        self.design_actions: dict[str, QAction] = {}
        for kind in DESIGN_BLOCKS:
            label = DESIGN_BLOCK_LABELS.get(kind, kind.title())
            act = QAction(label, self)
            act.triggered.connect(
                lambda _checked=False, k=kind: self._on_active_tab(
                    "insert_design_block", k
                )
            )
            self.design_actions[kind] = act

        self.act_new_journal = QAction("Add Journal...", self)
        self.act_new_journal.triggered.connect(self._new_journal)

        self.act_export_docx = QAction("Export DOCX...", self)
        self.act_export_docx.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.act_export_docx.triggered.connect(self._export_docx)

        self.act_export_latex = QAction("Export LaTeX...", self)
        self.act_export_latex.triggered.connect(self._export_latex)

        self.act_export_pdf = QAction("Export PDF...", self)
        self.act_export_pdf.setShortcut(QKeySequence("Ctrl+P"))
        self.act_export_pdf.triggered.connect(self._export_pdf)

        self.act_export_html = QAction("Export HTML...", self)
        self.act_export_html.triggered.connect(self._export_html)

        self.act_manual_en = QAction("User Manual (English)", self)
        self.act_manual_en.triggered.connect(
            lambda: self._open_manual("welcome.md")
        )
        self.act_manual_es = QAction("User Manual (Spanish)", self)
        self.act_manual_es.triggered.connect(
            lambda: self._open_manual("welcome_es.md")
        )

        self.act_about = QAction("About epy_papers...", self)
        self.act_about.triggered.connect(self._show_about)

        # Language radio group
        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusive(True)
        self.lang_actions: dict[str, QAction] = {}
        for code, name in i18n.LANGUAGES.items():
            act = QAction(name, self, checkable=True)
            act.setData(code)
            self.lang_group.addAction(act)
            self.lang_actions[code] = act
        self.lang_group.triggered.connect(
            lambda action: self._set_language(action.data())
        )

        # Theme actions (only when epy_reports themes are available)
        self.theme_group: QActionGroup | None = None
        self.theme_actions: dict[str, QAction] = {}
        if _THEMES_AVAILABLE and _themes is not None:
            self._build_theme_actions()

    def _build_theme_actions(self) -> None:
        """(Re)create the exclusive group of theme radio actions."""
        if not _THEMES_AVAILABLE or _themes is None:
            return
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions = {}
        for theme in _themes.THEMES.values():
            act = QAction(theme.display_name, self, checkable=True)
            act.setData(theme.id)
            self.theme_group.addAction(act)
            self.theme_actions[theme.id] = act
        self.theme_group.triggered.connect(
            lambda action: self._apply_theme(action.data())
        )

    def _build_menu(self) -> None:
        """Build popup menus for the toolbar dropdowns."""
        self.file_menu = QMenu("&File", self)
        self.file_menu.addAction(self.act_new)
        self.file_menu.addAction(self.act_open)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.act_save)
        self.file_menu.addAction(self.act_save_as)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.act_reload)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.act_close)
        self.file_menu.addAction(self.act_quit)

        self.text_menu = QMenu("&Text", self)
        self.text_menu.addAction(self.act_bold)
        self.text_menu.addAction(self.act_italic)
        self.text_menu.addSeparator()
        self.text_menu.addAction(self.act_link)

        self.paper_menu = QMenu("&Paper", self)
        self.paper_menu.addAction(self.act_ins_title)
        self.paper_menu.addAction(self.act_ins_authors)
        self.paper_menu.addAction(self.act_ins_abstract)
        self.paper_menu.addAction(self.act_ins_keywords)
        self.paper_menu.addAction(self.act_ins_highlights)
        self.paper_menu.addAction(self.act_ins_declarations)
        self.paper_menu.addSeparator()
        self.paper_menu.addAction(self.act_ins_figure)
        self.paper_menu.addAction(self.act_ins_table)
        self.paper_menu.addAction(self.act_ins_equation)
        self.paper_menu.addAction(self.act_ins_citation)
        self.paper_menu.addAction(self.act_ins_code)
        self.design_sub = self.paper_menu.addMenu("Design block")
        for act in self.design_actions.values():
            self.design_sub.addAction(act)
        self.paper_menu.addSeparator()
        self.paper_menu.addAction(self.act_new_journal)

        self.export_menu = QMenu("E&xport", self)
        self.export_menu.addAction(self.act_export_docx)
        self.export_menu.addAction(self.act_export_latex)
        self.export_menu.addAction(self.act_export_pdf)
        self.export_menu.addAction(self.act_export_html)

        self.view_menu = QMenu("&View", self)
        if _THEMES_AVAILABLE and _themes is not None:
            self.theme_sub = self.view_menu.addMenu("Theme")
            self._populate_theme_menu()
            self.view_menu.addSeparator()
        self.language_menu = self.view_menu.addMenu("Language")
        for act in self.lang_group.actions():
            self.language_menu.addAction(act)

        self.help_menu = QMenu("&Help", self)
        self.help_menu.addAction(self.act_manual_en)
        self.help_menu.addAction(self.act_manual_es)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.act_about)

    def _populate_theme_menu(self) -> None:
        """Fill the Theme submenu with radio actions."""
        if not hasattr(self, "theme_sub"):
            return
        self.theme_sub.clear()
        if self.theme_group is not None:
            for act in self.theme_group.actions():
                self.theme_sub.addAction(act)

    def _build_toolbar(self) -> None:
        """Build the main toolbar with dropdown buttons + journal selector."""
        bar = QToolBar("Main", self)
        bar.setMovable(False)
        self.addToolBar(bar)

        self._toolbar_buttons: list[tuple[QToolButton, str]] = []

        self._add_dropdown(bar, "File", self.file_menu)
        self._add_dropdown(bar, "Text", self.text_menu)
        self._add_dropdown(bar, "Paper", self.paper_menu)
        self._add_dropdown(bar, "Export", self.export_menu)
        self._add_dropdown(bar, "View", self.view_menu)
        self._add_dropdown(bar, "Help", self.help_menu)

        bar.addSeparator()

        # Journal label + combo
        self._journal_label = QLabel(i18n.tr("Journal:") + " ")
        bar.addWidget(self._journal_label)
        self._journal_combo = self._build_journal_combo()
        bar.addWidget(self._journal_combo)

        self._add_journal_btn = QToolButton(self)
        self._add_journal_btn.setText("+")
        self._add_journal_btn.setToolTip(i18n.tr("Add a new journal"))
        self._add_journal_btn.clicked.connect(self._new_journal)
        bar.addWidget(self._add_journal_btn)

        bar.addSeparator()

        # Validate button
        self._validate_btn = QToolButton(self)
        self._validate_btn.setText(i18n.tr("Validate"))
        self._validate_btn.setShortcut("Ctrl+Shift+V")
        self._validate_btn.clicked.connect(self._run_validation)
        bar.addWidget(self._validate_btn)

    def _add_dropdown(
        self, bar: QToolBar, text: str, menu: QMenu
    ) -> None:
        """Add a popup-style QToolButton to ``bar`` that opens ``menu``."""
        btn = QToolButton(self)
        btn.setText(i18n.tr(text))
        btn.setMenu(menu)
        btn.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        bar.addWidget(btn)
        self._toolbar_buttons.append((btn, text))

    def _build_journal_combo(self) -> QComboBox:
        """Build and return a journal QComboBox populated from catalog."""
        from epy_papers import available_journals  # noqa: PLC0415

        combo = QComboBox()
        combo.setMinimumWidth(220)
        try:
            journals = available_journals()
        except Exception:
            journals = []
        for jid, jname in journals:
            combo.addItem(jname, jid)

        saved = str(self._settings.value("journal_id", ""))
        if saved:
            for i in range(combo.count()):
                if combo.itemData(i) == saved:
                    combo.setCurrentIndex(i)
                    break

        combo.currentIndexChanged.connect(self._on_journal_changed)
        return combo

    def _current_journal_id(self) -> str:
        """Return the journal id currently selected in the combo."""
        return str(self._journal_combo.currentData() or "")

    def _current_profile(self) -> dict | None:
        """Return the raw profile dict for the selected journal, or None."""
        jid = self._current_journal_id()
        if not jid:
            return None
        try:
            from epy_papers import journal_profile  # noqa: PLC0415

            return journal_profile(jid)
        except Exception:
            return None

    def _apply_journal_to_tabs(self) -> None:
        """Push the selected journal's format to every open tab's preview."""
        profile = self._current_profile()
        from epy_papers.tab import PaperTab  # noqa: PLC0415

        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, PaperTab):
                widget.set_journal(profile)

    def _on_journal_changed(self) -> None:
        """Persist the journal choice, reformat previews and re-validate."""
        jid = self._current_journal_id()
        self._settings.setValue("journal_id", jid)
        self._apply_journal_to_tabs()
        self._run_validation()

    def _refresh_journal_combo(self, select_id: str | None = None) -> None:
        """Rebuild the journal combo from the catalog, keeping a selection."""
        from epy_papers import available_journals  # noqa: PLC0415

        combo = self._journal_combo
        keep = select_id or self._current_journal_id()
        combo.blockSignals(True)
        combo.clear()
        try:
            for jid, jname in available_journals():
                combo.addItem(jname, jid)
        except Exception:
            pass
        for i in range(combo.count()):
            if combo.itemData(i) == keep:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)
        self._on_journal_changed()

    def _new_journal(self) -> None:
        """Open a dialog to add a journal profile to the user catalog."""
        from PySide6.QtWidgets import (  # noqa: PLC0415
            QCheckBox,
            QComboBox,
            QDialogButtonBox,
            QFormLayout,
            QHBoxLayout,
            QLineEdit,
            QSpinBox,
        )

        dlg = QDialog(self)
        dlg.setWindowTitle(i18n.tr("Add Journal"))
        dlg.setMinimumWidth(440)
        form = QFormLayout(dlg)

        ed_id = QLineEdit()
        ed_id.setPlaceholderText("my-journal")
        ed_name = QLineEdit()
        ed_publisher = QLineEdit()
        cb_columns = QComboBox()
        cb_columns.addItems(["1", "2"])
        cb_spacing = QComboBox()
        cb_spacing.addItems(["single", "1.5", "double"])
        cb_spacing.setCurrentText("double")
        ed_font = QLineEdit("Times New Roman")
        sp_size = QSpinBox()
        sp_size.setRange(8, 18)
        sp_size.setValue(12)
        cb_page = QComboBox()
        cb_page.addItems(["letter", "a4"])
        chk_lineno = QCheckBox(i18n.tr("Number lines (continuous)"))
        cb_csl = QComboBox()
        for label, stem in (
            ("IEEE", "ieee"),
            ("APA", "apa"),
            ("ASCE", "american-society-of-civil-engineers"),
            ("Vancouver", "elsevier-vancouver"),
            ("Elsevier (Harvard)", "elsevier-harvard"),
            ("Springer", "springer-basic-author-date"),
            ("Nature", "nature"),
            ("Science", "science"),
            ("Chicago", "chicago-author-date"),
            ("Harvard", "harvard-cite-them-right"),
            ("MLA", "modern-language-association"),
            ("ACS", "american-chemical-society"),
            ("AMA", "american-medical-association"),
        ):
            cb_csl.addItem(label, stem)
        sp_abs = QSpinBox()
        sp_abs.setRange(50, 1000)
        sp_abs.setSingleStep(10)
        sp_abs.setValue(250)
        chk_docx = QCheckBox("DOCX")
        chk_docx.setChecked(True)
        chk_tex = QCheckBox("LaTeX")
        chk_pdf = QCheckBox("PDF")
        fmt_row = QHBoxLayout()
        for box in (chk_docx, chk_tex, chk_pdf):
            fmt_row.addWidget(box)
        fmt_widget = QWidget()
        fmt_widget.setLayout(fmt_row)

        form.addRow(i18n.tr("Journal ID") + " *", ed_id)
        form.addRow(i18n.tr("Name") + " *", ed_name)
        form.addRow(i18n.tr("Publisher"), ed_publisher)
        form.addRow(i18n.tr("Columns"), cb_columns)
        form.addRow(i18n.tr("Line spacing"), cb_spacing)
        form.addRow(i18n.tr("Font"), ed_font)
        form.addRow(i18n.tr("Font size (pt)"), sp_size)
        form.addRow(i18n.tr("Page size"), cb_page)
        form.addRow(i18n.tr("Line numbers"), chk_lineno)
        form.addRow(i18n.tr("Citation style"), cb_csl)
        form.addRow(i18n.tr("Abstract max words"), sp_abs)
        form.addRow(i18n.tr("Export formats"), fmt_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        jid = ed_id.text().strip()
        name = ed_name.text().strip()
        if not jid or not name:
            QMessageBox.warning(
                self, APP_NAME, i18n.tr("Journal ID and Name are required.")
            )
            return
        formats = [
            fmt
            for box, fmt in (
                (chk_docx, "docx"),
                (chk_tex, "tex"),
                (chk_pdf, "pdf"),
            )
            if box.isChecked()
        ] or ["docx"]
        profile = {
            "name": name,
            "publisher": ed_publisher.text().strip(),
            "columns": int(cb_columns.currentText()),
            "spacing": cb_spacing.currentText(),
            "font": ed_font.text().strip() or "Times New Roman",
            "font_size_pt": sp_size.value(),
            "page_size": cb_page.currentText(),
            "line_numbers": (
                "continuous" if chk_lineno.isChecked() else "off"
            ),
            "csl": cb_csl.currentData(),
            "citation": cb_csl.currentData(),
            "abstract_words": sp_abs.value(),
            "formats": formats,
            "latex_class": "",
        }
        try:
            from epy_papers import add_journal  # noqa: PLC0415

            add_journal(jid, profile)
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, str(exc))
            return
        self._refresh_journal_combo(select_id=jid)
        self.statusBar().showMessage(
            i18n.tr("Journal added") + f": {name}", 4000
        )

    # ------------------------------------------ validation dock

    def _build_validation_dock(self) -> None:
        """Create and add the validation results dock widget."""
        dock = QDockWidget(i18n.tr("Validation"), self)
        dock.setObjectName("ValidationDock")
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        validate_btn = QPushButton(i18n.tr("Validate"))
        validate_btn.setShortcut("Ctrl+Shift+V")
        validate_btn.clicked.connect(self._run_validation)
        layout.addWidget(validate_btn)

        self._validation_list = QListWidget()
        layout.addWidget(self._validation_list)

        dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self._validation_dock = dock

    def _run_validation(self) -> None:
        """Validate the current paper against the selected journal."""
        tab = self._current_tab()
        lw = self._validation_list
        lw.clear()
        if tab is None:
            return
        text = tab.text()
        journal_id = self._current_journal_id()
        if not journal_id:
            return
        try:
            from epy_papers import Paper  # noqa: PLC0415

            base_dir = tab.path.parent if tab.path else None
            paper = Paper(text, base_dir)
            result = paper.validate(journal_id)
            warnings = list(result)
            if not warnings:
                item = QListWidgetItem(i18n.tr("No issues found"))
                item.setForeground(QColor("#008800"))
                lw.addItem(item)
            else:
                sev_colors = {
                    "ERROR": "#cc0000",
                    "WARNING": "#e07000",
                    "INFO": "#0066cc",
                }
                for w in warnings:
                    sev = str(w.severity).upper()
                    color = sev_colors.get(sev, "#333333")
                    item = QListWidgetItem(
                        f"[{sev}] {w.message}"
                    )
                    item.setForeground(QColor(color))
                    lw.addItem(item)
        except Exception as exc:
            item = QListWidgetItem(f"Validation error: {exc}")
            item.setForeground(QColor("#cc0000"))
            lw.addItem(item)

    # ------------------------------------------ themes

    def _apply_theme(
        self, theme_id: str, *, persist: bool = True
    ) -> None:
        """Apply a theme from epy_reports (if available)."""
        if not _THEMES_AVAILABLE or _themes is None:
            return
        try:
            theme = _themes.get(theme_id)
        except Exception:
            return
        qapp = QApplication.instance()
        if isinstance(qapp, QApplication):
            try:
                _themes.apply_palette(qapp, theme)
                qapp.setStyleSheet(_themes.qss_for(theme))
            except Exception:
                pass
        if theme.id in self.theme_actions:
            self.theme_actions[theme.id].setChecked(True)
        if persist:
            self._settings.setValue("theme", theme.id)

    # ------------------------------------------ i18n

    def _capture_i18n(self) -> None:
        """Snapshot English text of every stable action/menu."""
        self._tr_actions: dict[QAction, str] = {}
        self._tr_menus: dict[QMenu, str] = {}
        for obj in vars(self).values():
            if isinstance(obj, QAction):
                if obj.text():
                    self._tr_actions[obj] = obj.text()
            elif isinstance(obj, QMenu):
                if obj.title():
                    self._tr_menus[obj] = obj.title()
            elif isinstance(obj, QActionGroup):
                for act in obj.actions():
                    if act.text():
                        self._tr_actions[act] = act.text()
            elif isinstance(obj, dict):
                for act in obj.values():
                    if isinstance(act, QAction) and act.text():
                        self._tr_actions[act] = act.text()

    def _retranslate_ui(self) -> None:
        """Re-apply translations to every captured widget."""
        for action, english in self._tr_actions.items():
            action.setText(i18n.tr(english))
        for menu, english in self._tr_menus.items():
            menu.setTitle(i18n.tr(english))
        for btn, english in getattr(self, "_toolbar_buttons", []):
            btn.setText(i18n.tr(english))
        if hasattr(self, "_journal_label"):
            self._journal_label.setText(i18n.tr("Journal:") + " ")
        if hasattr(self, "_validate_btn"):
            self._validate_btn.setText(i18n.tr("Validate"))
        self._sync_language_menu()

    def _set_language(self, code: str) -> None:
        """Persist the chosen UI language and relabel the UI live."""
        self._settings.setValue("language", code)
        i18n.set_language(code)

    def _sync_language_menu(self) -> None:
        """Tick the radio item matching the active language."""
        act = self.lang_actions.get(i18n.current_language())
        if act is not None:
            act.setChecked(True)

    # ------------------------------------------ on-active-tab helper

    def _on_active_tab(self, fn_name: str, *args) -> None:
        """Forward an action to the active tab if one is open."""
        tab = self._current_tab()
        if tab is None:
            return
        method = getattr(tab, fn_name, None)
        if method is not None:
            method(*args)

    # ------------------------------------------ export handlers

    def _export_docx(self) -> None:
        """Export the current paper as a DOCX draft."""
        tab = self._current_tab()
        if tab is None:
            return
        default = (
            str(tab.path.with_suffix(".docx"))
            if tab.path
            else "draft.docx"
        )
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export DOCX", default, "Word document (*.docx)"
        )
        if not filename:
            return
        target = Path(filename)
        if not target.suffix:
            target = target.with_suffix(".docx")
        self._do_export(tab, target, "docx")

    def _export_latex(self) -> None:
        """Export the current paper as a LaTeX source file."""
        tab = self._current_tab()
        if tab is None:
            return
        default = (
            str(tab.path.with_suffix(".tex"))
            if tab.path
            else "draft.tex"
        )
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export LaTeX", default, "LaTeX (*.tex)"
        )
        if not filename:
            return
        target = Path(filename)
        if not target.suffix:
            target = target.with_suffix(".tex")
        self._do_export(tab, target, "tex")

    def _export_pdf(self) -> None:
        """Export the current paper as a PDF via LaTeX."""
        tab = self._current_tab()
        if tab is None:
            return
        default = (
            str(tab.path.with_suffix(".pdf"))
            if tab.path
            else "draft.pdf"
        )
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", default, "PDF (*.pdf)"
        )
        if not filename:
            return
        target = Path(filename)
        if not target.suffix:
            target = target.with_suffix(".pdf")
        self._do_export(tab, target, "pdf")

    def _export_html(self) -> None:
        """Save the current preview HTML to a file."""
        tab = self._current_tab()
        if tab is None:
            return
        default = (
            str(tab.path.with_suffix(".html"))
            if tab.path
            else "draft.html"
        )
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export HTML", default, "HTML (*.html)"
        )
        if not filename:
            return
        target = Path(filename)
        if not target.suffix:
            target = target.with_suffix(".html")
        from epy_papers.tab import _build_preview_html  # noqa: PLC0415

        try:
            html = _build_preview_html(tab.text(), self._current_profile())
            target.write_text(html, encoding="utf-8")
            self.statusBar().showMessage(
                f"Exported: {target.name}", 5000
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Export HTML failed", str(exc)
            )

    def _do_export(
        self, tab, target: Path, fmt: str
    ) -> None:
        """Run paper.to_draft for the given format and report result."""
        from epy_papers import Paper  # noqa: PLC0415

        text = tab.text()
        base_dir = tab.path.parent if tab.path else None
        journal_id = self._current_journal_id()
        try:
            paper = Paper(text, base_dir)
            paper.to_draft(journal_id, target, fmt=fmt)
            self.statusBar().showMessage(
                f"Exported: {target.name}", 5000
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                f"Export {fmt.upper()} failed",
                str(exc),
            )

    # ------------------------------------------ About dialog

    def _show_about(self) -> None:
        """Open the About epy_papers dialog modally."""
        from epy_papers.about_dialog import AboutDialog  # noqa: PLC0415

        dlg = AboutDialog(self)
        dlg.exec()

    # ------------------------------------------ Help / manuals

    def _open_manual(self, filename: str) -> None:
        """Open a bundled manual document in a new tab."""
        try:
            text = (
                importlib.resources.files("epy_papers.assets")
                .joinpath(filename)
                .read_text(encoding="utf-8")
            )
        except Exception:
            QMessageBox.warning(
                self,
                APP_NAME,
                f"Could not load manual '{filename}'.",
            )
            return
        tab = self._create_tab()
        tab.set_initial_text(text, path=None)

    # ------------------------------------------ tab management

    def _open_welcome_tab(self) -> None:
        """Create the initial tab with the bundled welcome text."""
        tab = self._create_tab()
        tab.set_initial_text(WELCOME_TEXT, path=None)

    def _create_tab(self):
        """Instantiate a new PaperTab and wire its signals."""
        tab = self._PaperTab(self)
        tab.dirtyChanged.connect(
            lambda _flag, t=tab: self._refresh_tab_title(t)
        )
        tab.pathChanged.connect(
            lambda t=tab: self._refresh_tab_title(t)
        )
        index = self.tabs.addTab(tab, tab.title())
        self.tabs.setCurrentIndex(index)
        tab.set_journal(self._current_profile())
        return tab

    def _refresh_tab_title(self, tab) -> None:
        """Update the tab label and window title for ``tab``."""
        index = self.tabs.indexOf(tab)
        if index < 0:
            return
        self.tabs.setTabText(index, tab.title())
        if tab.path is not None:
            self.tabs.setTabToolTip(index, str(tab.path))
        if tab is self._current_tab():
            self._update_window_title()

    def _update_window_title(self) -> None:
        """Reflect the current tab's title in the main window title."""
        tab = self._current_tab()
        if tab is None:
            self.setWindowTitle(APP_NAME)
            return
        self.setWindowTitle(f"{APP_NAME} — {tab.title()}")
        if tab.path is not None:
            self.statusBar().showMessage(str(tab.path))
        else:
            self.statusBar().clearMessage()

    def _current_tab(self):
        """Return the currently visible PaperTab, if any."""
        from epy_papers.tab import PaperTab  # noqa: PLC0415

        widget = self.tabs.currentWidget()
        if isinstance(widget, PaperTab):
            return widget
        return None

    def _on_current_changed(self, _index: int) -> None:
        """Refresh window title and re-run validation on tab switch."""
        self._update_window_title()
        self._run_validation()

    # ------------------------------------------ file actions

    def _new_tab(self):
        """Create an empty untitled tab and focus it."""
        tab = self._create_tab()
        tab.set_initial_text("", path=None)
        return tab

    def _open_dialog(self) -> None:
        """Show an open-file dialog and load selected files in tabs."""
        current = self._current_tab()
        start = (
            str(current.path.parent)
            if current is not None and current.path is not None
            else ""
        )
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "Open paper", start, FILE_FILTER
        )
        for filename in filenames:
            self.open_path(Path(filename))

    def open_path(self, path: Path) -> None:
        """Open ``path`` in a new tab, or focus the existing tab."""
        if not path.is_file():
            QMessageBox.warning(
                self, APP_NAME, f"Not a file:\n{path}"
            )
            return
        path = path.resolve()
        from epy_papers.tab import PaperTab  # noqa: PLC0415

        for i in range(self.tabs.count()):
            existing = self.tabs.widget(i)
            if (
                isinstance(existing, PaperTab)
                and existing.path is not None
                and existing.path.resolve() == path
            ):
                self.tabs.setCurrentIndex(i)
                return
        target = self._current_tab()
        if (
            target is None
            or target.path is not None
            or target.dirty
            or target.text().strip()
        ):
            target = self._create_tab()
        target.load_file(path)
        self._refresh_tab_title(target)
        self._run_validation()

    def _save_current(self) -> bool:
        """Save the current tab, falling back to Save As if needed."""
        tab = self._current_tab()
        if tab is None:
            return False
        if tab.path is None:
            return self._save_current_as()
        tab.save()
        self._refresh_tab_title(tab)
        self.statusBar().showMessage(f"Saved: {tab.path}", 3000)
        self._run_validation()
        return True

    def _save_current_as(self) -> bool:
        """Prompt for a target path and write the current tab there."""
        tab = self._current_tab()
        if tab is None:
            return False
        default = (
            str(tab.path) if tab.path is not None else "paper.md"
        )
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save As", default, FILE_FILTER
        )
        if not filename:
            return False
        target = Path(filename)
        if not target.suffix:
            target = target.with_suffix(".md")
        tab.save_as(target)
        self._refresh_tab_title(tab)
        self.statusBar().showMessage(f"Saved: {target}", 3000)
        self._run_validation()
        return True

    def _reload_current(self) -> None:
        """Discard buffer changes and reload the current tab from disk."""
        tab = self._current_tab()
        if tab is None or tab.path is None:
            return
        if tab.dirty:
            choice = QMessageBox.question(
                self,
                "Reload",
                "Discard unsaved changes and reload from disk?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
        tab.reload()
        self.statusBar().showMessage(f"Reloaded: {tab.path}", 2000)
        self._run_validation()

    # ------------------------------------------ closing logic

    def _confirm_close(self, tab) -> bool:
        """Prompt how to handle a dirty tab. Returns False to abort."""
        if not tab.dirty:
            return True
        name = (
            tab.path.name
            if tab.path is not None
            else "untitled.md"
        )
        choice = QMessageBox.question(
            self,
            "Unsaved changes",
            f"'{name}' has unsaved changes. Save before closing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if choice == QMessageBox.StandardButton.Save:
            self.tabs.setCurrentWidget(tab)
            return self._save_current()
        return choice == QMessageBox.StandardButton.Discard

    def _close_tab_at(self, index: int) -> None:
        """Handle the close button on a specific tab."""
        from epy_papers.tab import PaperTab  # noqa: PLC0415

        widget = self.tabs.widget(index)
        if not isinstance(widget, PaperTab):
            return
        if not self._confirm_close(widget):
            return
        self.tabs.removeTab(index)
        widget.cleanup_preview_tmp()
        widget.deleteLater()
        if self.tabs.count() == 0:
            self._open_welcome_tab()

    def _close_current_tab(self) -> None:
        """Close the active tab via keyboard shortcut."""
        index = self.tabs.currentIndex()
        if index >= 0:
            self._close_tab_at(index)

    def closeEvent(self, event) -> None:  # noqa: N802
        """Prompt to save every dirty tab before exiting."""
        from epy_papers.tab import PaperTab  # noqa: PLC0415

        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, PaperTab) and not self._confirm_close(
                widget
            ):
                event.ignore()
                return
        event.accept()

    # ------------------------------------------ drag & drop

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        """Accept drags that carry file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        """Open every dropped Markdown file in its own tab."""
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                self.open_path(path)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the epy_papers console/GUI script."""
    parser = argparse.ArgumentParser(
        prog="epy_papers",
        description="Paper authoring editor.",
    )
    parser.add_argument(
        "files", nargs="*", help="Paper files to open."
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit.",
    )
    args = parser.parse_args(argv)

    if args.version:
        try:
            from epy_papers import __version__  # noqa: PLC0415
        except Exception:
            __version__ = "0.1.0"
        print(f"epy_papers {__version__}")
        return 0

    app = QApplication.instance() or QApplication(sys.argv)
    logo_pix = _load_branding_pixmap("epy_papers.png")
    if not logo_pix.isNull():
        app.setWindowIcon(QIcon(logo_pix))
    win = PaperWindow()
    win.show()
    for f in args.files:
        p = Path(f)
        if p.exists():
            win.open_path(p)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
