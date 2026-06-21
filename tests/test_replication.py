"""Navarro-Mora replication: real publications as submission-format targets.

Each fixture is a faithful structural skeleton of a real article (metadata,
abstract, keywords, sections) used purely to prove epy_papers reproduces the
submission shape for its venue. There is no relationship to the formats.

Render assertions skip gracefully when Pandoc is absent; the validation and
composition assertions always run.
"""

from __future__ import annotations

import epy_papers as ep
from _pandoc import needs_pandoc

# (fixture file, target journal id, expected language pair)
CASES = [
    ("navarro_bridge_health_index.md", "tec-marcha"),
    ("navarro_timber_beam_values.md", "eng-structures"),
    ("navarro_upala_bridge_forensic.md", "asce-jse"),
]


def _load(fixtures_dir, name):
    """Load a fixture paper bound to the fixtures directory."""
    return ep.Paper.from_file(fixtures_dir / name)


def test_fixtures_parse(fixtures_dir):
    """All three replication fixtures parse with real metadata."""
    for name, _ in CASES:
        paper = _load(fixtures_dir, name)
        assert not paper.manuscript.title.is_empty()
        assert paper.manuscript.authors
        assert paper.manuscript.authors[0].orcid == "0000-0002-0539-7014"


def test_bilingual_fixture_is_clean_for_bilingual_venue(fixtures_dir):
    """The Tecnologia en Marcha fixture has both languages and validates."""
    paper = _load(fixtures_dir, "navarro_bridge_health_index.md")
    res = paper.validate("tec-marcha")
    # Bilingual title/abstract/keywords are present -> none of those codes.
    codes = {w.code for w in res}
    assert "abstract-bilingual" not in codes
    assert "title-bilingual" not in codes
    assert "keywords-bilingual" not in codes


def test_elsevier_fixture_has_highlights_and_declarations(fixtures_dir):
    """The Engineering Structures fixture satisfies highlights + CRediT."""
    paper = _load(fixtures_dir, "navarro_timber_beam_values.md")
    res = paper.validate("eng-structures")
    codes = {w.code for w in res}
    assert "highlights-missing" not in codes
    # All required declarations are supplied in the fixture.
    assert "declaration-missing" not in codes


def test_asce_fixture_validates(fixtures_dir):
    """The ASCE fixture validates without an error-severity finding."""
    paper = _load(fixtures_dir, "navarro_upala_bridge_forensic.md")
    res = paper.validate("asce-jse")
    assert res.ok


@needs_pandoc
def test_replication_drafts_produced(fixtures_dir, tmp_path):
    """Each replication target produces a non-empty DOCX draft."""
    for name, jid in CASES:
        paper = _load(fixtures_dir, name)
        out = paper.to_draft(jid, tmp_path / f"{jid}.docx", fmt="docx")
        assert out.exists() and out.stat().st_size > 0


@needs_pandoc
def test_replication_latex_for_class_journals(fixtures_dir, tmp_path):
    """Elsevier and ASCE fixtures produce LaTeX using their official class."""
    es = _load(fixtures_dir, "navarro_timber_beam_values.md")
    es_out = es.to_draft("eng-structures", tmp_path / "es.tex", fmt="tex")
    assert "elsarticle" in es_out.read_text(encoding="utf-8")

    asce = _load(fixtures_dir, "navarro_upala_bridge_forensic.md")
    asce_out = asce.to_draft("asce-jse", tmp_path / "asce.tex", fmt="tex")
    assert "ascelike" in asce_out.read_text(encoding="utf-8")
