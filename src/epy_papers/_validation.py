"""Structured validation of a manuscript against a journal profile.

``validate`` returns a :class:`ValidationResult` carrying typed
:class:`Warning` records (each with a ``code``, ``severity`` and
human-readable ``message``) instead of plain strings, so callers can filter
and present them. Validation never blocks: every surveyed journal phrases its
rules as recommendations, so epy_papers reports rather than refuses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._authoring import LANGS, Manuscript

__all__ = ["Severity", "Warning", "ValidationResult", "validate"]


class Severity:
    """Severity levels for a validation warning."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Warning:
    """A single validation finding."""

    code: str
    severity: str
    message: str

    def __str__(self) -> str:
        """Return ``[SEVERITY] message`` for plain-text display."""
        return f"[{self.severity}] {self.message}"


@dataclass
class ValidationResult:
    """The collected findings of validating a manuscript for a journal."""

    journal_id: str
    journal_name: str
    warnings: list[Warning] = field(default_factory=list)

    def add(self, code: str, severity: str, message: str) -> None:
        """Append a warning."""
        self.warnings.append(Warning(code, severity, message))

    @property
    def ok(self) -> bool:
        """Whether there are no ``error``-severity findings."""
        return not any(w.severity == Severity.ERROR for w in self.warnings)

    def messages(self) -> list[str]:
        """Return the findings as plain strings (back-compat helper)."""
        return [w.message for w in self.warnings]

    def __iter__(self):
        """Iterate over warnings."""
        return iter(self.warnings)

    def __len__(self) -> int:
        """Number of findings."""
        return len(self.warnings)

    def __bool__(self) -> bool:
        """Truthy when there is at least one finding."""
        return bool(self.warnings)


def _int(profile: Any, key: str, default: int = 0) -> int:
    """Read an integer profile field with a default."""
    try:
        return int(profile.get(key, default) or default)
    except (TypeError, ValueError):
        return default


# Tokens that identify author identity in a blinded title page.
_BLINDING_BLIND = {"double", "blind"}


def validate(
    manuscript: Manuscript, profile: Any, journal_id: str
) -> ValidationResult:
    """Validate ``manuscript`` against a journal ``profile``.

    ``profile`` is anything exposing ``get(key, default)`` and a ``name``
    attribute (the :class:`~epy_papers.JournalProfile` view satisfies this).
    """
    res = ValidationResult(
        journal_id=journal_id,
        journal_name=getattr(profile, "name", journal_id),
    )
    name = res.journal_name
    default_lang = manuscript.language or "en"

    bilingual = "bilingual-abstract" in (profile.get("declarations") or [])
    _check_title(res, manuscript, profile, name, default_lang, bilingual)
    _check_abstract(res, manuscript, profile, name, default_lang, bilingual)
    _check_keywords(res, manuscript, profile, name, default_lang, bilingual)
    _check_highlights(res, manuscript, profile, name)
    _check_declarations(res, manuscript, profile, name)
    _check_blinding(res, manuscript, profile, name)
    _check_page_size(res, profile, name)
    _check_citation(res, profile, name)
    return res


def _check_title(res, ms, profile, name, lang, bilingual):
    """Title presence (bilingual) and character limit."""
    limit = _int(profile, "title_chars")
    if ms.title.is_empty():
        res.add("title-missing", Severity.ERROR, "Title is missing.")
        return
    if bilingual:
        for lc in LANGS:
            if not ms.title.has(lc):
                res.add(
                    "title-bilingual",
                    Severity.WARNING,
                    f"{name} requires a bilingual title; "
                    f"the '{lc}' title is missing.",
                )
    if limit:
        for lc in LANGS:
            text = ms.title.get(lc)
            if text and len(text) > limit:
                res.add(
                    "title-too-long",
                    Severity.WARNING,
                    f"Title ({lc}) is {len(text)} characters; "
                    f"{name} allows {limit}.",
                )


def _check_abstract(res, ms, profile, name, lang, bilingual):
    """Abstract presence (bilingual) and word limit per language."""
    limit = _int(profile, "abstract_words")
    if ms.abstract.is_empty():
        res.add(
            "abstract-missing", Severity.ERROR, "Abstract is missing."
        )
        return
    if bilingual:
        for lc in LANGS:
            if not ms.abstract.has(lc):
                res.add(
                    "abstract-bilingual",
                    Severity.WARNING,
                    f"{name} requires a bilingual abstract; "
                    f"the '{lc}' abstract is missing.",
                )
    if limit:
        for lc in LANGS:
            text = ms.abstract.get(lc)
            words = len(text.split())
            if text and words > limit:
                res.add(
                    "abstract-too-long",
                    Severity.WARNING,
                    f"Abstract ({lc}) is {words} words; "
                    f"{name} allows {limit}.",
                )


def _check_keywords(res, ms, profile, name, lang, bilingual):
    """Keyword count bounds and bilingual presence."""
    kmax = _int(profile, "keywords_max")
    kmin = _int(profile, "keywords_min")
    langs = LANGS if bilingual else (lang,)
    for lc in langs:
        words = ms.keywords.get(lc)
        if bilingual and not words:
            res.add(
                "keywords-bilingual",
                Severity.WARNING,
                f"{name} requires bilingual keywords; "
                f"the '{lc}' keywords are missing.",
            )
            continue
        if kmax and len(words) > kmax:
            res.add(
                "keywords-too-many",
                Severity.WARNING,
                f"{len(words)} keywords ({lc}); {name} allows {kmax}.",
            )
        if kmin and 0 < len(words) < kmin:
            res.add(
                "keywords-too-few",
                Severity.INFO,
                f"{len(words)} keywords ({lc}); {name} asks for {kmin}+.",
            )


def _check_highlights(res, ms, profile, name):
    """Highlights presence, count and per-item character limit."""
    if not profile.get("highlights"):
        return
    hmin = _int(profile, "highlights_min", 3)
    hmax = _int(profile, "highlights_max", 5)
    hchars = _int(profile, "highlight_chars", 85)
    items = ms.highlights
    if not items:
        res.add(
            "highlights-missing",
            Severity.WARNING,
            f"{name} requests a Highlights section "
            f"({hmin}-{hmax} bullets, <= {hchars} chars each).",
        )
        return
    if len(items) < hmin or len(items) > hmax:
        res.add(
            "highlights-count",
            Severity.WARNING,
            f"{len(items)} highlights; {name} wants {hmin}-{hmax}.",
        )
    for i, item in enumerate(items, 1):
        if len(item) > hchars:
            res.add(
                "highlight-too-long",
                Severity.WARNING,
                f"Highlight {i} is {len(item)} characters; "
                f"{name} allows {hchars}.",
            )


def _check_declarations(res, ms, profile, name):
    """Required declarations present in the manuscript."""
    # Synthetic markers are derived, not authored as declaration keys.
    synthetic = {"bilingual-abstract", "practical-applications"}
    for key in profile.get("declarations") or []:
        if key in synthetic:
            continue
        if not ms.declarations.get(key):
            res.add(
                "declaration-missing",
                Severity.WARNING,
                f"{name} requires a '{key}' declaration.",
            )


def _check_blinding(res, ms, profile, name):
    """Double-blind compliance: no author identity must be authored."""
    blinding = str(profile.get("blinding", "none"))
    if blinding not in _BLINDING_BLIND:
        return
    named = [a.name for a in ms.authors if a.name]
    if named:
        res.add(
            "blinding-author-identity",
            Severity.WARNING,
            f"{name} requires a blinded manuscript; author identity "
            "(names/emails) will be stripped from the title page.",
        )


def _check_page_size(res, profile, name):
    """Note A4-forbidding journals when the profile is A4."""
    page = str(profile.get("page_size", "letter"))
    if page == "a4" and "ACS" in name:
        res.add(
            "page-size",
            Severity.WARNING,
            f"{name} forbids A4; use US Letter.",
        )


def _check_citation(res, profile, name):
    """Note when the profile has no bundled CSL for its citation style."""
    if not profile.get("csl"):
        res.add(
            "citation-style",
            Severity.INFO,
            f"{name} has no bundled CSL; references use the Pandoc default.",
        )
