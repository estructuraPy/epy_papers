"""Test the Spanish entries required for the UI no longer fall back.

A missing or self-mapping translation is silent: ``tr()`` falls back to the
English key, so a Spanish reader sees English in that menu and nothing
reports it.
"""

from epy_papers._core import _i18n

# Keys added by the Spanish UI sweep; all are English-only source strings.
_SPANISH_SWEEP_KEYS = (
    "Design block…",
    "Browse themes…",
    "Add Journal...",
    "Disclosure",
    "Install LaTeX for PDF export",
    "Unsaved changes",
    "An export is already running.",
    "TinyTeX install failed",
    "Discard unsaved changes and reload from disk?",
    "Export HTML failed",
    "Design block",
    "Choose a design block:",
    "Type paper Markdown here. Preview updates on the right.",
    "Themes",
    "Choose a theme:",
)


def test_spanish_sweep_keys_are_present_and_translated() -> None:
    """Every new key must exist in _ES and map to Spanish, not itself."""
    for key in _SPANISH_SWEEP_KEYS:
        assert key in _i18n._ES
        assert _i18n._ES[key] != key
