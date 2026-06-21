"""Tests for the structured validation layer."""

from __future__ import annotations

import epy_papers as ep
from epy_papers import Severity, ValidationResult


def _codes(result: ValidationResult) -> set[str]:
    """Return the set of warning codes in a result."""
    return {w.code for w in result}


def test_validate_returns_structured_result():
    """validate yields a typed ValidationResult, not strings."""
    paper = ep.Paper(
        "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n#x"
    )
    res = paper.validate("generic-manuscript")
    assert isinstance(res, ValidationResult)
    for w in res:
        assert hasattr(w, "code")
        assert w.severity in (
            Severity.ERROR,
            Severity.WARNING,
            Severity.INFO,
        )


def test_abstract_word_limit_per_language():
    """An over-limit abstract is flagged for the right language."""
    long_abstract = " ".join(["word"] * 400)
    src = (
        "---\n"
        "title: {en: T}\n"
        f"abstract: {{en: {long_abstract}}}\n"
        "keywords: {en: [k]}\n"
        "---\n# Body\n"
    )
    res = ep.Paper(src).validate("eng-structures")  # 250-word limit
    assert "abstract-too-long" in _codes(res)


def test_title_char_limit():
    """A title over the profile's char limit is flagged."""
    long_title = "T" * 120
    src = (
        f"---\ntitle: {{en: {long_title}}}\n"
        "abstract: {en: A}\nkeywords: {en: [k]}\n---\n# Body\n"
    )
    res = ep.Paper(src).validate("asce-jse")  # 100-char title limit
    assert "title-too-long" in _codes(res)


def test_keywords_over_max():
    """Too many keywords are flagged."""
    src = (
        "---\ntitle: {en: T}\nabstract: {en: A}\n"
        "keywords: {en: [a, b, c, d, e, f, g, h, i, j]}\n---\n# B\n"
    )
    res = ep.Paper(src).validate("eng-structures")  # max 7
    assert "keywords-too-many" in _codes(res)


def test_bilingual_required_flags_missing_language():
    """A bilingual venue flags a missing language variant."""
    src = (
        "---\ntitle: {en: Only English}\n"
        "abstract: {en: English only}\nkeywords: {en: [k]}\n---\n# B\n"
    )
    res = ep.Paper(src).validate("tec-marcha")  # bilingual-abstract
    codes = _codes(res)
    assert "abstract-bilingual" in codes
    assert "title-bilingual" in codes
    assert "keywords-bilingual" in codes


def test_highlights_required_and_char_limit():
    """Missing highlights and an over-long highlight are flagged."""
    src = (
        "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n# B"
    )
    res = ep.Paper(src).validate("eng-structures")  # highlights: true
    assert "highlights-missing" in _codes(res)

    long_hl = "H" * 120
    src2 = (
        "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n"
        f"highlights: [ok one, ok two, {long_hl}]\n---\n# B"
    )
    res2 = ep.Paper(src2).validate("eng-structures")
    assert "highlight-too-long" in _codes(res2)


def test_required_declaration_missing():
    """A required declaration that is absent is flagged."""
    src = (
        "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n"
        "highlights: [a, b, c]\n---\n# B"
    )
    res = ep.Paper(src).validate("eng-structures")
    # eng-structures requires data-availability, credit, competing-interests
    assert "declaration-missing" in _codes(res)


def test_blinding_flags_author_identity():
    """A double-blind venue flags authored author identity."""
    src = (
        "---\ntitle: {en: T, es: T2}\n"
        "abstract: {en: A, es: A2}\nkeywords: {en: [k], es: [k]}\n"
        "authors: [{name: Real Name}]\n---\n# B"
    )
    res = ep.Paper(src).validate("tec-marcha")  # double-blind
    assert "blinding-author-identity" in _codes(res)


def test_missing_title_is_error():
    """A missing title produces an error-severity finding."""
    src = "---\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n# B"
    res = ep.Paper(src).validate("generic-manuscript")
    assert "title-missing" in _codes(res)
    assert not res.ok


def test_messages_backcompat():
    """messages() returns plain strings for back-compat callers."""
    src = "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n#"
    res = ep.Paper(src).validate("eng-structures")
    msgs = res.messages()
    assert all(isinstance(m, str) for m in msgs)
