---
title:
  en: "epy_paper User Manual"
  es: "Manual de usuario epy_paper"
language: en
authors:
  - name: "Ing. Angel Navarro-Mora M.Sc."
    orcid: "0000-0002-0539-7014"
    affiliation: "Instituto Tecnologico de Costa Rica"
    email: "ahnavarro@itcr.ac.cr"
    corresponding: true
abstract:
  en: >
    epy_paper is a Python library and desktop editor for authoring
    journal submission manuscripts from a single Markdown source.
    The author writes once and exports a journal-compliant draft for
    any of the 50 supported journals, driven by per-journal profiles.
    This manual documents the public API, the authoring format, the
    desktop editor, and the export workflow.
  es: >
    epy_paper es una librería Python y editor de escritorio para la
    redacción de manuscritos de revistas científicas a partir de una
    única fuente Markdown. El autor escribe una vez y exporta un
    borrador conforme a la revista para cualquiera de las 50 revistas
    soportadas, guiado por perfiles por revista. Este manual documenta
    la API pública, el formato de autoría, el editor de escritorio y el
    flujo de exportación.
keywords:
  en: [manuscript, journal, submission, Markdown, Python]
  es: [manuscrito, revista, envío, Markdown, Python]
highlights:
  - Write the paper once in Markdown; export a draft for any supported journal.
  - 50 journal profiles covering civil, structural, and multidisciplinary venues.
  - Bilingual title, abstract, and keywords for Latin American submission venues.
  - Live preview with bilingual front-matter display and Markdown body rendering.
  - Validation panel flags abstract length, missing bilingual fields, and blinding leaks.
declarations:
  credit: "A.N.M.: conceptualization, methodology, software, writing."
  competing-interests: "The author declares no competing interests."
  data-availability: "Data and source code are available at the project repository."
  funding: "This work received no external funding."
  ai-disclosure: "No generative AI tools were used in writing this manual."
bibliography: refs.bib
---

# Introduction

epy_paper solves a practical problem faced by every researcher who submits to
multiple journals: formatting. The manuscript content — title, abstract, body,
references — is always the same. What changes is the layout, the citation style,
the font, and the structural requirements of each journal.

The epy_paper approach is simple: write the full paper **once** in a structured
Markdown format, then export a journal-compliant **draft** for each target venue.
A draft is a ready-to-submit Word, LaTeX, or PDF file styled according to the
journal's requirements. The editorial team handles the final typesetting into two
columns and the publisher's house style; what you deliver is a clean,
well-structured manuscript, not a pixel-perfect copy of the journal layout.

This document is itself written in the epy_paper authoring format. You can read
it in the live preview on the right, use the toolbar menus to insert elements,
and open this buffer as a starting point for your own paper.


# Authoring Format

A paper source file is a plain-text Markdown file with a YAML front-matter block
at the top. The front matter contains all structured metadata; the body contains
the prose.

## YAML Front Matter

The front matter is delimited by triple dashes (`---`). Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `title` | bilingual string or string | Paper title |
| `authors` | list of author objects | Author list |
| `abstract` | bilingual string or string | Paper abstract |
| `keywords` | bilingual list or list | Index keywords |
| `bibliography` | string | Path to BibTeX `.bib` file |

Optional fields:

| Field | Type | Description |
|-------|------|-------------|
| `language` | string | Primary language (`en` or `es`) |
| `highlights` | list of strings | 3-5 highlights (max 85 chars each) |
| `declarations` | object | Author declarations (credit, funding, etc.) |

### Bilingual Fields

Fields that accept bilingual content use a dictionary with language keys:

```yaml
title:
  en: "Nonlinear Pushover Analysis of RC Frames"
  es: "Análisis pushover no lineal de marcos de concreto"
abstract:
  en: "This paper presents..."
  es: "Este artículo presenta..."
keywords:
  en: [pushover, seismic, reinforced concrete]
  es: [pushover, sísmico, concreto reforzado]
```

When a field is a simple string, it is treated as the primary language value.

### Author Objects

Each entry in the `authors` list may include:

```yaml
authors:
  - name: "Ing. Angel Navarro-Mora M.Sc."
    orcid: "0000-0002-0539-7014"
    affiliation: "Instituto Tecnologico de Costa Rica"
    email: "ahnavarro@itcr.ac.cr"
    corresponding: true
```

All fields except `name` are optional. Set `corresponding: true` for the
corresponding author.

### Declarations

The `declarations` block accepts any key-value pairs. Common keys recognized
by journal profiles include:

- `credit` — CRediT author contribution statement
- `competing-interests` — conflict of interest statement
- `data-availability` — data availability statement
- `funding` — funding sources
- `ai-disclosure` — AI use disclosure

### Highlights

Highlights are short bullet points summarizing the main findings. The
validation system checks:

- Between 3 and 5 highlights are present.
- Each highlight is at most 85 characters long.

## Body

The body is standard Markdown, placed after the closing `---` of the front
matter. All standard Markdown features are supported:

- `# Heading 1`, `## Heading 2`, `### Heading 3` (auto-numbered by journals)
- `**bold**`, `*italic*`
- Bullet lists and numbered lists
- Fenced code blocks
- Pipe tables
- Images with captions

### Cross-references and Labels

Use Quarto-style labels to create cross-referenceable elements. The label
goes in curly braces `{#kind-N}` immediately after the element:

```markdown
![Figure 1: Description](figures/fig1.png){#fig-1 width=80%}

: Table 1: Caption {#tbl-1}

| A | B |
|---|---|
| 1 | 2 |

$$
\sigma = E \varepsilon
$$ {#eq-1}
```

Cite these with `@fig-1`, `@tbl-1`, `@eq-1` in the body text.

### Citations

Cite bibliography entries with `[@key]` or `@key`. The key must be present
in the linked `.bib` file. The citation style is determined by the journal
profile.

```markdown
The result follows from classical beam theory [@timoshenko_1951].
```


# Public API

epy_paper exposes a clean, minimal Python API. All public symbols are
importable from the top-level package.

## Paper Class

The central class is `Paper`. It wraps a manuscript source and provides
methods for validation and export.

```python
from epy_paper import Paper

# Create from source text
paper = Paper(source_text, base_dir=Path("."))

# Create from a file path
paper = Paper.from_file(Path("manuscript.md"))
```

**Constructor signature:**

```python
Paper(source: str, base_dir: Path | str | None = None)
```

- `source`: Full Markdown source text including YAML front matter.
- `base_dir`: Directory used to resolve relative paths (e.g., images,
  bibliography files). Defaults to the current working directory.

### Paper.from_file

```python
@classmethod
Paper.from_file(path: Path | str) -> Paper
```

Reads the file at `path`, sets `base_dir` to the file's parent directory,
and returns a `Paper` instance. Equivalent to:

```python
path = Path(path)
paper = Paper(path.read_text(encoding="utf-8"), base_dir=path.parent)
```

### Paper.validate

```python
paper.validate(journal_id: str) -> ValidationResult
```

Validates the manuscript against the profile for `journal_id`. Returns a
`ValidationResult` which is iterable (yields `Warning` objects) and
truth-evaluates to `True` when there are no ERROR-severity findings.

```python
result = paper.validate("asce_journal_structural_engineering")
if not result.ok:
    for warning in result:
        print(warning)  # [ERROR] Abstract exceeds 250 words
```

### Paper.to_draft

```python
paper.to_draft(
    journal_id: str,
    out_path: Path,
    *,
    fmt: str | None = None,
) -> Path
```

Exports a journal-compliant draft to `out_path`. The format is inferred
from `out_path.suffix` when `fmt` is not given. Supported values for `fmt`:

- `"docx"` — Word document using the journal's reference DOCX template
- `"tex"` — LaTeX source using the journal's document class
- `"pdf"` — PDF compiled from LaTeX via `pdflatex`
- `"html"` — Standalone HTML preview

```python
path = paper.to_draft("ieee_access", Path("draft_ieee.docx"))
```

Raises `PandocMissingError` when Pandoc is not installed and `OSError`
for I/O failures.

### Paper.render_notes

```python
paper.render_notes(journal_id: str, fmt: str) -> list[str]
```

Returns a list of notes about the export without actually performing it.
Notes describe fallbacks, missing assets, and format-specific gaps.

```python
notes = paper.render_notes("elsevier_energy", "docx")
for note in notes:
    print(note)
```

## Catalog Functions

### available_journals

```python
from epy_paper import available_journals

journals = available_journals()
# Returns: [("asce_journal_structural_engineering", "ASCE Journal of ..."), ...]
```

Returns a list of `(journal_id, journal_name)` tuples for all 50 bundled
journal profiles, sorted alphabetically by name.

### journal_profile

```python
from epy_paper import journal_profile

profile = journal_profile("ieee_access")
# Returns: {"name": "IEEE Access", "formats": ["docx", "tex"], ...}
```

Returns the raw profile dictionary for a given journal id.

### load_journals

```python
from epy_paper import load_journals

all_profiles = load_journals()
# Returns: {"asce_journal_structural_engineering": {...}, ...}
```

Loads and returns the full journals dictionary. Keys starting with `_` are
stripped (they are internal metadata).

### add_journal

```python
from epy_paper import add_journal, available_journals

add_journal(
    "my-journal",
    {"name": "My Journal", "columns": 1, "spacing": "double",
     "line_numbers": "continuous", "font_size_pt": 12,
     "page_size": "letter", "csl": "ieee", "formats": ["docx", "tex"]},
)
```

Adds or updates a journal profile in the writable user catalog
(`~/.epy_paper/journals.json`, or `$EPY_PAPER_USER_JOURNALS`), merged on top of
the bundled catalog so it survives app updates. In the desktop editor the **+**
button beside the Journal selector opens a dialog that does the same, and the
new journal appears in the selector immediately. `remove_user_journal(id)`
deletes a user entry.

When a journal is selected, both the live preview and the exported draft are
reformatted to that journal's submission rules — single/double column, line
spacing, font size, page size and continuous line numbers — so the draft is not
just validated but formatted ready to submit.

## Validation API

```python
from epy_paper import Severity, Warning, ValidationResult
```

- `Severity.ERROR` — must be fixed before submission
- `Severity.WARNING` — should be reviewed
- `Severity.INFO` — informational note

`Warning(code, severity, message)` is a frozen dataclass. `str(warning)`
returns `"[SEVERITY] message"`.

`ValidationResult` is iterable, has `len()`, and the `.ok` property is
`True` when there are no `ERROR`-severity findings.

## Exception Classes

```python
from epy_paper import PandocMissingError
```

Raised by `Paper.to_draft` and `Paper.render_notes` when Pandoc is not
found on the system PATH or via `pypandoc-binary`.


# Desktop Editor

The epy_paper desktop editor (`python -m epy_paper`) provides a
multi-tab Markdown editor with a live academic preview on the right side.

## Starting the Editor

```bash
python -m epy_paper                  # open with welcome tab
python -m epy_paper manuscript.md    # open a specific file
python -m epy_paper --version        # print version
```

Or use the installed GUI entry point:

```bash
epy_paper manuscript.md
```

## Toolbar Menus

The toolbar contains six dropdown menus:

| Menu | Contents |
|------|----------|
| **File** | New, Open, Save, Save As, Reload, Close Tab, Quit |
| **Text** | Bold, Italic, Insert Link |
| **Paper** | Insert front-matter blocks and body elements |
| **Export** | Export DOCX, LaTeX, PDF, HTML |
| **View** | Theme (when epy_reports is installed), Language |
| **Help** | User Manual (English), User Manual (Spanish), About |

## Journal Selector

The toolbar contains a **Journal** dropdown populated from all 50 bundled
journal profiles. Select a journal before validating or exporting to apply
that journal's requirements and citation style.

The selected journal is persisted across sessions.

## Validation Panel

The validation dock on the right side lists all issues for the current
paper against the selected journal. Each item is color-coded by severity:

- Red — ERROR (must fix before submission)
- Orange — WARNING (should review)
- Blue — INFO (informational)

Click the **Validate** button or press `Ctrl+Shift+V` to run validation.
Validation also runs automatically when you switch tabs or change the
selected journal.

## Paper Menu — Inserting Elements

The **Paper** menu provides one-click insertion of all structured elements:

| Action | Shortcut | Inserts |
|--------|----------|---------|
| Insert Title Block | Ctrl+Shift+Y | Full YAML front-matter template |
| Insert Authors | — | Authors YAML block |
| Insert Abstract | — | Bilingual abstract block |
| Insert Keywords | — | Bilingual keywords block |
| Insert Highlights | — | Highlights list |
| Insert Declarations | — | Declarations block |
| Insert Figure | Ctrl+Shift+F | Figure Markdown with label |
| Insert Table | Ctrl+Shift+T | Pipe table with caption |
| Insert Equation | Ctrl+Shift+Q | Display equation with label |
| Insert Citation | Ctrl+Shift+C | Citation placeholder |
| Insert Code Block | Ctrl+Shift+K | Fenced code block |


# Export Formats

## DOCX (Word)

The DOCX export uses Pandoc with the journal's bundled reference DOCX
template. The reference document sets the styles (heading fonts, paragraph
spacing, citation format) so the resulting file is ready to submit.

**Shortcut:** `Ctrl+Shift+D`

```python
paper.to_draft("asce_journal_structural_engineering",
               Path("submission.docx"), fmt="docx")
```

## LaTeX

The LaTeX export uses the journal's document class when bundled. For
journals without a bundled class, a generic LaTeX template is used.

```python
paper.to_draft("elsevier_energy", Path("draft.tex"), fmt="tex")
```

The resulting `.tex` file can be compiled with `pdflatex` or submitted to
journal portals that accept LaTeX source.

## PDF

The PDF export compiles the LaTeX source via `pdflatex`. Requires a working
LaTeX installation in addition to Pandoc.

```python
paper.to_draft("ieee_access", Path("draft.pdf"), fmt="pdf")
```

## HTML

The HTML export produces a standalone preview page. It is useful for
proofreading and sharing before submission but is not a submission format.

```python
paper.to_draft("nature", Path("preview.html"), fmt="html")
```


# Supported Journals

epy_paper bundles 50 journal profiles covering major civil, structural,
and multidisciplinary engineering venues. A few examples:

| ID | Journal Name |
|----|-------------|
| `asce_journal_structural_engineering` | ASCE Journal of Structural Engineering |
| `asce_journal_bridge_engineering` | ASCE Journal of Bridge Engineering |
| `elsevier_energy` | Elsevier Energy |
| `elsevier_engineering_structures` | Engineering Structures (Elsevier) |
| `ieee_access` | IEEE Access |
| `nature` | Nature |
| `springer_bulletin_earthquake_engineering` | Bulletin of Earthquake Engineering |

Use `available_journals()` to get the full list programmatically.


# Figure Example

The figure below illustrates the epy_paper workflow: the author writes
once in Markdown, selects a journal from the dropdown, and exports a
compliant draft. The journal profile controls the template, citation
style, and validation rules.

![Figure 1: epy_paper export workflow](figures/workflow.png){#fig-1 width=80%}


# Table Example

Table @tbl-1 summarizes the supported export formats.

: Table 1: Export formats and their characteristics. {#tbl-1}

| Format | Extension | Notes |
|--------|-----------|-------|
| DOCX   | .docx     | Word submission, journal-styled reference |
| LaTeX  | .tex      | LaTeX class when bundled; generic template otherwise |
| PDF    | .pdf      | Built from LaTeX via pdflatex |
| HTML   | .html     | Preview only; not a submission format |


# Equation Example

The energy-mass equivalence from special relativity (@eq-1) is a classic
example of a display equation in epy_paper:

$$
E = mc^2
$$ {#eq-1}

Equations are numbered automatically in the LaTeX and DOCX outputs. In the
live preview, display math is rendered as plain text; install the `markdown`
package with math extensions for richer preview rendering.


# Code Example

The following snippet shows a complete end-to-end usage of the epy_paper
API:

```python
from pathlib import Path
from epy_paper import Paper, available_journals

# List all supported journals
for jid, jname in available_journals():
    print(f"{jid}: {jname}")

# Load a paper source file
paper = Paper.from_file(Path("manuscript.md"))

# Validate against a journal
result = paper.validate("asce_journal_structural_engineering")
if result.ok:
    print("No errors found.")
else:
    for w in result:
        print(w)

# Export a DOCX draft
draft = paper.to_draft(
    "asce_journal_structural_engineering",
    Path("submission.docx"),
    fmt="docx",
)
print(f"Draft written to: {draft}")
```


# Citation Example

This manual cites the author's prior work on structural analysis and
seismic assessment [@navarro_mora_2024]. Full citation details are in the
linked bibliography file `refs.bib`.

For multiple citations, use a semicolon-separated list:
`[@author_2020; @author_2021]`.


# Quick-Start Checklist

1. Open epy_paper from the command line: `python -m epy_paper`
2. Use **Paper > Insert Title Block** to insert the front-matter template.
3. Fill in your title, authors, abstract, keywords, and bibliography path.
4. Write your paper body in Markdown using the Paper menu to insert
   figures, tables, equations, and citations.
5. Select your target journal from the Journal dropdown in the toolbar.
6. Press `Ctrl+Shift+V` to validate. Fix any errors before exporting.
7. Use **Export > Export DOCX** (`Ctrl+Shift+D`) to generate the draft.
8. Submit the draft to the journal's manuscript portal.
