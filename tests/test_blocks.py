"""Tests for the per-profile content-block composition."""

from __future__ import annotations

import epy_paper as ep
from epy_paper._blocks import compose_manuscript

BILINGUAL_PAPER = (
    "---\n"
    "title: {en: English title, es: Titulo espanol}\n"
    "language: es\n"
    "authors: [{name: Real Author, affiliation: TEC, email: a@x.cr, "
    "corresponding: true, orcid: 0000-0002-0539-7014}]\n"
    "abstract: {en: English abstract., es: Resumen espanol.}\n"
    "keywords: {en: [a, b], es: [c, d]}\n"
    "highlights: [One., Two., Three.]\n"
    "declarations: {credit: Stmt., competing-interests: None., "
    "funding: No funding.}\n"
    "---\n\n# Introduction\n\nBody.\n"
)


def _profile(jid):
    """Return a JournalProfile view for the given id."""
    return ep.Paper(BILINGUAL_PAPER).profile(jid)


def test_bilingual_block_emits_both_languages():
    """A bilingual venue emits both es and en abstracts and keywords."""
    paper = ep.Paper(BILINGUAL_PAPER)
    doc = compose_manuscript(paper.manuscript, _profile("tec-marcha"))
    md = doc.markdown
    assert "## Resumen" in md
    assert "## Abstract" in md
    assert "Palabras clave" in md
    assert "Keywords" in md


def test_bilingual_primary_language_first():
    """The primary (es) abstract heading appears before the en one."""
    paper = ep.Paper(BILINGUAL_PAPER)
    doc = compose_manuscript(paper.manuscript, _profile("tec-marcha"))
    assert doc.markdown.index("## Resumen") < doc.markdown.index(
        "## Abstract"
    )


def test_non_bilingual_emits_single_language():
    """A non-bilingual venue emits only the primary language abstract."""
    paper = ep.Paper(BILINGUAL_PAPER)
    doc = compose_manuscript(paper.manuscript, _profile("eng-structures"))
    md = doc.markdown
    # Primary language is es; only the Spanish abstract heading appears.
    assert "## Resumen" in md
    assert "## Abstract" not in md


def test_blinding_strips_author_identity():
    """A double-blind venue removes author names from the title page."""
    paper = ep.Paper(BILINGUAL_PAPER)
    doc = compose_manuscript(paper.manuscript, _profile("tec-marcha"))
    assert doc.blinded is True
    assert "Real Author" not in doc.markdown
    assert "removed for double-blind" in doc.markdown.lower()


def test_non_blind_keeps_author_identity():
    """A single-blind venue keeps the author identity."""
    paper = ep.Paper(BILINGUAL_PAPER)
    doc = compose_manuscript(paper.manuscript, _profile("eng-structures"))
    assert doc.blinded is False
    assert "Real Author" in doc.markdown
    assert "0000-0002-0539-7014" in doc.markdown


def test_highlights_emitted_when_profile_requires():
    """Highlights are emitted only when the profile requests them."""
    paper = ep.Paper(BILINGUAL_PAPER)
    with_hl = compose_manuscript(
        paper.manuscript, _profile("eng-structures")
    )
    assert "Highlights" in with_hl.markdown or "destacados" in (
        with_hl.markdown
    )
    without_hl = compose_manuscript(
        paper.manuscript, _profile("bioresources")
    )
    assert "Highlights" not in without_hl.markdown


def test_declarations_block_emitted():
    """Declarations the author supplied are rendered with titles."""
    paper = ep.Paper(BILINGUAL_PAPER)
    doc = compose_manuscript(paper.manuscript, _profile("eng-structures"))
    assert "CRediT author statement" in doc.markdown
    assert "Declaration of competing interest" in doc.markdown
