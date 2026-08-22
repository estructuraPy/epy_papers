"""Export the Brooklyn Bridge manuscript as journal-compliant drafts.

From the single source ``brooklyn_bridge.md`` this renders the submission
manuscript for a few representative journals, each in every format the profile
allows plus a self-contained HTML preview:

* **ASCE Journal of Structural Engineering** (``asce-jse``) — ``ascelike``
  LaTeX class.
* **Elsevier Engineering Structures** (``eng-structures``) — ``elsarticle``
  LaTeX class.

For each journal the script writes DOCX, LaTeX source and standalone HTML. A
PDF is also produced **when a LaTeX engine is available** — one on ``PATH`` or
the private TinyTeX the app manages; if none is found the PDF step is skipped
with a note (PDF is the only format that needs LaTeX).

Run it from this directory::

    python render_drafts.py                 # every target journal
    python render_drafts.py asce-jse        # a single journal

Output lands in ``_render/`` (git-ignored).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Prefer an installed epy_papers; fall back to the in-repo source tree so the
# example runs straight from a clone without `pip install -e .`.
try:
    from epy_papers import Paper
    from epy_papers._core._latex import LatexMissingError, find_engine
except ImportError:
    sys.path.insert(0, str(ROOT.parent.parent / "src"))
    from epy_papers import Paper
    from epy_papers._core._latex import LatexMissingError, find_engine

SOURCE = ROOT / "brooklyn_bridge.md"
OUT_DIR = ROOT / "_render"

# (output suffix, source file) — the base .md is English, _es is Spanish; the
# example ships both languages and every journal draft is rendered in each one.
LANGS = [("", SOURCE), ("_es", ROOT / "brooklyn_bridge_es.md")]

# Representative target journals (id -> human label). Both are structural-
# engineering venues whose official LaTeX class epy_papers bundles, so the
# LaTeX / PDF drafts use the journal's real class, not the generic fallback.
TARGETS = {
    "asce-jse": "ASCE Journal of Structural Engineering",
    "eng-structures": "Elsevier Engineering Structures",
}


def render(
    source: Path, journal_id: str, label: str, suffix: str, *, have_latex: bool
) -> None:
    """Export every format of the draft for one journal, one language."""
    print(f"\n=== {journal_id}{suffix or ' (en)'} — {label} ===")
    paper = Paper.from_file(source)
    stem = f"brooklyn_{journal_id.replace('-', '_')}{suffix}"
    formats = ["docx", "tex", "html"]
    if have_latex:
        formats.append("pdf")
    else:
        print("  PDF   skipped (no LaTeX engine found)")
    for fmt in formats:
        out = OUT_DIR / f"{stem}.{fmt}"
        try:
            paper.to_draft(journal_id, out, fmt=fmt)
            size = out.stat().st_size if out.exists() else 0
            print(f"  {fmt.upper():5s} -> {out.name}  ({size:,} bytes)")
        except LatexMissingError:
            print(f"  {fmt.upper():5s} skipped (no LaTeX engine)")
        except (OSError, RuntimeError) as exc:
            print(f"  {fmt.upper():5s} FAILED: {exc}")


def main() -> int:
    """Render the draft for the requested journal(s)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    targets = {only: TARGETS.get(only, only)} if only else TARGETS
    have_latex = find_engine() is not None
    if not have_latex:
        print(
            "No LaTeX engine found — exporting DOCX / LaTeX / HTML only "
            "(install TinyTeX from the app to enable PDF)."
        )
    for suffix, src in LANGS:
        if not src.is_file():
            continue
        for jid, label in targets.items():
            render(src, jid, label, suffix, have_latex=have_latex)
    print("\nAll drafts rendered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
