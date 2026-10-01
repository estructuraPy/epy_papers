"""epy_papers — write a paper once, export a journal-compliant draft.

Single public API for the suite (mirrors ``epy_reports.Report`` /
``epy_slides.SlideDeck`` / ``epy_project.ProjectManager``)::

    from epy_papers import Paper, available_journals

    available_journals()                       # [(id, name), ...]
    paper = Paper.from_file("manuscript.md")
    result = paper.validate("eng-structures")  # ValidationResult (typed)
    paper.to_draft("eng-structures", "draft.docx")   # or fmt="tex"/"pdf"

The published two-column typeset is produced by the publisher, never the
author; epy_papers produces the *submission manuscript* (single column,
double-spaced, line-numbered, the journal's citation style and page size),
driven by a per-journal **profile** in ``_config/_data/journals.json``. The
author's source is one Markdown file whose YAML front matter models bilingual
``title`` / ``abstract`` / ``keywords``, ``highlights`` and ``declarations``
(see :mod:`epy_papers._core._authoring` and ``REQUIREMENTS.md``).

This module is a WRAP: it re-exports the catalogue and :class:`Paper` from
``_core`` and defines nothing itself.
"""

from __future__ import annotations

# The ICU pin lived here, in epy_reports and in epy_slides, and this
# copy's docstring said outright that it mirrored the first. It is
# epy_export's now. The call stays explicit and stays HERE, ahead of
# anything that touches Qt: the ordering is the whole point, and a
# side effect fired from an unrelated import is how it stops being
# reviewable.
from epy_export import pin_system_icu

pin_system_icu()

from epy_papers._core._authoring import (  # noqa: E402
    Author,
    Bilingual,
    BilingualList,
    Manuscript,
)
from epy_papers._core._catalog import (  # noqa: E402
    JournalProfile,
    add_journal,
    available_journals,
    journal_profile,
    load_journals,
    load_user_journals,
    remove_user_journal,
    user_journals_path,
)
from epy_papers._core._paper import Paper  # noqa: E402
from epy_papers._core._validation import (  # noqa: E402
    Severity,
    ValidationResult,
    Warning,
)
from epy_papers._core.renderer import PandocMissingError  # noqa: E402

__version__ = "0.5.0"

__all__ = [
    "Paper",
    "JournalProfile",
    "Manuscript",
    "Author",
    "Bilingual",
    "BilingualList",
    "ValidationResult",
    "Warning",
    "Severity",
    "PandocMissingError",
    "available_journals",
    "journal_profile",
    "load_journals",
    "load_user_journals",
    "user_journals_path",
    "add_journal",
    "remove_user_journal",
]
