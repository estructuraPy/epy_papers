"""Authoring source format for epy_paper.

The author writes the paper **once** in a single Markdown file with a YAML
front matter and a Markdown body. The front matter models everything the
submission draft needs, independent of any single journal::

    ---
    title:
      en: A faithful manuscript engine for journal submissions
      es: Un motor de manuscritos fiel para envios a revistas
    authors:
      - name: Angel Navarro-Mora
        orcid: 0000-0002-0539-7014
        affiliation: Instituto Tecnologico de Costa Rica
        email: ahnavarro@itcr.ac.cr
        corresponding: true
    abstract:
      en: >
        We present ...
      es: >
        Presentamos ...
    keywords:
      en: [timber, trusses, calibration]
      es: [madera, cerchas, calibracion]
    highlights:
      - A reusable manuscript engine driven by per-journal profiles.
      - Bilingual title, abstract and keywords for Latin-American venues.
    declarations:
      credit: "A.N.M.: conceptualization, methodology, writing."
      competing-interests: "The authors declare no competing interests."
      funding: "This work received no external funding."
      data-availability: "Data are available on request."
    bibliography: refs.bib
    ---

    # Introduction

    Body text ...

Title / abstract / keywords accept either a plain scalar (single language)
or a ``{es, en}`` mapping (bilingual). The ``language`` field of the
front matter (default ``en``) decides which variant is the *primary* one;
the profile decides whether BOTH must be emitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "Author",
    "Manuscript",
    "Bilingual",
    "split_front_matter",
]

# Languages epy_paper models explicitly for bilingual venues.
LANGS = ("en", "es")


def split_front_matter(source: str) -> tuple[str, str]:
    """Return ``(front_matter_text, body_text)`` from a Markdown source.

    The front matter is the block between the first ``---`` line and the
    next ``---`` line. If there is no front matter, the first element is an
    empty string and the body is the whole source.
    """
    if not source.startswith("---"):
        return "", source
    lines = source.splitlines(keepends=True)
    # First line is the opening fence; find the closing fence.
    for idx in range(1, len(lines)):
        if lines[idx].rstrip("\r\n") in ("---", "..."):
            fm = "".join(lines[1:idx])
            body = "".join(lines[idx + 1 :])
            return fm, body
    return "", source


@dataclass
class Bilingual:
    """A value available in one or both modelled languages."""

    values: dict[str, str]

    @classmethod
    def coerce(cls, raw: Any) -> Bilingual:
        """Build a :class:`Bilingual` from a scalar or an ``{es, en}`` map."""
        if isinstance(raw, Bilingual):
            return raw
        if isinstance(raw, dict):
            return cls({k: str(v) for k, v in raw.items() if v is not None})
        if raw is None:
            return cls({})
        return cls({"en": str(raw)})

    def get(self, lang: str) -> str:
        """Return the value for ``lang`` or an empty string."""
        return self.values.get(lang, "")

    def has(self, lang: str) -> bool:
        """Whether a non-empty value exists for ``lang``."""
        return bool(self.values.get(lang, "").strip())

    def primary(self, default_lang: str) -> str:
        """Return the primary-language value, or any available value."""
        if self.has(default_lang):
            return self.get(default_lang)
        for lang in LANGS:
            if self.has(lang):
                return self.get(lang)
        return ""

    def is_empty(self) -> bool:
        """Whether no language has content."""
        return not any(v.strip() for v in self.values.values())


@dataclass
class BilingualList:
    """A list value (e.g. keywords) available per language."""

    values: dict[str, list[str]]

    @classmethod
    def coerce(cls, raw: Any) -> BilingualList:
        """Build from a scalar list, a comma string, or an ``{es, en}`` map."""
        if isinstance(raw, BilingualList):
            return raw
        if isinstance(raw, dict):
            out: dict[str, list[str]] = {}
            for lang, val in raw.items():
                out[lang] = _as_list(val)
            return cls(out)
        return cls({"en": _as_list(raw)})

    def get(self, lang: str) -> list[str]:
        """Return the list for ``lang`` or an empty list."""
        return self.values.get(lang, [])

    def has(self, lang: str) -> bool:
        """Whether a non-empty list exists for ``lang``."""
        return bool(self.values.get(lang))

    def primary(self, default_lang: str) -> list[str]:
        """Return the primary-language list, or any available list."""
        if self.has(default_lang):
            return self.get(default_lang)
        for lang in LANGS:
            if self.has(lang):
                return self.get(lang)
        return []


def _as_list(raw: Any) -> list[str]:
    """Normalize keywords given as a list or a comma/semicolon string."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x).strip() for x in raw if str(x).strip()]
    text = str(raw)
    sep = ";" if ";" in text else ","
    return [part.strip() for part in text.split(sep) if part.strip()]


@dataclass
class Author:
    """One author entry from the front matter."""

    name: str
    affiliation: str = ""
    email: str = ""
    orcid: str = ""
    corresponding: bool = False

    @classmethod
    def coerce(cls, raw: Any) -> Author:
        """Build an :class:`Author` from a string or a mapping."""
        if isinstance(raw, str):
            return cls(name=raw.strip())
        if isinstance(raw, dict):
            return cls(
                name=str(raw.get("name", "")).strip(),
                affiliation=str(raw.get("affiliation", "")).strip(),
                email=str(raw.get("email", "")).strip(),
                orcid=str(raw.get("orcid", "")).strip(),
                corresponding=bool(raw.get("corresponding", False)),
            )
        return cls(name=str(raw))


@dataclass
class Manuscript:
    """A parsed authoring source: typed front matter plus the Markdown body."""

    title: Bilingual
    abstract: Bilingual
    keywords: BilingualList
    body: str
    authors: list[Author] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    declarations: dict[str, str] = field(default_factory=dict)
    language: str = "en"
    bibliography: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    base_dir: Path | None = None

    @classmethod
    def from_source(
        cls, source: str, base_dir: Path | None = None
    ) -> Manuscript:
        """Parse a full Markdown source (front matter + body)."""
        fm_text, body = split_front_matter(source)
        meta: dict[str, Any] = {}
        if fm_text.strip():
            loaded = yaml.safe_load(fm_text)
            if isinstance(loaded, dict):
                meta = loaded
        authors = [Author.coerce(a) for a in (meta.get("authors") or [])]
        declarations = {
            str(k): str(v)
            for k, v in (meta.get("declarations") or {}).items()
        }
        return cls(
            title=Bilingual.coerce(meta.get("title")),
            abstract=Bilingual.coerce(meta.get("abstract")),
            keywords=BilingualList.coerce(meta.get("keywords")),
            body=body,
            authors=authors,
            highlights=_as_list(meta.get("highlights")),
            declarations=declarations,
            language=str(meta.get("language", "en")),
            bibliography=(
                str(meta["bibliography"])
                if meta.get("bibliography")
                else None
            ),
            raw=meta,
            base_dir=base_dir,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> Manuscript:
        """Parse an authoring source file."""
        p = Path(path)
        return cls.from_source(
            p.read_text(encoding="utf-8"), base_dir=p.parent
        )

    # -- convenience views ---------------------------------------------

    def has_corresponding(self) -> bool:
        """Whether any author is flagged as corresponding."""
        return any(a.corresponding for a in self.authors)
