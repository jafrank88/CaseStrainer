"""Unit tests for brief golden expectation matching (no PDF I/O)."""

from __future__ import annotations

import json
from pathlib import Path

from src.utils.brief_golden_expectations import verify_expectation

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "citation_display_shape.json"


def test_verify_citation_count_and_required_substrings():
    errs = verify_expectation(
        {
            "min_citations": 2,
            "citation_substrings_required": ["U.S."],
            "citation_substrings_forbidden": ["9999"],
        },
        text_length=1000,
        citations=[{"citation": "410 U.S. 113"}, {"citation": "505 U.S. 100"}],
        clusters=[{"citations": [{"citation": "410 U.S. 113"}]}],
    )
    assert errs == []


def test_verify_fails_missing_substring():
    errs = verify_expectation(
        {"citation_substrings_required": ["WL"]},
        text_length=5000,
        citations=[{"citation": "410 U.S. 113"}],
        clusters=[],
    )
    assert any("WL" in e for e in errs)


def test_verify_cluster_rule_case_name():
    clusters = [
        {
            "cluster_case_name": "Foo v. Bar",
            "citations": [{"citation": "593 U.S. 155", "extracted_case_name": "Foo v. Bar"}],
        }
    ]
    errs = verify_expectation(
        {
            "cluster_rules": [
                {"case_name_contains": "Foo", "any_citation_contains": ["593 U.S.", "155"]}
            ]
        },
        text_length=100,
        citations=[{"citation": "593 U.S. 155"}],
        clusters=clusters,
    )
    assert errs == []


def test_citation_field_rules_passes_with_fixture():
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    cit = data["sample_citation_verified_scotus"]
    rules = data["citation_field_rules_example"]
    errs = verify_expectation(
        {"citation_field_rules": rules},
        text_length=100,
        citations=[cit],
        clusters=[],
    )
    assert errs == []


def test_citation_field_rules_fails_wrong_year():
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    cit = dict(data["sample_citation_verified_scotus"])
    cit["canonical_year"] = "1900"
    errs = verify_expectation(
        {
            "citation_field_rules": [
                {
                    "citation_contains": "606 U.S. 831",
                    "canonical_year": "2024",
                }
            ]
        },
        text_length=100,
        citations=[cit],
        clusters=[],
    )
    assert errs and any("citation_field_rules" in e for e in errs)
