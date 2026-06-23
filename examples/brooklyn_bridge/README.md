# Brooklyn Bridge — journal draft example

A real, submission-style manuscript that exercises the epy_papers pipeline end
to end: from one clean Markdown source it exports a **journal-compliant draft**
for any target journal, in every format that journal accepts.

The paper is a short engineering-history note, *"The Inclined Stays of the
Brooklyn Bridge: Roebling's Hybrid Answer to the Wind"*, by
Ing. Angel Navarro-Mora M.Sc. It uses the full authoring model:

- Bilingual front matter — `title`, `abstract`, `keywords`, each `{en, es}`
- Structured `authors` (affiliation, email, ORCID, corresponding)
- `highlights` and `declarations` (competing interests, AI disclosure)
- A BibTeX bibliography (`bibliography: refs.bib`) with `[@key]` citations
  resolved by the journal's citation style (CSL)
- Display equations and numbered sections

## Files

| File | Role |
|------|------|
| `brooklyn_bridge.md` | The single source manuscript |
| `refs.bib` | BibTeX bibliography |
| `render_drafts.py` | Exports the draft per journal, per format |

## Render the drafts

```bash
pip install -e ".[dev]"   # from the repo root, once
cd examples/brooklyn_bridge
python render_drafts.py
```

Output lands in `examples/brooklyn_bridge/_render/` (git-ignored). For each
target journal the script writes:

- `brooklyn_<journal>.docx` — Word submission manuscript (reference-styled)
- `brooklyn_<journal>.tex` — LaTeX source using the journal's official class
  (`ascelike` for ASCE, `elsarticle` for Elsevier)
- `brooklyn_<journal>.html` — standalone, self-contained HTML preview
- `brooklyn_<journal>.pdf` — typeset PDF, **only when a LaTeX engine is
  available**

The two target journals are **ASCE Journal of Structural Engineering**
(`asce-jse`) and **Elsevier Engineering Structures** (`eng-structures`) — both
structural venues whose official LaTeX class epy_papers bundles, so the
LaTeX/PDF drafts use the journal's real class, not the generic fallback. Pass a
journal id to render just one:

```bash
python render_drafts.py asce-jse
```

## A note on PDF / LaTeX

PDF is the only format that needs a LaTeX engine. epy_papers does **not** bundle
LaTeX: when you export a PDF and no engine is found, the app offers to download a
self-contained TinyTeX (~70 MB) on demand. DOCX, LaTeX source and HTML never
need LaTeX and always work.
