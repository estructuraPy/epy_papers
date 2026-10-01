"""Paper facade: one source manuscript that exports a journal-compliant draft.

Moved out of the package facade (which is a wrap).
"""

from __future__ import annotations

from pathlib import Path

from epy_papers._core._authoring import Manuscript
from epy_papers._core._catalog import JournalProfile, journal_profile
from epy_papers._core._validation import ValidationResult, validate
from epy_papers._core.renderer import Renderer


class Paper:
    """A single source paper that exports a journal-compliant draft.

    The source is the author's "final" content: one Markdown file whose YAML
    front matter models ``title`` / ``abstract`` / ``keywords`` (each plain or
    bilingual ``{es, en}``), ``authors``, ``highlights``, ``declarations`` and
    ``bibliography``. See :class:`epy_papers.Manuscript`.
    """

    def __init__(self, source: str, base_dir: Path | None = None) -> None:
        """Build a Paper from Markdown ``source`` text."""
        self.source = source
        self.base_dir = base_dir
        self.manuscript = Manuscript.from_source(source, base_dir=base_dir)

    @classmethod
    def from_file(cls, path: str | Path) -> Paper:
        """Build a Paper by reading a Markdown file."""
        p = Path(path)
        return cls(p.read_text(encoding="utf-8"), base_dir=p.parent)

    # -- profiles -------------------------------------------------------

    def profile(self, journal_id: str) -> JournalProfile:
        """Return the :class:`JournalProfile` for ``journal_id``."""
        return JournalProfile(journal_id, journal_profile(journal_id))

    def validate(self, journal_id: str) -> ValidationResult:
        """Return structured warnings where the paper breaks the profile.

        Non-blocking: every surveyed journal "recommends" rather than
        hard-fails, so this reports issues (abstract too long, missing
        bilingual abstract, missing highlights, blinding leaks, …) as a typed
        :class:`ValidationResult`. The result is iterable and ``len``-able for
        back-compatible use; ``result.messages()`` yields plain strings.
        """
        prof = self.profile(journal_id)
        return validate(self.manuscript, prof, journal_id)

    # -- export ---------------------------------------------------------

    def to_draft(
        self, journal_id: str, out_path: str | Path, *, fmt: str | None = None
    ) -> Path:
        """Export the submission manuscript for ``journal_id``.

        ``fmt`` defaults to the journal's preferred format (``docx`` for
        Word-only journals, ``tex`` where a LaTeX class exists). The draft is
        single-column, double-spaced and line-numbered per the profile, with
        the journal's citation style applied via the bundled CSL and, for
        LaTeX/PDF, its official class when one is bundled.
        """
        prof = self.profile(journal_id)
        out = Path(out_path)
        fmt = fmt or (prof.get("formats") or ["docx"])[0]
        renderer = Renderer(self.manuscript, prof)
        if fmt == "tex":
            renderer.to_latex(out)
        elif fmt == "pdf":
            renderer.to_pdf(out)
        elif fmt == "html":
            renderer.to_html(out)
        else:
            renderer.to_docx(out)
        return out

    def render_notes(self, journal_id: str, fmt: str) -> list[str]:
        """Return the gaps/fallbacks a render for ``journal_id`` would log.

        Useful to surface (e.g. in a UI) that a LaTeX class was not bundled
        and the generic template was used, without performing the render.
        """
        renderer = Renderer(self.manuscript, self.profile(journal_id))
        if fmt in ("tex", "pdf"):
            renderer.latex_class()
        return renderer.notes
