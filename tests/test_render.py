"""Tests for the Pandoc-backed rendering pipeline.

Pandoc-dependent tests skip gracefully when Pandoc is absent.
"""

from __future__ import annotations

import epy_papers as ep
from _pandoc import needs_pandoc
from epy_papers._core._render import Renderer

SIMPLE = (
    "---\ntitle: {en: A test manuscript}\n"
    "abstract: {en: A short abstract.}\nkeywords: {en: [test]}\n"
    "---\n\n# Introduction\n\nBody text.\n"
)


def _renderer(jid: str) -> Renderer:
    """Build a Renderer for the given journal id."""
    paper = ep.Paper(SIMPLE)
    return Renderer(paper.manuscript, paper.profile(jid))


def test_latex_class_bundled_elsarticle():
    """Engineering Structures resolves to the bundled elsarticle class."""
    cls, bundled = _renderer("eng-structures").latex_class()
    assert cls == "elsarticle"
    assert bundled is True


def test_latex_class_bundled_ascelike():
    """An ASCE journal resolves to the bundled ascelike class."""
    cls, bundled = _renderer("asce-jse").latex_class()
    assert cls == "ascelike"
    assert bundled is True


def test_latex_class_fallback_records_note():
    """An unbundled class falls back to article and records a note."""
    r = _renderer("bee")  # svjour3 is not bundled
    cls, bundled = r.latex_class()
    assert cls == "article"
    assert bundled is False
    assert any("not bundled" in n for n in r.notes)


def test_latex_class_no_class_uses_article():
    """A profile with no class uses the generic article template."""
    cls, bundled = _renderer("aci-structural").latex_class()
    assert cls == "article"
    assert bundled is False


@needs_pandoc
def test_to_docx_produces_file(tmp_path):
    """DOCX export writes a non-empty file."""
    out = ep.Paper(SIMPLE).to_draft(
        "generic-manuscript", tmp_path / "draft.docx", fmt="docx"
    )
    assert out.exists() and out.stat().st_size > 0


@needs_pandoc
def test_to_latex_selects_elsarticle(tmp_path):
    """LaTeX export for Engineering Structures uses elsarticle."""
    out = ep.Paper(SIMPLE).to_draft(
        "eng-structures", tmp_path / "draft.tex", fmt="tex"
    )
    text = out.read_text(encoding="utf-8")
    assert "\\documentclass" in text
    assert "elsarticle" in text


@needs_pandoc
def test_to_latex_ascelike(tmp_path):
    """LaTeX export for an ASCE journal uses ascelike."""
    out = ep.Paper(SIMPLE).to_draft(
        "asce-jse", tmp_path / "asce.tex", fmt="tex"
    )
    assert "ascelike" in out.read_text(encoding="utf-8")


@needs_pandoc
def test_latex_applies_line_numbers_for_continuous(tmp_path):
    """Continuous line numbers add the lineno package."""
    out = ep.Paper(SIMPLE).to_draft(
        "eng-structures", tmp_path / "ln.tex", fmt="tex"
    )
    assert "lineno" in out.read_text(encoding="utf-8")


@needs_pandoc
def test_latex_figures_at_end_uses_endfloat(tmp_path):
    """A figures-at-end profile pulls in endfloat."""
    out = ep.Paper(SIMPLE).to_draft(
        "asce-jse", tmp_path / "end.tex", fmt="tex"
    )
    assert "endfloat" in out.read_text(encoding="utf-8")


@needs_pandoc
def test_a4_geometry_for_a4_profile(tmp_path):
    """An A4 profile renders with a4paper geometry."""
    out = ep.Paper(SIMPLE).to_draft(
        "eng-structures", tmp_path / "a4.tex", fmt="tex"
    )
    assert "a4paper" in out.read_text(encoding="utf-8")
