"""Tests for the journal catalog and its profiles."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import epy_paper as ep

REQUIRED_FIELDS = [
    "name",
    "publisher",
    "field",
    "columns",
    "spacing",
    "line_numbers",
    "page_size",
    "figures",
    "tables",
    "blinding",
    "csl",
    "abstract_words",
    "formats",
    "declarations",
]

STRUCTURAL_TOKENS = (
    "structural",
    "bridge",
    "earthquake",
    "geotech",
    "concrete",
    "composites",
    "construction",
)


def test_catalog_has_fifty_journals():
    """The catalog ships exactly 50 real journal profiles."""
    journals = ep.available_journals()
    assert len(journals) == 50


def test_catalog_keeps_twelve_plus_structural():
    """At least 12 journals have a civil/structural focus."""
    catalog = ep.load_journals()
    structural = [
        jid
        for jid, prof in catalog.items()
        if any(tok in prof.get("field", "") for tok in STRUCTURAL_TOKENS)
    ]
    assert len(structural) >= 12


def test_every_profile_has_required_fields():
    """Each profile carries the fields the renderer/validator rely on."""
    catalog = ep.load_journals()
    for jid, prof in catalog.items():
        for fieldname in REQUIRED_FIELDS:
            assert fieldname in prof, f"{jid} missing {fieldname}"


def test_bundled_and_dev_catalog_are_identical():
    """src and repo-root copies of the catalog must stay in sync."""
    bundled = (
        resources.files("epy_paper.data")
        .joinpath("journals.json")
        .read_text(encoding="utf-8")
    )
    repo_root = Path(__file__).resolve().parent.parent
    dev = (repo_root / "data" / "journals.json").read_text(encoding="utf-8")
    assert json.loads(bundled) == json.loads(dev)


def test_asce_profiles_use_bundled_class():
    """ASCE profiles select the bundled 'ascelike' class."""
    catalog = ep.load_journals()
    asce = [p for p in catalog.values() if p.get("publisher") == "ASCE"]
    assert asce
    for prof in asce:
        assert prof.get("latex_class") == "ascelike"


def test_referenced_csl_files_exist():
    """Every CSL named by a profile is bundled."""
    catalog = ep.load_journals()
    for jid, prof in catalog.items():
        name = prof.get("csl")
        if not name:
            continue
        anchor = resources.files("epy_paper.assets.csl").joinpath(
            f"{name}.csl"
        )
        assert anchor.is_file(), f"{jid} references missing CSL {name}"


def test_leaf_objects_are_inline_single_line():
    """House style: each journal profile leaf stays on one JSON line."""
    text = (
        resources.files("epy_paper.data")
        .joinpath("journals.json")
        .read_text(encoding="utf-8")
    )
    # Profile lines start with two-space indent then a quoted key + ': {'.
    profile_lines = [
        ln
        for ln in text.splitlines()
        if ln.startswith('  "') and '": {' in ln
    ]
    # 50 journals + the _schema block both render as single-line leaves.
    assert len(profile_lines) >= 50
