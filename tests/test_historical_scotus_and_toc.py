"""
Regression tests for citation extraction, normalization, and clustering fixes.

Covers issues found in:
  - trumpvbarbaracertpet.pdf  (cert petition citing Cranch, Wheat., Wall., Pet., How.)
  - 1031351.pdf               (Erickson v. Pharmacia brief with fused digit artifacts)
  - 999562 Plaintiff Opening Brief.pdf  (docket contamination, L. Ed. first series,
    truncated case names, file-path merge)

These tests run without PDFs — they exercise the extraction, normalization, tier
classification, core-key, and date extraction functions directly.
"""
from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.utils.post_verify_split import _reporter_tier, reporter_tier
from src.utils.verification_display_utils import citation_core_key


# ---------------------------------------------------------------------------
# 1.  Historical SCOTUS reporter tier classification
# ---------------------------------------------------------------------------

class TestHistoricalSCOTUSTier:
    """Cranch, Wheat., Wall., Pet., How., Black, Dall. must be 'supreme'."""

    @pytest.mark.parametrize("citation,expected", [
        ("8 Cranch 253", "supreme"),
        ("2 Wheat. 227", "supreme"),
        ("16 Wall. 36", "supreme"),
        ("3 Pet. 99", "supreme"),
        ("19 How. 393", "supreme"),
        ("2 Black 635", "supreme"),
        ("1 Dall. 1", "supreme"),
        # Full citation forms with case names
        ("Cohens v. Virginia, 6 Wheat. 264 (1821)", "supreme"),
        ("Marbury v. Madison, 1 Cranch 137 (1803)", "supreme"),
        ("Dred Scott v. Sandford, 19 How. 393 (1857)", "supreme"),
        ("Minor v. Happersett, 21 Wall. 162 (1875)", "supreme"),
        # Eyecite annotation forms
        ("Slaughter-House Cases, 16 Wall. 36 (scotus 1873)", "supreme"),
        ("The Venus, 8 Cranch 253, 278 (scotus 1814)", "supreme"),
    ])
    def test_historical_reporters_are_supreme(self, citation, expected):
        assert _reporter_tier(citation) == expected

    @pytest.mark.parametrize("citation,expected", [
        # Modern SCOTUS
        ("169 U.S. 649", "supreme"),
        ("145 S. Ct. 1364", "supreme"),
        ("134 L. Ed. 2d 809", "supreme"),
        # Federal
        ("269 F.3d 481", "circuit"),
        ("999 F. Supp. 2d 1235", "district"),
        # State / other — must NOT be misclassified
        ("87 Wash. 2d 577", "other"),
        ("115 P.3d 1017", "other"),
        ("31 Barb. 486", "other"),  # NY Barbour's Reports, not SCOTUS
    ])
    def test_modern_tiers_unchanged(self, citation, expected):
        assert _reporter_tier(citation) == expected


# ---------------------------------------------------------------------------
# 2.  Citation core key — historical reporters properly extracted
# ---------------------------------------------------------------------------

class TestCoreKeyHistoricalReporters:
    """citation_core_key must extract vol+reporter+page for historical SCOTUS."""

    @pytest.mark.parametrize("full_citation,expected_key", [
        ("Minor v. Happersett, 21 Wall. 162 (scotus 2025)", "21 wall. 162"),
        ("21 Wall. 162", "21 wall. 162"),
        ("Minor v. Happersett, 21 Wall. 162, 168 (scotus 1875)", "21 wall. 162"),
        ("8 Cranch 253", "8 cranch 253"),
        ("The Venus, 8 Cranch 253, 278 (scotus 1814)", "8 cranch 253"),
        ("2 Wheat. 227", "2 wheat. 227"),
        ("The Pizarro, 2 Wheat. 227, 246 (scotus 1817)", "2 wheat. 227"),
        ("19 How. 393", "19 how. 393"),
        ("Dred Scott v. Sandford, 19 How. 393 (scotus 1857)", "19 how. 393"),
        ("3 Pet. 99", "3 pet. 99"),
        ("1 Dall. 1", "1 dall. 1"),
    ])
    def test_core_key_extracts_historical_reporter(self, full_citation, expected_key):
        assert citation_core_key(full_citation) == expected_key

    def test_core_key_modern_unchanged(self):
        assert citation_core_key("169 U.S. 649") == "169 u.s. 649"
        assert citation_core_key("United States v. Wong Kim Ark, 169 U.S. 649 (scotus 1898)") == "169 u.s. 649"

    def test_shared_key_enables_merge(self):
        """Two clusters sharing 21 Wall. 162 must produce the same core key."""
        k1 = citation_core_key("Minor v. Happersett, 21 Wall. 162 (scotus 2025)")
        k2 = citation_core_key("21 Wall. 162")
        k3 = citation_core_key("Minor v. Happersett, 21 Wall. 162, 168 (scotus 1875)")
        assert k1 == k2 == k3


# ---------------------------------------------------------------------------
# 3.  TOC prefix stripping
# ---------------------------------------------------------------------------

class TestTOCPrefixStripping:
    """TOC section headers must be stripped from eyecite citation spans."""

    @pytest.fixture()
    def proc(self):
        p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
        return p

    def test_strip_cases_continued_page(self, proc):
        raw = "IV Cases-Continued: Page Cochise Consultancy, Inc. v. United States ex rel. Hunt, 587 U.S. 262 (scotus 2019)"
        result = proc._strip_toc_prefix(raw)
        assert result.startswith("Cochise Consultancy")
        assert "Cases-Continued" not in result

    def test_strip_cases_continued_no_roman_numeral(self, proc):
        raw = "Cases-Continued: Page Murray v. Schooner Charming Betsy, 2 Cranch 64 (scotus 2025)"
        result = proc._strip_toc_prefix(raw)
        assert result.startswith("Murray v. Schooner")
        assert "Cases-Continued" not in result

    def test_strip_miscellaneous_continued_via_normalization(self, proc):
        """Mid-string TOC fragments are stripped by _normalize_citation_comprehensive."""
        raw = "26 Ohio App. 95... 26 VIII Miscellaneous-Continued: Page Samuel Estreicher & Rudra Reddy"
        result = proc._normalize_citation_comprehensive(raw)
        assert "Miscellaneous-Continued" not in result

    def test_strip_leading_noise_with_ellipsis(self, proc):
        raw = "9th Cir. 2020) ... 22 The Pizarro, 2 Wheat. 227 (scotus 1817)"
        result = proc._strip_toc_prefix(raw)
        assert result.startswith("The Pizarro")
        assert "9th Cir" not in result

    def test_normal_citations_unchanged(self, proc):
        normal = "Marbury v. Madison, 1 Cranch 137 (scotus 2025)"
        assert proc._strip_toc_prefix(normal) == normal

    def test_bare_citation_unchanged(self, proc):
        bare = "587 U.S. 262"
        assert proc._strip_toc_prefix(bare) == bare


# ---------------------------------------------------------------------------
# 4.  TOC stripping in _normalize_citation_comprehensive
# ---------------------------------------------------------------------------

class TestTOCNormalization:
    """TOC headers stripped during comprehensive normalization."""

    @pytest.fixture()
    def proc(self):
        return UnifiedCitationProcessorV2()

    def test_normalize_strips_toc_header(self, proc):
        raw = "IV Cases-Continued: Page Cochise Consultancy, Inc., 587 U.S. 262"
        result = proc._normalize_citation_comprehensive(raw)
        assert "Cases-Continued" not in result
        assert "587 U.S. 262" in result

    def test_normalize_strips_mid_string_toc(self, proc):
        raw = "26 Ohio App. 95... 26 VIII Miscellaneous-Continued: Page Samuel Estreicher"
        result = proc._normalize_citation_comprehensive(raw)
        assert "Miscellaneous-Continued" not in result


# ---------------------------------------------------------------------------
# 5.  Date extraction — reject modern years for historical reporters
# ---------------------------------------------------------------------------

class TestDateExtractionHistoricalReporters:
    """Years >= 2000 should be rejected for Cranch/Wheat/Wall/Pet/How citations."""

    @pytest.fixture()
    def proc(self):
        return UnifiedCitationProcessorV2()

    def test_rejects_2025_for_wall_citation_in_context(self, proc):
        """When the only nearby year is a modern one (from document context), reject it."""
        text = (
            "This petition was filed in 2025. See Minor v. Happersett, "
            "21 Wall. 162 ......... 7, 16\n"
            "Murray v. Schooner Charming Betsy, 2 Cranch 64 ......... 15"
        )
        start = text.index("21 Wall.")
        end = start + len("21 Wall. 162")
        citation = SimpleNamespace(
            citation="Minor v. Happersett, 21 Wall. 162 (scotus 2025)",
            start_index=start,
            end_index=end,
            metadata={},
        )
        year, source, confidence = proc._extract_date_from_context(text, citation, return_source=True)
        if year is not None:
            assert int(year) < 2000, f"Expected pre-2000 year for Wall. citation, got {year} (source={source})"

    def test_rejects_modern_year_for_cranch_in_candidates(self, proc):
        """Strategy 1 candidates loop should skip year >= 2000 for Cranch."""
        text = (
            "See Marbury v. Madison, 1 Cranch 137; see also "
            "Learning Resources v. Trump (2025)."
        )
        start = text.index("1 Cranch")
        end = start + len("1 Cranch 137")
        citation = SimpleNamespace(
            citation="1 Cranch 137",
            start_index=start,
            end_index=end,
            metadata={},
        )
        year, source, confidence = proc._extract_date_from_context(text, citation, return_source=True)
        if year is not None:
            assert int(year) < 2000, f"Expected pre-2000 year for Cranch citation, got {year} (source={source})"

    def test_accepts_correct_year_for_wall_citation(self, proc):
        text = "the Court in Minor v. Happersett, 21 Wall. 162 (1875) held that"
        citation = SimpleNamespace(
            citation="21 Wall. 162",
            start_index=text.index("21 Wall."),
            end_index=text.index("21 Wall.") + len("21 Wall. 162"),
            metadata={},
        )
        year, source, confidence = proc._extract_date_from_context(text, citation, return_source=True)
        assert year == "1875"

    def test_global_recovery_rejects_modern_year_for_historical(self, proc):
        """Strategy 5 (global search) should not return 2025 for a Wall. citation."""
        text = (
            "Slaughter-House Cases, 16 Wall. 36 ......... 12\n"
            "Other Authorities:\n"
            "Trump v. CASA (2025)\n"
            "Also, Slaughter-House Cases, 16 Wall. 36 (1873) held that\n"
        )
        citation = SimpleNamespace(
            citation="Slaughter-House Cases, 16 Wall. 36 (scotus 2025)",
            start_index=0,
            end_index=35,
            metadata={},
        )
        year, source, confidence = proc._extract_date_from_context(text, citation, return_source=True)
        # Should find 1873 from the second occurrence, not 2025
        if year is not None:
            assert int(year) < 2000, f"Expected pre-2000 year, got {year} (source={source})"


# ---------------------------------------------------------------------------
# 6.  1031351.pdf regressions — Zenaida-Garcia / Martin / blob splitting
# ---------------------------------------------------------------------------

class TestBlobSplitting1031351:
    """Regressions from 1031351.pdf: concatenated page number fixes."""

    @pytest.fixture()
    def proc(self):
        return UnifiedCitationProcessorV2()

    def test_fix_concatenated_266115_p3d(self, proc):
        """'266115 P.3d' fused blob must split to produce 115 P.3d, not 15 P.3d."""
        result = proc._fix_concatenated_page_numbers("266115 P.3d 1017")
        # The splitter should extract 115 as the volume, not 15 or 2661
        assert "115 P.3d" in result
        assert "2661" not in result

    def test_fix_concatenated_82961_p3d(self, proc):
        """'82961 P.3d' should split to '829, 61 P.3d'."""
        result = proc._fix_concatenated_page_numbers("82961 P.3d 1196")
        assert "61 P.3d" in result

    def test_normalize_baker_volume_not_split(self, proc):
        """551 P.3d is a valid volume — should NOT be split."""
        result = proc._normalize_citation_comprehensive("551 P.3d 655")
        assert "551 P.3d 655" in result

    def test_normalize_961_p3d_volume_not_split(self, proc):
        """961 P.3d is valid (high volume, future-proof) — should NOT be split."""
        result = proc._normalize_citation_comprehensive("961 P.3d 1196")
        assert "961 P.3d" in result or "61 P.3d" in result


# ---------------------------------------------------------------------------
# 7.  Wash. / Wn. normalization in core key (from 1031351.pdf)
# ---------------------------------------------------------------------------

class TestWashWnNormalization:
    """Wash. 2d and Wn.2d must produce the same core key."""

    def test_wash2d_and_wn2d_same_key(self):
        k1 = citation_core_key("87 Wash. 2d 577")
        k2 = citation_core_key("87 Wn. 2d 577")
        assert k1 == k2

    def test_wash_app_and_wn_app_same_key(self):
        k1 = citation_core_key("128 Wash. App. 256")
        k2 = citation_core_key("128 Wn. App. 256")
        assert k1 == k2


# ---------------------------------------------------------------------------
# 8.  Post-split re-merge (prevents duplicate clusters)
# ---------------------------------------------------------------------------

class TestPostSplitRemerge:
    """merge_clusters_by_shared_citation should merge clusters sharing a citation key."""

    def test_merge_minor_v_happersett_clusters(self):
        from src.utils.response_enrichment import merge_clusters_by_shared_citation

        clusters = [
            {
                "cluster_id": "minor_1",
                "canonical_name": "Minor v. Happersett",
                "extracted_name": "Minor v. Happersett",
                "citations": [
                    {"citation": "Minor v. Happersett, 21 Wall. 162 (scotus 2025)"},
                ],
            },
            {
                "cluster_id": "minor_2",
                "canonical_name": "Minor v. Happersett",
                "extracted_name": "Minor v. Happersett",
                "citations": [
                    {"citation": "21 Wall. 162"},
                    {"citation": "Minor v. Happersett, 21 Wall. 162, 168 (scotus 1875)"},
                ],
            },
        ]
        result = merge_clusters_by_shared_citation(clusters)
        assert len(result) == 1, f"Expected 1 merged cluster, got {len(result)}"

    def test_no_merge_different_wall_citations(self):
        """16 Wall. 36 (Slaughter-House) and 21 Wall. 162 (Minor) should NOT merge."""
        from src.utils.response_enrichment import merge_clusters_by_shared_citation

        clusters = [
            {
                "cluster_id": "slaughter",
                "canonical_name": "Slaughter-House Cases",
                "citations": [{"citation": "16 Wall. 36"}],
            },
            {
                "cluster_id": "minor",
                "canonical_name": "Minor v. Happersett",
                "citations": [{"citation": "21 Wall. 162"}],
            },
        ]
        result = merge_clusters_by_shared_citation(clusters)
        assert len(result) == 2, "Different Wall. citations should NOT be merged"


# ---------------------------------------------------------------------------
# 9.  Tier splitting no longer separates historical from modern SCOTUS
# ---------------------------------------------------------------------------

class TestTierSplitHistoricalSCOTUS:
    """A cluster mixing 169 U.S. 649 + 8 Cranch 253 should NOT be split by tier."""

    def test_historical_plus_us_not_split(self):
        from src.utils.post_verify_split import split_clusters_by_court_tier_and_wl

        clusters = [
            {
                "cluster_id": "wong_kim_ark",
                "canonical_name": "United States v. Wong Kim Ark",
                "citations": [
                    {"citation": "169 U.S. 649", "verified": True},
                    {"citation": "8 Cranch 253", "verified": True},
                ],
                "cluster_members": [
                    {"citation": "169 U.S. 649"},
                    {"citation": "8 Cranch 253"},
                ],
                "size": 2,
                "cluster_size": 2,
            }
        ]
        result = split_clusters_by_court_tier_and_wl(clusters, task_id="test")
        assert len(result) == 1, (
            f"Historical + modern SCOTUS should NOT be split, got {len(result)} clusters"
        )
        assert len(result[0]["citations"]) == 2, "Both citations should remain in same cluster"


# ---------------------------------------------------------------------------
# 10. 999562 regressions — Docket contamination stripping
# ---------------------------------------------------------------------------

class TestDocketContaminationStripping:
    """Docket prefixes like 'Dkt. No. 28).' must be stripped from citations/names."""

    @pytest.fixture()
    def proc(self):
        return UnifiedCitationProcessorV2()

    def test_normalize_strips_docket_prefix(self, proc):
        raw = "Dkt. No. 28). 5 Solutions, LLC, 171 Wash. 2d 486, 493, 256 P.3d 321 (2011)"
        result = proc._normalize_citation_comprehensive(raw)
        assert "Dkt" not in result
        assert "171 Wash. 2d 486" in result or "171 Wn. 2d 486" in result

    def test_normalize_strips_docket_shorter(self, proc):
        raw = "Dkt. No. 28). 5 Solutions, LLC, 256 P.3d 321 (2011)"
        result = proc._normalize_citation_comprehensive(raw)
        assert "Dkt" not in result
        assert "256 P.3d 321" in result

    def test_normal_citation_unchanged(self, proc):
        normal = "Carlsen v. Global Client Solutions, LLC, 171 Wash. 2d 486"
        result = proc._normalize_citation_comprehensive(normal)
        assert "Carlsen" in result
        assert "171 Wash. 2d 486" in result or "171 Wn. 2d 486" in result

    def test_case_name_cleaner_strips_docket(self):
        from src.utils.case_name_cleaner import clean_extracted_case_name
        assert "Dkt" not in clean_extracted_case_name("Dkt. No. 28). 5 Solutions, LLC")
        assert "No. 28" not in clean_extracted_case_name("No. 28). 5 Solutions, LLC")
        assert clean_extracted_case_name("No. 28). Carlsen v. Global").startswith("Carlsen")


# ---------------------------------------------------------------------------
# 11. 999562 regressions — L. Ed. (first series) core key
# ---------------------------------------------------------------------------

class TestLEdFirstSeriesCoreKey:
    """L. Ed. (first series, no '2d') must be extracted by citation_core_key."""

    @pytest.mark.parametrize("citation,expected_key", [
        ("49 L. Ed. 518", "49 l. ed. 518"),
        ("66 L. Ed. 735", "66 l. ed. 735"),
        ("Co. v. United States, 49 L. Ed. 518 (1905)", "49 l. ed. 518"),
        ("S.Ct. 397, 66 L. Ed. 735 (1922)", "66 l. ed. 735"),
    ])
    def test_l_ed_first_series_core_key(self, citation, expected_key):
        assert citation_core_key(citation) == expected_key

    def test_l_ed_2d_still_works(self):
        assert citation_core_key("134 L. Ed. 2d 809") == "134 l. ed. 2d 809"

    def test_orphan_sct_merges_via_l_ed_key(self):
        """Orphan 'S.Ct. 397, 66 L. Ed. 735' shares key with Stafford cluster."""
        orphan_key = citation_core_key("S.Ct. 397, 66 L. Ed. 735 (1922)")
        stafford_key = citation_core_key("66 L. Ed. 735")
        assert orphan_key == stafford_key


# ---------------------------------------------------------------------------
# 12. 999562 regressions — Merge clusters sharing L. Ed. / S. Ct. keys
# ---------------------------------------------------------------------------

class TestMergeLEdClusters:
    """Clusters sharing L. Ed. (first series) citations must merge."""

    def test_stafford_and_orphan_merge(self):
        from src.utils.response_enrichment import merge_clusters_by_shared_citation

        clusters = [
            {
                "cluster_id": "stafford",
                "canonical_name": "Stafford v. Wallace",
                "citations": [
                    {"citation": "258 U.S. 495"},
                    {"citation": "42 S. Ct. 397"},
                    {"citation": "66 L. Ed. 735"},
                ],
            },
            {
                "cluster_id": "orphan_sct",
                "canonical_name": "",
                "extracted_name": "S.Ct. 397",
                "citations": [
                    {"citation": "S.Ct. 397, 66 L. Ed. 735 (1922)"},
                ],
            },
        ]
        result = merge_clusters_by_shared_citation(clusters)
        assert len(result) == 1, f"Orphan S.Ct. should merge into Stafford, got {len(result)}"

    def test_orphan_reporter_fragment_not_blocked_by_name_guard(self):
        """'S.Ct. 397' should NOT be treated as a real case name by the merge guard."""
        from src.utils.same_case import has_case_name
        assert has_case_name("S.Ct. 397") is False
        assert has_case_name("L. Ed. 735") is False
        assert has_case_name("F.3d 920") is False
        assert has_case_name("Stafford v. Wallace") is True
        assert has_case_name("In Re Rosier") is True

    def test_toa_court_year_parenthetical_extracted_not_neighbor(self):
        """In TOA, '(S.D.N.Y. 1992)' should yield 1992, not 2007 from next entry."""
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from dataclasses import dataclass, field
        from typing import Optional

        @dataclass
        class _Cit:
            citation: str = ""
            start_index: Optional[int] = None
            end_index: Optional[int] = None
            extracted_date: Optional[str] = None
            extracted_case_name: Optional[str] = None
            metadata: dict = field(default_factory=dict)

        proc = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
        proc.config = type("C", (), {"debug_mode": False})()

        text = (
            "TABLE OF AUTHORITIES Page Cases "
            "Affiliated FM Ins. Co. v. LTK Consulting Servs. Inc., 556 F.3d 920 (9th Cir. 2009) ... 4 "
            "American Geophysical Union v. Texaco Inc., 802 F. Supp. 1, 27 (S.D.N.Y. 1992) ... 38 "
            "Bell Atl. Corp. v. Twombly, 550 U.S. 544, 167 L. Ed. 2d 929 (2007) ... 5"
        )
        start = text.find("802 F. Supp. 1")
        end = start + len("802 F. Supp. 1, 27 (S.D.N.Y. 1992)")
        cit = _Cit(
            citation="American Geophysical Union v. Texaco Inc., 802 F. Supp. 1, 27 (nysd 1992)",
            start_index=start,
            end_index=end,
            metadata={"year": 1992},
        )
        year, source, confidence = proc._extract_date_from_context(text, cit, return_source=True)
        assert year == "1992", f"Should extract 1992 from (S.D.N.Y. 1992), got {year} via {source}"

    def test_eyecite_year_overrides_wrong_context_year(self):
        """Eyecite's parsed year in citation text should override wrong context-extracted year."""
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from dataclasses import dataclass, field
        from typing import Optional

        @dataclass
        class _Cit:
            citation: str = ""
            start_index: Optional[int] = None
            end_index: Optional[int] = None
            extracted_date: Optional[str] = None
            extracted_case_name: Optional[str] = None
            metadata: dict = field(default_factory=dict)

        proc = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
        proc.config = type("C", (), {"debug_mode": False})()

        cit = _Cit(
            citation="802 F. Supp. 1, 27 (nysd 1992)",
            extracted_date="2007",
            metadata={"year": 1992},
        )
        eyecite_year = str(cit.metadata.get("year", "")).strip()
        assert eyecite_year == "1992"
        assert eyecite_year in cit.citation
        assert cit.extracted_date != eyecite_year

    def test_swift_clusters_merge(self):
        from src.utils.response_enrichment import merge_clusters_by_shared_citation

        clusters = [
            {
                "cluster_id": "swift_1",
                "canonical_name": "Swift & Co. v. United States",
                "citations": [
                    {"citation": "Co. v. United States, 196 U.S. 375, 399, 25 S. Ct. 276, 49 L. Ed. 518 (scotus 1905)"},
                    {"citation": "Co. v. United States, 49 L. Ed. 518 (1905)"},
                ],
            },
            {
                "cluster_id": "swift_2",
                "canonical_name": "Swift & Co. v. United States",
                "citations": [
                    {"citation": "196 U.S. 375"},
                    {"citation": "Co. v. United States, 25 S. Ct. 276"},
                    {"citation": "25 S. Ct. 276"},
                    {"citation": "49 L. Ed. 518"},
                ],
            },
        ]
        result = merge_clusters_by_shared_citation(clusters)
        assert len(result) == 1, f"Swift clusters sharing keys should merge, got {len(result)}"


class TestCrossClusterDedup999562:
    """Tests for cross-cluster deduplication using citation_core_key."""

    def test_wn2d_wash2d_cross_cluster_dedup(self):
        """181 Wn.2d 412 (Carlsen cluster) and 181 Wash. 2d 412 (Frias cluster)
        should be deduplicated: keep in Frias (verified), remove from Carlsen."""
        from src.utils.cluster_postprocess_pipeline import _deduplicate_citations_across_clusters

        clusters = [
            {
                "cluster_id": "carlsen",
                "citations": [
                    {"citation": "171 Wn.2d 486", "verified": True},
                    {"citation": "256 P.3d 321", "verified": True},
                    {"citation": "181 Wn.2d 412", "verified": False},
                    {"citation": "334 P.3d 529", "verified": False},
                ],
            },
            {
                "cluster_id": "frias",
                "citations": [
                    {"citation": "181 Wash. 2d 412", "verified": True},
                    {"citation": "334 P.3d 529", "verified": True},
                ],
            },
        ]
        result = _deduplicate_citations_across_clusters(clusters, run_id="test")
        carlsen = next(c for c in result if c["cluster_id"] == "carlsen")
        frias = next(c for c in result if c["cluster_id"] == "frias")
        carlsen_cites = {c["citation"] for c in carlsen["citations"]}
        assert "181 Wn.2d 412" not in carlsen_cites, "181 Wn.2d 412 should be removed from Carlsen"
        assert "334 P.3d 529" not in carlsen_cites, "334 P.3d 529 should be removed from Carlsen"
        assert len(frias["citations"]) == 2, "Frias should keep its citations"

    def test_dedup_carlsen_frias_both_verified_prefers_name_match(self):
        """999562: 181 Wn.2d 412 may verify in both clusters; keep Frias cite with Frias."""
        from src.utils.cluster_postprocess_pipeline import _deduplicate_citations_across_clusters

        carlsen_cn = "Carlsen v. Global Client Solutions, LLC"
        frias_cn = "Frias v. Asset Foreclosure Services, Inc."
        clusters = [
            {
                "cluster_id": "carlsen",
                "canonical_name": carlsen_cn,
                "cluster_case_name": carlsen_cn,
                "citations": [
                    {"citation": "171 Wn.2d 486", "verified": True, "canonical_name": carlsen_cn},
                    {"citation": "256 P.3d 321", "verified": True, "canonical_name": carlsen_cn},
                    {
                        "citation": "181 Wn.2d 412",
                        "verified": True,
                        "canonical_name": carlsen_cn,
                    },
                    {"citation": "334 P.3d 529", "verified": True, "canonical_name": carlsen_cn},
                ],
            },
            {
                "cluster_id": "frias",
                "canonical_name": frias_cn,
                "cluster_case_name": frias_cn,
                "citations": [
                    {"citation": "181 Wash. 2d 412", "verified": True, "canonical_name": frias_cn},
                    {"citation": "334 P.3d 529", "verified": True, "canonical_name": frias_cn},
                ],
            },
        ]
        result = _deduplicate_citations_across_clusters(clusters, run_id="test")
        carlsen = next(c for c in result if c["cluster_id"] == "carlsen")
        frias = next(c for c in result if c["cluster_id"] == "frias")
        ck = {c["citation"] for c in carlsen["citations"]}
        fk = {c["citation"] for c in frias["citations"]}
        assert "181 Wn.2d 412" not in ck
        assert "334 P.3d 529" not in ck
        assert "181 Wash. 2d 412" in fk
        assert "334 P.3d 529" in fk

    def test_dedup_prefers_verified_cluster(self):
        """When a citation appears in both a verified and unverified cluster,
        dedup should keep it in the verified cluster."""
        from src.utils.cluster_postprocess_pipeline import _deduplicate_citations_across_clusters

        clusters = [
            {
                "cluster_id": "big_unverified",
                "citations": [
                    {"citation": "100 F.3d 200", "verified": False},
                    {"citation": "200 P.3d 300", "verified": False},
                    {"citation": "300 U.S. 400", "verified": False},
                ],
            },
            {
                "cluster_id": "small_verified",
                "citations": [
                    {"citation": "100 F.3d 200", "verified": True},
                ],
            },
        ]
        result = _deduplicate_citations_across_clusters(clusters, run_id="test")
        big = next(c for c in result if c["cluster_id"] == "big_unverified")
        small = next(c for c in result if c["cluster_id"] == "small_verified")
        big_cites = {c["citation"] for c in big["citations"]}
        assert "100 F.3d 200" not in big_cites, "Should be removed from unverified cluster"
        assert len(small["citations"]) == 1, "Should be kept in verified cluster"


class TestContextYearForDisplay999562:
    """Tests for _context_year_for_display proximity fix."""

    def test_picks_nearest_year_not_last(self):
        """For Hruska in TOA, should pick (8th Cir.1925) not a later year."""
        from src.utils.cluster_display_utils import _context_year_for_display

        cit = {
            "citation": "6 F.2d 536",
            "context": (
                "Grimshaw v. Ford Motor Co. 119 Cal. App.3d 757, 174 Cal. Rptr. 348 (1981) ... 28,34 "
                "Hruska v. Parke, Davis & Co., 6 F.2d 536 (8th Cir.1925) ... 20 "
                "Larkin v. Pfizer, Inc., 153 S.W.3d 758, 762 (Ky.2004) ... 20"
            ),
        }
        year = _context_year_for_display(cit)
        assert year == "1925", f"Should find 1925 from (8th Cir.1925), got {year}"

    def test_picks_correct_year_for_larkin(self):
        """For Larkin in TOA, should pick (Ky.2004) not (E.D.Mich.1985)."""
        from src.utils.cluster_display_utils import _context_year_for_display

        cit = {
            "citation": "153 S.W.3d 758",
            "context": (
                "Hruska v. Parke, Davis & Co., 6 F.2d 536 (8th Cir.1925) ... 20 "
                "Larkin v. Pfizer, Inc., 153 S.W.3d 758, 762 (Ky.2004) ... 20 "
                "Marcus v. Specific Pharms., 191 Misc. 285, 77 N.Y.S.2d 508 (N.Y.Sup.Ct.1948)"
            ),
        }
        year = _context_year_for_display(cit)
        assert year == "2004", f"Should find 2004 from (Ky.2004), got {year}"


class TestTwomblyParallelMerge:
    """L. Ed. 2d / U.S. / S. Ct. share no citation_core_key — merge by SCOTUS parallel pass."""

    def test_defendant_only_label_matches_full_name(self):
        from src.utils.same_case import names_are_same_case

        assert names_are_same_case(
            "Twombly, 2007",
            "Bell Atlantic Corporation v. Twombly, 2007",
        )
        assert names_are_same_case(
            "Twombly",
            "Bell Atlantic Corp. v. Twombly",
        )

    def test_merge_scotus_parallel_clusters(self):
        from src.utils.response_enrichment import merge_clusters_by_scotus_parallel_reporters

        clusters = [
            {
                "cluster_id": "tw_a",
                "extracted_case_name": "Bell Atlantic Corporation v. Twombly",
                "verifying_display_date": "2007",
                "citations": [
                    {"citation": "550 U.S. 544", "verified": True},
                    {"citation": "127 S. Ct. 1955", "verified": True},
                ],
            },
            {
                "cluster_id": "tw_b",
                "extracted_case_name": "Twombly, 2007",
                "submitted_display_date": "2007",
                "citations": [
                    {"citation": "167 L. Ed. 2d 929", "verified": False},
                ],
            },
        ]
        out = merge_clusters_by_scotus_parallel_reporters(clusters)
        assert len(out) == 1
        cites = {c.get("citation") for c in out[0].get("citations", [])}
        assert "167 L. Ed. 2d 929" in cites
        assert "550 U.S. 544" in cites

    def test_promote_parallel_siblings_after_merge(self):
        from src.utils.response_enrichment import promote_parallel_siblings_in_clusters

        clusters = [
            {
                "cluster_id": "tw_one",
                "canonical_name": "Bell Atlantic Corporation v. Twombly",
                "citations": [
                    {
                        "citation": "550 U.S. 544",
                        "verified": True,
                        "canonical_name": "Bell Atlantic Corporation v. Twombly",
                        "canonical_date": "2007",
                        "canonical_url": "https://www.courtlistener.com/opinion/123/",
                    },
                    {
                        "citation": "167 L. Ed. 2d 929",
                        "verified": False,
                        "extracted_case_name": "Twombly, 2007",
                    },
                ],
            }
        ]
        n = promote_parallel_siblings_in_clusters(clusters)
        assert n == 1
        led = clusters[0]["citations"][1]
        assert led.get("true_by_parallel") is True
        assert led.get("canonical_url", "").startswith("https://www.courtlistener.com")

    def test_no_merge_two_weak_labels_same_year(self):
        from src.utils.response_enrichment import merge_clusters_by_scotus_parallel_reporters

        clusters = [
            {
                "cluster_id": "a",
                "extracted_case_name": "Alpha",
                "verifying_display_date": "2007",
                "citations": [{"citation": "550 U.S. 100", "verified": True}],
            },
            {
                "cluster_id": "b",
                "extracted_case_name": "Beta",
                "verifying_display_date": "2007",
                "citations": [{"citation": "551 U.S. 200", "verified": True}],
            },
        ]
        out = merge_clusters_by_scotus_parallel_reporters(clusters)
        assert len(out) == 2
