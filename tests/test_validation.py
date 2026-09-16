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


def test_warning_str_is_bracketed_severity_plus_message():
    from epy_papers._core._validation import Severity, Warning

    w = Warning(code="x", severity=Severity.ERROR, message="Bad thing.")
    assert str(w) == "[error] Bad thing."


def test_result_bool_is_true_only_with_findings():
    from epy_papers._core._validation import ValidationResult

    empty = ValidationResult(journal_id="j", journal_name="J")
    assert bool(empty) is False
    empty.add("code", Severity.INFO, "msg")
    assert bool(empty) is True


def test_int_helper_falls_back_on_an_unparseable_value():
    """A malformed profile field (string junk instead of a number) must
    degrade to the default, not raise out of every validation call.
    """
    src = "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n#"
    profile = ep.JournalProfile(
        "junk-profile", {"name": "Junk Journal", "title_chars": "not-a-number"}
    )
    from epy_papers import Manuscript
    from epy_papers._core._validation import validate

    res = validate(Manuscript.from_source(src), profile, "junk-profile")
    # No crash, and no spurious "too long" finding from a limit of 0.
    assert "title-too-long" not in _codes(res)


def test_keywords_too_few_is_an_info_finding():
    from epy_papers import Manuscript
    from epy_papers._core._validation import validate

    src = (
        "---\ntitle: {en: T}\nabstract: {en: A}\n"
        "keywords: {en: [only-one]}\n---\n# B\n"
    )
    profile = ep.JournalProfile(
        "kw-min-test",
        {"name": "KW Journal", "keywords_min": 3, "keywords_max": 7},
    )
    res = validate(Manuscript.from_source(src), profile, "kw-min-test")
    assert "keywords-too-few" in _codes(res)
    for w in res:
        if w.code == "keywords-too-few":
            assert w.severity == Severity.INFO


def test_highlights_count_out_of_range_when_some_are_present():
    """One highlight against a 3-5 requirement is a COUNT finding, not
    the (already-covered) MISSING one -- the two must not collapse.
    """
    src = (
        "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n"
        "highlights: [Only one highlight here.]\n---\n# B"
    )
    res = ep.Paper(src).validate("eng-structures")  # wants 3-5
    codes = _codes(res)
    assert "highlights-count" in codes
    assert "highlights-missing" not in codes


def test_page_size_a4_forbidden_by_an_acs_journal():
    from epy_papers import Manuscript
    from epy_papers._core._validation import validate

    src = "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n#"
    profile = ep.JournalProfile(
        "acs-a4-test", {"name": "ACS Fake Journal", "page_size": "a4"}
    )
    res = validate(Manuscript.from_source(src), profile, "acs-a4-test")
    assert "page-size" in _codes(res)


def test_page_size_a4_allowed_by_a_non_acs_journal():
    """Counter-example: the same A4 page size is fine for a journal whose
    name does not contain 'ACS'.
    """
    from epy_papers import Manuscript
    from epy_papers._core._validation import validate

    src = "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n#"
    profile = ep.JournalProfile(
        "other-a4-test", {"name": "Some Other Journal", "page_size": "a4"}
    )
    res = validate(Manuscript.from_source(src), profile, "other-a4-test")
    assert "page-size" not in _codes(res)


def test_citation_style_flagged_when_profile_has_no_csl():
    from epy_papers import Manuscript
    from epy_papers._core._validation import validate

    src = "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n#"
    profile = ep.JournalProfile("no-csl-test", {"name": "No CSL Journal"})
    res = validate(Manuscript.from_source(src), profile, "no-csl-test")
    assert "citation-style" in _codes(res)


def test_citation_style_not_flagged_when_a_csl_is_declared():
    """CONTROL: every real bundled journal declares a CSL (verified by
    ``load_journals()`` having none without one), so this direction is
    otherwise never exercised.
    """
    res = ep.Paper(
        "---\ntitle: {en: T}\nabstract: {en: A}\nkeywords: {en: [k]}\n---\n#"
    ).validate("eng-structures")
    assert "citation-style" not in _codes(res)
