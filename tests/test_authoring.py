"""Tests for the authoring source parser."""

from __future__ import annotations

from epy_papers import Author, Manuscript
from epy_papers._core._authoring import (
    Bilingual,
    BilingualList,
    split_front_matter,
)

BILINGUAL_SOURCE = """---
title:
  en: English title
  es: Titulo en espanol
language: es
authors:
  - name: Angel Navarro-Mora
    orcid: 0000-0002-0539-7014
    affiliation: TEC
    email: a@itcr.ac.cr
    corresponding: true
  - Second Author
abstract:
  en: An English abstract.
  es: Un resumen en espanol.
keywords:
  en: [alpha, beta]
  es: [gamma, delta]
highlights:
  - First highlight.
  - Second highlight.
declarations:
  credit: Author statement.
bibliography: refs.bib
---

# Body

Text.
"""

SCALAR_SOURCE = """---
title: A single-language title
abstract: A single-language abstract.
keywords: one, two, three
---

# Body
"""


def test_split_front_matter():
    """Front matter and body are split on the fenced block."""
    fm, body = split_front_matter(BILINGUAL_SOURCE)
    assert "title:" in fm
    assert body.strip().startswith("# Body")


def test_split_no_front_matter():
    """Source without front matter returns empty FM and full body."""
    fm, body = split_front_matter("# Just a body\n\ntext")
    assert fm == ""
    assert body.startswith("# Just a body")


def test_bilingual_coerce_scalar():
    """A scalar coerces to an English-keyed bilingual value."""
    b = Bilingual.coerce("hola")
    assert b.get("en") == "hola"
    assert b.primary("es") == "hola"


def test_bilingual_coerce_mapping():
    """A mapping keeps both languages."""
    b = Bilingual.coerce({"en": "hi", "es": "hola"})
    assert b.has("en") and b.has("es")
    assert b.primary("es") == "hola"


def test_bilingual_list_from_comma_string():
    """Comma-separated keywords parse into a list."""
    kl = BilingualList.coerce("one, two, three")
    assert kl.get("en") == ["one", "two", "three"]


def test_manuscript_parses_bilingual_source():
    """The full bilingual source maps into typed fields."""
    ms = Manuscript.from_source(BILINGUAL_SOURCE)
    assert ms.language == "es"
    assert ms.title.get("en") == "English title"
    assert ms.title.get("es") == "Titulo en espanol"
    assert ms.abstract.has("en") and ms.abstract.has("es")
    assert ms.keywords.get("es") == ["gamma", "delta"]
    assert len(ms.highlights) == 2
    assert ms.declarations["credit"] == "Author statement."
    assert ms.bibliography == "refs.bib"


def test_manuscript_parses_authors():
    """Authors parse from both mapping and string forms."""
    ms = Manuscript.from_source(BILINGUAL_SOURCE)
    assert len(ms.authors) == 2
    first = ms.authors[0]
    assert isinstance(first, Author)
    assert first.corresponding is True
    assert first.orcid == "0000-0002-0539-7014"
    assert ms.authors[1].name == "Second Author"
    assert ms.has_corresponding()


def test_manuscript_scalar_source():
    """A single-language source still parses cleanly."""
    ms = Manuscript.from_source(SCALAR_SOURCE)
    assert ms.title.get("en") == "A single-language title"
    assert ms.keywords.get("en") == ["one", "two", "three"]
    assert ms.authors == []


def test_split_front_matter_no_closing_fence_returns_whole_source():
    """An opening ``---`` with no closing fence is not front matter at
    all -- the whole thing is treated as body, not silently truncated.
    """
    source = "---\ntitle: Unterminated\n\n# Body still here\n"
    fm, body = split_front_matter(source)
    assert fm == ""
    assert body == source


def test_bilingual_coerce_is_idempotent_on_an_existing_instance():
    original = Bilingual.coerce({"en": "hi"})
    assert Bilingual.coerce(original) is original


def test_bilingual_primary_is_empty_string_with_no_content_anywhere():
    assert Bilingual.coerce(None).primary("en") == ""
    assert Bilingual({"en": "", "es": "  "}).primary("en") == ""


def test_bilingual_list_coerce_is_idempotent_on_an_existing_instance():
    original = BilingualList.coerce(["a", "b"])
    assert BilingualList.coerce(original) is original


def test_bilingual_list_has_and_primary_fall_back_across_languages():
    kl = BilingualList({"es": ["uno", "dos"]})
    assert kl.has("es") is True
    assert kl.has("en") is False
    assert kl.primary("en") == ["uno", "dos"]  # falls back to es


def test_bilingual_list_primary_is_empty_with_nothing_in_any_language():
    kl = BilingualList({"en": [], "es": []})
    assert kl.primary("en") == []


def test_author_coerce_falls_back_to_str_for_an_unexpected_type():
    """Neither a string nor a mapping (e.g. a bare int from malformed
    YAML): the author is still recorded, not dropped or crashed on.
    """
    author = Author.coerce(12345)
    assert author.name == "12345"
    assert author.affiliation == ""
    assert author.corresponding is False


def test_manuscript_from_file_reads_and_parses_a_real_file(tmp_path):
    """``Paper.from_file`` never calls this (it reads the text itself and
    goes through ``from_source``), so this is the only caller of
    ``Manuscript.from_file`` in the whole codebase.
    """
    path = tmp_path / "paper.md"
    path.write_text(SCALAR_SOURCE, encoding="utf-8")
    ms = Manuscript.from_file(path)
    assert ms.title.get("en") == "A single-language title"
    assert ms.base_dir == tmp_path
