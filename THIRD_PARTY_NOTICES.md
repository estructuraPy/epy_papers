# Third-Party Notices and Asset Licensing

epy_paper's **source code** is licensed under the MIT License (see
[LICENSE](LICENSE)). The distributed application bundles or links the
following third-party components, each governed by its own license.

## Bundled / linked components

| Component | License | Notes |
|---|---|---|
| [Qt for Python (PySide6)](https://www.qt.io/qt-for-python) | LGPL-3.0 | Dynamically linked. The frozen distribution keeps the Qt shared libraries as separate files (PyInstaller onedir layout), so they can be replaced as required by the LGPL. Source: <https://code.qt.io/> |
| [Pandoc](https://github.com/jgm/pandoc) | GPL-2.0-or-later | Distributed as a separate, unmodified executable (`pandoc`) invoked as an external tool — mere aggregation, not a derived work. Source code: <https://github.com/jgm/pandoc> |
| [pypandoc](https://github.com/JessicaTegner/pypandoc) | MIT | Python wrapper used to call Pandoc. |
| [PyYAML](https://pyyaml.org/) | MIT | Parses the manuscript YAML front matter. |
| [python-docx](https://github.com/python-openxml/python-docx) | MIT | Build-time only — generates the Word submission reference document. |
| [PyInstaller](https://pyinstaller.org/) | GPL-2.0 with bootloader exception | Build-time only; the exception explicitly permits distributing frozen applications under any license. |
| [Inno Setup](https://jrsoftware.org/isinfo.php) | Inno Setup License | Build-time only (Windows installer compiler). |

## Bundled citation and typesetting resources (each under its own license)

These files are redistributed **unmodified** for the user's convenience and
remain the property of their respective authors. They are **not** covered by
the MIT license above:

| Resource | License | Source |
|---|---|---|
| `assets/csl/*.csl` — Citation Style Language styles | CC BY-SA 3.0 | <https://github.com/citation-style-language/styles> |
| `assets/latex/elsarticle.cls`, `elsarticle-*.bst` (Elsevier) | LaTeX Project Public License (LPPL) | <https://ctan.org/pkg/elsarticle> |
| `assets/latex/IEEEtran.cls` (IEEE) | LaTeX Project Public License (LPPL) | <https://ctan.org/pkg/ieeetran> |
| `assets/latex/ascelike.cls`, `ascelike.bst` (ASCE community class) | see the package's own terms on CTAN | <https://ctan.org/pkg/ascelike> |

## Proprietary assets (NOT covered by the MIT license)

The following bundled assets are Copyright (c) 2026
**Ing. Angel Navarro-Mora M.Sc. / ANM Ingeniería (estructuraPy)** —
**all rights reserved**:

- `src/epy_paper/assets/reference_docx/submission.docx` — the Word
  submission reference (style) template.
- `assets_build/` — source image(s) for the application icon and any
  ANM Ingeniería / estructuraPy brand images.

These assets are licensed to you **only for use as an integral part of
unmodified epy_paper distributions**. Extracting, modifying, rebranding, or
redistributing them separately — in particular for use with other
manuscript-generation products — requires prior written permission from
ANM Ingeniería (<ahnavarro@anmingenieria.com>).
