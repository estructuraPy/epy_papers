"""Tests for the WYSIWYG (Pandoc-rendered) faithful preview."""

from __future__ import annotations

import pytest


def _pandoc_available() -> bool:
    try:
        import pypandoc

        pypandoc.get_pandoc_version()
        return True
    except Exception:
        return False


def test_mathjax_block_bundled():
    from epy_paper.tab import _mathjax_block

    block = _mathjax_block()
    assert "window.MathJax" in block
    # the bundled tex-svg script should be inlined (>100 KB)
    assert len(block) > 100_000


def test_to_html_fragment_renders_body():
    if not _pandoc_available():
        pytest.skip("pandoc not available")
    from epy_paper._authoring import Manuscript
    from epy_paper._render import Renderer

    src = (
        "---\ntitle: Faithful Test\nabstract: An abstract.\n---\n\n"
        "# Introduction\n\nA paragraph with **bold** text.\n\n"
        "| A | B |\n|---|---|\n| 1 | 2 |\n"
    )
    frag = Renderer(Manuscript.from_source(src), {}).to_html_fragment()
    assert "<table" in frag  # tables render faithfully
    assert "Introduction" in frag
    # number-sections numbers the heading
    assert "<h1" in frag or "<h2" in frag


def test_faithful_preview_wraps_in_page_with_mathjax():
    if not _pandoc_available():
        pytest.skip("pandoc not available")
    from epy_paper.tab import _build_preview_faithful

    src = (
        "---\ntitle: T\nabstract: A.\n---\n\n"
        "Body paragraph one.\n\nBody paragraph two.\n"
    )
    html = _build_preview_faithful(
        src, {"name": "J", "line_numbers": "continuous", "columns": 1}
    )
    assert 'class="page"' in html
    assert "window.MathJax" in html
    assert "epy-lnum-gutter" in html  # line-number gutter injected
    assert "_epyNumberLines" in html


def test_faithful_preview_no_line_numbers_when_off():
    if not _pandoc_available():
        pytest.skip("pandoc not available")
    from epy_paper.tab import _build_preview_faithful

    src = "---\ntitle: T\nabstract: A.\n---\n\nBody.\n"
    html = _build_preview_faithful(src, {"name": "J", "line_numbers": "off"})
    assert "epy-lnum-gutter" not in html
    assert 'class="page"' in html
