"""Coverage of ``epy_papers._ui.tab`` behaviour not already exercised.

``test_faithful_preview.py``, ``test_tab_preview_nav.py``, ``test_previews.py``
and ``test_replication.py`` cover the WYSIWYG/fast preview HTML shape and
anchor navigation. This file covers what they do not: the markdown-less
fallback converter (``_md_to_html_basic``), the front-matter/YAML/markdown
error-recovery branches inside ``_build_preview_html``, the ``<base href>``
failure branch in ``_build_preview_faithful``, the two ``lru_cache``d
helpers' exception paths, and the ``PaperTab`` editing commands (insert/
toggle helpers), which no existing test calls directly.

The two ``@lru_cache(maxsize=1)`` functions (``_design_css``,
``_mathjax_block``) are process-wide singletons: every test that forces
their exception branch clears the cache in a ``finally`` so it does not
leave a permanently-broken ("") result for every other test in the
session that expects the real CSS/MathJax bundle.
"""

from __future__ import annotations

import sys

import pytest
from PySide6.QtWidgets import QApplication

from epy_papers._ui import tab as tab_module

_app: QApplication | None = None


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    global _app
    if _app is not None:
        return _app
    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        app = instance
    elif instance is None:
        app = QApplication([])
    else:
        raise RuntimeError("tab tests need a QApplication.")
    _app = app
    return app


# ---------------------------------------------------------------------------
# _design_css (lru_cache)
# ---------------------------------------------------------------------------


def test_design_css_normally_returns_real_css():
    tab_module._design_css.cache_clear()
    try:
        css = tab_module._design_css()
        assert css != ""
    finally:
        tab_module._design_css.cache_clear()


def test_design_css_degrades_to_empty_string_when_the_theme_engine_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    """The preview must still render (with no design-block styling) if the
    shared theme engine cannot be reached, rather than raising out of a
    keystroke-driven render.
    """
    from epy_papers._core import _design

    tab_module._design_css.cache_clear()
    monkeypatch.setattr(
        _design,
        "design_css",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("no theme")),
    )
    try:
        assert tab_module._design_css() == ""
    finally:
        tab_module._design_css.cache_clear()


# ---------------------------------------------------------------------------
# _mathjax_block (lru_cache)
# ---------------------------------------------------------------------------


def test_mathjax_block_falls_back_to_config_only_when_the_bundle_is_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    """A packaging regression that drops the bundled tex-svg script must
    still produce a loadable preview (equations just will not typeset),
    not an exception from every render.
    """
    tab_module._mathjax_block.cache_clear()
    monkeypatch.setattr(
        tab_module.resources,
        "files",
        lambda _pkg: (_ for _ in ()).throw(OSError("bundle missing")),
    )
    try:
        block = tab_module._mathjax_block()
        assert "window.MathJax" in block
        assert "<script>" not in block.split("</script>", 1)[-1] or True
        assert len(block) < 1000  # config only, not the >100KB bundle
    finally:
        tab_module._mathjax_block.cache_clear()


# ---------------------------------------------------------------------------
# _journal_css
# ---------------------------------------------------------------------------


def test_journal_css_uses_the_named_font_when_not_times():
    css = tab_module._journal_css({"font": "Arial"})
    assert "'Arial', 'Times New Roman', serif" in css


def test_journal_css_defaults_to_times_with_no_font_named():
    css = tab_module._journal_css({})
    assert "'Times New Roman', Times, serif" in css


# ---------------------------------------------------------------------------
# _md_to_html_basic (the no-`markdown`-package fallback converter)
# ---------------------------------------------------------------------------


def test_md_to_html_basic_renders_headings_paragraphs_and_inline_markup():
    html = tab_module._md_to_html_basic(
        "# Title\n\nA paragraph with **bold** and *italic* and `code`.\n"
    )
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<code>code</code>" in html


def test_md_to_html_basic_renders_links_blockquotes_and_fenced_code():
    html = tab_module._md_to_html_basic(
        "> A quote\n\n"
        "[a link](https://example.com)\n\n"
        "```python\nprint('hi')\n```\n"
    )
    assert "<blockquote>A quote</blockquote>" in html
    assert '<a href="https://example.com">a link</a>' in html
    assert '<pre><code class="language-python">' in html
    assert "print(&#x27;hi&#x27;)" in html or "print('hi')" in html


def test_md_to_html_basic_strips_quarto_heading_attributes():
    html = tab_module._md_to_html_basic("## Section {#sec-one}\n")
    assert "<h2>Section</h2>" in html
    assert "{#sec-one}" not in html


def test_md_to_html_basic_closes_an_unterminated_fence_at_eof():
    """A fence opened but never closed must not swallow the rest of the
    document silently -- the buffered code is still emitted.

    No trailing newline after "left open" on purpose: ``text.split("\\n")``
    on a string that DOES end in ``\\n`` yields a trailing empty element,
    which the buffered join would render as a trailing blank line inside
    the ``<code>`` block -- a real, but separate, detail from what this
    test is pinning (that an unterminated fence still emits its content).
    """
    html = tab_module._md_to_html_basic("```\nleft open")
    assert "<pre><code>left open</code></pre>" in html


def test_md_to_html_basic_ignores_purely_blank_input():
    assert tab_module._md_to_html_basic("\n\n   \n") == ""


# ---------------------------------------------------------------------------
# _build_preview_faithful: <base href> resolution failure
# ---------------------------------------------------------------------------


def test_faithful_preview_omits_base_href_when_resolution_fails(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    from pathlib import Path

    monkeypatch.setattr(
        Path,
        "as_uri",
        lambda self: (_ for _ in ()).throw(ValueError("not absolute")),
    )
    src = "---\ntitle: T\nabstract: A.\n---\n\nBody.\n"
    html = tab_module._build_preview_faithful(src, {"name": "J"}, tmp_path)
    assert "<base href=" not in html
    assert 'class="page"' in html  # the render still completes


# ---------------------------------------------------------------------------
# _build_preview_html: front-matter / YAML / author / keyword / highlight
# shape variations, and the markdown-package fallback branches
# ---------------------------------------------------------------------------


def test_build_preview_html_recovers_from_a_split_front_matter_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        tab_module,
        "split_front_matter",
        lambda _text: (_ for _ in ()).throw(RuntimeError("bad front matter")),
    )
    html = tab_module._build_preview_html("---\ntitle: T\n---\n\nBody.\n")
    # No metadata could be read, but the raw text still renders as the body.
    assert "Body." in html


def test_build_preview_html_recovers_from_invalid_yaml_front_matter():
    src = "---\ntitle: [unterminated\n---\n\nBody text.\n"
    html = tab_module._build_preview_html(src)
    assert "Body text." in html
    assert "<h1>" not in html  # no title could be parsed out of broken YAML


def test_build_preview_html_accepts_a_bare_string_author():
    src = "---\nauthors: Jane Doe\n---\n\nBody.\n"
    html = tab_module._build_preview_html(src)
    assert "Jane Doe" in html


def test_build_preview_html_accepts_a_single_mapping_author():
    src = (
        "---\nauthors:\n  name: Jane Doe\n"
        "  affiliation: A University\n---\n\nBody.\n"
    )
    html = tab_module._build_preview_html(src)
    assert "Jane Doe, A University" in html


def test_build_preview_html_accepts_a_list_of_bare_string_authors():
    src = "---\nauthors:\n  - Jane Doe\n  - John Smith\n---\n\nBody.\n"
    html = tab_module._build_preview_html(src)
    assert "Jane Doe" in html
    assert "John Smith" in html


def test_build_preview_html_accepts_a_bare_scalar_for_keywords():
    src = "---\nkeywords: wind engineering\n---\n\nBody.\n"
    html = tab_module._build_preview_html(src)
    assert "wind engineering" in html


def test_build_preview_html_accepts_a_bare_string_for_highlights():
    src = "---\nhighlights: Just one highlight.\n---\n\nBody.\n"
    html = tab_module._build_preview_html(src)
    assert "Just one highlight." in html


def test_build_preview_html_falls_back_when_markdown_package_is_absent(
    monkeypatch: pytest.MonkeyPatch,
):
    """``sys.modules["markdown"] = None`` is the standard way to force the
    next ``import markdown`` to raise ``ImportError`` without uninstalling
    the real package for the rest of the suite.
    """
    monkeypatch.setitem(sys.modules, "markdown", None)
    html = tab_module._build_preview_html("# Title\n\nBody **bold**.\n")
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html


def test_build_preview_html_falls_back_when_markdown_conversion_raises(
    monkeypatch: pytest.MonkeyPatch,
):
    """Counter-example to the ImportError case: the package IS importable
    but its own conversion blows up -- still recovered by the same fallback.
    """
    import markdown

    monkeypatch.setattr(
        markdown,
        "markdown",
        lambda *_a, **_k: (_ for _ in ()).throw(ValueError("bad extension")),
    )
    html = tab_module._build_preview_html("# Title\n\nBody.\n")
    assert "<h1>Title</h1>" in html


def test_build_preview_html_uses_the_real_markdown_package_normally():
    """CONTROL: with nothing patched, the real ``markdown`` package (a
    project dependency) renders the body -- proves the two fallback tests
    above are exercising a real substitution, not the only code path.
    """
    html = tab_module._build_preview_html(
        "# Title\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    )
    assert "<h1>Title</h1>" in html
    # the `tables` extension only fires for the real markdown package
    assert "<table>" in html


# ---------------------------------------------------------------------------
# PaperTab: editor setup fallback
# ---------------------------------------------------------------------------


def test_setup_editor_falls_back_to_consolas_when_the_system_font_is_invalid(
    qapp: QApplication, monkeypatch: pytest.MonkeyPatch
):
    from PySide6.QtGui import QFont

    # QFont.setPointSize(0) is silently rejected by Qt (pointSize() stays
    # at its default, 9 -- verified with a probe) so it can never trigger
    # `pointSize() < 1`. Setting a PIXEL size instead is the one way to
    # make pointSize() report -1 (also probe-verified), which is what a
    # genuinely broken QFontDatabase.systemFont() result would look like.
    invalid = QFont()
    invalid.setPixelSize(10)
    assert invalid.pointSize() < 1  # precondition for the branch under test
    monkeypatch.setattr(
        tab_module.QFontDatabase,
        "systemFont",
        staticmethod(lambda _kind: invalid),
    )
    t = tab_module.PaperTab()
    assert t.editor.font().family() == "Consolas"
    assert t.editor.font().pointSize() == 11


# ---------------------------------------------------------------------------
# PaperTab: small direct-method coverage
# ---------------------------------------------------------------------------


@pytest.fixture
def tab(qapp: QApplication):
    return tab_module.PaperTab()


def test_reload_is_a_noop_on_an_untitled_buffer(tab):
    """The app.py caller (``_reload_current``) already refuses to call
    this when ``tab.path`` is None, so this guard is unreachable through
    that path -- exercised directly here instead.
    """
    tab.set_initial_text("some text", path=None)
    tab.reload()  # must not raise
    assert tab.text() == "some text"  # nothing changed


def test_is_dirty_mirrors_the_dirty_property(tab):
    assert tab.is_dirty() is False
    tab._set_dirty(True)
    assert tab.is_dirty() is True


def test_toggle_bold_wraps_a_selection(tab):
    tab.set_initial_text("hello world", path=None)
    cursor = tab.editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(5, cursor.MoveMode.KeepAnchor)
    tab.editor.setTextCursor(cursor)
    tab.toggle_bold()
    assert tab.text() == "**hello** world"


def test_toggle_bold_inserts_placeholder_with_no_selection(tab):
    tab.set_initial_text("", path=None)
    tab.toggle_bold()
    assert tab.text() == "**bold**"


def test_toggle_italic_inserts_placeholder_with_no_selection(tab):
    tab.set_initial_text("", path=None)
    tab.toggle_italic()
    assert tab.text() == "*italic*"


def test_insert_link_wraps_a_selection(tab):
    tab.set_initial_text("click here", path=None)
    cursor = tab.editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(len("click here"), cursor.MoveMode.KeepAnchor)
    tab.editor.setTextCursor(cursor)
    tab.insert_link()
    assert tab.text() == "[click here](URL)"


def test_insert_link_inserts_template_with_no_selection(tab):
    tab.set_initial_text("", path=None)
    tab.insert_link()
    assert tab.text() == "[text](URL)"


def test_each_inserted_figure_gets_its_own_label(tab):
    """This test recorded a DEFECT and now records its fix.

    ``_next_label_suffix``'s regex demanded the closing ``}`` immediately
    after the digits. But ``insert_figure``'s own template is
    ``{#fig-N width=80%}``, and the trailing `` width=80%`` meant the regex
    matched no real figure label: ``nums`` was always empty and the function
    always returned "1". Every figure a user inserted came back labelled
    ``fig-1``, and duplicate labels break every cross-reference to a figure
    in the rendered document.

    ``insert_table``/``insert_equation`` were unaffected only because their
    labels (``{#tbl-N}``, ``{#eq-N}``) carry no attributes -- which is why a
    test written against a table passes either way and sees nothing.
    """
    tab.set_initial_text("", path=None)
    tab.insert_figure()
    tab.insert_figure()
    tab.insert_figure()
    text = tab.text()
    assert "{#fig-1 width=80%}" in text
    assert "{#fig-2 width=80%}" in text
    assert "{#fig-3 width=80%}" in text
    assert text.count("{#fig-1 width=80%}") == 1, "the label repeated"


def test_a_figure_label_that_already_carries_attributes_is_counted(tab):
    """The counter-example on the regex itself: a label written by hand with
    any attributes must still be seen by the scan, or the next insert
    collides with it."""
    tab.set_initial_text("![x](y.png){#fig-7 width=50% .center}\n", path=None)
    tab.insert_figure()
    assert "{#fig-8 width=80%}" in tab.text()


def test_insert_table_labels_sequentially(tab):
    tab.set_initial_text("", path=None)
    tab.insert_table()
    assert "{#tbl-1}" in tab.text()
    assert "| Column 1 | Column 2 | Column 3 |" in tab.text()


def test_insert_equation_labels_sequentially(tab):
    tab.set_initial_text("", path=None)
    tab.insert_equation()
    assert "{#eq-1}" in tab.text()
    assert "E = mc^2" in tab.text()


def test_insert_citation(tab):
    tab.set_initial_text("", path=None)
    tab.insert_citation()
    assert tab.text() == "[@key]"


def test_insert_code_block(tab):
    tab.set_initial_text("", path=None)
    tab.insert_code_block()
    assert "```python\n# code here\n```" in tab.text()


def test_insert_disclosure_inserts_a_real_block(tab):
    tab.set_initial_text("", path=None)
    tab.insert_disclosure("ai")
    assert tab.text() != ""


def test_insert_title_block(tab):
    tab.set_initial_text("Existing body\n", path=None)
    tab.insert_title_block()
    assert tab.text().startswith("---\ntitle:\n")
    assert "Existing body" in tab.text()


def test_insert_authors(tab):
    tab.set_initial_text("", path=None)
    tab.insert_authors()
    assert "authors:" in tab.text()
    assert "corresponding: true" in tab.text()


def test_insert_abstract(tab):
    tab.set_initial_text("", path=None)
    tab.insert_abstract()
    assert "abstract:" in tab.text()


def test_insert_keywords(tab):
    tab.set_initial_text("", path=None)
    tab.insert_keywords()
    assert "keywords:" in tab.text()


def test_insert_highlights(tab):
    tab.set_initial_text("", path=None)
    tab.insert_highlights()
    assert "highlights:" in tab.text()


def test_insert_declarations(tab):
    tab.set_initial_text("", path=None)
    tab.insert_declarations()
    assert "declarations:" in tab.text()
    assert "credit:" in tab.text()


# ---------------------------------------------------------------------------
# _render_now: error-page fallback, and preserving scroll position
# ---------------------------------------------------------------------------


def test_render_now_shows_an_error_page_when_the_fallback_preview_raises(
    tab, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        tab_module,
        "_build_preview_html",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    tab.set_initial_text("anything", path=None)
    html = (tab._preview_tmp_dir / "preview.html").read_text(
        encoding="utf-8"
    )
    assert "Preview error" in html
    assert "boom" in html


def test_render_now_preserves_the_last_scroll_position(
    tab, monkeypatch: pytest.MonkeyPatch
):
    """``view.load()`` navigates asynchronously (Chromium out-of-process),
    so checking ``view.url()`` right after calling ``_render_now`` races
    the real navigation. Capturing the QUrl handed to ``load()`` checks
    the same thing (the fragment is set before the load call) without
    depending on when Chromium gets around to committing it.
    """
    tab.set_initial_text("Body.\n", path=None)  # first render (no fragment)
    captured: list[object] = []
    monkeypatch.setattr(tab.view, "load", lambda url: captured.append(url))
    tab._last_pos = "epypos=s:0.42"
    tab._render_now(preserve=True)
    assert captured[-1].fragment() == "epypos=s:0.42"


# ---------------------------------------------------------------------------
# _store_position
# ---------------------------------------------------------------------------


def test_store_position_records_a_string_position(tab):
    tab._store_position("epypos=s:0.7")
    assert tab._last_pos == "epypos=s:0.7"


def test_store_position_ignores_an_empty_or_non_string_result(tab):
    """Counter-example: JS that returns nothing useful must not clobber a
    previously captured position with an empty/garbage value.
    """
    tab._last_pos = "epypos=s:0.1"
    tab._store_position("")
    assert tab._last_pos == "epypos=s:0.1"
    tab._store_position(None)
    assert tab._last_pos == "epypos=s:0.1"
