"""
JSON success/error responses for the POST /analyze path.

Formerly lived in analyze_pipeline as _format_response / _format_error.
"""

import copy
import json
import logging
import os
import time
import re
import html
import uuid

from flask import jsonify

from src.schemas import normalize_citation_dict, normalize_cluster_dict
from src.utils.response_enrichment import (
    extract_display_base_citation,
    compute_citation_score_and_similarity,
    build_fallback_clusters,
    deduplicate_cluster_citations,
    enrich_citations_with_cluster_members,
    apply_proprietary_display_fallback,
    compute_cluster_sections,
)
from src.utils.verification_display_utils import is_effectively_verified_citation
from src.utils.cluster_display_utils import finalize_cluster_for_response
from src.utils.response_finalize import merge_dedupe_and_refinalize_clusters
from src.utils.cluster_postprocess_pipeline import apply_post_verify_cluster_splits
from src.metrics import record_citations
from src.config import CASESTRAINER_LOG_FULL_API_RESPONSES

logger = logging.getLogger(__name__)


def _validate_api_response_data(response_data):
    """Validate API response structure; return list of error strings or empty list."""
    errors = []
    if not isinstance(response_data, dict):
        errors.append("response_data must be a dict")
        return errors
    if "citations" in response_data and not isinstance(response_data["citations"], list):
        errors.append("citations must be a list")
    if "clusters" in response_data and not isinstance(response_data["clusters"], list):
        errors.append("clusters must be a list")
    return errors


def format_analyze_success_response(result, request_id, metadata, start_time):
    """Format a successful response with consistent structure"""
    processing_time_ms = int((time.time() - start_time) * 1000)

    try:
        citations = result.get("citations", [])
        if citations and len(citations) > 1:
            # Import the parallel verification function
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

            processor = UnifiedCitationProcessorV2()

            # Convert dict citations to CitationResult objects if needed
            from src.models import CitationResult

            citation_objects = []

            for cit in citations:
                if isinstance(cit, dict):
                    # Convert dict to CitationResult object
                    cit_obj = CitationResult(
                        citation=cit.get("citation", ""),
                        extracted_case_name=cit.get("extracted_case_name", ""),
                        extracted_date=cit.get("extracted_date", ""),
                        canonical_name=cit.get("canonical_name", ""),
                        canonical_date=cit.get("canonical_date", ""),
                        canonical_url=cit.get("canonical_url", ""),
                        verified=cit.get("verified", False),
                        true_by_parallel=cit.get("true_by_parallel", False),
                        possible_match=cit.get("possible_match", False),
                        error=cit.get("error"),
                        source=cit.get("source", "Unknown"),
                        start_index=cit.get("start_index"),
                        end_index=cit.get("end_index"),
                        method=cit.get("method", ""),
                        confidence=cit.get("confidence", 0.0),
                        metadata=cit.get("metadata", {}),
                    )
                    citation_objects.append(cit_obj)
                else:
                    citation_objects.append(cit)

            # Apply parallel verification
            processor.propagate_canonical_to_cluster(citation_objects)
            print("_format_response: Parallel verification completed")

            # Update the result with parallel verification data
            updated_citations = []
            for i, cit_obj in enumerate(citation_objects):
                if isinstance(citations[i], dict):
                    # Convert back to dict, preserving existing metadata
                    citations[i]["true_by_parallel"] = getattr(cit_obj, "true_by_parallel", False)
                    citations[i]["verified"] = getattr(cit_obj, "verified", False)
                    citations[i]["canonical_name"] = getattr(cit_obj, "canonical_name", "")
                    citations[i]["canonical_date"] = getattr(cit_obj, "canonical_date", "")
                    citations[i]["canonical_url"] = getattr(cit_obj, "canonical_url", "")
                    citations[i]["possible_match"] = getattr(cit_obj, "possible_match", False)

                    # Preserve existing metadata and merge with verification metadata
                    existing_metadata = citations[i].get("metadata", {})
                    verification_metadata = getattr(cit_obj, "metadata", {})

                    # Merge metadata, with verification metadata taking precedence
                    merged_metadata = {**existing_metadata, **verification_metadata}

                    # Ensure verification status is consistent
                    if citations[i].get("verified", False):
                        merged_metadata["verification_status"] = "verified"
                    elif not merged_metadata.get("verification_status"):
                        merged_metadata["verification_status"] = "unverified"

                    citations[i]["metadata"] = merged_metadata
                    updated_citations.append(citations[i])
                else:
                    updated_citations.append(cit_obj)

            result["citations"] = updated_citations

            # Log if parallel verification was applied
            parallel_count = 0
            for c in updated_citations:
                if isinstance(c, dict):
                    if c.get("true_by_parallel", False):
                        parallel_count += 1
                else:
                    if getattr(c, "true_by_parallel", False):
                        parallel_count += 1
            if parallel_count > 0:
                logger.info(f"[_format_response] Applied parallel verification to {parallel_count} citations")

    except Exception as parallel_error:
        logger.warning(f"[_format_response] Parallel verification failed (non-critical): {parallel_error}")
        import traceback

        logger.warning(f"[_format_response] Parallel verification error details: {traceback.format_exc()}")

    if not isinstance(result, dict):
        result = {}

    metadata.update(
        {
            "processing_time_ms": processing_time_ms,
            "processing_mode": result.get("metadata", {}).get(
                "processing_mode", metadata.get("processing_mode", "unknown")
            ),
            "status": result.get("status", "completed"),
            "success": result.get("success", True),
        }
    )

    def _normalize_legal_name(s):
        try:
            import re
            import html

            if not s:
                return ""
            x = html.unescape(str(s)).lower()
            x = x.replace("" ', "' ").replace('`', " '").replace(' " ", "'")
            patterns = [
                (r"\bdep[''.\']?t\b", "department"),
                (r"\bcomm[''.\']?n\b", "commission"),
                (r"\binfo\.?\b", "information"),  # FIX DEC 2025: Info. -> Information
                (r"\bpub\.?\b", "public"),
                (r"\butil\.?\b", "utility"),
                (r"\bins\.?\b", "insurance"),
                (r"\bfed[''.\']?n\b", "federation"),
                (r"\bass[''.\']?n\b", "association"),
                (r"\bpa\.?\b", "pennsylvania"),
                (r"\bu\.?s\.?\b", "united states"),
                (r"\bsec\.?\b", "securities"),
                (r"\bexch\.?\b", "exchange"),
                (r"\bmfrs?\.?\b", "manufacturers"),
                (r"\bindus\.?\b", "industries"),
                (r"\bnat[''.\']?l\b", "national"),
                (r"\bcommw\.?\b", "commonwealth"),
                # FIX DEC 2025: Additional legal abbreviations
                (r"\bhous\.?\b", "housing"),
                (r"\bauth\.?\b", "authority"),
                (r"\bcmtys?\.?\b", "communities"),
                (r"\bwash\.?\b", "washington"),
                (r"\bcty\.?\b", "county"),
                (r"\brsrv\.?\b", "reservation"),
                (r"\bbd\.?\b", "board"),
                (r"\btrs\.?\b", "trustees"),
                (r"\bcommc\.?\b", "communications"),
                (r"\bsoc[''.\']?y\b", "society"),
                (r"\bdef\.?\b", "defense"),
                (r"\bcent\.?\b", "central"),
                (r"\bdev\.?\b", "development"),
                (r"\bserv\.?\b", "services"),
                (r"\bsrvs\.?\b", "services"),
            ]
            for pat, repl in patterns:
                x = re.sub(pat, repl, x)
            x = re.sub(r"[\.,\-_/&()]+", " ", x)
            x = re.sub(r"\s+", " ", x).strip()
            stop = {
                "inc",
                "llc",
                "ltd",
                "corp",
                "co",
                "company",
                "limited",
                "plc",
                "s.a.",
                "sa",
                "gmbh",
                "ag",
                # permissive: ignore common agency qualifiers to reduce false negatives
                "department",
                "dept",
                "division",
                "bureau",
                "office",
                "ministry",
                "agency",
                "administration",
            }
            tokens = [t for t in x.split() if t not in stop]
            return " ".join(tokens)
        except Exception:
            return str(s or "").strip().lower()

    def _jaccard(a, b):
        sa = set((a or "").split())
        sb = set((b or "").split())
        if not sa or not sb:
            return 0.0
        inter = len(sa & sb)
        uni = len(sa | sb)
        return inter / max(1, uni)

    def _names_equivalent(a, b):
        """Lenient: prefer false positives over false negatives."""
        try:
            if not a or not b:
                return False
            if a == b:
                return True
            # Accept substring containment after normalization
            if a in b or b in a:
                return True
            # Lower Jaccard threshold to be lenient
            return _jaccard(a, b) >= 0.5
        except Exception:
            return False

    # USER FIX 2024-10-21: Convert CitationResult objects to dicts BEFORE building response
    citations_raw = result.get("citations", [])
    logger.debug(
        "[format_analyze_success_response] citations count=%s first=%r",
        len(citations_raw),
        citations_raw[0] if citations_raw else None,
    )

    citations_serialized = []
    for cit in citations_raw:
        # Serialize citation object/dict first
        if hasattr(cit, "to_dict"):
            d = cit.to_dict()
        elif isinstance(cit, dict):
            d = dict(cit)
        else:
            d = cit.__dict__ if hasattr(cit, "__dict__") else {"raw": str(cit)}

        # Enforce strict data separation: extracted_* must come from document
        try:
            # Prefer original_case_name/date captured pre-verification
            original_case = None
            original_date = None
            if isinstance(cit, dict):
                original_case = cit.get("original_case_name")
                original_date = cit.get("original_date")
            else:
                original_case = getattr(cit, "original_case_name", None)
                original_date = getattr(cit, "original_date", None)

            if original_case:
                if not d.get("extracted_case_name") or d.get("extracted_case_name") == "N/A":
                    d["extracted_case_name"] = original_case
                d["extracted_source"] = "document"
            # Do not overwrite extracted_date with canonical; restore original when present
            if original_date:
                if not d.get("extracted_date") or d.get("extracted_date") == "N/A":
                    d["extracted_date"] = original_date

            # Ensure canonical fields remain separate
            # (no action needed if d already has 'canonical_name'/'canonical_date')
        except Exception as _e:
            logger.warning(f"[RESPONSE] Data separation enforcement skipped for a citation: {_e}")

        citations_serialized.append(d)

    # Filter out court-year-only items (e.g., "N.J. 1997") from citations and clusters
    try:
        import re

        def _is_court_year_only(cit_text: str) -> bool:
            """Filter only short court-year-only strings (e.g. 'N.J. 1997'), not full citations that contain a year."""
            if not cit_text:
                return False
            t = str(cit_text).strip()
            # Reporter citation starts with volume (e.g. "123 F.3d 456") - keep those
            looks_like_reporter = re.match(r"^\d+\s+[A-Za-z\.]", t) is not None
            if looks_like_reporter:
                return False
            has_year = re.search(r"(17|18|19|20)\d{2}\b", t) is not None
            if not has_year:
                return False
            # Only treat as court-year-only if string is short (no full case name + citation)
            # so we don't drop e.g. "Milkovich v. Lorain Journal Co., 497 U.S. 1 (1990)"
            if len(t) > 40:
                return False
            return True

        # Filter individual citations (sync-only; async task_status returns pipeline output unfiltered)
        before_c = len(citations_serialized)
        removed = [c for c in citations_serialized if _is_court_year_only(c.get("citation"))]
        citations_serialized = [c for c in citations_serialized if not _is_court_year_only(c.get("citation"))]
        after_c = len(citations_serialized)
        if removed:
            logger.info(
                f"[FILTER] Removed {len(removed)} court-year-only items from citations (sync); "
                f"remaining {after_c} (async may have {before_c} before this filter)"
            )
            for i, c in enumerate(removed[:10]):
                cit_text = (c.get("citation") or c.get("text") or "")[:80]
                logger.debug(f"[FILTER] court-year-only removed [{i+1}]: {repr(cit_text)}")
            if len(removed) > 10:
                logger.debug(f"[FILTER] ... and {len(removed) - 10} more court-year-only citations")
    except Exception as _e:
        logger.warning(f"[FILTER] Failed filtering court-year-only citations: {_e}")

    # Normalize citations to stable DTO shape
    try:
        citations_serialized = [normalize_citation_dict(c) for c in citations_serialized]
    except Exception as _e:
        logger.warning(f"[SCHEMAS] Citation normalization failed, using raw dicts: {_e}")

    try:
        import re

        def _year_from(s):
            if not s:
                return ""
            m = re.search(r"(17|18|19|20)\d{2}", str(s))
            return m.group(0) if m else ""

        for c in citations_serialized:
            # Prefer year embedded in the citation string (eyecite style "(ca2 1990)", "(dcd 1987)", "(scotus 1954)")
            # over any context-derived extracted_date. This is robust for unseen documents and TOA-heavy briefs.
            try:
                raw_cit = (c.get("citation") or c.get("text") or "").toString() if False else (c.get("citation") or c.get("text") or "")
            except Exception:
                raw_cit = (c.get("citation") or c.get("text") or "")
            try:
                md = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
                my = str(md.get("year") or "").strip()
                if my.isdigit() and 1700 <= int(my) <= 2030:
                    src = str(md.get("extracted_date_source") or "")
                    if my in str(raw_cit) or src.startswith("citation_"):
                        # Force extracted_date to the embedded year so UI "Extracted from Document" is correct.
                        c["extracted_date"] = my
                        md["extracted_date_source"] = md.get("extracted_date_source") or "citation_metadata_year"
                        md["extracted_date_confidence"] = "high"
                        c["metadata"] = md
            except Exception:
                pass

            exn = c.get("extracted_case_name") or ""
            can = c.get("canonical_name") or c.get("canonical_case_name") or ""
            nex = _normalize_legal_name(exn)
            ncan = _normalize_legal_name(can)
            c["normalized_extracted_name"] = nex
            c["normalized_canonical_name"] = ncan
            eq = _names_equivalent(nex, ncan) if (nex and ncan) else False
            c["names_equivalent"] = eq
            # Only flag mismatch on strong disagreement (very low similarity and no substring)
            if nex and ncan:
                j = _jaccard(nex, ncan)
                c["name_mismatch"] = (nex not in ncan) and (ncan not in nex) and (j < 0.3)
            else:
                c["name_mismatch"] = False
            # Document-side fields: only use values extracted from the document.
            # Do NOT fall back to canonical name/date here (avoid contaminating the extracted display).
            c["submitted_display_name"] = html.unescape(exn) if str(exn).strip() else "N/A"
            _exd = str(c.get("extracted_date") or "").strip()
            c["submitted_display_date"] = _exd if _exd else "N/A"
            
            # USER FIX 2026-01-09: Map 'verified' to 'found' for UI compatibility
            # The UI checks citation.found to determine verification status
            if "verified" in c and "found" not in c:
                c["found"] = c["verified"]
            # CAPTCHA masking: if canonical appears to be 'capcha/captcha', treat as unverified with no verifying display
            if ncan and ("captcha" in ncan or ncan == "capcha"):
                try:
                    c["verified"] = False
                except Exception as captcha_err:
                    logger.debug(f"[RESPONSE] CAPTCHA masking verify reset skipped: {captcha_err}")
                # Clear canonical fields so UI won't display placeholder
                if "canonical_name" in c:
                    c["canonical_name"] = None
                if "canonical_case_name" in c:
                    c["canonical_case_name"] = None
                if "canonical_date" in c and not c.get("canonical_date"):
                    c["canonical_date"] = None
                c["verifying_display_name"] = ""
                c["error"] = c.get("error") or "captcha_blocked"
            else:
                # Clean canonical fields for API consumers
                if c.get("canonical_name"):
                    c["canonical_name"] = html.unescape(c["canonical_name"])
                if c.get("canonical_case_name"):
                    c["canonical_case_name"] = html.unescape(c["canonical_case_name"])
                c["verifying_display_name"] = html.unescape(can)
            # Normalize to year for display consistency with submitted_display_date (avoids false "Different date" when years match)
            c["verifying_display_date"] = _year_from(c.get("canonical_date")) or c.get("canonical_date") or ""
    except Exception as _e:
        logger.warning(f"[RESPONSE] Failed to add name normalization fields: {_e}")

    # Add display_base_citation, citation_score, name_similarity (backend single source of truth)
    try:
        for c in citations_serialized:
            raw = c.get("citation") or c.get("text") or ""
            c["display_base_citation"] = extract_display_base_citation(raw)
            score, name_sim = compute_citation_score_and_similarity(c)
            c["citation_score"] = score
            c["name_similarity"] = name_sim
            c["score_color"] = "text-success" if score >= 4 else ("text-warning" if score >= 2 else "text-danger")
    except Exception as _e:
        logger.warning(f"[RESPONSE] Failed to add citation display/score fields: {_e}")

    # Add progress endpoints for UI polling/streaming
    result["progress_endpoint"] = f"/casestrainer/api/analyze/progress/{request_id}"
    result["progress_stream"] = f"/casestrainer/api/analyze/progress-stream/{request_id}"

    # Prepare clusters with filtered inner citations if present (preserve objects and verified flags)
    clusters_data = result.get("clusters", [])
    # When pipeline returns citations but no clusters, build fallback clusters on backend (single source of truth)
    if not clusters_data and citations_serialized:
        try:
            clusters_data = build_fallback_clusters(citations_serialized)
            logger.info(f"[RESPONSE] Built {len(clusters_data)} fallback clusters from {len(citations_serialized)} citations")
        except Exception as _e:
            logger.warning(f"[RESPONSE] Fallback cluster build failed: {_e}")

    # Final cluster-field sync for citations: always trust the cluster objects by cluster_id.
    # This prevents stale/wrong cluster_case_name leaking onto citations when intermediate steps
    # copied a different cluster's display identity.
    try:
        cl_by_id = {
            cl.get("cluster_id"): cl
            for cl in (clusters_data or [])
            if isinstance(cl, dict) and cl.get("cluster_id")
        }
        for c in citations_serialized:
            if not isinstance(c, dict):
                continue
            cid = c.get("cluster_id")
            cl = cl_by_id.get(cid) if cid else None
            if not cl:
                continue
            if cl.get("cluster_case_name"):
                c["cluster_case_name"] = cl.get("cluster_case_name")
            if cl.get("cluster_year") is not None:
                c["cluster_year"] = cl.get("cluster_year")
            if cl.get("cluster_size") is not None:
                c["cluster_size"] = cl.get("cluster_size")
    except Exception as _e:
        logger.debug(f"[RESPONSE] cluster-field sync skipped: {_e}")

    try:

        def _filter_cluster_citations(citations_list):
            cleaned = []
            for it in citations_list or []:
                if isinstance(it, dict):
                    text = it.get("citation") or it.get("text") or ""
                    if _is_court_year_only(text):
                        continue
                    # ensure 'citation' field exists for matching
                    if not it.get("citation") and it.get("text"):
                        it["citation"] = it["text"]
                    cleaned.append(it)
                else:
                    text = str(it)
                    if _is_court_year_only(text):
                        continue
                    cleaned.append(text)
            return cleaned

        def _norm_cit(v):
            return (str(v or "")).strip()

        def _extract_cit_key(v: str) -> str:
            s = _norm_cit(v)
            try:
                m = re.search(r"\b\d+\s+[A-Za-z][A-Za-z\.\d]*\s+\d+\b", s)
                if m:
                    return m.group(0).strip()
            except Exception as key_err:
                logger.debug(f"[RESPONSE] Citation key extraction fallback used: {key_err}")
            # as-is fallback
            return s

        # build lookup from individual citations for enrichment (full and short key so cluster enrichment finds)
        _cit_lut = {}
        for c in citations_serialized:
            key = _norm_cit(c.get("citation"))
            if key:
                _cit_lut[key] = c
            short = _extract_cit_key((c.get("citation") or c.get("text")) or "")
            if short and short not in _cit_lut:
                _cit_lut[short] = c

        for cl in clusters_data:
            if isinstance(cl, dict) and "citations" in cl:
                items = _filter_cluster_citations(cl.get("citations"))
                enriched = []
                for it in items:
                    if isinstance(it, dict):
                        key = _extract_cit_key((it.get("citation") or it.get("text")) or "")
                        match = _cit_lut.get(key)
                        if match:
                            merged = dict(match)
                            # overlay original minimal fields cautiously (don't overwrite protected fields)
                            protected = {
                                "extracted_case_name",
                                "extracted_date",
                                "canonical_name",
                                "canonical_case_name",
                                "canonical_date",
                                "verified",
                                "verification_source",
                                "verification_url",
                            }
                            for k, v in it.items():
                                if v in [None, ""]:
                                    continue
                                if k in protected:
                                    # do not overwrite protected keys
                                    if not merged.get(k):
                                        merged[k] = v
                                else:
                                    merged[k] = v
                            enriched.append(merged)
                        else:
                            # ensure 'verified' key present for UI logic
                            if "verified" not in it:
                                it["verified"] = False
                            enriched.append(it)
                    else:
                        key = _extract_cit_key(it)
                        match = _cit_lut.get(key)
                        if match:
                            enriched.append(match)
                        else:
                            enriched.append({"text": key, "citation": key, "verified": False})
                cl["citations"] = enriched

                # CRITICAL FIX: Calculate cluster verified status from child citations
                # Cluster is verified if any citation is verified and has canonical_url
                any_verified = False
                best_canonical_name = None
                best_canonical_date = None
                best_canonical_url = None
                for cit in enriched:
                    if isinstance(cit, dict):
                        if is_effectively_verified_citation(cit):
                            any_verified = True
                            if cit.get("canonical_name"):
                                best_canonical_name = cit.get("canonical_name")
                                best_canonical_date = cit.get("canonical_date")
                                best_canonical_url = cit.get("canonical_url")
                # Set cluster verified flag based on child citations
                cl["verified"] = any_verified
                if best_canonical_url:
                    cl["canonical_url"] = best_canonical_url
                if best_canonical_name:
                    cl["canonical_name"] = best_canonical_name
                    cl["verifying_display_name"] = best_canonical_name
                if best_canonical_date:
                    cl["canonical_date"] = best_canonical_date

                # Do NOT propagate cluster canonical fields onto child citations.
                # That can contaminate mixed-tier clusters (e.g., F. Supp. inheriting U.S. canonical URL/name).
                # Only set citation-local display alias when the citation itself is verified with its own canonical name.
                for cit in cl["citations"]:
                    if not isinstance(cit, dict):
                        continue
                    if cit.get("verified") and cit.get("canonical_name") and cit.get("canonical_name") != "N/A":
                        cit["cluster_case_name"] = cit["canonical_name"]

        # Safety pass: enforce canonical post-cluster split rules here too, so fallback
        # clusters or response-enriched clusters cannot ship mixed court tiers.
        clusters_data = apply_post_verify_cluster_splits(
            clusters_data,
            run_id=request_id,
        )

        # Annotate mismatch flags using centralized mismatch_utils (single source of truth)
        try:
            from src.utils.mismatch_utils import annotate_mismatch_flags
            citations_flat = [c for cl in clusters_data for c in (cl.get("citations") or []) if isinstance(c, dict)]
            annotate_mismatch_flags(citations_flat, clusters_data, name_threshold=0.4, year_tolerance=0)
        except Exception as _ann:
            logger.warning(f"[FILTER] annotate_mismatch_flags failed: {_ann}")
    except Exception as _e:
        logger.warning(f"[FILTER] Failed filtering/annotating clusters: {_e}")

    # Normalize clusters to stable DTO shape (preserve enriched data)
    try:
        clusters_data = [normalize_cluster_dict(cl) if isinstance(cl, dict) else cl for cl in clusters_data]
    except Exception as _e:
        logger.warning(f"[SCHEMAS] Cluster normalization failed, using raw dicts: {_e}")

    # Last-mile response hygiene: normalize proprietary messages (dedupe runs after display finalization).
    try:
        apply_proprietary_display_fallback(citations_serialized)
        for _cl in clusters_data:
            if not isinstance(_cl, dict):
                continue
            apply_proprietary_display_fallback(_cl.get("citations") or [])
    except Exception as _e:
        logger.warning(f"[RESPONSE] Final response hygiene failed: {_e}")

    # Add cluster-level display fields and lenient equivalence for UI
    try:
        import re

        def _year_only(s):
            if not s:
                return ""
            m = re.search(r"(17|18|19|20)\d{2}", str(s))
            return m.group(0) if m else ""

        for cl in clusters_data:
            if not isinstance(cl, dict):
                continue
            cits = cl.get("citations") or []
            rep = None
            for it in cits:
                if isinstance(it, dict) and (
                    it.get("extracted_case_name") or it.get("canonical_name") or it.get("canonical_case_name")
                ):
                    rep = it
                    if it.get("verified"):
                        break
            if rep is None and cits:
                rep = cits[0] if isinstance(cits[0], dict) else None
            exn = _normalize_legal_name(rep.get("extracted_case_name") if rep else "")
            can = _normalize_legal_name((rep.get("canonical_name") or rep.get("canonical_case_name")) if rep else "")
            j = _jaccard(exn, can) if (exn and can) else 0.0
            names_eq = _names_equivalent(exn, can) if (exn and can) else False
            name_mm = False if names_eq else (exn not in can and can not in exn and j < 0.4) if (exn and can) else False
            
            # Use shared backend finalizer as single source of truth for
            # submitted/verifying display fields and unverified canonical clearing.
            finalize_cluster_for_response(
                cl,
                clean_names=False,
                clear_unverified_canonical=True,
                clear_unverified_citations=True,
            )
            # Lenient flags for UI
            cl["names_equivalent"] = names_eq
            cl["name_mismatch"] = name_mm
            cl["name_similarity"] = j

            # Backend-provided deduplicated list for display (by display_base_citation, prefer verified)
            # Enrich truncated citations (e.g. "31 Wn. App. 2") with fuller text from cluster_members
            try:
                cits = enrich_citations_with_cluster_members(
                    cl.get("citations") or [],
                    cl.get("cluster_members") or [],
                )
                cl["display_citations"] = deduplicate_cluster_citations(cits)
            except Exception:
                cl["display_citations"] = cl.get("citations") or []

        try:
            clusters_data = merge_dedupe_and_refinalize_clusters(
                clusters_data,
                clean_names=False,
                rebuild_display_citations=True,
            )
        except Exception as _dedupe_err:
            logger.warning(f"[RESPONSE] Cluster merge/dedupe after finalize failed: {_dedupe_err}")
    except Exception as _e:
        logger.warning(f"[RESPONSE] Failed to add cluster display fields: {_e}")

    # Pre-categorized cluster sections for frontend (optional: frontend can use cluster_sections or compute locally)
    cluster_sections = {}
    try:
        cluster_sections = compute_cluster_sections(clusters_data)
    except Exception as _e:
        logger.warning(f"[RESPONSE] Failed to compute cluster_sections: {_e}")

    # Best-effort: record citations count when returning a completed, successful response
    try:
        if isinstance(citations_serialized, list):
            status_flag = result.get("status", "completed")
            success_flag = bool(result.get("success", True))
            if success_flag and status_flag == "completed" and len(citations_serialized) > 0:
                record_citations(len(citations_serialized))
    except Exception as record_err:
        logger.debug(f"[RESPONSE] record_citations skipped: {record_err}")

    response_data = {
        "citations": citations_serialized,  # Move to top level
        "clusters": clusters_data,  # Move to top level
        "cluster_sections": cluster_sections,  # Pre-categorized: unverified, case_mismatch, date_mismatch, etc.
        "result": {
            "statistics": result.get("statistics", {}),
        },
        "request_id": request_id,
        "success": result.get("success", True),
        "status": result.get("status", "completed"),  # Always include status
        "metadata": {**result.get("metadata", {}), **metadata},
    }

    if "progress_data" in result:
        response_data["metadata"]["progress_data"] = result["progress_data"]

    if "task_id" in result:
        # Add task_id to both top level AND inside result for frontend compatibility
        response_data.update(
            {
                "task_id": result["task_id"],
                "status": result.get("status", "processing"),
                "message": result.get("message", "Request is being processed"),
            }
        )
        response_data["result"]["task_id"] = result["task_id"]  # Also add inside result

    for key in ["message", "warnings", "debug", "verification_status", "async_verification_queued"]:
        if key in result and key not in response_data:
            response_data[key] = result[key]

    # Perform data integrity validation before returning response
    validation_errors = _validate_api_response_data(response_data)
    if validation_errors:
        logger.error(f"[Request {request_id}] Data integrity validation failed: {validation_errors}")
        # Log the validation errors but don't fail the request - let frontend handle it
        response_data["metadata"]["validation_warnings"] = validation_errors

    log_data = copy.deepcopy(response_data)

    def safe_serialize(obj):
        """Safely serialize objects to JSON, handling custom objects"""
        # USER FIX 2024-10-21: Check to_dict() FIRST before __dict__
        # CitationResult has both, but to_dict() includes proper serialization logic
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        elif isinstance(obj, (list, tuple)):
            return [safe_serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: safe_serialize(v) for k, v in obj.items()}
        return str(obj)  # Fallback to string representation

    if "result" in log_data:
        result_data = log_data["result"]
        if "citations" in result_data:
            if len(result_data["citations"]) > 5:
                result_data["citations"] = f"[list of {len(result_data['citations'])} citations]"
            else:
                result_data["citations"] = safe_serialize(result_data["citations"])

        if "clusters" in result_data:
            if len(result_data["clusters"]) > 3:
                result_data["clusters"] = f"[list of {len(result_data['clusters'])} clusters]"
            else:
                result_data["clusters"] = safe_serialize(result_data["clusters"])

    logger.info(f"[Request {request_id}] Request completed successfully in {processing_time_ms}ms")

    if CASESTRAINER_LOG_FULL_API_RESPONSES:
        try:
            os.makedirs("/app/logs", exist_ok=True)

            serializable_data = safe_serialize(response_data)

            with open("/app/logs/frontend_api_results.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(serializable_data, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write API response to log file: {e}")

    try:
        json.dumps(response_data)
    except (TypeError, ValueError) as e:
        logger.error(f"Response contains non-serializable data: {e}")
        try:
            if "result" in response_data and response_data["result"]:
                if "citations" in response_data["result"]:
                    response_data["result"]["citations"] = [
                        cit.to_dict() if hasattr(cit, "to_dict") else safe_serialize(cit)
                        for cit in response_data["result"]["citations"]
                    ]
                if "clusters" in response_data["result"]:
                    response_data["result"]["clusters"] = [
                        {k: (v.to_dict() if hasattr(v, "to_dict") else safe_serialize(v)) for k, v in cluster.items()}
                        for cluster in response_data["result"]["clusters"]
                    ]

            json.dumps(response_data)
        except (TypeError, ValueError) as e2:
            logger.error(f"Failed to fix non-serializable data: {e2}")
            response_data = safe_serialize(response_data)

    return jsonify(response_data)


def format_analyze_error_response(message, details=None, status_code=400, request_id=None, metadata=None):
    """Format an error response with consistent structure"""
    error_data = {
        "error": message,
        "details": details or message,
        "request_id": request_id or str(uuid.uuid4()),
        "success": False,
        "citations": [],
        "clusters": [],
        "metadata": metadata or {},
    }

    if "request_id" not in error_data["metadata"] and request_id:
        error_data["metadata"]["request_id"] = request_id

    if "status" not in error_data["metadata"]:
        error_data["metadata"]["status"] = "error"

    logger.error(f"[Request {request_id or 'unknown'}] Error: {message}")
    if details and details != message:
        logger.error(f"[Request {request_id or 'unknown'}] Details: {details}")

    return jsonify(error_data), status_code
