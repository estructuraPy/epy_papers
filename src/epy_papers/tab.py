"""A single editor/preview tab for epy_papers."""

from __future__ import annotations

import html as _html
import re
import shutil
import tempfile
from functools import lru_cache
from importlib import resources
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QFont, QFontDatabase, QTextCursor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from epy_papers._authoring import split_front_matter

RENDER_DEBOUNCE_MS = 250
POS_POLL_MS = 400
UNTITLED = "untitled.md"

_CAPTURE_POS_JS = (
    "(function () {"
    "  try {"
    "    var el = document.scrollingElement || document.documentElement;"
    "    if (!el) return '';"
    "    var d = el.scrollHeight - el.clientHeight;"
    "    return d > 0 ? 'epypos=s:' + (el.scrollTop / d) : '';"
    "  } catch (e) { return ''; }"
    "})()"
)

# Structural CSS shared by every preview. The journal-specific page metrics
# (font family, size, line spacing, columns, line numbers, page width) are
# layered on top by _journal_css() so the preview matches the manuscript the
# selected journal would receive.
_BASE_CSS = """
.page h1, .page h2, .page h3, .page h4 {
    font-family: inherit; color: #111;
    margin-top: 1.3em; margin-bottom: 0.4em; line-height: 1.3;
}
.page h1 { font-size: 1.5em; text-align: center; margin-top: 0; }
.byline { text-align: center; color: #333; margin-bottom: 1em; }
.abstract-block {
    border-left: 3px solid #999; margin: 1.2em 0;
    padding: 0.5em 1em; background: #f8f8f8;
}
.abstract-block h4 {
    font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.08em;
    color: #555; margin: 0 0 0.4em 0;
}
.lang-tag {
    font-size: 0.75em; color: #888; font-style: italic;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.keywords-block { color: #444; margin: 0.8em 0; }
.highlights-block {
    background: #f0f4f8; border: 1px solid #ccd; border-radius: 3px;
    padding: 0.6em 1em; margin: 0.8em 0;
}
.highlights-block ul { margin: 0.3em 0; padding-left: 1.4em; }
.declarations-block {
    color: #666; border-top: 1px solid #ddd;
    margin-top: 1.5em; padding-top: 0.8em; font-size: 0.85em;
}
.body-section { margin-top: 2em; }
pre, code { font-family: 'Courier New', monospace; background: #f5f5f5; }
pre { padding: 0.8em 1em; overflow-x: auto; border-radius: 2px; }
code { padding: 0.1em 0.3em; border-radius: 2px; }
blockquote {
    border-left: 3px solid #bbb; margin: 1em 0;
    padding: 0.3em 1em; color: #555;
}
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #ccc; padding: 0.4em 0.8em; text-align: left; }
th { background: #f0f0f0; font-weight: bold; }
img { max-width: 100%; height: auto; }
.fmt-bar {
    font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px;
    color: #44505f; background: #eef2f6; border: 1px solid #d7e0ea;
    border-radius: 4px; padding: 7px 14px; margin: 18px auto 0 auto;
}
.fmt-bar b { color: #243b53; }
"""


@lru_cache(maxsize=1)
def _design_css() -> str:
    """Theme-driven CSS for the shared design blocks (cards, stats, ...).

    Derived from the default suite theme so a big stat, card, timeline or
    agenda inserted in a paper renders with the same vocabulary the slides
    and reports apps use. Returns an empty string if the theme engine is
    unavailable, so the preview degrades gracefully.
    """
    try:
        from epy_papers import themes as _t  # noqa: PLC0415
        from epy_papers._design import design_css  # noqa: PLC0415

        return design_css(_t.get(_t.DEFAULT_THEME_ID), scope="")
    except Exception:
        return ""


def _journal_css(profile: dict | None) -> str:
    """Build page CSS from a journal profile.

    Translates the profile's submission requirements (font, size, line
    spacing, single/double column, line numbers, page size) into the CSS so
    the live preview looks like the manuscript that journal would receive.
    """
    p = profile or {}
    font_pt = p.get("font_size_pt", 12) or 12
    spacing = str(p.get("spacing", "double")).lower()
    line_height = {"single": "1.15", "1.5": "1.6", "double": "2.0"}.get(
        spacing, "2.0"
    )
    font_name = str(p.get("font", "") or "")
    if not font_name or "times" in font_name.lower():
        family = "'Times New Roman', Times, serif"
    else:
        family = f"'{font_name}', 'Times New Roman', serif"
    page_w = (
        "8.5in" if str(p.get("page_size", "letter")) == "letter" else "210mm"
    )
    try:
        columns = int(p.get("columns", 1) or 1)
    except (TypeError, ValueError):
        columns = 1
    col_css = "column-count: 2; column-gap: 0.4in;" if columns >= 2 else ""
    # Line numbering is NOT done here. A per-block CSS counter would number
    # paragraphs, not the typeset rows a journal numbers; the preview instead
    # paints a per-visual-row gutter (see _LINE_NUMBER_JS), which matches what
    # the DOCX (w:lnNumType) and LaTeX (lineno) exports actually produce.
    return (
        "html, body { margin: 0; padding: 0; background: #e9edf1; }"
        f"body {{ font-family: {family}; font-size: {font_pt}pt;"
        f" line-height: {line_height}; color: #111; }}"
        ".page {"
        f" width: {page_w}; box-sizing: border-box; background: #fff;"
        " margin: 14px auto 28px auto; padding: 1in 1in 1in 1.6in;"
        " box-shadow: 0 1px 8px rgba(0,0,0,0.18); }"
        f".page .body-section {{ {col_css} }}"
        f".fmt-bar {{ width: {page_w}; box-sizing: border-box; }}"
    )


def _format_summary(profile: dict | None) -> str:
    """Return a one-line, human-readable summary of the journal format."""
    p = profile or {}
    name = str(p.get("name", "")) or "no journal selected"
    try:
        columns = int(p.get("columns", 1) or 1)
    except (TypeError, ValueError):
        columns = 1
    col = "double column" if columns >= 2 else "single column"
    spacing = {"single": "single", "1.5": "1.5", "double": "double"}.get(
        str(p.get("spacing", "double")).lower(), "double"
    )
    font_pt = p.get("font_size_pt", 12) or 12
    page = str(p.get("page_size", "letter")).upper()
    ln = str(p.get("line_numbers", "off")).lower() not in (
        "off", "", "false", "no", "none", "0"
    )
    return (
        f"Formatted for <b>{_html.escape(name)}</b> &middot; {col} &middot; "
        f"{spacing} spaced &middot; {font_pt} pt &middot; {page} &middot; "
        f"line numbers {'on' if ln else 'off'}"
    )


def _md_to_html_basic(text: str) -> str:
    """Convert Markdown to HTML without external dependencies.

    Handles headings, bold, italic, code blocks, fenced code, inline
    code, blockquotes, and paragraphs. Used when the ``markdown`` package
    is not installed.
    """
    lines = text.split("\n")
    out: list[str] = []
    in_code = False
    code_buf: list[str] = []
    code_lang = ""
    para_buf: list[str] = []

    def flush_para() -> None:
        if para_buf:
            content = " ".join(para_buf).strip()
            if content:
                out.append(f"<p>{content}</p>")
            para_buf.clear()

    def inline(s: str) -> str:
        s = _html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        s = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            r'<a href="\2">\1</a>',
            s,
        )
        return s

    for line in lines:
        # Fenced code block toggle
        fence = re.match(r"^```(\w*)", line)
        if fence:
            if not in_code:
                flush_para()
                in_code = True
                code_lang = fence.group(1)
                code_buf = []
            else:
                lang_cls = (
                    f' class="language-{code_lang}"' if code_lang else ""
                )
                body = _html.escape("\n".join(code_buf))
                out.append(
                    f"<pre><code{lang_cls}>{body}</code></pre>"
                )
                in_code = False
                code_buf = []
            continue
        if in_code:
            code_buf.append(line)
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            flush_para()
            level = len(m.group(1))
            # Strip Quarto attributes {#id ...}
            heading = re.sub(r"\{[^}]+\}", "", m.group(2)).strip()
            out.append(f"<h{level}>{inline(heading)}</h{level}>")
            continue

        # Blockquote
        m = re.match(r"^>\s?(.*)", line)
        if m:
            flush_para()
            out.append(f"<blockquote>{inline(m.group(1))}</blockquote>")
            continue

        # Blank line → paragraph boundary
        if not line.strip():
            flush_para()
            continue

        para_buf.append(inline(line))

    flush_para()
    if in_code and code_buf:
        body = _html.escape("\n".join(code_buf))
        out.append(f"<pre><code>{body}</code></pre>")

    return "\n".join(out)


@lru_cache(maxsize=1)
def _mathjax_block() -> str:
    """Return the MathJax v3 config + bundled tex-svg script (cached)."""
    cfg = (
        "<script>window.MathJax={tex:{inlineMath:[['$','$'],"
        "['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']],"
        "processEscapes:true,tags:'none'},svg:{fontCache:'global'},"
        "startup:{ready(){MathJax.startup.defaultReady();"
        "MathJax.startup.promise.then(function(){"
        "window._mathjax_done=true;});}}};</script>"
    )
    try:
        js = (
            resources.files("epy_papers.assets.mathjax")
            .joinpath("tex-svg-full.js")
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        return cfg
    return cfg + f"<script>{js}</script>"


_LINE_NUMBER_CSS = (
    ".page { position: relative; }"
    ".epy-lnum-gutter { position: absolute; top: 0; left: 0;"
    " width: 1.4in; height: 100%; pointer-events: none; }"
    ".epy-lnum { position: absolute; left: 0.35in; width: 0.8in;"
    " text-align: right; color: #b6b6b6;"
    " font: 0.66em/1 'Segoe UI', Arial, sans-serif; }"
)

_LINE_NUMBER_JS = """
<script>
(function () {
  function number() {
    var page = document.querySelector('.page'); if (!page) return;
    var body = page.querySelector('.body-section') || page;
    var old = page.querySelector('.epy-lnum-gutter'); if (old) old.remove();
    var g = document.createElement('div'); g.className = 'epy-lnum-gutter';
    page.appendChild(g);
    var base = page.getBoundingClientRect(), n = 0;
    var blocks = body.querySelectorAll(
      'p, li, h2, h3, h4, blockquote, figcaption, dd, dt');
    blocks.forEach(function (b) {
      var rng = document.createRange(); rng.selectNodeContents(b);
      var rects = rng.getClientRects(), seen = {};
      for (var i = 0; i < rects.length; i++) {
        var r = rects[i];
        if (r.width < 2 || r.height < 2) continue;
        var k = Math.round(r.top); if (seen[k]) continue; seen[k] = 1;
        n++;
        var d = document.createElement('div');
        d.className = 'epy-lnum'; d.textContent = n;
        d.style.top = (r.top - base.top) + 'px';
        g.appendChild(d);
      }
    });
  }
  window._epyNumberLines = number;
  var tries = 0;
  function wait() {
    tries++;
    if (window._mathjax_done === true || tries > 50 || !window.MathJax) {
      try { number(); } catch (e) {}
    } else { setTimeout(wait, 80); }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wait);
  } else { wait(); }
  var t;
  window.addEventListener('resize', function () {
    clearTimeout(t);
    t = setTimeout(function () { try { number(); } catch (e) {} }, 150);
  });
})();
</script>
"""


def _wants_line_numbers(profile: dict | None) -> bool:
    """Whether the profile asks for numbered manuscript lines."""
    return str((profile or {}).get("line_numbers", "off")).lower() not in (
        "off", "", "false", "no", "none", "0"
    )


def _build_preview_faithful(
    text: str, profile: dict | None, base_dir: Path | None = None
) -> str:
    """Render a WYSIWYG preview through the export's Pandoc pipeline.

    The body is rendered by Pandoc exactly as it would be exported — citations
    resolved with the journal's CSL, numbered sections, double-blind author
    stripping — wrapped in the journal's page geometry, with MathJax
    typesetting equations and real per-visual-line numbering when the journal
    requires it. Raises when Pandoc is unavailable so the caller can fall back
    to the fast preview.
    """
    from epy_papers import Paper  # noqa: PLC0415
    from epy_papers._render import Renderer  # noqa: PLC0415

    paper = Paper(text, base_dir)
    fragment = Renderer(paper.manuscript, profile or {}).to_html_fragment()
    css = _journal_css(profile) + _BASE_CSS + _design_css()
    line_numbers = _wants_line_numbers(profile)
    ln_css = _LINE_NUMBER_CSS if line_numbers else ""
    ln_js = _LINE_NUMBER_JS if line_numbers else ""
    base_href = ""
    if base_dir is not None:
        try:
            base_href = f'<base href="{base_dir.resolve().as_uri()}/">'
        except (ValueError, OSError):
            base_href = ""
    fmt_bar = f'<div class="fmt-bar">{_format_summary(profile)}</div>'
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"{base_href}"
        f"<style>{css}{ln_css}.page .body-section{{margin-top:0;}}</style>"
        f"{_mathjax_block()}"
        "</head><body>"
        f"{fmt_bar}"
        f'<div class="page"><div class="body-section">{fragment}</div></div>'
        f"{ln_js}"
        "</body></html>"
    )


def _build_preview_html(text: str, profile: dict | None = None) -> str:
    """Generate a journal-formatted HTML preview from paper Markdown source.

    When a journal ``profile`` is supplied, the page metrics (font, line
    spacing, columns, line numbers, page size) and submission rules (author
    blinding) match the manuscript that journal would receive.
    """
    profile = profile or {}
    blinded = str(profile.get("blinding", "")).lower() in (
        "double", "double-blind", "double_blind"
    )
    try:
        fm_text, body_text = split_front_matter(text)
    except Exception:
        fm_text, body_text = "", text

    meta: dict = {}
    try:
        import yaml
        if fm_text.strip():
            meta = yaml.safe_load(fm_text) or {}
    except Exception:
        pass

    # --- title ---
    title_raw = meta.get("title", "")
    if isinstance(title_raw, dict):
        title_str = (
            title_raw.get("en")
            or title_raw.get("es")
            or next(iter(title_raw.values()), "")
        )
    else:
        title_str = str(title_raw) if title_raw else ""

    # --- authors ---
    authors_raw = meta.get("authors", meta.get("author", []))
    if isinstance(authors_raw, str):
        authors_raw = [{"name": authors_raw}]
    elif isinstance(authors_raw, dict):
        authors_raw = [authors_raw]
    author_names: list[str] = []
    for a in (authors_raw or []):
        if isinstance(a, dict):
            n = a.get("name", "")
            aff = a.get("affiliation", "")
            author_names.append(
                f"{n}, {aff}" if aff else n
            )
        elif isinstance(a, str):
            author_names.append(a)

    # --- abstract ---
    abstract_raw = meta.get("abstract", "")
    if isinstance(abstract_raw, dict):
        abstract_str = (
            abstract_raw.get("en")
            or abstract_raw.get("es")
            or next(iter(abstract_raw.values()), "")
        )
    else:
        abstract_str = str(abstract_raw) if abstract_raw else ""

    # --- keywords ---
    kw_raw = meta.get("keywords", [])
    if isinstance(kw_raw, dict):
        kw_list = kw_raw.get("en") or kw_raw.get("es") or []
    elif isinstance(kw_raw, list):
        kw_list = kw_raw
    else:
        kw_list = [str(kw_raw)] if kw_raw else []
    keywords_str = ", ".join(str(k) for k in kw_list)

    # --- highlights ---
    highlights = meta.get("highlights", [])
    if isinstance(highlights, str):
        highlights = [highlights]

    # --- declarations ---
    decl_raw = meta.get("declarations", {})
    decl_items = (
        list(decl_raw.items()) if isinstance(decl_raw, dict) else []
    )

    # --- body HTML ---
    try:
        import markdown
        body_html = markdown.markdown(
            body_text,
            extensions=["tables", "fenced_code"],
        )
    except ImportError:
        body_html = _md_to_html_basic(body_text)
    except Exception:
        body_html = _md_to_html_basic(body_text)

    # --- assemble ---
    parts: list[str] = []

    if title_str:
        parts.append(f"<h1>{_html.escape(title_str)}</h1>")

    if author_names and not blinded:
        byline = "; ".join(_html.escape(n) for n in author_names)
        parts.append(f'<p class="byline">{byline}</p>')
    elif author_names and blinded:
        parts.append(
            '<p class="byline"><em>[author identities withheld '
            "&mdash; double-blind submission]</em></p>"
        )

    if abstract_str:
        parts.append(
            '<div class="abstract-block">'
            "<h4>Abstract</h4>"
            f"<p>{_html.escape(abstract_str.strip())}</p>"
            "</div>"
        )

    if keywords_str:
        parts.append(
            f'<p class="keywords-block">'
            f"<strong>Keywords:</strong> {_html.escape(keywords_str)}"
            f"</p>"
        )

    if highlights:
        items = "".join(
            f"<li>{_html.escape(str(h))}</li>" for h in highlights
        )
        parts.append(
            '<div class="highlights-block">'
            "<strong>Highlights</strong>"
            f"<ul>{items}</ul>"
            "</div>"
        )

    if decl_items:
        decl_html = " &bull; ".join(
            f"<em>{_html.escape(str(k))}:</em> {_html.escape(str(v))}"
            for k, v in decl_items
        )
        parts.append(
            f'<div class="declarations-block">{decl_html}</div>'
        )

    if body_html:
        parts.append(f'<div class="body-section">{body_html}</div>')

    page_title = _html.escape(title_str) if title_str else "epy_papers"
    body_content = "\n".join(parts)
    css = _journal_css(profile) + _BASE_CSS + _design_css()
    fmt_bar = f'<div class="fmt-bar">{_format_summary(profile)}</div>'
    line_numbers = _wants_line_numbers(profile)
    ln_css = _LINE_NUMBER_CSS if line_numbers else ""
    ln_js = _LINE_NUMBER_JS if line_numbers else ""

    return (
        "<!DOCTYPE html><html><head>"
        f"<meta charset='utf-8'><title>{page_title}</title>"
        f"<style>{css}{ln_css}</style>"
        "</head><body>"
        f"{fmt_bar}"
        f'<div class="page">{body_content}</div>'
        f"{ln_js}"
        "</body></html>"
    )


class PaperTab(QWidget):
    """Editor + live preview for one paper Markdown buffer.

    Signals:
        pathChanged: Emitted when the on-disk path is set or changed.
        dirtyChanged: Emitted with the new dirty flag when it flips.
    """

    pathChanged = Signal()  # noqa: N815
    dirtyChanged = Signal(bool)  # noqa: N815

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the editor, the web preview and the debounce timer."""
        super().__init__(parent)

        self._path: Path | None = None
        self._dirty = False
        self._suppress_change = False
        self._render_seq = 0
        self._last_pos = ""
        self._preview_tmp_dir: Path | None = None
        self._journal_profile: dict | None = None

        self.editor = QPlainTextEdit(self)
        self._setup_editor()

        self.view = QWebEngineView(self)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([520, 600])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(RENDER_DEBOUNCE_MS)
        self._render_timer.timeout.connect(self._render)

        self._pos_timer = QTimer(self)
        self._pos_timer.setInterval(POS_POLL_MS)
        self._pos_timer.timeout.connect(self._poll_position)
        self._pos_timer.start()

        self.editor.textChanged.connect(self._on_text_changed)

    def _setup_editor(self) -> None:
        """Configure the editor with monospace font and 4-space tabs."""
        font = QFontDatabase.systemFont(
            QFontDatabase.SystemFont.FixedFont
        )
        if font.pointSize() < 1:
            font = QFont("Consolas")
        font.setPointSize(11)
        self.editor.setFont(font)
        metrics = self.editor.fontMetrics()
        self.editor.setTabStopDistance(
            4 * metrics.horizontalAdvance(" ")
        )
        self.editor.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth
        )
        self.editor.setPlaceholderText(
            "Type paper Markdown here. "
            "Preview updates on the right."
        )

    # ---------------------------------------------------------------- API

    @property
    def path(self) -> Path | None:
        """Return the on-disk path, or ``None`` for unsaved buffers."""
        return self._path

    @property
    def dirty(self) -> bool:
        """Return ``True`` if the buffer has unsaved changes."""
        return self._dirty

    def is_dirty(self) -> bool:
        """Alias for the ``dirty`` property."""
        return self._dirty

    def title(self) -> str:
        """Return the tab title, suffixed with ``*`` when dirty."""
        base = self._path.name if self._path is not None else UNTITLED
        return f"{base} *" if self._dirty else base

    def text(self) -> str:
        """Return the current editor text."""
        return self.editor.toPlainText()

    def set_initial_text(
        self, text: str, path: Path | None = None
    ) -> None:
        """Populate the buffer from a string, then render.

        Args:
            text: Initial buffer contents.
            path: Optional path that ``text`` was loaded from.
        """
        self._suppress_change = True
        self.editor.setPlainText(text)
        self._suppress_change = False
        self._path = path
        self._set_dirty(False)
        self._render_now()
        self.pathChanged.emit()

    def load_file(self, path: Path) -> None:
        """Load a Markdown file from disk into this tab."""
        text = path.read_text(encoding="utf-8")
        self.set_initial_text(text, path)

    def save(self) -> bool:
        """Save the buffer to its current path.

        Returns:
            ``True`` if the buffer was written, ``False`` when no path
            is associated (caller should fall back to Save As).
        """
        if self._path is None:
            return False
        self._path.write_text(
            self.editor.toPlainText(), encoding="utf-8"
        )
        self._set_dirty(False)
        return True

    def save_as(self, path: Path) -> None:
        """Save the buffer to ``path`` and adopt it as current path."""
        path.write_text(
            self.editor.toPlainText(), encoding="utf-8"
        )
        self._path = path
        self._set_dirty(False)
        self.pathChanged.emit()
        self._render_now()

    def reload(self) -> None:
        """Reload the buffer from disk, discarding in-memory changes."""
        if self._path is None:
            return
        self.load_file(self._path)

    def cleanup_preview_tmp(self) -> None:
        """Delete the temp dir backing the live preview (call on close)."""
        tmp = getattr(self, "_preview_tmp_dir", None)
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
            self._preview_tmp_dir = None

    def set_journal(self, profile: dict | None) -> None:
        """Set the active journal profile and re-render to match its format."""
        self._journal_profile = profile
        self._render_now(preserve=True)

    # ----------------------------------------------- insert helpers

    def toggle_bold(self) -> None:
        """Wrap the current selection (or caret) in ``**...**``."""
        self._wrap_selection("**", "**", placeholder="bold")

    def toggle_italic(self) -> None:
        """Wrap the current selection (or caret) in ``*...*``."""
        self._wrap_selection("*", "*", placeholder="italic")

    def insert_link(self) -> None:
        """Insert ``[text](URL)`` at the cursor."""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            sel = cursor.selectedText()
            cursor.insertText(f"[{sel}](URL)")
        else:
            self._insert_template("[text](URL)", "URL")
        self.editor.setFocus()

    def insert_figure(self) -> None:
        """Insert a figure template with sequential label."""
        n = self._next_label_suffix("fig")
        tmpl = (
            f"\n![Figure {n}: Caption]"
            f"(figures/figure-{n}.png)"
            f"{{#fig-{n} width=80%}}\n"
        )
        self._insert_raw(tmpl)

    def insert_table(self) -> None:
        """Insert a pipe table template with sequential label."""
        n = self._next_label_suffix("tbl")
        tmpl = (
            f"\n: Table {n}: Caption {{#tbl-{n}}}\n\n"
            "| Column 1 | Column 2 | Column 3 |\n"
            "|----------|----------|----------|\n"
            "| Cell     | Cell     | Cell     |\n"
        )
        self._insert_raw(tmpl)

    def insert_equation(self) -> None:
        """Insert a display equation with sequential label."""
        n = self._next_label_suffix("eq")
        tmpl = f"\n$$\nE = mc^2\n$$ {{#eq-{n}}}\n"
        self._insert_raw(tmpl)

    def insert_citation(self) -> None:
        """Insert a citation placeholder at the cursor."""
        self._insert_template("[@key]", "key")

    def insert_code_block(self) -> None:
        """Insert a fenced Python code block skeleton."""
        tmpl = "\n```python\n# code here\n```\n"
        self._insert_raw(tmpl)

    def insert_design_block(self, kind: str = "stat") -> None:
        """Insert a shared design block (card, big stat, timeline, ...)."""
        from epy_papers._design import design_block  # noqa: PLC0415

        skeleton, token = design_block(kind)
        self._insert_template(skeleton, token)

    def insert_title_block(self) -> None:
        """Insert a YAML front matter template at the cursor."""
        tmpl = (
            "---\n"
            "title:\n"
            '  en: "Title in English"\n'
            '  es: "Título en Español"\n'
            "language: en\n"
            "authors:\n"
            "  - name: Author Name\n"
            "    affiliation: Institution\n"
            "    email: email@example.com\n"
            "    corresponding: true\n"
            "abstract:\n"
            '  en: "Abstract in English."\n'
            '  es: "Resumen en Español."\n'
            "keywords:\n"
            "  en: [keyword1, keyword2]\n"
            "  es: [palabra1, palabra2]\n"
            "bibliography: refs.bib\n"
            "---\n"
        )
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)
        cursor.insertText(tmpl)
        self.editor.setFocus()

    def insert_authors(self) -> None:
        """Insert an authors YAML block at the cursor."""
        tmpl = (
            "\nauthors:\n"
            "  - name: Author Name\n"
            "    affiliation: Institution\n"
            "    email: email@example.com\n"
            "    orcid: 0000-0000-0000-0000\n"
            "    corresponding: true\n"
        )
        self._insert_raw(tmpl)

    def insert_abstract(self) -> None:
        """Insert an abstract YAML block at the cursor."""
        tmpl = (
            "\nabstract:\n"
            '  en: "Abstract text in English."\n'
            '  es: "Texto del resumen en Español."\n'
        )
        self._insert_raw(tmpl)

    def insert_keywords(self) -> None:
        """Insert a keywords YAML block at the cursor."""
        tmpl = (
            "\nkeywords:\n"
            "  en: [keyword1, keyword2, keyword3]\n"
            "  es: [palabra1, palabra2, palabra3]\n"
        )
        self._insert_raw(tmpl)

    def insert_highlights(self) -> None:
        """Insert a highlights YAML block at the cursor."""
        tmpl = (
            "\nhighlights:\n"
            "  - First highlight (max 85 characters per item).\n"
            "  - Second highlight.\n"
            "  - Third highlight.\n"
        )
        self._insert_raw(tmpl)

    def insert_declarations(self) -> None:
        """Insert a declarations YAML block at the cursor."""
        tmpl = (
            "\ndeclarations:\n"
            '  credit: "Author: conceptualization, writing."\n'
            '  competing-interests: "No competing interests."\n'
            '  data-availability: "Data available at repository."\n'
            '  funding: "No external funding."\n'
        )
        self._insert_raw(tmpl)

    # -------------------------------------------------- internals

    def _next_label_suffix(self, kind: str) -> str:
        """Return the next sequential integer suffix for ``kind`` labels."""
        text = self.editor.toPlainText()
        pattern = rf"\{{#(?:{kind})-(\d+)\}}"
        nums = [int(m) for m in re.findall(pattern, text)]
        return str(max(nums) + 1) if nums else "1"

    def _insert_raw(self, tmpl: str) -> None:
        """Insert ``tmpl`` at the cursor position."""
        cursor = self.editor.textCursor()
        cursor.insertText(tmpl)
        self.editor.setFocus()

    def _insert_template(
        self, template: str, select_token: str
    ) -> None:
        """Insert ``template`` and select ``select_token`` inside it."""
        cursor = self.editor.textCursor()
        start = cursor.position()
        cursor.insertText(template)
        index = template.find(select_token)
        if index >= 0:
            cursor.setPosition(start + index)
            cursor.setPosition(
                start + index + len(select_token),
                QTextCursor.MoveMode.KeepAnchor,
            )
            self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _wrap_selection(
        self, left: str, right: str, placeholder: str = ""
    ) -> None:
        """Wrap the selection in ``left``/``right`` or insert markers."""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"{left}{text}{right}")
        else:
            cursor.insertText(f"{left}{placeholder}{right}")
            end = cursor.position()
            cursor.setPosition(end - len(right) - len(placeholder))
            cursor.setPosition(
                end - len(right),
                QTextCursor.MoveMode.KeepAnchor,
            )
            self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _set_dirty(self, value: bool) -> None:
        """Update the dirty flag and notify listeners on change."""
        if self._dirty != value:
            self._dirty = value
            self.dirtyChanged.emit(value)

    def _on_text_changed(self) -> None:
        """React to user edits: flag dirty and schedule a re-render."""
        if self._suppress_change:
            return
        if not self._dirty:
            self._set_dirty(True)
        self._render_timer.start()

    def _render(self) -> None:
        """Debounced re-render after an edit."""
        self._render_now(preserve=True)

    def _render_now(self, *, preserve: bool = False) -> None:
        """Render the buffer into the preview view.

        With a journal selected, the preview is rendered through the export's
        Pandoc pipeline (faithful WYSIWYG); if Pandoc is unavailable or the
        render fails, it falls back to the fast in-process preview.
        """
        text = self.editor.toPlainText()
        base_dir = self._path.parent if self._path is not None else None
        html = None
        if self._journal_profile:
            try:
                html = _build_preview_faithful(
                    text, self._journal_profile, base_dir
                )
            except Exception:
                html = None
        if html is None:
            try:
                html = _build_preview_html(text, self._journal_profile)
            except Exception:
                html = (
                    "<html><body>"
                    "<p style='color:red'>Preview error.</p>"
                    "</body></html>"
                )
        if self._preview_tmp_dir is None:
            self._preview_tmp_dir = Path(
                tempfile.mkdtemp(prefix="epy_papers_preview_")
            )
        preview_path = self._preview_tmp_dir / "preview.html"
        preview_path.write_text(html, encoding="utf-8")
        url = QUrl.fromLocalFile(str(preview_path.resolve()))
        self._render_seq += 1
        url.setQuery(f"r={self._render_seq}")
        if preserve and self._last_pos:
            url.setFragment(self._last_pos)
        self.view.load(url)

    def _poll_position(self) -> None:
        """Cache the preview scroll position for the next render."""
        page = self.view.page()
        if page is not None:
            page.runJavaScript(
                _CAPTURE_POS_JS, self._store_position
            )

    def _store_position(self, pos: object) -> None:
        """Record a captured ``epypos=…`` token."""
        if isinstance(pos, str) and pos:
            self._last_pos = pos
