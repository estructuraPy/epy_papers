"""Bridge module between epy_papers and the optional epy_docs package.

Independence contract
---------------------
This is the **only** module in epy_papers that may reference
``epy_docs``, and it does not reach it directly: ``epy_export`` owns the
engine catalogue, the availability route and the render, and this module
is the thin layer that speaks this application's vocabulary to it.

What it produces, and why it is a second option rather than a better
one. This editor's own engine builds a manuscript in a NAMED JOURNAL's
shape -- its class file, its citation style, its geometry. ePy Docs
builds the house document instead, with the corporate cover and the
legal note. Neither is a substitute for the other, which is exactly why
both are offered.
"""

from __future__ import annotations

from pathlib import Path

from epy_export import (
    APPEARANCES,
    DOCUMENT_TYPES,
    EngineUnavailableError,
    RenderOptions,
    available,
    render,
)

ENGINE_ID = "docs"
"""The engine this bridge speaks for, as the shared catalogue names it."""

# One condition, one name, matching the rest of the family: a caller
# cannot know which of two unrelated exception types to catch, so it
# catches one and the other escapes into a dialog unhandled.
BridgeUnavailableError = EngineUnavailableError


def epy_docs_available() -> bool:
    """Return whether this machine can render through epy_docs.

    Asks the shared route, which answers about the MACHINE rather than
    about this process's import path: inside the frozen bundle the
    engine can never be imported, and ePy Studio publishes the
    interpreter that carries it.

    Returns:
        Whether the engine can be reached. Nothing is imported and no
        subprocess is started, so this stays cheap enough to build a
        menu with.
    """
    return available(ENGINE_ID)


def list_layouts() -> list[str]:
    """Return the layout names this family publishes.

    Returns:
        The nine names, in the family's own order.
    """
    return list(APPEARANCES)


def list_document_types() -> list[str]:
    """Return the document kinds the generic writer can build.

    Returns:
        The kinds, in the family's own order.
    """
    return list(DOCUMENT_TYPES)


def render_document(
    source_path: Path,
    layout: str,
    document_type: str,
    output_dir: Path,
    pdf: bool,
    html: bool,
    docx: bool = False,
) -> list[Path]:
    """Render ``source_path`` through epy_docs and return what it made.

    Args:
        source_path: Absolute path to the manuscript source.
        layout: Layout name as returned by :func:`list_layouts`.
        document_type: Document kind as returned by
            :func:`list_document_types`.
        output_dir: Directory for the output; created when absent.
        pdf: When ``True``, request PDF output.
        html: When ``True``, request HTML output.
        docx: When ``True``, request Word (.docx) output.

    Returns:
        One path per format produced. Each is checked to exist before
        this returns: the engine reports success and writes nothing when
        Quarto is missing, so its own answer is not evidence.

    Raises:
        BridgeUnavailableError: When the engine cannot be reached.
        RenderFailedError: When it ran and produced nothing sound.
        ValueError: When no format was asked for, or the layout or the
            document kind is not one the family publishes.

    Note:
        No journal profile travels with this. It is read by ePy Papers
        alone, and the dispatcher refuses an option meant for another
        engine BY NAME rather than dropping it -- so asking the generic
        writer for a journal's shape says so instead of quietly
        returning the house document.

        ``source_kind`` is ``"markdown"``: a manuscript is Markdown with
        front matter, not a Quarto document with executable cells.
        Declared rather than guessed from the suffix, because the two
        entry points are different methods on the writer.
    """
    if not epy_docs_available():
        # Said here rather than left to the dispatcher. Its message is
        # right for a caller ("install it, or choose another engine")
        # and wrong for a reader: this engine is not something you
        # install, it is something you buy.
        raise BridgeUnavailableError(
            "ePy Docs is not available on this machine. It is a "
            "commercial add-on by ANM Ingenieria: "
            "ahnavarro@anmingenieria.com"
        )
    formats = [
        name
        for name, wanted in (("pdf", pdf), ("html", html), ("docx", docx))
        if wanted
    ]
    return render(
        source_path,
        output_dir,
        engine_id=ENGINE_ID,
        formats=formats,
        options=RenderOptions(
            appearance=layout,
            document_type=document_type,
            source_kind="markdown",
        ),
    )
