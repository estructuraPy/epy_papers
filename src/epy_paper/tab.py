"""A single editor/preview tab for epy_paper."""

from __future__ import annotations

import html as _html
import re
import shutil
import tempfile
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

from epy_paper._authoring import split_front_matter

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

_PREVIEW_CSS = """
body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 40px;
    background: #ffffff;
    color: #1a1a1a;
}
h1, h2, h3, h4 {
    font-family: 'Palatino Linotype', Palatino, serif;
    color: #1a1a1a;
    margin-top: 1.4em;
    margin-bottom: 0.4em;
}
h1 { font-size: 1.6em; text-align: center; margin-top: 0; }
.byline {
    text-align: center;
    color: #333;
    font-size: 0.95em;
    margin-bottom: 1em;
}
.abstract-block {
    border-left: 3px solid #999;
    margin: 1.2em 0;
    padding: 0.5em 1em;
    background: #f8f8f8;
    font-size: 0.93em;
}
.abstract-block h4 {
    font-size: 0.88em;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #555;
    margin: 0 0 0.4em 0;
}
.keywords-block {
    font-size: 0.88em;
    color: #444;
    margin: 0.8em 0;
}
.highlights-block {
    background: #f0f4f8;
    border: 1px solid #ccd;
    border-radius: 3px;
    padding: 0.6em 1em;
    font-size: 0.88em;
    margin: 0.8em 0;
}
.highlights-block ul { margin: 0.3em 0; padding-left: 1.4em; }
.declarations-block {
    font-size: 0.8em;
    color: #666;
    border-top: 1px solid #ddd;
    margin-top: 1.5em;
    padding-top: 0.8em;
}
.body-section { margin-top: 2em; }
pre, code {
    font-family: 'Courier New', monospace;
    font-size: 0.88em;
    background: #f5f5f5;
    border-radius: 2px;
}
pre { padding: 0.8em 1em; overflow-x: auto; }
code { padding: 0.1em 0.3em; }
blockquote {
    border-left: 3px solid #bbb;
    margin: 1em 0;
    padding: 0.3em 1em;
    color: #555;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 0.9em;
}
th, td { border: 1px solid #ccc; padding: 0.4em 0.8em; text-align: left; }
th { background: #f0f0f0; font-weight: bold; }
img { max-width: 100%; height: auto; }
"""


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


def _build_preview_html(text: str) -> str:
    """Generate a styled HTML preview from paper Markdown source."""
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

    if author_names:
        byline = "; ".join(_html.escape(n) for n in author_names)
        parts.append(f'<p class="byline">{byline}</p>')

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

    page_title = _html.escape(title_str) if title_str else "epy_paper"
    body_content = "\n".join(parts)

    return (
        "<!DOCTYPE html><html><head>"
        f"<meta charset='utf-8'><title>{page_title}</title>"
        f"<style>{_PREVIEW_CSS}</style>"
        "</head><body>"
        f"{body_content}"
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
        """Render the buffer into the preview view."""
        text = self.editor.toPlainText()
        try:
            html = _build_preview_html(text)
        except Exception:
            html = (
                "<html><body>"
                "<p style='color:red'>Preview error.</p>"
                "</body></html>"
            )
        if not hasattr(self, "_preview_tmp_dir"):
            self._preview_tmp_dir = Path(
                tempfile.mkdtemp(prefix="epy_paper_preview_")
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
