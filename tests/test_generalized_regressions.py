import pytest
from types import SimpleNamespace

try:
    from src.utils.response_enrichment import (
        apply_proprietary_display_fallback,
        deduplicate_clusters_for_response,
    )
except ModuleNotFoundError:
    apply_proprietary_display_fallback = None
    deduplicate_clusters_for_response = None
from src.utils.case_name_cleaner import clean_extracted_case_name
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.utils.cluster_display_utils import apply_display_fields_to_cluster, finalize_cluster_display_identity


def test_cluster_dedupe_uses_stable_citation_set_key():
    if deduplicate_clusters_for_response is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    clusters = [
        {
            "cluster_id": "a",
            "citations": [{"citation": "606 U.S. 831", "verified": True, "canonical_url": "https://example/1"}],
            "verifying_display_name": "Trump v. CASA, Inc.",
            "verifying_display_date": "2025",
        },
        {
            "cluster_id": "b",
            "citations": [{"citation": "606 U.S. 831", "verified": True, "canonical_url": "https://example/1"}],
            "verifying_display_name": "Trump v. CASA",
            "verifying_display_date": "2025",
        },
    ]

    out = deduplicate_clusters_for_response(clusters)
    assert len(out) == 1
    assert out[0]["cluster_id"] in {"a", "b"}


def test_unverified_wl_gets_proprietary_reason():
    if apply_proprietary_display_fallback is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    citations = [{"citation": "2020 WL 1061442", "verified": False, "canonical_url": None, "url": None}]
    apply_proprietary_display_fallback(citations)

    c = citations[0]
    assert c["verification_status"] == "proprietary_format"
    assert "Proprietary format" in c.get("error", "")
    assert c.get("verified") is False


def test_verified_wl_with_url_not_overridden():
    if apply_proprietary_display_fallback is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    citations = [{"citation": "2025 WL 1773631", "verified": True, "canonical_url": "https://example/wl", "url": "https://example/wl"}]
    apply_proprietary_display_fallback(citations)

    c = citations[0]
    assert c.get("verified") is True
    assert c.get("canonical_url") == "https://example/wl"


def test_possible_match_without_url_downgrades_to_unverified_for_wl():
    if apply_proprietary_display_fallback is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    citations = [
        {
            "citation": "2025 WL 1534852",
            "verified": False,
            "possible_match": True,
            "canonical_name": "AMBILA v. JOYCE",
            "canonical_date": "2025",
            "canonical_url": None,
            "url": None,
            "metadata": {"possible_match_name": "AMBILA v. JOYCE", "possible_match_date": "2025"},
        }
    ]
    apply_proprietary_display_fallback(citations)

    c = citations[0]
    assert c.get("possible_match") is False
    assert c.get("verification_status") == "proprietary_format"


def test_verified_wl_without_direct_url_becomes_verified_by_parallel():
    if apply_proprietary_display_fallback is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    citations = [
        {
            "citation": "2025 WL 1773631",
            "verified": True,
            "is_verified": True,
            "canonical_url": "https://www.courtlistener.com/opinion/10776816/trump-v-casa-inc/",
            "url": None,
            "metadata": {},
        }
    ]
    apply_proprietary_display_fallback(citations)
    c = citations[0]
    assert c.get("verified") is False
    assert c.get("is_verified") is False
    assert c.get("true_by_parallel") is True
    assert c.get("verification_status") == "verified_by_parallel_not_in_document"
    assert c.get("metadata", {}).get("parallel_not_in_document") is True


def test_cleaner_repairs_hawkinsex_rel_and_rapuanoet_al():
    """PDF word-join: Hawkinsex rel, Rapuanoet al (space between ex/et and rel/al)."""
    assert "ex rel" in clean_extracted_case_name("Hawkinsex rel. Hawkins v. Comm'r")
    assert "et al" in clean_extracted_case_name("Kristina Rapuanoet al. v. Trustees")


def test_cleaner_strips_docket_and_prose_prefix():
    """Docket and prose contamination before case names."""
    r = clean_extracted_case_name("Trump No. 24-1287 Learning Resources, Inc. v. Trump, 2025")
    assert r.startswith("Learning Resources")
    r2 = clean_extracted_case_name(
        "Generalis concurrently filing a petition for a writ of certiorari in Trump v. Washington, N/A"
    )
    assert "Trump v. Washington" in r2


def test_cleaner_repairs_garc_a_ayala_accent():
    """PDF accent corruption: Garc A-Ayala -> Garcia-Ayala."""
    r = clean_extracted_case_name("Zenaida Garc A-Ayala v. Lederle Parenterals")
    assert "Garcia-Ayala" in r


def test_cleaner_repairs_joined_legal_tokens():
    name = "Hawkinsexrel. Hawkins v. Comm'r of N. H., Rapuanoetal."
    cleaned = clean_extracted_case_name(name)
    assert "ex rel." in cleaned
    assert "et al." in cleaned


def test_truncated_corporate_name_repair_recovers_fuller_left_party():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    name = "Health Ctr., Inc. v. Rullan"
    text = "Rio Grande Community Health Center, Inc. v. Rullan, 397 F.3d 56 (1st Cir. 2005)"

    repaired = processor._repair_truncated_case_name(
        name=name,
        text=text,
        start_index=40,
        citation_text="397 F.3d 56",
        context_override=text,
    )
    assert repaired.startswith("Rio Grande Community Health Center, Inc. v. Rullan")


def test_truncated_corporate_name_extends_backwards_until_non_capitalized_non_stopword():
    """Amcast Corp v. Detrex: first party starts mid-name; extend backwards past 'quoting'."""
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    text = (
        "Haroco, Inc. v. Am. Nat'l Bank & Tr. Co., 38 F.3d 1429, 1439 (7th Cir. 1994) "
        "(quoting Amcast Indus. Corp v. Detrex Corp., 2 F.3d 746, 749 (7th Cir. 1993)"
    )
    start = text.find("Corp v. Detrex")
    repaired = processor._repair_truncated_case_name(
        name="Corp v. Detrex Corp.",
        text=text,
        start_index=start,
        citation_text="Corp v. Detrex Corp., 2 F.3d 746, 749 (ca7 1993)",
    )
    assert repaired.startswith("Amcast Indus. Corp")
    assert "Detrex" in repaired


def test_pdf_ocr_artifact_normalization():
    """King v. Ortiz: C\\', F.DNY, Friedman, Supp3d OCR corruptions are fixed."""
    from src.utils.text_normalizer import normalize_text

    backslash = chr(92)
    text = (
        "Defendant should produce any other relevant materials. See King v. Ortiz, 17 C"
        + backslash
        + "' 7507 (F.DNY May 2, 2019) 1-\"crdman v. CBS Interactive Inc., 342 F. Supp3d 515"
    )
    norm = normalize_text(text)
    assert "Cv. 7507" in norm
    assert "S.D.N.Y." in norm
    assert "Friedman" in norm
    assert "Supp. 3d" in norm


def test_scotus_courtlistener_minus_one_year_is_allowed():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    compare_year, source = processor._derive_compare_year(
        citation_text="578 U.S. 330",
        canonical_date="2015-12-31",
        extracted_date="2016",
        verification_source="courtlistener_api",
        in_toa_section=False,
    )
    assert compare_year == "2016"
    assert source == "scotus_cl_minus_one"


def test_non_scotus_courtlistener_minus_one_year_not_allowed():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    compare_year, source = processor._derive_compare_year(
        citation_text="397 F.3d 56",
        canonical_date="2004-12-01",
        extracted_date="2005",
        verification_source="courtlistener_api",
        in_toa_section=False,
    )
    assert compare_year == "2004"
    assert source == "canonical_date"


def test_year_diff_one_is_hard_mismatch_no_tolerance():
    """One-year tolerance removed: year_diff==1 must return hard_mismatch."""
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    result = processor._evaluate_year_alignment(
        citation_text="397 F.3d 56",
        extracted_date="2005",
        canonical_date="2004-12-01",
        verification_source="courtlistener_api",
        in_toa_section=False,
        allow_soft_mismatch=False,
    )
    assert result["hard_mismatch"] is True
    assert result["year_diff"] == 1


def test_scotus_sct_reporter_minus_one_year_is_allowed():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    compare_year, source = processor._derive_compare_year(
        citation_text="139 S. Ct. 1112",
        canonical_date="2018-10-11",
        extracted_date="2019",
        verification_source="courtlistener_api",
        in_toa_section=False,
    )
    assert compare_year == "2019"
    assert source == "scotus_cl_minus_one"


def test_citation_local_year_extraction_prefers_parenthetical_year():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    text = (
        "A. B. v. Hawaii State Dep't of Educ., 30 F.4th 828, 838 (9th Cir. 2022) "
        "(quoting Rodriguez v. Hayes, 591 F.3d 1105, 1118 (9th Cir. 2010) "
        "(abrogation on other grounds recognized by Rodriguez Diaz v. Garland, "
        "53 F.4th 1189 (9th Cir. 2022)))."
    )
    citation_text = "591 F.3d 1105"
    start = text.index(citation_text)
    end = start + len(citation_text)
    citation = SimpleNamespace(citation=citation_text, start_index=start, end_index=end, metadata={})

    extracted = processor._extract_date_from_context(text, citation, return_source=True)
    assert isinstance(extracted, tuple) and len(extracted) == 3
    year, source, confidence = extracted
    assert year == "2010"
    assert source == "citation_parenthetical"
    assert confidence == "high"


def test_extracted_date_provenance_is_written_for_unified_extraction():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    text = "Rodriguez v. Hayes, 591 F.3d 1105, 1118 (9th Cir. 2010)."
    citation_text = "591 F.3d 1105"
    start = text.index(citation_text)
    end = start + len(citation_text)
    citation = SimpleNamespace(
        citation=citation_text,
        start_index=start,
        end_index=end,
        extracted_date=None,
        metadata={},
    )

    extracted = processor._extract_date_from_context(text, citation, return_source=True)
    assert isinstance(extracted, tuple) and len(extracted) == 3
    year, source, confidence = extracted
    citation.extracted_date = year
    processor._set_extracted_date_provenance(citation, source, confidence)

    assert citation.extracted_date == "2010"
    assert citation.metadata.get("extracted_date_source") == "citation_parenthetical"
    assert citation.metadata.get("extracted_date_confidence") == "high"


def test_gate_reject_canonical_hidden_for_non_scotus_without_core_match():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    result = SimpleNamespace(raw_data={"citation_core_match": False})
    assert processor._should_expose_gate_reject_canonical("591 F.3d 1105", result) is False


def test_gate_reject_canonical_visible_for_non_scotus_with_core_match():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    result = SimpleNamespace(raw_data={"citation_core_match": True})
    assert processor._should_expose_gate_reject_canonical("591 F.3d 1105", result) is True


def test_gate_reject_canonical_visible_for_scotus_even_without_core_match():
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    result = SimpleNamespace(raw_data={"citation_core_match": False})
    assert processor._should_expose_gate_reject_canonical("606 U.S. 831", result) is True


def test_cluster_display_keeps_extracted_date_when_context_has_later_year():
    cluster = {
        "citations": [
            {
                "citation": "591 F.3d 1105",
                "extracted_case_name": "Rodriguez v. Hayes",
                "extracted_date": "2010",
                "context": (
                    "Rodriguez v. Hayes, 591 F.3d 1105, 1118 (9th Cir. 2010) "
                    "(abrogation on other grounds recognized by Rodriguez Diaz v. Garland, 53 F.4th 1189 (9th Cir. 2022))"
                ),
                "verified": False,
            }
        ]
    }
    apply_display_fields_to_cluster(cluster)
    assert cluster.get("submitted_display_date") == "2010"


def test_unverified_cluster_gets_google_search_fallback_url():
    cluster = {
        "citations": [
            {
                "citation": "2025 WL 1534852",
                "extracted_case_name": "Ambila v. Joyce",
                "extracted_date": "2025",
                "verified": False,
            }
        ]
    }
    finalize_cluster_display_identity(cluster)
    assert str(cluster.get("display_canonical_url") or "").startswith("https://www.google.com/search?")


def test_unverified_cluster_google_search_fallback_uses_citation_when_name_missing():
    cluster = {
        "citations": [
            {
                "citation": "2025 WL 1534852",
                "extracted_case_name": "N/A",
                "extracted_date": "2025",
                "verified": False,
            }
        ]
    }
    finalize_cluster_display_identity(cluster)
    url = str(cluster.get("display_canonical_url") or "")
    assert url.startswith("https://www.google.com/search?")
    assert "2025+WL+1534852" in url


def test_in_re_rosier_deduplicated_when_same_citation():
    """Clusters with same citation (one via citations, one via cluster_members only) should dedupe to one."""
    from src.utils.response_enrichment import deduplicate_clusters_for_response

    clusters = [
        {
            "cluster_id": "c1",
            "citations": [{"citation": "717 P.3d 1353", "verified": True}],
            "cluster_members": ["717 P.3d 1353"],
            "submitted_display_name": "In re Rosier",
            "submitted_display_date": "1986",
        },
        {
            "cluster_id": "c2",
            "citations": [],
            "cluster_members": ["717 P.3d 1353"],
            "submitted_display_name": "In re Rosier",
            "submitted_display_date": "1986",
        },
    ]
    deduped = deduplicate_clusters_for_response(clusters)
    assert len(deduped) == 1


def test_lloyds_pope_res_clusters_with_pope_res():
    """Lloyd's of London Pope Res., LP and Pope Res., LP should cluster together (same case)."""
    from src.unified_clustering_master_optimized import cluster_citations_minimal

    citations = [
        {
            "extracted_case_name": "Lloyd's of London Pope Res., LP v. Certain Underwriters at Lloyd's of London",
            "citation": "19 Wn. App. 2d 113",
            "verified": False,
        },
        {
            "extracted_case_name": "Pope Res., LP v. Certain Underwriters at Lloyd's of London",
            "citation": "494 P.3d 1076",
            "verified": False,
        },
    ]
    clusters = cluster_citations_minimal(citations)
    assert len(clusters) == 1
    assert len(clusters[0]["citations"]) == 2
    cites = {c["citation"] for c in clusters[0]["citations"]}
    assert "19 Wn. App. 2d 113" in cites
    assert "494 P.3d 1076" in cites


def test_buchanan_same_name_different_eras_not_clustered():
    """67 S.E.2d 289 (1951) and 431 S.E.2d 289 (1993) are different cases - should NOT cluster."""
    from src.unified_clustering_master_optimized import cluster_citations_minimal

    citations = [
        {"extracted_case_name": "Buchanan v. Doe", "citation": "67 S.E.2d 289", "verified": False},
        {"extracted_case_name": "Buchanan v. John Doe", "citation": "431 S.E.2d 289", "verified": False},
    ]
    clusters = cluster_citations_minimal(citations)
    assert len(clusters) == 2
    cites_per = [{c["citation"] for c in cl["citations"]} for cl in clusters]
    assert {"67 S.E.2d 289"} in cites_per
    assert {"431 S.E.2d 289"} in cites_per


def test_state_v_kier_and_state_v_stalker_not_clustered():
    """State v. Kier and State v. Stalker are different cases (generic plaintiff 'State') - should NOT cluster."""
    from src.unified_clustering_master_optimized import cluster_citations_minimal

    citations = [
        {"extracted_case_name": "State v. Kier", "citation": "164 Wn.2d 798", "verified": False},
        {"extracted_case_name": "State v. Stalker", "citation": "219 P.3d 722", "verified": False},
    ]
    clusters = cluster_citations_minimal(citations)
    assert len(clusters) == 2
    cites_per = [{c["citation"] for c in cl["citations"]} for cl in clusters]
    assert {"164 Wn.2d 798"} in cites_per
    assert {"219 P.3d 722"} in cites_per


def test_parallel_detection_rejects_year_mismatch():
    """717 P.3d 1353 (1986) and 940 P.2d 261 (1997) should not be parallel (different cases)."""
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    from src.models import CitationResult

    proc = UnifiedCitationProcessorV2()
    c1 = CitationResult(citation="717 P.3d 1353", extracted_case_name="In re Rosier", extracted_date="1986")
    c2 = CitationResult(citation="940 P.2d 261", extracted_case_name="In re Rosier", extracted_date="1997")
    text = "In re Rosier, 717 P.3d 1353 (1986). See also 940 P.2d 261 (1997)."
    result = proc._are_likely_parallel_citations(c1, c2, text)
    assert result is False
