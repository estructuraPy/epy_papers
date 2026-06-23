"""Pandoc-driven rendering of the submission manuscript.

One universal manuscript template (single column, double spaced, continuous
line numbers, 12 pt serif, Letter/A4) is parameterised per journal profile:

- **DOCX** uses a generated reference document
  (``assets/reference_docx/submission.docx``) for the page geometry, double
  spacing and Times New Roman body; per-profile spacing / page size are passed
  as Pandoc metadata that the reference doc respects.
- **LaTeX / PDF** use a bundled Pandoc template
  (``assets/templates/manuscript.latex``) plus the journal's official class
  (``elsarticle`` / ``IEEEtran`` / ``ascelike``) when the profile names one and
  the class file is bundled; otherwise a generic ``article`` fallback is used
  and the gap is recorded on the renderer.

Layout overrides driven by the profile:

- ``spacing`` -> line stretch (single / 1.5 / double).
- ``line_numbers`` -> ``lineno`` package (LaTeX) / metadata (DOCX).
- ``page_size`` -> ``letterpaper`` / ``a4paper``.
- ``figures``/``tables`` == ``end`` -> ``endfloat`` (LaTeX) + a metadata flag.
- ``font_size_pt`` -> base font size.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from ._authoring import Manuscript
from ._blocks import compose_manuscript

__all__ = ["Renderer", "PandocMissingError"]

# LaTeX classes we bundle and can therefore select faithfully.
_BUNDLED_CLASSES = {"elsarticle", "IEEEtran", "ascelike"}

# Map profile spacing tokens to LaTeX setspace stretch values.
_SPACING = {"single": "1", "1.5": "1.5", "double": "2"}


class PandocMissingError(RuntimeError):
    """Raised when Pandoc is required but not installed."""


def _spacing_value(profile) -> str:
    """Return the LaTeX line-stretch value for the profile's spacing."""
    return _SPACING.get(str(profile.get("spacing", "double")), "2")


def _geometry(profile) -> str:
    """Return the geometry paper option for the profile's page size."""
    return (
        "letterpaper"
        if str(profile.get("page_size", "letter")) == "letter"
        else "a4paper"
    )


class Renderer:
    """Render a manuscript to DOCX / LaTeX / PDF for a journal profile."""

    def __init__(self, manuscript: Manuscript, profile) -> None:
        """Bind the manuscript and its target journal profile."""
        self.ms = manuscript
        self.profile = profile
        self.notes: list[str] = []
        self._doc = compose_manuscript(manuscript, profile)

    # -- asset resolution ----------------------------------------------

    def _asset(self, package: str, filename: str) -> Path | None:
        """Resolve a bundled asset file to a real path, or ``None``."""
        anchor = resources.files(package).joinpath(filename)
        with resources.as_file(anchor) as p:
            return Path(p) if Path(p).is_file() else None

    def _csl_path(self) -> Path | None:
        """Resolve the profile's bundled CSL file, if present."""
        name = self.profile.get("csl", "")
        if not name:
            return None
        return self._asset("epy_papers.assets.csl", f"{name}.csl")

    def _latex_dir(self) -> Path | None:
        """Resolve the bundled LaTeX assets dir (for the class search)."""
        anchor = resources.files("epy_papers.assets.latex")
        with resources.as_file(anchor) as p:
            return Path(p) if Path(p).is_dir() else None

    def latex_class(self) -> tuple[str, bool]:
        """Return ``(class_name, is_bundled)`` for this profile.

        Falls back to ``article`` when the profile names no class or names one
        epy_papers does not bundle; the fallback is recorded in ``notes``.
        """
        requested = str(self.profile.get("latex_class", "") or "")
        if requested in _BUNDLED_CLASSES:
            return requested, True
        if requested:
            self.notes.append(
                f"LaTeX class '{requested}' is not bundled; "
                "falling back to the generic 'article' template."
            )
        return "article", False

    # -- pandoc plumbing -----------------------------------------------

    def _bibliography_path(self) -> str | None:
        """Resolve the bibliography file relative to the source dir."""
        bib = self.ms.bibliography
        if not bib:
            return None
        base = self.ms.base_dir
        return str(base / bib if base else bib)

    def _common_args(self) -> list[str]:
        """Pandoc args shared by every output format."""
        args = ["--wrap=preserve"]
        csl = self._csl_path()
        bib = self._bibliography_path()
        if bib and csl is not None:
            args += ["--citeproc", f"--csl={csl}"]
            args.append(f"--bibliography={bib}")
        elif bib:
            args += ["--citeproc", f"--bibliography={bib}"]
        if self.ms.base_dir is not None:
            args.append(f"--resource-path={self.ms.base_dir}")
        return args

    def _figures_at_end(self) -> bool:
        """Whether the profile wants figures and tables at the end."""
        return (
            str(self.profile.get("figures", "inline")) == "end"
            or str(self.profile.get("tables", "inline")) == "end"
        )

    def _has_line_numbers(self) -> bool:
        """Whether the profile asks for numbered manuscript lines."""
        return str(self.profile.get("line_numbers", "off")).lower() not in (
            "off", "", "false", "no", "none", "0"
        )

    def _require_pandoc(self):
        """Import pypandoc, raising :class:`PandocMissingError` if absent."""
        try:
            # Lazy import: the library imports without the heavy pandoc
            # dependency; it is only needed when actually rendering.
            import pypandoc  # noqa: PLC0415 - lazy render-time dependency
        except ImportError as exc:  # pragma: no cover - env guard
            raise PandocMissingError(
                "pypandoc is required to render drafts."
            ) from exc
        try:
            pypandoc.get_pandoc_version()
        except OSError as exc:  # pragma: no cover - env guard
            raise PandocMissingError(
                "Pandoc binary is not available."
            ) from exc
        return pypandoc

    # -- outputs --------------------------------------------------------

    def to_docx(self, out: Path) -> Path:
        """Render a Word submission manuscript."""
        pypandoc = self._require_pandoc()
        args = self._common_args()
        ref_name = (
            "submission_lineno.docx"
            if self._has_line_numbers()
            else "submission.docx"
        )
        ref = self._asset("epy_papers.assets.reference_docx", ref_name)
        if ref is None and self._has_line_numbers():
            # Fall back to the plain reference if the line-numbered variant
            # is not bundled; line numbers are then dropped for this draft.
            ref = self._asset(
                "epy_papers.assets.reference_docx", "submission.docx"
            )
            self.notes.append(
                "Line-numbered reference DOCX not bundled; "
                "exporting without line numbers."
            )
        if ref is not None:
            args.append(f"--reference-doc={ref}")
        else:
            self.notes.append(
                "Reference DOCX not bundled; using Pandoc default styles."
            )
        pypandoc.convert_text(
            self._doc.markdown,
            to="docx",
            format="markdown",
            outputfile=str(out),
            extra_args=args,
        )
        return out

    def _latex_args(self) -> list[str]:
        """Build the metadata/variable args for LaTeX and PDF output."""
        cls, _ = self.latex_class()
        paper = (
            "letterpaper"
            if str(self.profile.get("page_size", "letter")) == "letter"
            else "a4paper"
        )
        args = self._common_args() + [
            "--standalone",
            f"--variable=documentclass:{cls}",
            f"--variable=geometry:{_geometry(self.profile)}",
            f"--variable=papersize:{paper}",
            f"--variable=linestretch:{_spacing_value(self.profile)}",
            f"--variable=fontsize:{self.profile.get('font_size_pt', 12)}pt",
        ]
        template = self._asset(
            "epy_papers.assets.templates", "manuscript.latex"
        )
        if template is not None:
            args.append(f"--template={template}")
        if self._has_line_numbers():
            args.append("--variable=linenumbers:true")
        if self._figures_at_end():
            args.append("--variable=figsatend:true")
        # Let LaTeX find the bundled classes.
        latex_dir = self._latex_dir()
        if latex_dir is not None:
            args.append(f"--resource-path={latex_dir}")
        return args

    def to_html_fragment(self) -> str:
        """Render the composed manuscript to an HTML fragment for preview.

        Uses the same Pandoc pipeline as the exports — the journal's citation
        style (CSL) resolves the references and sections are numbered — so the
        live preview is a faithful rendering of the submission body, not an
        approximation. Equations are left as TeX for MathJax to typeset in the
        preview.
        """
        pypandoc = self._require_pandoc()
        args = self._common_args() + ["--number-sections"]
        return pypandoc.convert_text(
            self._doc.markdown,
            to="html5",
            format="markdown",
            extra_args=args,
        )

    def to_html(self, out: Path) -> Path:
        """Render a standalone, self-contained HTML manuscript.

        Same Pandoc pipeline as the preview (journal CSL resolves the
        references, sections numbered), wrapped as a self-contained page with
        equations as MathML so the file renders offline without scripts.
        """
        pypandoc = self._require_pandoc()
        args = self._common_args() + [
            "--standalone",
            "--embed-resources",
            "--number-sections",
            "--mathml",
        ]
        pypandoc.convert_text(
            self._doc.markdown,
            to="html5",
            format="markdown",
            outputfile=str(out),
            extra_args=args,
        )
        return out

    def to_latex(self, out: Path) -> Path:
        """Render a LaTeX submission manuscript."""
        pypandoc = self._require_pandoc()
        pypandoc.convert_text(
            self._doc.markdown,
            to="latex",
            format="markdown",
            outputfile=str(out),
            extra_args=self._latex_args(),
        )
        return out

    def to_pdf(self, out: Path) -> Path:
        """Render a PDF submission manuscript via LaTeX."""
        pypandoc = self._require_pandoc()
        pypandoc.convert_text(
            self._doc.markdown,
            to="pdf",
            format="markdown",
            outputfile=str(out),
            extra_args=self._latex_args(),
        )
        return out
