"""epy_papers — write a paper once, export a journal-compliant draft.

Single public API for the suite (mirrors ``epy_reports.Report`` /
``epy_slides.SlideDeck`` / ``epy_project.ProjectManager``)::

    from epy_papers import Paper, available_journals

    available_journals()                       # [(id, name), ...]
    paper = Paper.from_file("manuscript.md")
    result = paper.validate("eng-structures")  # ValidationResult (typed)
    paper.to_draft("eng-structures", "draft.docx")   # or fmt="tex"/"pdf"

The published two-column typeset is produced by the publisher, never the
author; epy_papers produces the *submission manuscript* (single column,
double-spaced, line-numbered, the journal's citation style and page size),
driven by a per-journal **profile** in ``_config/_data/journals.json``. The
author's source is one Markdown file whose YAML front matter models bilingual
``title`` / ``abstract`` / ``keywords``, ``highlights`` and ``declarations``
(see :mod:`epy_papers._authoring` and ``REQUIREMENTS.md``).
"""

from __future__ import annotations

import json
import os
import warnings
from importlib import resources
from pathlib import Path
from typing import Any

from ._authoring import Author, Bilingual, BilingualList, Manuscript
from ._render import PandocMissingError, Renderer
from ._validation import Severity, ValidationResult, Warning, validate

__version__ = "0.1.8"

__all__ = [
    "Paper",
    "JournalProfile",
    "Manuscript",
    "Author",
    "Bilingual",
    "BilingualList",
    "ValidationResult",
    "Warning",
    "Severity",
    "PandocMissingError",
    "available_journals",
    "journal_profile",
    "load_journals",
    "load_user_journals",
    "user_journals_path",
    "add_journal",
    "remove_user_journal",
]


# --------------------------------------------------------------------------
# Journal catalog
# --------------------------------------------------------------------------


def user_journals_path() -> Path:
    """Return the writable catalog where user-added journals are stored.

    Defaults to ``~/.epy_papers/journals.json``; override with the
    ``EPY_PAPERS_USER_JOURNALS`` environment variable. User journals persist
    across app updates and merge on top of the bundled catalog.
    """
    override = os.environ.get("EPY_PAPERS_USER_JOURNALS")
    if override:
        return Path(override)
    return Path.home() / ".epy_papers" / "journals.json"


def load_user_journals() -> dict[str, dict[str, Any]]:
    """Return user-added journal profiles (empty dict if none).

    When the catalog file exists but cannot be read or parsed, a
    ``UserWarning`` is emitted and an empty dict is returned so the bundled
    journals remain usable.  Callers that need to distinguish "no user
    journals" from "catalog corrupted" should catch the warning via
    ``warnings.catch_warnings`` or check the file directly.
    """
    path = user_journals_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        warnings.warn(
            f"User journal catalog at {path} could not be read and will be "
            f"ignored: {exc}",
            UserWarning,
            stacklevel=2,
        )
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


def load_journals() -> dict[str, dict[str, Any]]:
    """Return the full journal catalog (bundled + user), id -> profile dict.

    User journals (see :func:`add_journal`) extend and override the bundled
    catalog, so a user can add new venues or tweak an existing profile without
    touching the shipped data.
    """
    text = (
        resources.files("epy_papers._config._data")
        .joinpath("journals.json")
        .read_text(encoding="utf-8")
    )
    data = json.loads(text)
    catalog = {k: v for k, v in data.items() if not k.startswith("_")}
    catalog.update(load_user_journals())
    return catalog


def _dumps_compact(obj: Any, level: int = 0) -> str:
    """Serialize JSON keeping leaf objects (all-scalar dicts) on one line."""
    ind, ind1 = "  " * level, "  " * (level + 1)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        if all(not isinstance(v, (dict, list)) for v in obj.values()):
            inner = ", ".join(
                f"{json.dumps(k, ensure_ascii=False)}: "
                f"{json.dumps(v, ensure_ascii=False)}"
                for k, v in obj.items()
            )
            return "{" + inner + "}"
        lines = [
            f"{ind1}{json.dumps(k, ensure_ascii=False)}: "
            f"{_dumps_compact(v, level + 1)}"
            for k, v in obj.items()
        ]
        return "{\n" + ",\n".join(lines) + f"\n{ind}}}"
    if isinstance(obj, list):
        if not obj:
            return "[]"
        if all(not isinstance(v, (dict, list)) for v in obj):
            return json.dumps(obj, ensure_ascii=False)
        lines = [f"{ind1}{_dumps_compact(v, level + 1)}" for v in obj]
        return "[\n" + ",\n".join(lines) + f"\n{ind}]"
    return json.dumps(obj, ensure_ascii=False)


def add_journal(journal_id: str, profile: dict[str, Any]) -> Path:
    """Add or update a user journal profile; return the catalog path.

    The profile is written to the user catalog (see
    :func:`user_journals_path`) and immediately available from
    :func:`load_journals` / :func:`available_journals`.
    """
    journal_id = str(journal_id).strip()
    if not journal_id:
        raise ValueError("journal_id must be a non-empty string")
    path = user_journals_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    current: dict[str, Any] = {}
    if path.is_file():
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            warnings.warn(
                f"User journal catalog at {path} is unreadable; existing "
                f"entries will be lost when the new journal is written: {exc}",
                UserWarning,
                stacklevel=2,
            )
            current = {}
    current[journal_id] = dict(profile)
    path.write_text(_dumps_compact(current) + "\n", encoding="utf-8")
    return path


def remove_user_journal(journal_id: str) -> bool:
    """Delete a user journal profile; return ``True`` if one was removed.

    Raises ``OSError`` or ``json.JSONDecodeError`` when the catalog file
    exists but cannot be read or parsed, so callers can distinguish between
    "journal not in catalog" (``False`` return) and "catalog is unreadable"
    (exception).
    """
    path = user_journals_path()
    if not path.is_file():
        return False
    current = json.loads(path.read_text(encoding="utf-8"))
    if journal_id not in current:
        return False
    del current[journal_id]
    path.write_text(_dumps_compact(current) + "\n", encoding="utf-8")
    return True


def available_journals() -> list[tuple[str, str]]:
    """Return ``(id, display name)`` for every journal in the catalog."""
    return [
        (jid, prof.get("name", jid))
        for jid, prof in load_journals().items()
    ]


def journal_profile(journal_id: str) -> dict[str, Any]:
    """Return one journal's raw profile dict (raises KeyError if unknown)."""
    return load_journals()[journal_id]


class JournalProfile:
    """A typed view over one journal's submission requirements."""

    def __init__(self, journal_id: str, data: dict[str, Any]) -> None:
        """Wrap the raw catalog record for ``journal_id``."""
        self.id = journal_id
        self._d = data

    def __getattr__(self, name: str) -> Any:
        """Expose profile fields as attributes (e.g. ``profile.columns``)."""
        try:
            return self._d[name]
        except KeyError as exc:  # pragma: no cover - attribute miss
            raise AttributeError(name) from exc

    @property
    def name(self) -> str:
        """Human-readable journal name."""
        return self._d.get("name", self.id)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style access with a default."""
        return self._d.get(key, default)


# --------------------------------------------------------------------------
# Paper facade
# --------------------------------------------------------------------------


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
