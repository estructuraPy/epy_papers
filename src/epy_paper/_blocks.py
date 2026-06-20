"""Assemble the submission manuscript Markdown from a manuscript + profile.

The author writes one source; this module composes the per-journal front
content (title page, bilingual title/abstract/keywords, highlights,
declarations) and prepends it to the body. Pandoc then renders the result to
DOCX / LaTeX / PDF using the profile's reference doc, template and CSL.

The composed Markdown is intentionally plain so it renders the same way in
every output format. Per-profile *layout* (double spacing, line numbers,
figures-at-end, page size) is applied by the renderer through the reference
doc / template, not here.
"""

from __future__ import annotations

from ._authoring import LANGS, Manuscript

__all__ = ["compose_manuscript", "ManuscriptDoc"]

# Human labels per language for the standard blocks.
_LABELS = {
    "en": {
        "abstract": "Abstract",
        "keywords": "Keywords",
        "highlights": "Highlights",
        "declarations": "Declarations",
        "corresponding": "Corresponding author",
    },
    "es": {
        "abstract": "Resumen",
        "keywords": "Palabras clave",
        "highlights": "Aspectos destacados",
        "declarations": "Declaraciones",
        "corresponding": "Autor de correspondencia",
    },
}

# Display names for declaration keys.
_DECL_TITLES = {
    "credit": "CRediT author statement",
    "competing-interests": "Declaration of competing interest",
    "data-availability": "Data availability",
    "funding": "Funding",
    "ai-disclosure": "Declaration of generative AI use",
    "novelty": "Statement of novelty",
    "ethics": "Ethics statement",
    "practical-applications": "Practical Applications",
    "research-in-context": "Research in Context",
}

# Order in which declarations are emitted when present.
_DECL_ORDER = [
    "credit",
    "competing-interests",
    "funding",
    "data-availability",
    "ai-disclosure",
    "ethics",
    "novelty",
    "practical-applications",
    "research-in-context",
]


class ManuscriptDoc:
    """The composed Markdown plus metadata flags the renderer needs."""

    def __init__(self, markdown: str, *, blinded: bool) -> None:
        """Hold the composed Markdown and whether it was blinded."""
        self.markdown = markdown
        self.blinded = blinded


def _label(key: str, lang: str) -> str:
    """Return a localized label, falling back to English."""
    return _LABELS.get(lang, _LABELS["en"]).get(key, _LABELS["en"][key])


def _emit_title_page(
    ms: Manuscript, profile, langs: list[str], blinded: bool
) -> list[str]:
    """Title page lines: title(s), authors (unless blinded)."""
    out: list[str] = []
    for lang in langs:
        title = ms.title.get(lang)
        if title:
            # The first title is the document title (level-1 once).
            out.append(f"# {title}")
            out.append("")
    if blinded:
        out.append("*[Author identity removed for double-blind review.]*")
        out.append("")
        return out
    for author in ms.authors:
        line = f"**{author.name}**"
        if author.affiliation:
            line += f" --- {author.affiliation}"
        out.append(line)
        if author.orcid:
            out.append(f"ORCID: {author.orcid}")
        if author.corresponding and author.email:
            out.append(
                f"{_label('corresponding', ms.language)}: {author.email}"
            )
        out.append("")
    return out


def _emit_abstract(ms: Manuscript, langs: list[str]) -> list[str]:
    """Abstract block(s), one heading per requested language."""
    out: list[str] = []
    for lang in langs:
        text = ms.abstract.get(lang)
        if not text:
            continue
        out.append(f"## {_label('abstract', lang)}")
        out.append("")
        out.append(text.strip())
        out.append("")
    return out


def _emit_keywords(ms: Manuscript, langs: list[str]) -> list[str]:
    """Keywords line(s), one per requested language."""
    out: list[str] = []
    for lang in langs:
        words = ms.keywords.get(lang)
        if not words:
            continue
        out.append(f"**{_label('keywords', lang)}:** " + "; ".join(words))
        out.append("")
    return out


def _emit_highlights(ms: Manuscript) -> list[str]:
    """Highlights as a bullet list (Elsevier convention)."""
    if not ms.highlights:
        return []
    out = [f"## {_label('highlights', ms.language)}", ""]
    out += [f"- {item}" for item in ms.highlights]
    out.append("")
    return out


def _emit_declarations(ms: Manuscript, profile, blinded: bool) -> list[str]:
    """Declarations the profile requires and the author supplied."""
    required = list(profile.get("declarations") or [])
    if not any(k in ms.declarations for k in _DECL_ORDER):
        return []
    out: list[str] = []
    for key in _DECL_ORDER:
        if key not in required and key not in ms.declarations:
            continue
        text = ms.declarations.get(key, "")
        if not text:
            continue
        # Strip acknowledgments-style identity when blinded.
        if blinded and key in ("funding", "credit"):
            text = "[Removed for double-blind review.]"
        title = _DECL_TITLES.get(key, key.replace("-", " ").title())
        out.append(f"### {title}")
        out.append("")
        out.append(text.strip())
        out.append("")
    if out:
        out = [f"## {_label('declarations', ms.language)}", ""] + out
    return out


def _resolved_langs(ms: Manuscript, profile) -> list[str]:
    """Decide which language variants to emit for this journal."""
    bilingual = "bilingual-abstract" in (profile.get("declarations") or [])
    if bilingual:
        # Primary language first, then the other modelled language.
        primary = ms.language if ms.language in LANGS else "en"
        ordered = [primary] + [x for x in LANGS if x != primary]
        return [x for x in ordered if ms.title.has(x) or ms.abstract.has(x)]
    return [ms.language if ms.language in LANGS else "en"]


def compose_manuscript(ms: Manuscript, profile) -> ManuscriptDoc:
    """Compose the submission-ready Markdown for one journal profile.

    ``profile`` is a :class:`~epy_paper.JournalProfile`-like object exposing
    ``get(key, default)``.
    """
    blinded = str(profile.get("blinding", "none")) in {"double", "blind"}
    langs = _resolved_langs(ms, profile)

    parts: list[str] = []
    parts += _emit_title_page(ms, profile, langs, blinded)
    parts += _emit_abstract(ms, langs)
    parts += _emit_keywords(ms, langs)
    if profile.get("highlights"):
        parts += _emit_highlights(ms)

    # Body comes after the front matter; ensure a separating blank line.
    body = ms.body.strip()
    if body:
        parts.append(body)
        parts.append("")

    parts += _emit_declarations(ms, profile, blinded)

    markdown = "\n".join(parts).strip() + "\n"
    return ManuscriptDoc(markdown, blinded=blinded)
