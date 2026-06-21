# epy_papers — Minimum requirements for the paper publication system

**Author / credit:** Ing. Angel Navarro-Mora M.Sc. · ANM Ingeniería
**Status:** requirements derived from a survey of 30+ journals (see
`docs/journal_survey.md` and `data/journals.json`).

## 1. The core idea (what the system does)

The author writes the paper **once**, as a single clean "final" source
(Markdown/Quarto, the same authoring model as epy_reports). From that one
source the system must export, on demand, a **journal-compliant submission
draft (manuscript)** for any target journal, exactly as that journal's
"Instructions for Authors" require.

The decisive finding of the survey is that **the published two-column typeset
layout is produced by the publisher, not the author**. The author's job is the
**submission manuscript**, and across virtually every journal the submission
manuscript follows one small, recurring template that is then parameterised per
journal. So epy_papers does NOT need to reproduce 30 different final layouts — it
needs ONE good manuscript engine with a handful of tunable parameters, plus a
per-journal **profile** that sets those parameters.

Two outputs are therefore always available:
- **Final / preview** — a clean, readable rendering for the author (close to the
  published look), so the author sees a finished paper while writing.
- **Draft / manuscript** — the submission-ready document for the chosen journal,
  built from the journal profile.

## 2. The universal submission-manuscript formula (the minimum feature set)

Every parameter below was observed across the survey; the system must support
the full range. Defaults match the most common requirement.

| Parameter | Range observed | Default |
|---|---|---|
| Columns | single (most) · double (IEEE TPAMI, REVTeX reprint) | single |
| Line spacing | double (review standard) · 1.5 · single | double |
| Line numbers | continuous · per-page · off | continuous |
| Body font | serif, Times New Roman 12 pt · 11 pt (JMLR) · 10 pt (IEEE) | TNR 12 pt |
| Page size | US Letter · A4 (ACS forbids A4) | Letter |
| Margins | 1 in / 2.5 cm · class-controlled | 1 in |
| Figure placement | inline at first citation · all at end · separate files | inline (toggle: end) |
| Table placement | inline · at end | inline (toggle: end) |
| Figure captions | below figure | below |
| Table captions | above table | above |
| Title page | integrated · separate page | integrated (toggle: separate) |
| Author blinding | none · anonymised manuscript | none (toggle: anonymise) |

**Structural elements the engine must be able to emit/validate:**
- Title (with optional character limit, e.g. ACI 70, ASCE 100).
- **Bilingual title / abstract / keywords** — a hard requirement of Latin-
  American journals (≈ 6 of 7 surveyed: titulo + title, resumen + abstract,
  palabras clave + keywords). The source must model these as language-keyed
  fields (`title.es` / `title.en`, `abstract.es` / `abstract.en`,
  `keywords.es` / `keywords.en`) independent of the body language, and the
  profile decides which language pair (and ordering) a given journal needs.
- Abstract (structured or unstructured) with a configurable **word-limit check**
  (125 Science · 150 ACI/Nature/Cell · 150–175 ASCE · 200 JMLR/MDPI ·
  250 Elsevier/ACS/PNAS · 300 PLOS/Lancet).
- Keywords / index terms (configurable count limit, 0–10).
- **Highlights** block (Elsevier: 3–5 bullets, ≤ 85 chars each) — optional.
- **Graphical abstract / TOC graphic** (ACS, Angewandte) — optional.
- Standard declarations, each toggleable per profile: Data Availability,
  Author Contributions (CRediT), Competing Interests, Funding, AI/GenAI
  disclosure, ORCID, ethics/registration.
- Domain panels: ASCE "Practical Applications", Lancet "Research in Context".
- Figure-legend list and table-caption list pages (for "figures at end" mode).

## 3. Citation styles (integrate ALL of these)

Citation style is per-journal and must be selectable. The system ships the
Citation Style Language (CSL) files for at least:

- **Numbered, square brackets `[1]`** — IEEE, Elsevier (`elsarticle-num`:
  Engineering Structures, JCSR, Structural Safety, Thin-Walled), APS/PRL,
  Nature, Angewandte, BioResources, Springer.
- **Numbered, superscript** — ACS / JACS, ACI Structural, Vancouver
  (Lancet, NEJM, PLOS ONE).
- **Author–year** — ASCE (its own author-date), APA, Chicago author-date
  (JEE/T&F, Drvna Industrija), JMLR (natbib), Harvard, MLA, AMA, Science.

The bundled CSL set lives in each app's `assets/csl/` and is shared with
epy_reports and epy_slides (same set, same picker). The current set:
apa, ieee, vancouver (via elsevier-vancouver), chicago-author-date,
chicago-note-bibliography, harvard, mla, acs, ama, nature, science,
american-society-of-civil-engineers (ASCE), elsevier-harvard, elsevier-vancouver,
springer-basic-author-date, american-political-science-association.

## 4. Journal profiles (the catalog)

A **journal profile** is a small data record (see `data/journals.json`) that
binds a journal name to the parameters above plus its limits and required
sections. Selecting a journal applies its profile to the one source and
produces the compliant draft. Profiles are data, not code, so adding a journal
is a catalog edit, not a release.

Minimum catalog: **30 journals** (survey delivered this), preferred 50, of which
**≥ 3 with a civil/structural focus** (the survey already includes ASCE Journal
of Structural Engineering, Engineering Structures, Journal of Constructional
Steel Research, ACI Structural Journal, Structural Safety, Thin-Walled
Structures, Journal of Earthquake Engineering — well above the minimum), plus
**ASCE** explicitly. Latin-American (5) and Costa-Rican (2) journals are included
(Revista Tecnología en Marcha, Revista Forestal Mesoamericana Kurú, Maderas.
Ciencia y Tecnología, …).

### Output engines per profile
- **LaTeX** using the journal's official class when one exists (`IEEEtran`,
  `elsarticle`, `ascelike-new`, `achemso`, `revtex4-2`, T&F `interact`) — the
  most faithful route; the profile names the class + options.
- **DOCX manuscript** for Word-only journals (ACI forbids LaTeX; Lancet/NEJM
  prefer Word) — Pandoc + a manuscript reference doc parameterised by the
  profile (double-spaced, line-numbered, single-column).
- **PDF preview** from either, for the author.

## 5. Validation (what the system checks before export)

Per the selected profile, warn (not block) on: abstract over the word limit,
title over the character limit, too many keywords, missing required declarations,
missing highlights when required, figures inline when the journal wants them at
the end, wrong page size (A4 for ACS), wrong citation style.

## 6. Test cases (replication targets)

The publications of Ing. Angel Navarro-Mora (see
`docs/navarro_mora_publications.md`) are the acceptance fixtures: the system must
reproduce the submission draft of each venue (Revista Tecnología en Marcha,
Drvna Industrija, BioResources, Maderas. Ciencia y Tecnología, Journal of
Renewable Materials, IABSE Congress, …). There is no relationship between the
author and the formats — they are validation fixtures only.

## 6b. Authoring source format (the one source)

The author writes the paper **once** in a single Markdown file: a YAML front
matter (everything the submission draft needs, journal-independent) followed by
a Markdown body. Title / abstract / keywords accept either a plain scalar
(single language) or an ``{es, en}`` mapping (bilingual); ``language`` (default
``en``) names the primary variant, and the journal profile decides whether BOTH
are emitted. See `src/epy_papers/_authoring.py` and the fixtures under
`tests/fixtures/`.

```yaml
---
title:
  en: Structural health index for prioritizing bridge interventions
  es: Indice de salud estructural para la priorizacion de intervenciones
language: es
authors:
  - name: Angel Navarro-Mora
    orcid: 0000-0002-0539-7014
    affiliation: Instituto Tecnologico de Costa Rica
    email: ahnavarro@itcr.ac.cr
    corresponding: true
abstract:
  en: >
    A bridge health index is proposed to ...
  es: >
    Se propone un indice de salud estructural ...
keywords:
  en: [bridges, structural health, prioritization]
  es: [puentes, salud estructural, priorizacion]
highlights:                     # Elsevier: 3-5 bullets, <= 85 chars each
  - A reusable manuscript engine driven by per-journal profiles.
declarations:                   # emitted when the profile requires them
  credit: "A.N.M.: conceptualization, methodology, writing."
  competing-interests: "The authors declare no competing interests."
  data-availability: "Data are available on request."
  funding: "This work received no external funding."
  ai-disclosure: "No generative AI tools were used."
bibliography: refs.bib
---

# Introduction

Body text with citations [@key] ...
```

**Content blocks the engine assembles per profile** (`src/epy_papers/_blocks.py`):
title page (author identity stripped when double-blind), bilingual
title/abstract/keywords (both languages when the profile is bilingual, primary
first), Highlights list (when the profile requests it), and a Declarations
section (CRediT author statement, competing interests, funding, data
availability, AI disclosure, ASCE Practical Applications, Lancet Research in
Context).

## 6c. Rendering pipeline (universal template + per-profile overrides)

One universal manuscript (single column, double spaced, continuous line
numbers, 12 pt serif, Letter/A4) parameterised per profile
(`src/epy_papers/_render.py`):

- **DOCX** — Pandoc + a generated reference document
  (`assets/reference_docx/submission.docx`, built by
  `tools/make_reference_docx.py`) carrying the body font, double spacing,
  page geometry and heading styles.
- **LaTeX / PDF** — Pandoc + `assets/templates/manuscript.latex` plus the
  journal's **official class** when bundled (`assets/latex/`): `elsarticle`
  (Elsevier), `IEEEtran` (IEEE), `ascelike` (ASCE), with their `.bst` styles.
  A journal whose class is not bundled (e.g. `svjour3`, `revtex4-2`,
  `interact`, `achemso`, `mdpi`, `jmlr2e`) falls back to the generic
  `article` template and the gap is recorded on the renderer (the build never
  fails). Profile overrides: spacing -> line stretch; `line_numbers` ->
  `lineno`; `page_size` -> `letterpaper`/`a4paper`; figures/tables `end` ->
  `endfloat`; `font_size_pt` -> base size.

## 6d. Validation (structured)

`Paper.validate(journal)` returns a typed `ValidationResult` of `Warning`
records (`code`, `severity`, `message`) instead of plain strings
(`src/epy_papers/_validation.py`). It checks: abstract word count (per language),
title char limit, keyword min/max, highlights count and per-item char limit,
bilingual presence when required, required declarations present, double-blind
compliance (author identity removed), page size and citation style. It never
blocks — every surveyed journal phrases its rules as recommendations.

## 7. Ecosystem conventions (must follow)

- **One public API** per the suite convention: `from epy_papers import PaperWriter`
  (a single facade), mirroring `epy_reports`, `epy_slides`, `epy_project`, etc.
- Licensing, packaging (PyInstaller onedir + Inno Setup + `.deb`), themes and
  bilingual UI follow the same standards as epy_reports/epy_slides.
- Generated artefacts (code, UI, docs) in English; chat in Spanish.
