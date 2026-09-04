# Changelog

All notable changes to `epy_papers` are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] — 2026-09-04

### Added
- **An autosave the user can turn on or off.** A checkable *Autosave*
  action in the View menu, off on a fresh install and remembered between
  sessions. It writes only the current paper, only when it has a path
  and unsaved changes, and never while an export is running; a paper
  that has never been saved is skipped rather than raising a Save As
  dialog on somebody mid-sentence. Validation is not re-run on an
  autosave: that is what a person asks for on an explicit save.
- **Saves are atomic.** Every save, manual or automatic, writes a
  complete sibling file and renames it into place
  (`epy_export.write_text_atomic`), so a save that dies mid-write cannot
  truncate the only copy.

### Fixed
- **A PDF export froze the window for the whole LaTeX compile.**
  `Paper.to_draft` ran on the GUI thread: seconds on a note, minutes on
  a paper with figures, and for all of it the window stopped repainting,
  so the application looked hung and Windows offered to close it. The
  compile now runs on a worker thread behind the busy dialog the TinyTeX
  download already used. A second export while one is running is
  refused instead of writing the same file twice, and the retry after
  installing LaTeX happens exactly once.
- **An HTML export that failed said nothing in the status bar**, so a
  reader who dismissed the dialog had no trace left of what happened.
- **Fifteen interface strings were English in the Spanish UI** — the
  View menu, the LaTeX install offer and its failure, the reload and
  unsaved-changes prompts, the HTML export failure, the design block and
  theme dialogs, and the editor's placeholder. This dictionary had 58
  entries where epy_slides has 313.

### Changed
- The settings scope now takes its organisation name from
  `epy_export.ORGANIZATION`. It was spelled two ways across the family,
  which on Windows is two registry trees: ePy Studio read one and this
  editor wrote the other, so the language a reader chose here was never
  found by the launcher.

## [0.3.1] — 2026-08-06

### Fixed
- **The Ubuntu `.deb` builder wrote nowhere and versioned itself 0.0.0.**
  Its path arithmetic pointed above the repository, so it read a
  `pyproject.toml` that does not exist and aimed its output at a folder
  that no longer exists. Both are corrected, and the version reader now
  falls back to the package `__version__`.
- **Theme assets are read through one loader.** `_core/epyson` built its
  own `importlib.resources` lookups; every read now goes through
  `_config/_loader`, and a missing `colors.epyson` fails loudly instead
  of silently emptying every theme's callout colours.
- The bundled brand logos (`estructurapy.png`, `imagotipo_anm.png`) were
  missing from the packaging assets, so only this app lacked them there.
- `REQUIREMENTS.md` still pointed at pre-refactor module paths.

### Changed
- **Internal layout aligned with epy_reports and epy_slides** — same
  folders and module names across the three apps. The modules under
  `_core/` are packages (they were loose files here), `_render` is now
  `renderer` as in its siblings, the build tools lost their `installer/`
  and `tools/` wrappers, and the `Theme` model and catalogue moved to
  `_core`. No public API changed.

## [0.3.0] — 2026-08-05

### Fixed
- **Preview links.** In the Pandoc (journal) preview, citation, footnote
  and section links now jump in-page: the preview `<base href>` (needed
  for relative figures) was capturing every `href="#id"` and navigating
  the preview away. `target="_blank"` links were silently swallowed;
  they now open in the system browser.

### Added
- **Back/Forward in the preview.** Back returns the preview to the exact
  position it left before following a link (`Alt+Left` / `Alt+Right` or
  the context menu); re-renders no longer pollute the navigation history.

## [0.2.0] — 2026-08-05

### Added
- **Windows file-association CLI.** `epy_papers --register [--as-default]`,
  `--unregister` and `--set-default` now exist (HKCU, no admin), mirroring
  epy_reports: the app appears under "Open with" for `.md` / `.markdown`
  and in Settings > Default apps. The installer's `[Run]` entries — which
  always invoked these flags — finally work.

### Fixed
- **Qt startup crash in conda environments (Windows).** The package now
  pins the System32 ICU at import time (`_pin_system_icu`), preventing
  `ImportError: DLL load failed ... (WinError 127)` when conda's
  `Library\bin` ICU shadows the Windows one Qt links against.

## [0.1.7] — 2026-06-24

### Added
- **Illustrated user manual.** The in-app User Manual now walks through the
  desktop interface with real screenshots — the editor (Markdown source +
  journal-formatted live preview + validation panel), the theme gallery, and
  the design-block picker — in both English and Spanish. `__SHOT_*__`
  placeholders resolve to the bundled screenshots (mirroring the sibling apps),
  and `tools/capture_screenshots.py` regenerates them from the real UI.
- Tests covering the corrupt user-journal catalog warnings.

## [0.1.6] — 2026-06-24

### Changed
- **Example affiliation.** The Brooklyn Bridge example now lists the author
  affiliation as *ANM Ingeniería, Cartago, Costa Rica*.

## [0.1.5] — 2026-06-23

### Added
- **Insert ▸ Disclosure.** A typed disclosure note — AI assistance, document
  integrity, confidentiality or draft — inserted from the *Paper ▸ Disclosure*
  submenu and styled by the theme. The Brooklyn example now carries an AI-use
  disclosure inserted with this block.

## [0.1.4] — 2026-06-23

### Added
- `examples/brooklyn_bridge/` — a real submission-style manuscript with a
  `render_drafts.py` harness that exports the draft for ASCE and Elsevier
  targets in DOCX, LaTeX, HTML and (when a LaTeX engine is available) PDF.
- This changelog.

### Changed
- The bundled journal catalog is now the single source of truth
  (`src/epy_papers/data/journals.json`); the duplicate repo-root `data/` copy
  was removed.
- The Windows build generates its own icon in CI (`installer/make_icon.py`) and
  the PyInstaller spec no longer falls back to a sibling repository's icon, so
  the build is self-contained.

## [0.1.3] — 2026-06-23

### Added
- **On-demand LaTeX for PDF export.** PDF is the only format that needs a LaTeX
  engine, and epy_papers does not bundle one. When you export a PDF and no
  engine is found, the app offers to download a self-contained TinyTeX
  (~70 MB). The renderer resolves an engine on `PATH` or the managed TinyTeX and
  passes it to Pandoc explicitly, so PDF works even when LaTeX is not on `PATH`.

### Fixed
- PDF export now compiles for the bundled journal classes (`ascelike`,
  `elsarticle`, `IEEEtran`): the manuscript template supplies the preamble
  Pandoc expects (citeproc, longtable, counters), fixing the previous build
  errors.
- Manuscript line numbers no longer overlap in the preview.
- Exporting from an unsaved manuscript no longer fails to find the bibliography
  or images kept next to the output file.

## [0.1.2] — 2026-06-23

### Added
- Visual theme gallery and design-block picker, shared with the rest of the
  document suite so all three apps expose the same insert options.

## [0.1.0] — 2026-06-20

Initial release. `epy_papers` is a desktop manuscript editor: write a paper
once as one Markdown source and export a journal-compliant submission draft
(DOCX / LaTeX / HTML / PDF) for any of the 50 bundled journal profiles, with the
journal's page geometry, spacing, line numbering and citation style applied.
