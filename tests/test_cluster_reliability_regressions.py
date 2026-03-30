"""Regressions for cross-case cluster contamination, TOA name noise, and known cite typos."""

from __future__ import annotations

import pytest

from src.utils.case_name_cleaner import clean_extracted_case_name
from src.utils.extraction_cleaner import normalize_citation_text
from src.utils.response_enrichment import (
    merge_clusters_by_shared_citation,
    split_clusters_cross_case_contamination,
)


def _cite(txt: str, name: str, year: str, start: int) -> dict:
    return {
        "citation": txt,
        "extracted_case_name": name,
        "extracted_date": year,
        "start_index": start,
    }


def test_split_clusters_cross_case_yates_terry():
    """State v. Yates (2007) must not stay merged with Terry v. Ohio (1968)."""
    mixed = {
        "cluster_id": "cluster_28",
        "cluster_case_name": "mixed",
        "citations": [
            _cite("State v. Yates, 161 Wash. 2d 714", "State v. Yates", "2007", 100),
            _cite("161 Wn.2d 714, 168 P.3d 359", "State v. Yates", "2007", 110),
            _cite("392 U.S. 1", "Terry v. Ohio", "1968", 120),
            _cite("Terry v. Ohio, 88 S. Ct. 186", "Terry v. Ohio", "1968", 130),
        ],
        "cluster_members": [],
        "cluster_size": 4,
    }
    mixed["cluster_members"] = [c["citation"] for c in mixed["citations"]]
    out = split_clusters_cross_case_contamination([mixed])
    assert len(out) == 2
    sizes = sorted(len(c["citations"]) for c in out)
    assert sizes == [2, 2]
    names = {frozenset(c.get("extracted_case_name") for c in cl["citations"]) for cl in out}
    assert any("State v. Yates" in ns and "Terry v. Ohio" not in ns for ns in names)
    assert any("Terry v. Ohio" in ns and "State v. Yates" not in ns for ns in names)


def test_split_clusters_single_case_unchanged():
    cl = {
        "cluster_id": "cluster_0",
        "citations": [
            _cite("386 U.S. 18", "Chapman v. California", "1967", 10),
            _cite("87 S. Ct. 824", "Chapman v. California", "1967", 20),
        ],
        "cluster_members": ["386 U.S. 18", "87 S. Ct. 824"],
        "cluster_size": 2,
    }
    out = split_clusters_cross_case_contamination([cl])
    assert len(out) == 1
    assert out[0]["cluster_id"] == "cluster_0"


def test_shared_citation_merge_blocked_disjoint_years():
    """Shared citation-key merge must not join different cases with disjoint years."""
    a = {
        "cluster_id": "a",
        "extracted_case_name": "State v. Yates",
        "extracted_date": "2007",
        "citations": [
            {"citation": "161 Wash. 2d 714", "extracted_case_name": "State v. Yates", "extracted_date": "2007"}
        ],
        "cluster_members": ["161 Wash. 2d 714"],
    }
    b = {
        "cluster_id": "b",
        "extracted_case_name": "Terry v. Ohio",
        "extracted_date": "1968",
        "citations": [
            {"citation": "392 U.S. 1", "extracted_case_name": "Terry v. Ohio", "extracted_date": "1968"},
            {"citation": "161 Wash. 2d 714", "extracted_case_name": "Terry v. Ohio", "extracted_date": "1968"},
        ],
        "cluster_members": ["392 U.S. 1", "161 Wash. 2d 714"],
    }
    out = merge_clusters_by_shared_citation([a, b])
    assert len(out) == 2


def test_clean_extracted_case_name_strips_toa_federal_cases():
    raw = "TABLE OF AUTHORITIES Federal Cases Chapman v. California"
    assert clean_extracted_case_name(raw) == "Chapman v. California"


def test_normalize_citation_text_chapman_us_page_typo():
    assert "386 U.S. 18" in normalize_citation_text("See Chapman, 386 U.S. 188 (1967).")
    assert "386 U.S. 188" not in normalize_citation_text("See Chapman, 386 U.S. 188 (1967).")
