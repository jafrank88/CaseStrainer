from src.utils.response_enrichment import (
    apply_proprietary_display_fallback,
    deduplicate_clusters_for_response,
)
from src.utils.case_name_cleaner import clean_extracted_case_name
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2


def test_cluster_dedupe_uses_stable_citation_set_key():
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
    citations = [{"citation": "2020 WL 1061442", "verified": False, "canonical_url": None, "url": None}]
    apply_proprietary_display_fallback(citations)

    c = citations[0]
    assert c["verification_status"] == "proprietary_format"
    assert "Proprietary format" in c.get("error", "")
    assert c.get("verified") is False


def test_verified_wl_with_url_not_overridden():
    citations = [{"citation": "2025 WL 1773631", "verified": True, "canonical_url": "https://example/wl"}]
    apply_proprietary_display_fallback(citations)

    c = citations[0]
    assert c.get("verified") is True
    assert c.get("canonical_url") == "https://example/wl"


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
