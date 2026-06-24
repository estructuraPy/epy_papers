# Changelog

All notable changes to `epy_papers` are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
