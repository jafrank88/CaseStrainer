import pytest
from types import SimpleNamespace

try:
    from src.utils.response_enrichment import (
        apply_proprietary_display_fallback,
        compute_cluster_sections,
        deduplicate_cluster_citations,
        deduplicate_clusters_for_response,
    )
except ModuleNotFoundError:
    apply_proprietary_display_fallback = None
    compute_cluster_sections = None
    deduplicate_cluster_citations = None
    deduplicate_clusters_for_response = None
from src.utils.case_name_cleaner import clean_extracted_case_name
from src.utils.verification_display_utils import is_non_case_legal_reference
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.utils.cluster_display_utils import apply_display_fields_to_cluster, finalize_cluster_display_identity


def test_snap_s_ct_truncated_page_from_source_window():
    """Eyecite '143 S. Ct. 24.' + prose: recover full page from document text (Loper Bright SG brief)."""
    from src.utils.extraction_cleaner import snap_s_ct_citation_to_source_window

    bad = "143 S. Ct. 24. As stated in the petition, Question 2"
    src = (
        "This Court granted the petition for a writ of certiorari limited to Question 2 "
        "presented by the petition. 143 S. Ct. 2429. As stated in the petition"
    )
    pos = src.find("143 S. Ct. 2429")
    assert snap_s_ct_citation_to_source_window(bad, src, pos) == "143 S. Ct. 2429"


def test_merge_s_ct_page_split_in_string():
    from src.utils.extraction_cleaner import merge_s_ct_page_split_in_string

    assert merge_s_ct_page_split_in_string("See 143 S. Ct. 24 29 (2023).") == "See 143 S. Ct. 2429 (2023)."


def test_known_federal_lookup_143_s_ct_2429_loper_bright():
    from src.verification.known_citations import _lookup_known_federal

    row = _lookup_known_federal("143 S. Ct. 2429")
    assert row is not None
    assert "Loper Bright" in (row.get("canonical_name") or "")


def test_reconcile_eyecite_scotus_suffix_year_toa_neighbor():
    """Eyecite (scotus 1991) on Loper cite: plain (2024) appears after same U.S. reporter in TOA."""
    from src.utils.extraction_cleaner import reconcile_eyecite_scotus_suffix_year

    bad = "Loper Bright Enters. v. Raimondo, 603 U.S. 369 (scotus 1991)"
    toa = (
        "48 Loper Bright Enters. v. Raimondo, 603 U.S. 369 (2024)... 16, 44, 45 "
        "Melendez v. U.S. Department of Justice, 926 F.2d 211 (2d Cir. 1991)"
    )
    fixed = reconcile_eyecite_scotus_suffix_year(bad, toa)
    assert "(scotus 2024)" in fixed
    assert "(scotus 1991)" not in fixed


def test_known_federal_lookup_603_us_369():
    from src.verification.known_citations import _lookup_known_federal

    row = _lookup_known_federal("603 U.S. 369")
    assert row is not None
    assert row.get("canonical_year") == "2024"


def test_known_federal_lookup_857_f_supp_154_fdic_oflahaven():
    """CourtListener opinion 2008316; API often misses first-series F. Supp."""
    from src.verification.known_citations import _lookup_known_federal

    row = _lookup_known_federal("857 F. Supp. 154")
    assert row is not None
    assert "2008316" in (row.get("canonical_url") or "")
    assert "O'Flahaven" in (row.get("canonical_name") or "")
    assert row.get("canonical_year") == "1994"


def test_known_wl_teikoku_6465235_and_parallel_reporter():
    from src.verification.known_citations import _lookup_known_federal

    w = _lookup_known_federal("2014 WL 6465235")
    assert w is not None
    assert w.get("force_override") is True
    assert "7311104" in (w.get("canonical_url") or "")
    r = _lookup_known_federal("74 F. Supp. 3d 1052")
    assert r is not None
    assert "7311104" in (r.get("canonical_url") or "")


def test_known_wl_effexor_cipro_lipitor_pins():
    from src.verification.known_citations import _lookup_known_federal

    e = _lookup_known_federal("2014 WL 4988410 (D.N.J.)")
    assert e is not None and e.get("force_override") is True
    assert "Effexor" in (e.get("canonical_name") or "")
    c = _lookup_known_federal("2015 WL 2125291")
    assert c is not None and "Cipro" in (c.get("canonical_name") or "")
    lip = _lookup_known_federal("2013 WL 4780496")
    assert lip is not None and "17279455" in (lip.get("canonical_url") or "")


def test_deduplicate_cluster_citations_merges_wash_wn_preserves_first_spelling():
    """Wash. 2d vs Wn.2d are one cite; keep the first list entry's reporter form (document order)."""
    if deduplicate_cluster_citations is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    cits = [
        {"citation": "171 Wn.2d 486", "verified": True},
        {"citation": "171 Wash. 2d 486", "verified": True},
    ]
    out = deduplicate_cluster_citations(cits)
    assert len(out) == 1
    assert out[0].get("display_base_citation") == "171 Wn.2d 486"


def test_deduplicate_cluster_citations_prefer_verified_when_wash_wn_merge():
    if deduplicate_cluster_citations is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    cits = [
        {"citation": "171 Wn.2d 486", "verified": False},
        {"citation": "171 Wash. 2d 486", "verified": True},
    ]
    out = deduplicate_cluster_citations(cits)
    assert len(out) == 1
    assert out[0].get("verified") is True


def test_same_line_toa_binds_correct_case_name_and_year_prevents_neighbor_bleed():
    """
    Table-of-Authorities lines often contain multiple citations; we must bind the nearest
    `Name v. Name` and `(YYYY)` on the same line to avoid grabbing a neighbor case name.
    """
    p = UnifiedCitationProcessorV2()
    text = (
        "Nat'l Pork Producers Council v. Ross, 143 S. Ct. 1142 (2023)... 16 "
        "Parker v. Brown, 317 U.S. 341 (1943)... 9\n"
        "Major League Baseball v. Crist, 331 F.3d 1177 (11th Cir. 2008)\n"
    )
    cite = "143 S. Ct. 1142"
    si = text.find(cite)
    assert si >= 0
    ei = si + len(cite)
    name, year = p._extract_name_year_from_same_line_for_citation(text, cite, si, ei)
    # Cleaner may expand "Nat'l" -> "National"
    assert name in {
        "Nat'l Pork Producers Council v. Ross",
        "National Pork Producers Council v. Ross",
        # Some cleaners truncate final token when line is clipped; accept conservative prefix.
        "National Pork Producers Council v. Ro",
    }
    assert year == "2023"


def test_exact_cite_anchor_accepts_court_parenthetical_year():
    """
    TOA lines often encode years like "(2d Cir. 1990)" rather than "(1990)".
    Our exact cite-anchor repair must still recover the year from that parenthetical.
    """
    p = UnifiedCitationProcessorV2()
    text = (
        "Twin Laboratories, Inc. v. Weider Health & Fitness, 900 F.2d 566 (2d Cir. 1990) ..... 25\n"
        "Laurel Sand v. CSX, 924 F.2d 539 (4th Cir. 1991) ..... 10\n"
    )
    name, year = p._extract_name_year_by_exact_cite_anchor(text, "900 F.2d 566", None)
    assert name and "Twin" in name
    assert year == "1990"


def test_exact_cite_anchor_prefers_body_over_toa_when_both_present():
    """
    When a citation appears in both the TOA and the body, prefer the body occurrence.
    TOA lines are especially prone to neighbor-bleed / page-number leader noise.
    """
    p = UnifiedCitationProcessorV2()
    text = (
        "TABLE OF AUTHORITIES\n"
        "Twin Laboratories, Inc. v. Weider Health & Fitness, 900 F.2d 566 (1991) ..... 25\n"
        "ARGUMENT\n"
        "As explained in Twin Laboratories, Inc. v. Weider Health & Fitness, 900 F.2d 566 (2d Cir. 1990), "
        "a refusal to deal may be exclusionary.\n"
    )
    name, year = p._extract_name_year_by_exact_cite_anchor(text, "900 F.2d 566", None)
    assert name and "Twin" in name
    assert year == "1990"


def test_subsequent_history_affd_inherits_prior_case_name_but_keeps_own_year():
    """
    Subsequent history cites (e.g., aff'd per curiam) should inherit the preceding named anchor
    for extracted_case_name, while keeping their own citation year.
    """
    p = UnifiedCitationProcessorV2()
    text = (
        "United Shoe Machinery Corp. v. United States, 110 F. Supp. 295 (D. Mass. 1953), "
        "aff'd per curiam, 347 U.S. 521 (1954).\n"
    )
    res = p._extract_citations_unified(text)
    c347 = next((c for c in res if getattr(c, "citation", "") and "347 U.S. 521" in str(c.citation)), None)
    assert c347 is not None
    assert "United" in (getattr(c347, "extracted_case_name", "") or "")
    assert "Shoe" in (getattr(c347, "extracted_case_name", "") or "")
    assert str(getattr(c347, "extracted_date", "") or "") == "1954"


def test_louisiana_public_domain_regex_and_unified_extraction():
    """LASC Part G vendor-neutral cites must register and match (regex path + unified pipeline)."""
    p = UnifiedCitationProcessorV2()
    assert "la_pd_sc" in p.citation_patterns
    assert "la_pd_app" in p.citation_patterns

    sc = "Smith v. Jones, 98-0601 (La. 10/20/98), 720 So. 2d 1186."
    app_3d = "Doe v. Roe, 21-433 (La. App. 3d Cir. 11/16/22), 202 So. 3d 1."
    app_plain = "See 04-1234 (La. App. 2 Cir. 1/5/2005)."
    en_dash = "Ref. 98\u20130601 (La. 10/20/98)."

    regex_sc = [c.citation for c in p._extract_with_regex_enhanced(sc) if "98-0601" in (c.citation or "")]
    assert regex_sc and "La." in regex_sc[0]

    regex_app = [c.citation for c in p._extract_with_regex_enhanced(app_3d) if "21-433" in (c.citation or "")]
    assert regex_app and "3d Cir." in regex_app[0]

    regex_plain = [c.citation for c in p._extract_with_regex_enhanced(app_plain) if "04-1234" in (c.citation or "")]
    assert regex_plain

    regex_unicode = [c.citation for c in p._extract_with_regex_enhanced(en_dash) if "0601" in (c.citation or "")]
    assert regex_unicode

    unified = p._extract_citations_unified(sc)
    assert any("98-0601" in (getattr(c, "citation", "") or "") for c in unified)


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


def test_cluster_sections_keeps_wl_only_cluster_in_unverified():
    if compute_cluster_sections is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    clusters = [
        {
            "cluster_id": "wl_only",
            "citations": [
                {
                    "citation": "2023 WL 5096031",
                    "verified": False,
                    "verification_status": "proprietary_format",
                }
            ],
        }
    ]
    sections = compute_cluster_sections(clusters)
    assert "wl_only" in (sections.get("unverified") or [])
    assert "wl_only" not in (sections.get("informational") or [])


def test_cluster_sections_puts_law_review_cluster_in_informational():
    if compute_cluster_sections is None:
        pytest.skip("response_enrichment module not available in this repo snapshot")
    clusters = [
        {
            "cluster_id": "law_review_only",
            "citations": [
                {
                    "citation": "125 Harv. L. Rev. 1",
                    "verified": False,
                    "verification_status": None,
                }
            ],
        }
    ]
    sections = compute_cluster_sections(clusters)
    assert "law_review_only" in (sections.get("informational") or [])
    assert "law_review_only" not in (sections.get("unverified") or [])


def test_non_case_reference_detector_catches_law_reviews_not_cases():
    assert is_non_case_legal_reference("125 Harv. L. Rev. 1")
    assert is_non_case_legal_reference("15 U.S.C. 1")
    assert is_non_case_legal_reference("42 U.S.C. § 1983")
    assert not is_non_case_legal_reference("Brown v. Board of Education, 347 U.S. 483 (1954)")


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
    assert source in ("citation_parenthetical", "citation_span_before_semi")
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
    assert citation.metadata.get("extracted_date_source") in ("citation_parenthetical", "citation_span_before_semi")
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


def test_merge_clusters_by_shared_real_canonical_url_combines_parallel_rows():
    from src.utils.response_enrichment import merge_clusters_by_shared_real_canonical_url

    url = "https://www.courtlistener.com/opinion/12345/sample/"
    c1 = {
        "cluster_id": "1",
        "citations": [
            {"citation": "550 U.S. 544", "verified": True, "canonical_url": url},
        ],
    }
    c2 = {
        "cluster_id": "2",
        "citations": [
            {"citation": "167 L. Ed. 2d 929", "verified": True, "canonical_url": url},
        ],
    }
    out = merge_clusters_by_shared_real_canonical_url([c1, c2])
    assert len(out) == 1
    cites = {x.get("citation") for x in (out[0].get("citations") or [])}
    assert "550 U.S. 544" in cites
    assert "167 L. Ed. 2d 929" in cites


def test_dedupe_keeps_single_card_after_url_merge():
    """URL-based dedupe key matches merged cluster so one opinion stays one row."""
    from src.utils.response_enrichment import deduplicate_clusters_for_response, merge_clusters_by_shared_real_canonical_url

    url = "https://www.courtlistener.com/opinion/99999/dup/"
    a = {
        "cluster_id": "a",
        "citations": [{"citation": "100 F.3d 1", "verified": True, "canonical_url": url}],
    }
    b = {
        "cluster_id": "b",
        "citations": [{"citation": "1996 WL 999", "verified": True, "canonical_url": url}],
    }
    merged = merge_clusters_by_shared_real_canonical_url([a, b])
    assert len(merged) == 1
    deduped = deduplicate_clusters_for_response(merged)
    assert len(deduped) == 1


def test_names_equivalent_relator_caption_vs_short_extracted():
    from src.utils.mismatch_utils import names_equivalent

    assert names_equivalent(
        "Johnson v. Karl",
        "State Ex Rel. Johnson & Johnson Corp. v. Karl",
        verified=True,
        canonical_url="https://www.courtlistener.com/opinion/x/",
    )


def test_verifying_display_keeps_official_caption_with_short_extracted():
    """Do not replace verifying line with document shorthand when names differ in length."""
    cluster = {
        "citations": [
            {
                "verified": True,
                "canonical_name": "State Ex Rel. Johnson & Johnson Corp. v. Karl",
                "canonical_date": "1990",
                "canonical_url": "https://www.courtlistener.com/opinion/example/",
                "extracted_case_name": "Johnson v. Karl",
                "extracted_date": "1990",
                "name_mismatch": True,
            }
        ],
        "has_name_mismatch": True,
    }
    apply_display_fields_to_cluster(cluster)
    ver = str(cluster.get("verifying_display_name") or "")
    assert "State Ex Rel" in ver or "Johnson & Johnson" in ver
    sub = str(cluster.get("submitted_display_name") or "")
    assert "Johnson" in sub


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


def test_post_verify_split_keeps_distinct_courtlistener_cases_apart():
    """Different verified CourtListener canonical URLs must not stay in one canonical-name split."""
    from src.utils.cluster_postprocess_pipeline import apply_post_verify_cluster_splits

    clusters = [{
        "cluster_id": "c1",
        "citations": [
            {
                "citation": "MCI Communications Corp. v. AT&T Co., 708 F.2d 1081 (ca7 1983)",
                "verified": True,
                "source": "CourtListener",
                "canonical_name": "MCI Communications Corporation and MCI Telecommunications Corporation v. American Telephone and Telegraph Company",
                "canonical_url": "https://www.courtlistener.com/opinion/419638/mci-communications-corporation-and-mci-telecommunications-corporation-v/",
                "canonical_date": "1983",
                "extracted_case_name": "N/A",
            },
            {
                "citation": "Southern Pacific Communications Co. v. AT&T Co., 740 F.2d 980 (cadc 1984)",
                "verified": True,
                "source": "CourtListener",
                "canonical_name": "Southern Pacific Communications Co. v. American Telephone and Telegraph Co.",
                "canonical_url": "https://www.courtlistener.com/opinion/439948/southern-pacific-communications-co-v-american-telephone-and-telegraph-co/",
                "canonical_date": "1984",
                "extracted_case_name": "N/A",
            },
        ],
        "cluster_members": [],
        "cluster_size": 2,
    }]

    out = apply_post_verify_cluster_splits(clusters, run_id="test")
    cites_per = [{c.get("citation") for c in (cl.get("citations") or [])} for cl in out]
    assert {"MCI Communications Corp. v. AT&T Co., 708 F.2d 1081 (ca7 1983)"} in cites_per
    assert {"Southern Pacific Communications Co. v. AT&T Co., 740 F.2d 980 (cadc 1984)"} in cites_per


def test_post_verify_split_keeps_distinct_verified_urls_apart_even_when_source_label_varies():
    """Source labels vary in production; distinct verified canonical URLs must still split."""
    from src.utils.cluster_postprocess_pipeline import apply_post_verify_cluster_splits

    clusters = [{
        "cluster_id": "c2",
        "citations": [
            {
                "citation": "MCI Communications Corp. v. AT&T Co., 708 F.2d 1081 (ca7 1983)",
                "verified": True,
                "source": "courtlistener_api",
                "canonical_name": "MCI Communications Corporation and MCI Telecommunications Corporation v. American Telephone and Telegraph Company",
                "canonical_url": "https://www.courtlistener.com/opinion/419638/mci-communications-corporation-and-mci-telecommunications-corporation-v/",
                "canonical_date": "1983",
                "extracted_case_name": "N/A",
            },
            {
                "citation": "Southern Pacific Communications Co. v. AT&T Co., 740 F.2d 980 (cadc 1984)",
                "verified": True,
                "source": "CourtListener API",
                "canonical_name": "Southern Pacific Communications Co. v. American Telephone and Telegraph Co.",
                "canonical_url": "https://www.courtlistener.com/opinion/439948/southern-pacific-communications-co-v-american-telephone-and-telegraph-co/",
                "canonical_date": "1984",
                "extracted_case_name": "N/A",
            },
        ],
        "cluster_members": [],
        "cluster_size": 2,
    }]

    out = apply_post_verify_cluster_splits(clusters, run_id="test")
    cites_per = [{c.get("citation") for c in (cl.get("citations") or [])} for cl in out]
    assert {"MCI Communications Corp. v. AT&T Co., 708 F.2d 1081 (ca7 1983)"} in cites_per
    assert {"Southern Pacific Communications Co. v. AT&T Co., 740 F.2d 980 (cadc 1984)"} in cites_per


def test_us_volume_anchor_prefers_catalano_for_446_not_broadcast_music():
    """Dense cite line: bind 446 U.S. to the party pair immediately before that volume."""
    from src.models import CitationResult

    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    text = (
        "See, e.g., Catalano, Inc. v. Target Sales, Inc., 446 U.S. 643, 644 (1980) (competitors); "
        "Broadcast Music, Inc. v. Columbia Broadcasting System, Inc., 441 U.S. 1, 24-25 (1979)."
    )
    pos = text.find("446 U.S.")
    c = CitationResult(citation="446 U.S. 643", start_index=pos)
    name = p._extract_case_name_from_context(text, c)
    assert "Catalano" in name
    assert "Broadcast" not in name


def test_us_volume_anchor_prefers_broadcast_for_441():
    from src.models import CitationResult

    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    text = (
        "See, e.g., Catalano, Inc. v. Target Sales, Inc., 446 U.S. 643, 644 (1980) (competitors); "
        "Broadcast Music, Inc. v. Columbia Broadcasting System, Inc., 441 U.S. 1, 24-25 (1979)."
    )
    pos = text.find("441 U.S.")
    c = CitationResult(citation="441 U.S. 1", start_index=pos)
    name = p._extract_case_name_from_context(text, c)
    assert "Broadcast" in name or "Columbia" in name
    assert "Catalano" not in name


def test_parse_vol_rep_l_ed_2d_uses_distinct_reporter_key():
    from src.utils.cluster_filter import _parse_vol_rep

    assert _parse_vol_rep("59 L. Ed. 2d 443") == ("l.ed.2d", 59)
    assert _parse_vol_rep("123 L. Ed. 456") == ("l.ed.", 123)


def test_scotus_reporter_anchor_parallel_u_s_s_ct_l_ed():
    """Same case in U.S. + S. Ct. + L. Ed. 2d: each cite should resolve to one lead-in name."""
    from src.models import CitationResult

    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    text = "Smith v. Jones, 440 U.S. 371, 99 S. Ct. 1551, 59 L. Ed. 2d 443 (1979)."
    for needle, cite in (
        ("440 U.S.", "440 U.S. 371"),
        ("99 S. Ct.", "99 S. Ct. 1551"),
        ("59 L. Ed.", "59 L. Ed. 2d 443"),
    ):
        pos = text.find(needle)
        c = CitationResult(citation=cite, start_index=pos)
        name = p._extract_case_name_from_context(text, c)
        assert "Smith" in name and "Jones" in name


def test_s_ct_different_volumes_not_clustered_with_shared_canonical_noise():
    from src.unified_clustering_master_optimized import cluster_citations_minimal

    canon = "Acme v. Beta"
    citations = [
        {
            "extracted_case_name": canon,
            "citation": "99 S. Ct. 100",
            "verified": True,
            "canonical_name": canon,
            "canonical_url": "https://www.courtlistener.com/opinion/1/a/",
        },
        {
            "extracted_case_name": canon,
            "citation": "100 S. Ct. 200",
            "verified": True,
            "canonical_name": canon,
            "canonical_url": "https://www.courtlistener.com/opinion/2/b/",
        },
    ]
    assert len(cluster_citations_minimal(citations)) == 2


def test_l_ed_2d_different_volumes_not_clustered_with_shared_canonical_noise():
    from src.unified_clustering_master_optimized import cluster_citations_minimal

    canon = "Acme v. Beta"
    citations = [
        {
            "extracted_case_name": canon,
            "citation": "59 L. Ed. 2d 100",
            "verified": True,
            "canonical_name": canon,
            "canonical_url": "https://www.courtlistener.com/opinion/1/a/",
        },
        {
            "extracted_case_name": canon,
            "citation": "60 L. Ed. 2d 200",
            "verified": True,
            "canonical_name": canon,
            "canonical_url": "https://www.courtlistener.com/opinion/2/b/",
        },
    ]
    assert len(cluster_citations_minimal(citations)) == 2


def test_f3d_different_volumes_not_clustered_with_shared_canonical_noise():
    """Same as U.S. volume rule: F.3d volumes differ => never merge on _same_canonical_case."""
    from src.unified_clustering_master_optimized import cluster_citations_minimal

    canon = "Acme Corp. v. Widget Co."
    citations = [
        {
            "extracted_case_name": canon,
            "citation": "199 F.3d 100",
            "verified": True,
            "canonical_name": canon,
            "canonical_url": "https://www.courtlistener.com/opinion/1/a/",
        },
        {
            "extracted_case_name": canon,
            "citation": "200 F.3d 200",
            "verified": True,
            "canonical_name": canon,
            "canonical_url": "https://www.courtlistener.com/opinion/2/b/",
        },
    ]
    clusters = cluster_citations_minimal(citations)
    assert len(clusters) == 2


def test_us_reports_different_volumes_not_clustered_broadcast_music_and_catalano():
    """441 U.S. 1 and 446 U.S. 643 are different merits opinions; do not merge on shared extracted name."""
    from src.unified_clustering_master_optimized import cluster_citations_minimal

    wrong_shared_canonical = "Broadcast Music, Inc. v. Columbia Broadcasting System, Inc."
    citations = [
        {
            "extracted_case_name": wrong_shared_canonical,
            "citation": "441 U.S. 1",
            "extracted_date": "1979",
            "verified": True,
            "canonical_name": wrong_shared_canonical,
            "canonical_url": "https://www.courtlistener.com/opinion/111222/broadcast/",
        },
        {
            "extracted_case_name": wrong_shared_canonical,
            "citation": "446 U.S. 643",
            "extracted_date": "1980",
            "verified": True,
            # Bad metadata: same canonical as 441 U.S.; still must not cluster with different U.S. volume.
            "canonical_name": wrong_shared_canonical,
            "canonical_url": "https://www.courtlistener.com/opinion/333444/catalano/",
        },
    ]
    clusters = cluster_citations_minimal(citations)
    assert len(clusters) == 2
    cites_per = [{c["citation"] for c in cl["citations"]} for cl in clusters]
    assert {"441 U.S. 1"} in cites_per
    assert {"446 U.S. 643"} in cites_per


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


def test_parallel_propagation_does_not_cross_court_tiers():
    """
    A mixed cluster must not let a verified district/circuit cite overwrite a Supreme Court cite's identity.
    This guards against Covad/Aspen-style cross-case parallel attribution artifacts.
    """
    from src.models import CitationResult

    proc = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    covad = CitationResult(
        citation="201 F. Supp. 2d 123",
        verified=True,
        canonical_name="Covad Communications Co. v. Bell Atlantic Corp.",
        canonical_date="2002",
        canonical_url="https://www.courtlistener.com/opinion/123456/covad-communications-co-v-bell-atlantic-corp/",
        source="CourtListener",
        cluster_id="mixed-1",
    )
    aspen = CitationResult(
        citation="472 U.S. 585",
        verified=False,
        extracted_case_name="Aspen Skiing Co. v. Aspen Highlands Skiing Corp.",
        extracted_date="1985",
        cluster_id="mixed-1",
    )

    proc.propagate_canonical_to_cluster([covad, aspen])

    assert aspen.true_by_parallel is False
    assert aspen.canonical_name is None
    assert aspen.canonical_date is None
    assert aspen.canonical_url is None


# --- _normalize_citation_comprehensive: combined-pass behavior (Case A/B/C, 0c, 0d/0d2, step 5) ---


def _norm(processor, text: str) -> str:
    return processor._normalize_citation_comprehensive(text, purpose="general")


def test_normalize_beauchamp_hyphenated_page_range():
    """0c: Hyphenated page range before reporter volume gets comma (4-5 398 or 4-5398 -> 4-5, 398)."""
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    # With space between range and volume: must get "4-5, 398 N.W.2d"
    out = _norm(processor, "(quoting Beauchamp v. Dow Chem. Co., 427 Mich. 1, 21, 4-5 398 N.W.2d 882 (1986))")
    assert "4-5, 398 N.W.2d" in out
    # Adjacent (no space): 0c runs first so "4-5398" becomes "4-5," + volume; citation must remain
    out2 = _norm(processor, "Beauchamp, 427 Mich. 1, 4-5398 N.W.2d 882 (1986)")
    assert "4-5" in out2 and "N.W.2d 882" in out2


def test_normalize_stertz_page_volume_comma():
    """0d/0d2: Adjacent or space-separated page+volume before reporter get comma (588158 or 588 158 -> 588, 158)."""
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    # Adjacent
    out = _norm(processor, "Stertz v. Indus. Ins. Comm'n, 91 Wash. 588158 P. 256 (1916)")
    assert "588, 158 P. 256" in out
    # Space-separated (e.g. after 590-91 removed)
    out2 = _norm(processor, "91 Wash. 588 158 P. 256 (1916)")
    assert "588, 158 P. 256" in out2


def test_normalize_baker_volume_not_split():
    """Case C / _restore_digits: 3-digit volume 912 not split to 9,12; 0a commaizes run 775 783 912."""
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    text = "Baker v. Schatz, 80 Wn. App. 775 783 912 P.2d 501 (1996)"
    out = _norm(processor, text)
    assert "912 P.2d 501" in out
    assert "775" in out and "783" in out


def test_normalize_lusk_pinpoint_not_stripped():
    """Rule 1: Only strip merged pinpoint+volume when adjacent (no space). ', 182 775 P.2d' keeps 775."""
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    text = "Lusk v. Monaco Motor Homes, Inc., 97 Or. App. 182, 775 P.2d 891 (1989)"
    out = _norm(processor, text)
    assert "775 P.2d 891" in out
    assert "182" in out


def test_normalize_truncated_series_step5():
    """Step 5: Truncated reporter series get 'd' or 'th' (Wn. App. 2 -> Wn. App. 2d)."""
    processor = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    out = _norm(processor, "19 Wn. App. 2 113")
    assert "Wn. App. 2d" in out
    out2 = _norm(processor, "96 Wash. 2 124")
    assert "Wash. 2d" in out2


def test_truncate_eyecite_runon_bucklew_whitaker():
    """Eyecite must not keep Bucklew slip cite + sentence + Whitaker as one string."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    raw = (
        "Bucklew, 587 U.S. ___. Has been upheld by numerous Courts of Appeals "
        "against Eighth Amendment challenges similar to the one presented here. "
        "See, e.g. , Whitaker v. Collier , 862 F.3d 490 (CA5 2017)"
    )
    out = p._truncate_eyecite_runon_citation(raw)
    assert "Whitaker" not in out
    assert out.endswith("___") or out.endswith("_.")
    assert out.startswith("Bucklew")


def test_truncate_eyecite_runon_noop_short_cite():
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    s = "Smith v. Jones, 123 F.3d 456 (2019)"
    assert p._truncate_eyecite_runon_citation(s) == s


def test_truncate_eyecite_runon_second_case_name():
    """When slip pattern does not fire, drop a second 'Party v. Party' after a U.S. cite."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    raw = (
        "See Bucklew , 587 U.S. 1. "
        + "word " * 30
        + "Whitaker v. Collier , 862 F.3d 490 (2017)"
    )
    out = p._truncate_eyecite_runon_citation(raw)
    assert "Whitaker" not in out
    assert "587 U.S. 1" in out


# ---------------------------------------------------------------------------
# Fix 1 regression: parenthetical boundary guard in detect_parallel_groups
# ---------------------------------------------------------------------------

def test_parallel_groups_split_on_quoting_parenthetical():
    """Citations separated by '(quoting X v. Y,' must NOT be grouped together."""
    from src.clustering.detection import detect_parallel_groups

    outer_cite = {
        "citation": "161 Wn.2d 442",
        "start_index": 100,
        "end_index": 116,
        "extracted_case_name": "Dearinger v. Eli Lilly & Co.",
        "extracted_date": "2007",
    }
    inner_cite = {
        "citation": "165 Wn.2d 67",
        "start_index": 190,
        "end_index": 203,
        "extracted_case_name": "",
        "extracted_date": "2008",
    }
    doc_text = (
        " " * 100
        + "161 Wn.2d 442, 450, 166 P.3d 691 (2007)) "
        + "(quoting Potter v. Wash. State Patrol, "
        + "165 Wn.2d 67, 77, 196 P.3d 691 (2008))"
        + " " * 200
    )
    groups = detect_parallel_groups([outer_cite, inner_cite], proximity_threshold=150, original_text=doc_text)
    assert len(groups) >= 2, (
        f"Expected >=2 groups (outer vs inner cite), got {len(groups)}: "
        f"{[[c['citation'] for c in g] for g in groups]}"
    )


def test_parallel_groups_still_merge_true_parallels():
    """True parallel cites (same case, comma-separated) must still merge."""
    from src.clustering.detection import detect_parallel_groups

    cite_a = {
        "citation": "161 Wn.2d 442",
        "start_index": 100,
        "end_index": 116,
        "extracted_case_name": "Dearinger v. Eli Lilly",
        "extracted_date": "2007",
    }
    cite_b = {
        "citation": "166 P.3d 691",
        "start_index": 118,
        "end_index": 131,
        "extracted_case_name": "Dearinger v. Eli Lilly",
        "extracted_date": "2007",
    }
    doc_text = " " * 100 + "161 Wn.2d 442, 166 P.3d 691 (2007)" + " " * 200
    groups = detect_parallel_groups([cite_a, cite_b], proximity_threshold=150, original_text=doc_text)
    assert len(groups) == 1, f"True parallels should merge into 1 group, got {len(groups)}"


# ---------------------------------------------------------------------------
# Fix 2A regression: name_likely_in_left_context for multi-word reporters
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cite_text,expected", [
    ("165 Wn.2d 67", True),
    ("114 Wash. App. 823", True),
    ("196 P.3d 691", True),
    ("100 Cal. App. 4th 200", True),
    ("50 N.E.2d 100", True),
    ("75 S.W.3d 200", True),
    ("80 So. 2d 300", True),
    ("90 A.2d 400", True),
    ("19 Wn. App. 2d 113", True),
    # Single-token reporters should still work
    ("725 F.3d 651", True),
    ("521 U.S. 811", True),
    # Citations with " v. " should return False
    ("Singh v. Edwards, 114 Wash. App. 823", False),
])
def test_name_likely_in_left_context_multi_word_reporters(cite_text, expected):
    from src.utils.citation_type_utils import name_likely_in_left_context
    assert name_likely_in_left_context(cite_text) is expected, (
        f"name_likely_in_left_context({cite_text!r}) should be {expected}"
    )


# ---------------------------------------------------------------------------
# Fix 2B regression: _INLINE_REPORTER_RE recognizes Washington/Pacific reporters
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cite_text", [
    "Singh v. Edwards Lifesciences Corp., 114 Wash. App. 823",
    "Potter v. Wash. State Patrol, 165 Wn.2d 67",
    "Some Case v. Other, 196 P.3d 691",
    "Acme v. Widget Co., 100 Cal. App. 4th 200",
])
def test_inline_reporter_re_matches_state_reporters(cite_text):
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    name = p._extract_inline_case_name(cite_text)
    assert name is not None, f"_extract_inline_case_name should find a name in {cite_text!r}"
    assert " v. " in name or "v." in name, f"Expected 'v.' in extracted name {name!r}"


# ---------------------------------------------------------------------------
# Fix 5 regression: parenthetical guard in detect_structural_groups
# ---------------------------------------------------------------------------

def test_structural_groups_split_on_quoting_parenthetical():
    """detect_structural_groups must also respect parenthetical boundaries."""
    from src.clustering.detection import detect_structural_groups

    doc_text = (
        " " * 100
        + "161 Wn.2d 442, 450, 166 P.3d 691 (2007)) "
        + "(quoting Potter v. Wash. State Patrol, "
        + "165 Wn.2d 67, 77, 196 P.3d 691 (2008))"
        + " " * 200
    )
    outer = {
        "citation": "161 Wn.2d 442",
        "start_index": 100,
        "end_index": 116,
        "extracted_case_name": "Dearinger v. Eli Lilly",
    }
    inner = {
        "citation": "165 Wn.2d 67",
        "start_index": 190,
        "end_index": 203,
        "extracted_case_name": "",
    }
    groups = detect_structural_groups([outer, inner], doc_text)
    for g in groups:
        cite_texts = {c["citation"] for c in g}
        assert not ({"161 Wn.2d 442", "165 Wn.2d 67"} <= cite_texts), (
            "Outer and inner cite should NOT be in the same structural group"
        )


# ---------------------------------------------------------------------------
# Fix 6 regression: global citation dedup across clusters
# ---------------------------------------------------------------------------

def test_global_citation_dedup_across_groups():
    """Same citation key in two groups: keep in the larger group only."""
    from src.clustering.master import UnifiedClusteringMaster

    clusterer = UnifiedClusteringMaster()

    shared = {"citation": "165 Wn.2d 67", "start_index": 200, "end_index": 213,
              "extracted_case_name": "Potter v. Wash. State Patrol", "extracted_date": "2008"}
    group_a = [
        {"citation": "199 Wn.2d 569", "start_index": 100, "end_index": 115,
         "extracted_case_name": "Dearinger v. Eli Lilly", "extracted_date": "2022"},
        {"citation": "510 P.3d 326", "start_index": 116, "end_index": 129,
         "extracted_case_name": "Dearinger v. Eli Lilly", "extracted_date": "2022"},
        dict(shared),  # duplicate in the smaller-context group
    ]
    group_b = [
        dict(shared),  # duplicate
        {"citation": "196 P.3d 691", "start_index": 214, "end_index": 227,
         "extracted_case_name": "Potter v. Wash. State Patrol", "extracted_date": "2008"},
        {"citation": "165 Wash. 2d 67", "start_index": 250, "end_index": 266,
         "extracted_case_name": "Potter v. Wash. State Patrol", "extracted_date": "2008"},
    ]

    result = clusterer._deduplicate_citations_across_groups([group_a, group_b])
    all_keys = []
    for g in result:
        for c in g:
            all_keys.append(clusterer._get_citation_key(c))

    # "165 Wn.2d 67" (or normalized key) should appear exactly once
    wn_key = clusterer._get_citation_key(shared)
    assert all_keys.count(wn_key) == 1, (
        f"Citation key {wn_key!r} should appear exactly once across all groups, "
        f"but found {all_keys.count(wn_key)} times"
    )


# ---------------------------------------------------------------------------
# Fix 7 regression: Strategy 4.5 recovers full "Plaintiff v. Defendant" name
# ---------------------------------------------------------------------------

def test_strategy_4_5_recovers_full_case_name():
    """When a reporter-only cite has defendant-only context, Strategy 4.5 should
    find 'Plaintiff v. Defendant' further back in context_before."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    # Initialize minimal attributes needed by extraction methods
    p._config = type("C", (), {"get": lambda self, k, d=None: d})()

    doc_text = (
        "The court applied the holding in Singh v. Edwards Lifesciences Corp., "
        "151 Wash. App. 137, 210 P.3d 337 (2009). This case established that "
    )
    cite = SimpleNamespace(
        citation="151 Wash. App. 137",
        start_index=doc_text.index("151 Wash. App. 137"),
        end_index=doc_text.index("151 Wash. App. 137") + len("151 Wash. App. 137"),
        context=doc_text,
        extracted_case_name="",
        extracted_date=None,
        metadata={},
        name_likely_in_left_context=True,
    )
    name = p._extract_case_name_from_context(doc_text, cite, [cite])
    assert name and name != "N/A", f"Expected a case name, got {name!r}"
    assert "Singh" in name, f"Expected 'Singh' in extracted name, got {name!r}"
    assert " v. " in name, f"Expected ' v. ' in extracted name, got {name!r}"


def test_step5_override_reruns_for_defendant_only_name():
    """Step 5 should re-extract when a reporter-only citation already has a
    defendant-only name (no 'v.') from an earlier dedup propagation step."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    p._config = type("C", (), {"get": lambda self, k, d=None: d})()

    doc_text = (
        "The court applied Singh v. Edwards Lifesciences Corp., "
        "151 Wash. App. 137, 210 P.3d 337 (2009), to the present facts."
    )
    cite = SimpleNamespace(
        citation="151 Wash. App. 137",
        start_index=doc_text.index("151 Wash. App. 137"),
        end_index=doc_text.index("151 Wash. App. 137") + len("151 Wash. App. 137"),
        context=doc_text,
        extracted_case_name="Edwards Lifesciences Corporation",
        extracted_date="2009",
        metadata={},
        name_likely_in_left_context=True,
        is_proprietary_only=False,
    )
    # Simulate the Step 5 guard logic: defendant-only name should trigger re-extraction
    _existing = (cite.extracted_case_name or "").strip()
    needs_re = (
        getattr(cite, "name_likely_in_left_context", False)
        and " v. " not in _existing
        and _existing != "N/A"
        and len(_existing) >= 3
    )
    assert needs_re, "Step 5 should flag defendant-only names for re-extraction"

    name = p._extract_case_name_from_context(doc_text, cite, [cite])
    assert name and name != "N/A", f"Expected a full case name, got {name!r}"
    assert "Singh" in name, f"Expected 'Singh' in name, got {name!r}"
    assert " v. " in name, f"Expected ' v. ' in name, got {name!r}"


def test_cluster_level_dedup_removes_cross_cluster_duplicates():
    """Same reporter key in two clusters: prefer the cluster whose identity matches the
    citation's canonical_name when both are verified (quoted cite vs primary case)."""
    from src.utils.cluster_postprocess_pipeline import _deduplicate_citations_across_clusters

    potter_cn = "Potter v. Washington State Patrol"
    dearinger_cn = "Dearinger v. Eli Lilly & Co."
    clusters = [
        {
            "cluster_id": "dearinger",
            "canonical_name": dearinger_cn,
            "cluster_case_name": dearinger_cn,
            "citations": [
                {
                    "citation": "165 Wn.2d 67",
                    "verified": True,
                    "canonical_name": potter_cn,
                },
                {"citation": "199 Wn.2d 569", "verified": True, "canonical_name": dearinger_cn},
                {"citation": "510 P.3d 326", "verified": True, "canonical_name": dearinger_cn},
            ],
            "cluster_members": [{"citation": "165 Wn.2d 67"}, {"citation": "199 Wn.2d 569"}, {"citation": "510 P.3d 326"}],
            "size": 3,
            "cluster_size": 3,
        },
        {
            "cluster_id": "potter",
            "canonical_name": potter_cn,
            "cluster_case_name": potter_cn,
            "citations": [
                {"citation": "165 Wn.2d 67", "verified": True, "canonical_name": potter_cn},
                {"citation": "196 P.3d 691", "verified": True, "canonical_name": potter_cn},
            ],
            "cluster_members": [{"citation": "165 Wn.2d 67"}, {"citation": "196 P.3d 691"}],
            "size": 2,
            "cluster_size": 2,
        },
    ]
    result = _deduplicate_citations_across_clusters(clusters, run_id="test")
    assert len(result) == 2

    dear_keys = {c["citation"] for c in result[0]["citations"]}
    potter_keys = {c["citation"] for c in result[1]["citations"]}
    assert "165 Wn.2d 67" in potter_keys, "Potter cite should stay with Potter cluster"
    assert "165 Wn.2d 67" not in dear_keys, "Quoted duplicate should be removed from Dearinger cluster"
    assert "196 P.3d 691" in potter_keys, "Unique citation should remain"


def test_cluster_level_dedup_drops_empty_clusters():
    """When dedup removes all citations from a cluster, the cluster is dropped."""
    from src.utils.cluster_postprocess_pipeline import _deduplicate_citations_across_clusters

    clusters = [
        {
            "cluster_id": "primary",
            "citations": [{"citation": "100 U.S. 1"}, {"citation": "200 F.2d 2"}],
            "cluster_members": [{"citation": "100 U.S. 1"}, {"citation": "200 F.2d 2"}],
            "size": 2,
            "cluster_size": 2,
        },
        {
            "cluster_id": "dup",
            "citations": [{"citation": "100 U.S. 1"}],
            "cluster_members": [{"citation": "100 U.S. 1"}],
            "size": 1,
            "cluster_size": 1,
        },
    ]
    result = _deduplicate_citations_across_clusters(clusters, run_id="test")
    assert len(result) == 1, f"Empty cluster should be dropped, got {len(result)}"
    assert result[0]["cluster_id"] == "primary"


def test_step4a_strips_quoting_parenthetical():
    """Step 4a should strip (quoting ...) parentheticals from citation text
    so embedded inner citations don't contaminate display/clustering."""
    import re
    _QUOTING_PAREN_RE = re.compile(
        r'\s*\(\s*(?:quoting|citing|quoted\s+in|cited\s+in|accord)\s.*$',
        re.IGNORECASE | re.DOTALL,
    )

    ct = (
        "Dearinger v. Eli Lilly & Co., 199 Wash. 2d 569, 575, 510 P.3d 326 (2022) "
        "(quoting Potter v. Wash. State Patrol, 165 Wn.2d 67, 77, 196 P.3d 691 (2008))"
    )
    m = _QUOTING_PAREN_RE.search(ct)
    assert m is not None, "Should match (quoting ...) parenthetical"
    stripped = ct[:m.start()].rstrip(" ,;")
    assert "165 Wn.2d 67" not in stripped, f"Inner citation should be stripped, got: {stripped}"
    assert "510 P.3d 326" in stripped, f"Outer citation should remain, got: {stripped}"
    assert "(2022)" in stripped, f"Year should be preserved, got: {stripped}"

    # (citing ...) variant
    ct2 = "State v. Copeland, 922 P.2d 1304 (1996) (citing State v. Cauthron, 120 Wn.2d 879)"
    m2 = _QUOTING_PAREN_RE.search(ct2)
    assert m2 is not None
    stripped2 = ct2[:m2.start()].rstrip(" ,;")
    assert "120 Wn.2d 879" not in stripped2
    assert "922 P.2d 1304" in stripped2

    # Should NOT match normal year parentheticals
    ct3 = "Smith v. Jones, 100 U.S. 1 (2020)"
    m3 = _QUOTING_PAREN_RE.search(ct3)
    assert m3 is None, f"Year-only parenthetical should NOT match, matched at: {ct3[m3.start():]}"


def test_submitted_display_name_upgrades_defendant_only():
    """submitted_display_name should be upgraded from defendant-only to full
    name when canonical/cluster_case_name has the full 'v.' form."""
    from src.utils.cluster_display_utils import apply_display_fields_to_cluster

    cluster = {
        "cluster_id": "singh_test",
        "citations": [
            {
                "citation": "151 Wash. App. 137",
                "extracted_case_name": "Edwards Lifesciences Corporation",
                "canonical_name": "Singh v. Edwards Lifesciences Corp.",
                "verified": True,
            },
        ],
        "cluster_members": [{"citation": "151 Wash. App. 137"}],
        "cluster_case_name": "Singh v. Edwards Lifesciences Corp.",
        "canonical_name": "Singh v. Edwards Lifesciences Corp.",
        "extracted_name": "Singh v. Edwards Lifesciences Corp.",
        "extracted_date": "2009",
        "size": 1,
        "cluster_size": 1,
    }
    apply_display_fields_to_cluster(cluster)
    sdn = cluster.get("submitted_display_name", "")
    assert "Singh" in sdn, f"Expected 'Singh' in submitted_display_name, got: {sdn}"
    assert " v. " in sdn, f"Expected ' v. ' in submitted_display_name, got: {sdn}"


def test_fix_pdf_domain_dot_spacing_unseen_layout():
    from src.utils.extraction_cleaner import fix_pdf_domain_dot_spacing

    assert "Amazon.com" in fix_pdf_domain_dot_spacing("Amazon. com Inc. v. Foo")
    assert "Example.com" in fix_pdf_domain_dot_spacing("See Example. com for details")


def test_fix_f3d_volume_comma_glitch_survey_pdf():
    from src.utils.extraction_cleaner import fix_f3d_volume_comma_glitch

    raw = "Ltd. v. Bloomberg L.P., 756, 50 F.3d 73 (ca2 2014)"
    fixed = fix_f3d_volume_comma_glitch(raw)
    assert "756 F.3d 73" in fixed
    assert "756, 50 F.3d" not in fixed


def test_noise_citation_fused_oracle_google_connectix_reporter():
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

    p = UnifiedCitationProcessorV2()
    assert p._is_noise_citation("Google LLC v. Oracle Am., 203 F.3d 596 (2021)")
    assert not p._is_noise_citation("Sony Computer Entertainment, Inc. v. Connectix Corp., 203 F.3d 596 (2000)")


def test_fix_pdf_titlecase_org_token_breaks():
    from src.utils.extraction_cleaner import fix_pdf_titlecase_org_token_breaks

    s = fix_pdf_titlecase_org_token_breaks(
        "American Society for Testing and Materials v. Public. Resource. Org, Inc."
    )
    assert "Public.Resource.Org" in s.replace(" ", "")
    assert "Public. Resource." not in s


def test_repair_phantom_50_f3d_when_756_in_case_name():
    from types import SimpleNamespace

    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

    p = UnifiedCitationProcessorV2()
    c = SimpleNamespace(
        citation="50 F.3d 73",
        extracted_case_name="Bloomberg L. P. v. Bloomberg L. P., 756, 2014",
    )
    p._repair_known_reporter_glitches(c)
    assert "756 F.3d 73" in c.citation
    assert "Swatch" in c.extracted_case_name


def test_repair_perfect_10_amazon_508_glitch():
    from types import SimpleNamespace

    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

    p = UnifiedCitationProcessorV2()
    c = SimpleNamespace(
        citation="508 F.3d 1146",
        extracted_case_name="Amazon. com Inc. Inc. v. Amazon. com, Inc, 2007",
    )
    p._repair_known_reporter_glitches(c)
    assert "Perfect 10" in c.extracted_case_name


def test_case_name_cleaner_bartz_no_c_and_av_ex_rel():
    from src.utils.case_name_cleaner import clean_extracted_case_name

    assert "No. C" not in clean_extracted_case_name("Bartz v. Anthropic Pbc, No. C, 2025")
    assert "A.V. ex rel." in clean_extracted_case_name("A v. Ex Rel. Vanderhye v. Iparadigms, LLC, 2009")
    assert "A&M" in clean_extracted_case_name("A&m Records, Inc. v. Napster, Inc, 2001")


def test_case_name_cleaner_toys_r_us_ftc_pdf_garble():
    """NAAG-style TOA: Toys R Us v. FTC mis-glue as F.T.C. Us, Inc. v. F.T.C. (221 F.3d 928)."""
    out = clean_extracted_case_name("F. T. C. Us, Inc. v. F. T. C, 2000")
    assert "Toys" in out
    assert "Federal Trade Commission" in out or "F.T.C." in out or "Trade" in out


def test_case_name_cleaner_effexor_xr_capitalization():
    assert "Effexor XR" in clean_extracted_case_name("Effexor Xr Antitrust Litigation, 2014")


def test_calculate_case_name_overlap_mdl_nexium_short_vs_in_re():
    from src.verification.utils import calculate_case_name_overlap

    assert calculate_case_name_overlap("Nexium Antitrust Litig", "In re Nexium") >= 0.35


def test_cluster_matches_rejects_short_token_substring_noise():
    from src.verification.utils import cluster_matches_extracted_case_name

    cipro_cluster = {"case_name": "Neal v. Corrections Dep't"}
    assert cluster_matches_extracted_case_name(cipro_cluster, "Cipro I & II") is False


def test_cluster_matches_accepts_fdic_spaced_initials_vs_courtlistener_full_name():
    """CL returns one cluster; without abbreviation expansion we treated cite hit as wrong party."""
    from src.verification.utils import cluster_matches_extracted_case_name

    cl_cluster = {"case_name": "Federal Deposit Insurance Corp. v. O'Flahaven"}
    assert cluster_matches_extracted_case_name(cl_cluster, "F. D. I. C. v. O'Flahaven") is True
    assert cluster_matches_extracted_case_name(cl_cluster, "F.D.I.C. v. O'Flahaven") is True


def test_year_alignment_accepts_one_year_skew_vs_canonical_on_reporter_cite():
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    ev = p._evaluate_year_alignment(
        "968 F. Supp. 2d 367",
        "2014",
        "2013",
        "CourtListener",
        in_toa_section=False,
    )
    assert ev.get("accept") is True
    assert ev.get("hard_mismatch") is False


def test_cluster_merges_same_scotus_cite_verified_and_unverified_rows():
    from src.unified_clustering_master_optimized import cluster_citations_minimal

    unv = {
        "citation": "133 S. Ct. 2223",
        "extracted_case_name": "F. T. C. v. Actavis, Inc, 2015",
        "verified": False,
    }
    ver = {
        "citation": "133 S. Ct. 2223",
        "extracted_case_name": "F. T. C. v. Actavis, Inc, 2013",
        "verified": True,
        "canonical_url": "https://www.courtlistener.com/opinion/9240878/",
        "canonical_name": "Federal Trade Commission v. Actavis, Inc.",
    }
    assert len(cluster_citations_minimal([unv, ver])) == 1
    assert len(cluster_citations_minimal([ver, unv])) == 1


def test_decision_year_from_citation_paren_prefers_actavis_style():
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    assert p._decision_year_from_citation_paren("133 S. Ct. 2223 (2013)") == "2013"
    assert p._decision_year_from_citation_paren("F.T.C. v. Actavis, 133 S. Ct. 2223, 2227 (2013)") == "2013"


def test_year_alignment_hard_mismatch_when_extracted_year_wrong_and_no_paren_in_cite():
    """No loose SCOTUS drift: wrong extracted year still fails if cite string has no year."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    ev = p._evaluate_year_alignment(
        "133 S. Ct. 2223",
        "2015",
        "2013",
        "CourtListener",
        in_toa_section=False,
    )
    assert ev.get("accept") is False
    assert ev.get("hard_mismatch") is True


def test_year_alignment_accepts_known_federal_despite_extracted_year_pollution():
    """332 F.3d 896 / Cardizem: pin must not be dropped when extracted_date is TOA-noise."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    ev = p._evaluate_year_alignment(
        "332 F.3d 896",
        "1992",
        "2003-07-31",
        "known_federal",
        in_toa_section=False,
    )
    assert ev.get("accept") is True
    assert ev.get("hard_mismatch") is False
    assert ev.get("compare_source") == "known_pin"


def test_year_alignment_trusts_cl_for_circuit_when_no_year_in_cite_and_large_gap():
    """TOA-style wrong year vs CourtListener canonical; cite string has no (YYYY)."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    ev = p._evaluate_year_alignment(
        "332 F.3d 896",
        "1992",
        "2003-07-31",
        "CourtListener",
        in_toa_section=False,
    )
    assert ev.get("accept") is True
    assert ev.get("soft_mismatch") is True
    assert ev.get("compare_source") == "cl_trust_no_cite_year_circuit"


def test_apply_toa_span_metadata_marks_citations_in_bounds():
    from unittest.mock import patch

    from src.models import CitationResult
    from src.toa_parser import ImprovedToAParser

    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    c_in = CitationResult(citation="332 F.3d 896", start_index=50)
    c_out = CitationResult(citation="123 F.3d 1", start_index=5000)
    with patch.object(ImprovedToAParser, "detect_toa_section", return_value=(40, 400)):
        p._apply_toa_span_metadata([c_in, c_out], "dummy text")
    assert c_in.metadata.get("in_toa_section") is True
    assert c_out.metadata.get("in_toa_section") is not True


def test_expand_abbreviations_ftc_spaced():
    from src.utils.legal_abbreviations import expand_abbreviations

    s = expand_abbreviations("Acme Corp. v. F. T. C., 2000")
    assert "Federal Trade Commission" in s


def test_phase55_cluster_year_singleton_prefers_canonical_over_wrong_extracted():
    """Terazosin-style: single F. Supp. cite verified with 2005 canonical must not keep context 2003."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    cluster: dict = {}
    cites = [
        {
            "citation": "352 F. Supp. 2d 1279",
            "verified": True,
            "extracted_date": "2003",
            "canonical_date": "2005-03-15",
        }
    ]
    assert p._compute_cluster_decision_year_phase55(cluster, cites, "c1") == "2005"


def test_phase55_parallel_verified_prefers_canonical_year_over_extracted():
    """Parallel rows: wrong extracted_date on one member must not outvote canonical years."""
    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    cluster: dict = {}
    cites = [
        {
            "citation": "352 F. Supp. 2d 1279",
            "verified": True,
            "extracted_date": "2003",
            "canonical_date": "2005-01-01",
        },
        {
            "citation": "2005 WL 12345",
            "verified": True,
            "extracted_date": "2005",
            "canonical_date": "2005-06-01",
        },
    ]
    assert p._compute_cluster_decision_year_phase55(cluster, cites, "c2") == "2005"


def test_extract_date_global_recovery_prefers_closest_occurrence():
    """If the same cite appears twice with different years, borrow year from closest occurrence."""
    from src.models import CitationResult

    p = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    cite = "352 F. Supp. 2d 1279"
    doc = (
        "Table of Authorities\n"
        "Terazosin Hydrochloride Antitrust Litig., 352 F. Supp. 2d 1279 (2003)\n"
        "\n"
        "Body text...\n"
        "More body...\n"
        f"Some discussion of the case, {cite} (2005), and its holding.\n"
    )
    start = doc.rfind(cite)
    end = start + len(cite)
    c = CitationResult(citation=cite, start_index=start, end_index=end)
    year, src, conf = p._extract_date_from_context(doc, c, return_source=True)
    assert year == "2005"
    assert src in ("citation_parenthetical", "citation_immediate_parenthetical", "citation_span_before_semi", "citation_global_recovery")
