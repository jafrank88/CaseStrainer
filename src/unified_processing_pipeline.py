#!/usr/bin/env python3
"""
UNIFIED PROCESSING PIPELINE - Consolidated citation processing architecture

This replaces the fragmented processing pathways with a single, predictable pipeline
that all requests must go through. This makes debugging and future changes much easier.

KEY IMPROVEMENTS:
1. Single entry point for all citation processing
2. Clear stage-based processing with tracing
3. Guaranteed parallel verification execution
4. Comprehensive error handling and logging
5. Predictable data flow at every stage
"""

import asyncio
import logging
import os
import re
import time
import uuid
from datetime import date
from typing import List, Dict, Any, Optional
from src.models import CitationResult
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Shared pipeline context and helpers
from src.pipeline.context import ProcessingContext, _is_statute_name, _is_generic_fallback_name
from src.pipeline.extraction import run_extract_citations
from src.pipeline.verification import run_verify_citations, run_parallel_verification
from src.pipeline.clustering import (
    merge_cluster_group,
    merge_clusters_by_canonical_name,
    split_clusters_by_canonical,
    build_clusters as pipeline_build_clusters,
)

# Import helper for filtering cluster members
from src.utils.cluster_filter import filter_cluster_members_by_reporter, remove_bogus_same_reporter_citations
from src.utils.date_utils import (
    apply_canonical_date_overrides,
    extract_year_value,
    extract_year_from_citation,
)
from src.utils.mismatch_utils import compute_cluster_mismatch_flags
from src.utils.cluster_display_utils import finalize_cluster_for_response
from src.utils.cluster_postprocess_pipeline import apply_post_verify_cluster_splits

# Centralized case-name utilities
from src.utils.case_name_utils import (
    clean_case_name_contamination,
    is_document_case_contamination_post_process,
)

# Import placeholder resolver
from src.utils.placeholder_resolver import resolve_placeholder_citations, is_placeholder_citation

# Import clustering function from correct module
try:
    from src.unified_clustering_master_optimized import cluster_citations_optimized as cluster_citations_unified_master
except ImportError:
    try:
        from src.unified_clustering_master import cluster_citations_unified_master
    except ImportError:
        cluster_citations_unified_master = None


def _get_clustering_version() -> str:
    """Return clustering version for API metadata (to verify deployed code)."""
    try:
        from src.unified_clustering_master_optimized import CLUSTERING_VERSION
        return CLUSTERING_VERSION
    except Exception:
        return "fallback"


logger = logging.getLogger(__name__)


class UnifiedProcessingPipeline:
    """
    SINGLE ENTRY POINT for all citation processing in CaseStrainer.

    This replaces the multiple fragmented pathways:
    - unified_citation_processor_v2.py -> process_text()
    - unified_input_processor.py -> process_any_input()
    - clean_extraction_pipeline.py -> extract_citations()
    - citation_extraction_endpoint.py -> extract_citations_production()

    ALL requests now go through this predictable pipeline.
    """

    def __init__(self):
        self.processor = None  # Will be created with proper config
        logger.info("[PIPELINE] Unified processing pipeline initialized")

    async def process_citations(
        self,
        text: str,
        processing_mode: str = "enhanced_sync",
        enable_parallel_verification: bool = True,
        enable_verification: bool = True,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        MAIN ENTRY POINT - Process citations through unified pipeline

        Args:
            text: Input text to process
            processing_mode: sync, async, enhanced_sync, etc.
            enable_parallel_verification: Whether to apply parallel verification
            enable_verification: Whether to enable citation verification
            trace_id: Optional trace ID for debugging

        Returns:
            Standardized response format with citations and metadata
        """
        # CRITICAL: Preprocess text BEFORE extraction to remove Cite as headers, etc.
        # Prevents "594 U.S. _ (scotus 2021)" from contaminating Milkovich (497 U.S. 1)
        logger.info(f"[PIPELINE] process_citations entered, text_len={len(text or '')}")
        from src.input_fetchers import preprocess_extracted_text
        text = preprocess_extracted_text(text or "")
        logger.info(f"[PIPELINE] preprocess done, text_len={len(text)}")

        # Create processing context for tracing
        context = ProcessingContext(
            trace_id=trace_id if trace_id is not None else str(uuid.uuid4())[:8],
            start_time=time.time(),
            input_text=text,
            processing_mode=processing_mode,
        )

        # Create processor with proper configuration
        from src.models import ProcessingConfig

        config = ProcessingConfig(enable_verification=enable_verification)
        logger.info(
            f"[PIPELINE-{context.trace_id}] DEBUG: Creating processor with enable_verification={enable_verification}"
        )
        logger.info(
            f"[PIPELINE-{context.trace_id}] DEBUG: Processor config.enable_verification = {config.enable_verification}"
        )
        self.processor = UnifiedCitationProcessorV2(config=config)

        # Store progress callback if provided (for incremental progress updates)
        if hasattr(self, "_progress_callback"):
            setattr(self.processor, "_progress_callback", self._progress_callback)
            # Also set progress_callback (used by _update_progress for Phase 5+ progress)
            self.processor.progress_callback = self._progress_callback

        # CRITICAL FIX: Extract document primary case name for contamination filtering
        from src.unified_clustering_master import UnifiedClusteringMaster

        clustering_master = UnifiedClusteringMaster()
        document_primary_case_name = clustering_master._extract_document_primary_case_name(text)

        if document_primary_case_name:
            self.processor.document_primary_case_name = document_primary_case_name


        try:
            # STAGE 1: Citation Extraction
            context.trace_stage("extraction")
            extraction_result = await self._extract_citations(text, context)
            citations = extraction_result.get("citations", [])
            if len(citations) == 0:
                # Check for citation indicators
                citation_indicators = ["U.S.", "F.", "F.2d", "F.3d", "S.Ct.", "L.Ed.", "Wn.", "Wn.2d", "P.", "P.2d", "Cal.", "N.Y.", "v.", "v "]
                found_indicators = [ind for ind in citation_indicators if ind in text]

            # DIAGNOSTIC: Track Lukumi through pipeline stages
            def _lukumi_check(label, cit_list):
                for c in cit_list:
                    ct = getattr(c, 'citation', '') if hasattr(c, 'citation') else (c.get('citation','') if isinstance(c, dict) else '')
                    if '508 U.S. 520' in ct or '508 U. S. 520' in ct:
                        logger.error(f"[LUKUMI-TRACE] {label}: FOUND - {ct[:60]}")
                        return
                logger.error(f"[LUKUMI-TRACE] {label}: NOT FOUND in {len(cit_list)} citations")
            _lukumi_check("AFTER_EXTRACTION", citations)

            # STAGE 1.5: Filter out law review/secondary source citations
            from src.citation_extractor import is_law_review_citation
            original_count = len(citations)
            citations = [c for c in citations if not is_law_review_citation(getattr(c, 'citation', str(c)))]
            filtered_count = original_count - len(citations)
            _lukumi_check("AFTER_LAW_REVIEW_FILTER", citations)

            # STAGE 2: Citation Verification (only if enabled)
            # CRITICAL FIX: process_text() already runs verification internally via UnifiedCitationProcessorV2
            # Running verification AGAIN here would overwrite verified=True with verified=False
            # if the second lookup fails (e.g., CourtListener returns 404 on direct lookup but
            # the citation was verified via CourtListener_Search in enhanced fallback)
            context.trace_stage("verification")

            # Check if verification was already done in process_text()
            already_verified_count = sum(1 for c in citations if getattr(c, 'verified', False) or getattr(c, 'true_by_parallel', False))
            logger.info(
                f"[PIPELINE-{context.trace_id}] Stage 2 verification: enable_verification={enable_verification}, "
                f"already_verified_count={already_verified_count}, total_citations={len(citations)}"
            )

            # SKIP SECOND VERIFICATION PASS - it overwrites fallback verification results!
            # process_text() already does: extraction -> verification -> clustering -> fallback
            # Running _verify_citations again would call CourtListener lookup which returns 404
            # for citations that were verified via CourtListener_Search (different API endpoint)
            if enable_verification and already_verified_count > 0:
                verified_citations = citations
                logger.info(f"[PIPELINE-{context.trace_id}] Using citations already verified in process_text (skipping duplicate verification)")
            elif enable_verification:
                logger.info(
                    f"[PIPELINE-{context.trace_id}] [OK] Verification ENABLED, running verification for {len(citations)} citations..."
                )
                courtlistener_key = os.environ.get("COURTLISTENER_API_KEY", "")
                if courtlistener_key:
                    logger.info(
                        f"[PIPELINE-{context.trace_id}] CourtListener API key configured (length: {len(courtlistener_key)})"
                    )
                else:
                    logger.warning(
                        f"[PIPELINE-{context.trace_id}] [WARNING] No CourtListener API key found! Verification may fail."
                    )
                verified_citations = await self._verify_citations(citations, text, context)
            else:
                logger.warning(
                    f"[PIPELINE-{context.trace_id}] [OFF] Verification DISABLED, skipping verification for {len(citations)} citations"
                )
                verified_citations = citations

            # STAGE 3: Parallel Verification (CRITICAL - ALWAYS EXECUTED)
            if enable_parallel_verification and len(verified_citations) > 1:
                context.trace_stage("parallel_verification")
                parallel_citations = await self._apply_parallel_verification(verified_citations, context)
                citations = parallel_citations
            else:
                citations = verified_citations

            # STAGE 4: Final Formatting
            context.trace_stage("formatting")
            _lukumi_check("BEFORE_FORMAT_RESPONSE", citations)
            result = await self._format_response(citations, context)
            _lukumi_check("AFTER_FORMAT_RESPONSE", result.get('citations', []))

            # SUCCESS - Complete processing
            context.trace_stage("completed")
            elapsed = time.time() - context.start_time

            return result

        except Exception as e:
            logger.error(f"[PIPELINE-{context.trace_id}] PIPELINE EXCEPTION: {e}", exc_info=True)
            context.add_error(str(e), "pipeline_error")
            return self._format_error_response(context, str(e))

    async def _extract_citations(self, text: str, context: ProcessingContext) -> Dict[str, Any]:
        """Stage 1: Extract citations using the clean pipeline"""
        return await run_extract_citations(self.processor, text, context)

    async def _verify_citations(
        self, citations: List[CitationResult], text: str, context: ProcessingContext
    ) -> List[CitationResult]:
        """Stage 2: Verify citations and get canonical data with timeout protection"""
        return await run_verify_citations(self.processor, citations, text, context)

    async def _apply_parallel_verification(
        self, citations: List[CitationResult], context: ProcessingContext
    ) -> List[CitationResult]:
        """Stage 3: Apply parallel verification - GUARANTEED EXECUTION"""
        return await run_parallel_verification(self.processor, citations, context)

    async def _format_response(self, citations: List[CitationResult], context: ProcessingContext) -> Dict[str, Any]:
        """Stage 4: Format final response using clustering master"""
        try:
            # CRITICAL FIX: Use the clustering master instead of building simple clusters
            # Convert citations to dicts for clustering master
            citation_dicts = []

            # Get document primary case name for contamination filtering
            document_primary_case_name = getattr(self.processor, "document_primary_case_name", None)

            names_at_format = sum(
                1 for cit in citations
                if (getattr(cit, "extracted_case_name", None) or "").strip() not in ("", "N/A")
            )
            logger.info(
                f"[NAME-DIAG] _format_response: {names_at_format}/{len(citations)} citations have non-N/A extracted_case_name on CitationResult"
            )
            for cit in citations:
                cit_dict = cit.to_dict()
                # Ensure document-extracted fields are always present (never null/missing) for frontend display
                if cit_dict.get("extracted_case_name") is None or cit_dict.get("extracted_case_name") == "":
                    cit_dict["extracted_case_name"] = "N/A"
                if cit_dict.get("extracted_date") is None or cit_dict.get("extracted_date") == "":
                    cit_dict["extracted_date"] = "N/A"

                if "extracted_case_name" in cit_dict:
                    original_name = cit_dict["extracted_case_name"]
                    canonical_name = cit_dict.get("canonical_name")
                    cleaned_name = clean_case_name_contamination(original_name, canonical_name or "")
                    
                    # CRITICAL FIX: Strip citation signal phrases like "See", "See also", etc.
                    # These should never appear in extracted case names
                    signal_phrase_patterns = [
                        r"^See,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," or "See e.g.," or "See, e.g"
                        r"^See\s+also\s+",  # "See also"
                        r"^See\s+generally\s+",  # "See generally"
                        r"^But\s+see\s+",  # "But see"
                        r"^See\s+",  # "See " (standalone signal word)
                        r"^Accord\s+",  # "Accord "
                        r"^Compare\s+",  # "Compare "
                        r"^Cf\.?\s+",  # "Cf."
                        r"^E\.?g\.?\s*,?\s*",  # "E.g.,"
                        r"^I\.?e\.?\s*,?\s*",  # "I.e.,"
                    ]
                    
                    if cleaned_name and cleaned_name != "N/A":
                        original_cleaned = cleaned_name
                        for pattern in signal_phrase_patterns:
                            cleaned_name = re.sub(pattern, "", cleaned_name, flags=re.IGNORECASE).strip()
                        
                    
                    # CRITICAL FIX: Also strip signal phrases from canonical_name if present
                    # Sometimes APIs or cluster data might include signal phrases
                    if canonical_name and canonical_name != "N/A":
                        original_canonical = canonical_name
                        for pattern in signal_phrase_patterns:
                            canonical_name = re.sub(pattern, "", canonical_name, flags=re.IGNORECASE).strip()
                        
                        if canonical_name != original_canonical:
                            cit_dict["canonical_name"] = canonical_name

                    # CRITICAL FIX: When extraction fails (N/A or generic fallback) but verification succeeded,
                    # use canonical_name as extracted_case_name for better user experience
                    # This prevents showing "N/A" or "U.S. Supreme Court Case" when we actually know the case name
                    if _is_generic_fallback_name(cleaned_name) and canonical_name and canonical_name != "N/A":
                        logger.info(
                            f"[FORMAT-RESPONSE] Using canonical_name '{canonical_name}' as extracted_case_name "
                            f"(extraction returned '{cleaned_name}' which is generic fallback)"
                        )
                        cleaned_name = canonical_name
                        cit_dict["extraction_used_canonical"] = True  # Flag that we fell back to canonical

                    # CRITICAL: Final header pattern check before returning results
                    if cleaned_name and cleaned_name != "N/A":
                        cleaned_name_upper = cleaned_name.upper()
                        has_et_al = "ET AL" in cleaned_name_upper or "ETAL" in cleaned_name_upper.replace(
                            " ", ""
                        ).replace(".", "").replace(",", "")
                        has_role_word = any(
                            role in cleaned_name_upper
                            for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                        )
                        has_no = (
                            "NO." in cleaned_name_upper
                            or " NO " in cleaned_name_upper
                            or cleaned_name_upper.endswith(" NO")
                        )
                        header_pattern_match = re.search(
                            r"ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                            cleaned_name_upper,
                        )

                        if (has_et_al and has_role_word) or (has_role_word and has_no) or header_pattern_match:
                            logger.error(
                                f"[FORMAT-RESPONSE] FINAL REJECTION: Header pattern detected in '{cleaned_name}' for citation '{cit_dict.get('citation', 'unknown')}' - setting to N/A"
                            )
                            cleaned_name = "N/A"

                    # USER FIX: Reject fragment extractions like "Inc v. Montgomery"
                    if cleaned_name and cleaned_name != "N/A":
                        fragment_match = re.match(
                            r"^(Inc\.?|Corp\.?|LLC|L\.L\.C\.|Ltd\.?|Co\.?|Ass\'?n|Assoc\.?|Org\.?)\s+v\.?\s+",
                            cleaned_name,
                            re.IGNORECASE,
                        )
                        if fragment_match:
                            logger.error(
                                f"[FORMAT-RESPONSE] FRAGMENT REJECTION: '{cleaned_name}' starts with company suffix - using canonical or N/A"
                            )
                            if canonical_name and canonical_name != "N/A":
                                cleaned_name = canonical_name
                                cit_dict["fragment_fixed"] = True
                            else:
                                cleaned_name = "N/A"

                    # Reject quote/sentence misidentified as case name (e.g. "Time and again, the Supreme Court has said no")
                    if cleaned_name and cleaned_name != "N/A":
                        _ecn = cleaned_name.strip()
                        if " v. " not in _ecn and (len(_ecn) > 50 or re.match(r"^(Time\s+and|The\s+|And\s+|However,|Moreover,)", _ecn, re.IGNORECASE) or " the " in _ecn):
                            logger.info(
                                f"[FORMAT-RESPONSE] QUOTE REJECTION: Replacing quote-like name with N/A: '{_ecn[:50]}...'"
                            )
                            cleaned_name = "N/A"
                        elif " v. " in _ecn:
                            _left = _ecn.split(" v. ", 1)[0].strip()
                            if len(_left) > 45 or re.match(r"^(Time\s+and|The\s+|And\s+)", _left, re.IGNORECASE) or (" the " in _left and len(_left) > 25):
                                logger.info(
                                    f"[FORMAT-RESPONSE] QUOTE REJECTION: Replacing prose+case name with N/A: '{_ecn[:50]}...'"
                                )
                                cleaned_name = "N/A"

                    # CRITICAL: Check for document primary case contamination on ALL citations
                    # The primary case name can appear in headers/footers on any page, not just the beginning
                    if cleaned_name and cleaned_name != "N/A" and document_primary_case_name:
                        is_contaminated = is_document_case_contamination_post_process(
                            cleaned_name, document_primary_case_name
                        )
                        if is_contaminated:
                            logger.error(
                                f"[POST-PROCESS-CONTAMINATION] [REJECT] REJECTING contaminated name '{cleaned_name}' for citation '{cit_dict.get('citation', 'unknown')}' (matches document primary '{document_primary_case_name}')"
                            )
                            logger.info(
                                f"[POST-PROCESS-CONTAMINATION] Setting to N/A (canonical_name='{canonical_name}' available but not used per data separation rule)"
                            )
                            cleaned_name = "N/A"

                    # CRITICAL: Do NOT replace extracted_case_name with canonical_name
                    # This was previously causing contamination by overwriting extracted data with canonical data
                    # Instead, just flag the mismatch - the comparison logic will handle it properly
                    # The extracted_case_name must ONLY come from document extraction
                    if cleaned_name and cleaned_name != "N/A" and canonical_name and canonical_name != "N/A":
                        from src.utils.mismatch_utils import names_equivalent
                        equiv = names_equivalent(
                            cleaned_name, canonical_name,
                            verified=bool(cit_dict.get("verified")),
                            canonical_url=cit_dict.get("canonical_url"),
                        )
                        if not equiv:
                            # Log the mismatch but do NOT overwrite extracted with canonical
                            logger.info(
                                f"[DATA-SEPARATION] Extracted '{cleaned_name}' differs from canonical '{canonical_name}' - keeping both separate"
                            )
                            cit_dict["name_mismatch"] = True
                        else:
                            cit_dict["name_mismatch"] = False

                    # CRITICAL FIX: Apply soft hyphen normalization to extracted_case_name
                    # This fixes "Swin dle" -> "Swindle" and similar soft hyphen artifacts
                    if cleaned_name and cleaned_name != "N/A":
                        from src.utils.text_normalizer import normalize_case_name
                        cleaned_name = normalize_case_name(cleaned_name)

                    cit_dict["extracted_case_name"] = cleaned_name

                # CRITICAL FIX: Set verified=True if citation has canonical_url but verified=False
                # This fixes Chalkley and similar citations that have URLs but are marked unverified
                if cit_dict.get("canonical_url") and not cit_dict.get("verified"):
                    cit_dict["verified"] = True
                    cit_dict["is_verified"] = True
                    logger.info(f"[VERIFICATION-FIX] Set verified=True for {cit_dict.get('citation')} (has canonical_url)")

                # Add processing metadata
                cit_dict["processing_trace_id"] = context.trace_id
                cit_dict["processing_stages"] = context.stages_completed
                citation_dicts.append(cit_dict)

            # Handle aff'd/affirmed/reversed citations - these use the PRECEDING case name
            # but are treated as DIFFERENT cases (appellate history of the same underlying dispute)
            # CRITICAL: Do NOT contaminate extracted data with canonical data or vice versa
            previous_case_name = None
            for i, cit_dict in enumerate(citation_dicts):
                cit_dict.get("extracted_case_name")
                ext_year = cit_dict.get("extracted_date") or cit_dict.get("extracted_year")

                # Check if this citation is preceded by appellate history indicators
                cit_pos = cit_dict.get("start_index", 0)
                appellate_history_type = None
                if cit_pos and cit_pos > 10:
                    context_before = context.input_text[max(0, cit_pos - 50) : cit_pos].lower()

                    # Detect specific appellate history type using word boundaries
                    # CRITICAL: Use regex to avoid false positives like "reaffirmed" matching "affirmed"
                    # Only match standalone appellate history signals, typically preceded by comma
                    if re.search(r",\s*aff'?d\b", context_before) or re.search(r",\s*affirmed\b", context_before):
                        appellate_history_type = "affirmed"
                    elif re.search(r",\s*rev'?d\b", context_before) or re.search(r",\s*reversed\b", context_before):
                        appellate_history_type = "reversed"
                    elif re.search(r",\s*vacated\b", context_before):
                        appellate_history_type = "vacated"
                    elif re.search(r",\s*remanded\b", context_before):
                        appellate_history_type = "remanded"
                    elif re.search(r",\s*cert\.?\s*denied\b", context_before):
                        appellate_history_type = "cert_denied"
                    elif re.search(r",\s*cert\.?\s*granted\b", context_before):
                        appellate_history_type = "cert_granted"

                    if appellate_history_type and previous_case_name and previous_case_name != "N/A":
                        # Use previous case name but mark as DIFFERENT case (appellate history)
                        cit_dict["extracted_case_name"] = previous_case_name
                        cit_dict["is_appellate_history"] = True
                        cit_dict["appellate_history_type"] = appellate_history_type
                        cit_dict["appellate_of_citation"] = citation_dicts[i - 1].get("citation") if i > 0 else None
                        # Extract year from THIS citation's context (may differ from original case)
                        if not ext_year:
                            # Try to extract year from context after this citation
                            after_context = context.input_text[cit_pos : cit_pos + 100]
                            year_match = re.search(r"\((\d{4})\)", after_context)
                            if year_match:
                                cit_dict["extracted_date"] = year_match.group(1)
                                cit_dict["extracted_year"] = year_match.group(1)
                        logger.info(
                            f"[APPELLATE-HISTORY] Citation {cit_dict.get('citation')} is {appellate_history_type} of '{previous_case_name}'"
                        )
                        # Don't continue - still need to track this case name

                # CRITICAL: Do NOT set extracted_case_name from canonical_name
                # extracted data must remain purely from document extraction
                # If extraction failed, leave as N/A - this is honest data

                # Track previous case name for appellate history handling
                current_name = cit_dict.get("extracted_case_name")
                current_year = cit_dict.get("extracted_date") or cit_dict.get("extracted_year")
                if current_name and current_name != "N/A":
                    previous_case_name = current_name
                if current_year:
                    pass

            # CRITICAL FIX: Annotate mismatch flags BEFORE clustering
            # This ensures name_mismatch and date_mismatch are properly set for all citations
            try:
                from src.utils.mismatch_utils import annotate_mismatch_flags

                # Create empty clusters list for now - will be populated by clustering master
                # NOTE: Threshold lowered from 0.6 to 0.4 to reduce false positives
                annotate_mismatch_flags(citation_dicts, [], name_threshold=0.4, year_tolerance=0)
                logger.info(
                    f"[PIPELINE-{context.trace_id}] Annotated mismatch flags for {len(citation_dicts)} citations"
                )
            except Exception as e:
                pass

            # CRITICAL FIX: Remove placeholder citations from Cite as context BEFORE clustering
            # "594 U.S. _ (scotus 2021)" from page headers must not be clustered with Milkovich (497 U.S.)
            def _is_cite_as_header_placeholder(cit: dict) -> bool:
                if not is_placeholder_citation(cit.get("citation", "") or ""):
                    return False
                ctx = (cit.get("context") or "") + (cit.get("citation", "") or "")
                return bool(re.search(r"Cite\s+as", ctx, re.IGNORECASE))
            cite_as_placeholders = [c for c in citation_dicts if _is_cite_as_header_placeholder(c)]
            if cite_as_placeholders:
                citation_dicts = [c for c in citation_dicts if not _is_cite_as_header_placeholder(c)]
                logger.info(f"[CITE-AS-FILTER] Removed {len(cite_as_placeholders)} placeholder citations from Cite as headers")

            # Use clustering master to get proper clusters with all required fields
            # CRITICAL FIX: Ensure clusters are always returned, even if clustering fails
            clusters = []
            clustering_source = "unknown"
            try:
                pass

                if cluster_citations_unified_master is None:
                    logger.error(f"[CLUSTERING-TRACE] cluster_citations_unified_master is None, using fallback")
                    clustering_source = "fallback_parallel_citations"
                    clusters = self._create_clusters_from_parallel_citations(citation_dicts)
                else:
                    logger.error(
                        f"[CLUSTERING-TRACE] Calling cluster_citations_unified_master with {len(citation_dicts)} citations"
                    )
                    # CRITICAL FIX: Must pass enable_verification=True to preserve verified flag
                    # Even though citations are "already verified", the clustering master needs this flag
                    # to preserve canonical data on verified citations (otherwise it clears them)
                    clusters = cluster_citations_unified_master(
                        citation_dicts, original_text=context.input_text, enable_verification=True  # Preserve verified flag
                    )
                    if not clusters:
                        logger.error(
                            f"[CLUSTERING-TRACE] cluster_citations_unified_master returned empty, using fallback"
                        )
                        clustering_source = "fallback_parallel_citations"
                        clusters = self._create_clusters_from_parallel_citations(citation_dicts)
                    else:
                        clustering_source = "unified_master"
                        logger.error(
                            f"[CLUSTERING-TRACE] cluster_citations_unified_master returned {len(clusters)} clusters"
                        )
            except Exception as e:
                logger.error(f"[CLUSTERING-TRACE] Clustering failed with exception: {e}", exc_info=True)
                clustering_source = "fallback_parallel_citations"
                # Create fallback: build clusters from parallel_citations metadata
                clusters = self._create_clusters_from_parallel_citations(citation_dicts)

            # SAFETY NET: If we have citations but 0 clusters (e.g. clustering returned []), force fallback
            if citation_dicts and not clusters:
                logger.warning(
                    f"[CLUSTERING-TRACE] Had {len(citation_dicts)} citations but 0 clusters - forcing fallback"
                )
                clustering_source = "fallback_parallel_citations_forced"
                clusters = self._create_clusters_from_parallel_citations(citation_dicts)

            logger.info(f"[CLUSTERING-TRACE] Final source: {clustering_source}, clusters: {len(clusters)}")
            # DEBUG: Log first cluster's fields
            if clusters:
                first = clusters[0]
                logger.info(f"[CLUSTERING-TRACE] First cluster keys: {list(first.keys())}")
                logger.info(f"[CLUSTERING-TRACE] First cluster canonical_name: {first.get('canonical_name')}")
                logger.info(f"[CLUSTERING-TRACE] First cluster verified: {first.get('verified')}")

            # CRITICAL FIX: Ensure cluster's verified flag is set correctly based on citations
            for cluster in clusters:
                if isinstance(cluster, dict):
                    # Clusters may have either "citations" or "citation_objects" (or both)
                    citations = cluster.get("citations", []) or cluster.get("citation_objects", [])
                    
                    def is_citation_verified(cit):
                        """Check if a citation is verified, handling both dict and object formats."""
                        if isinstance(cit, dict):
                            return cit.get("verified", False) or cit.get("is_verified", False)
                        else:
                            # Handle CitationResult objects
                            return getattr(cit, "verified", False) or getattr(cit, "is_verified", False)
                    
                    cluster_verified = any(is_citation_verified(cit) for cit in citations if cit)
                    cluster["verified"] = cluster_verified

            # FIX DEC 2025: ALWAYS merge clusters with same canonical_name to reduce duplicates
            # This catches cases like Clarke v. Tri-Cities appearing 4 times
            clusters = self._merge_clusters_by_canonical_name(clusters)
            # Split any cluster that mixes different canonical cases (e.g. Davis/2008 + Meese/1987)
            clusters = self._split_clusters_by_canonical(clusters)
            # Apply post-verify structural splits (court-tier/WL/canonical) consistently in sync path.
            clusters = self._apply_post_verify_cluster_splits(clusters, trace_id=context.trace_id)
            context.metadata["cluster_count"] = len(clusters)

            # CRITICAL FIX: Resolve placeholder citations by matching to verified citations
            # Placeholders (e.g., "594 U.S. ____") are matched based on case name + year similarity
            logger.info(f"[PLACEHOLDER-RESOLUTION] Starting resolution for {len(citation_dicts)} citations")
            citation_dicts = resolve_placeholder_citations(citation_dicts)
            
            # Update clusters after placeholder resolution
            # Only remove UNRESOLVED placeholders from clusters; keep resolved ones
            placeholder_citations = [c for c in citation_dicts if is_placeholder_citation(c.get('citation', ''))]
            unresolved_placeholders = [c for c in placeholder_citations if not c.get('verified', False)]
            if placeholder_citations:
                resolved_count = len(placeholder_citations) - len(unresolved_placeholders)
                logger.info(f"[PLACEHOLDER-RESOLUTION] {len(placeholder_citations)} placeholders total, {resolved_count} resolved, {len(unresolved_placeholders)} unresolved")
                
                def _is_unresolved_placeholder(cit_text):
                    """Check if citation is an unresolved placeholder (should be removed from clusters)."""
                    ct = cit_text if isinstance(cit_text, str) else cit_text.get('citation', '') if isinstance(cit_text, dict) else str(cit_text)
                    if not is_placeholder_citation(ct):
                        return False
                    # Check if this placeholder was resolved (has case name with v. in text or ecn)
                    if isinstance(cit_text, str) and 'v.' in cit_text:
                        return False
                    if isinstance(cit_text, dict):
                        ecn = cit_text.get('extracted_case_name', '') or ''
                        if ecn and ecn != 'N/A' and 'v.' in ecn:
                            return False
                        if cit_text.get('verified', False):
                            return False
                    return True
                
                # Only remove unresolved placeholders from clusters
                for cluster in clusters:
                    if 'cluster_members' in cluster:
                        cluster['cluster_members'] = [
                            m for m in cluster['cluster_members'] 
                            if not _is_unresolved_placeholder(m.get('citation', '') if isinstance(m, dict) else m)
                        ]
                        cluster['cluster_size'] = len(cluster['cluster_members'])
                    if 'citations' in cluster:
                        cluster['citations'] = [
                            c for c in cluster['citations']
                            if not _is_unresolved_placeholder(c.get('citation', '') if isinstance(c, dict) else c)
                        ]

            # CRITICAL FIX: Annotate mismatch flags AGAIN after clustering
            # This updates cluster-level mismatch flags (has_name_mismatch, has_date_mismatch, mismatch_indices)
            try:
                from src.utils.mismatch_utils import annotate_mismatch_flags

                # NOTE: Threshold lowered from 0.6 to 0.4 to reduce false positives
                annotate_mismatch_flags(citation_dicts, clusters, name_threshold=0.4, year_tolerance=0)
                logger.info(
                    f"[PIPELINE-{context.trace_id}] Updated cluster-level mismatch flags for {len(clusters)} clusters"
                )
            except Exception as e:
                logger.warning(
                    f"[PIPELINE-{context.trace_id}] Failed to update cluster mismatch flags: {e}", exc_info=True
                )

            # FILTER: Remove Id. and short-form citations from clusters
            def should_filter_citation(citation_text):
                """Check if citation should be filtered out"""
                if not citation_text:
                    return True
                # Filter Id. citations
                if citation_text.lower() == "id." or citation_text.lower().startswith("id."):
                    return True
                # FIX 2026-02-05: Filter short-form citations (e.g., "346 F.R.D. at 105")
                # BUT: Keep full citations with pin cites like "481 U. S. 465, 473 (1987)"
                if " at " in citation_text:
                    # Check for year parenthesis - indicates full citation with pin cite
                    has_year = re.search(r'\(\d{4}\)', citation_text)
                    # Check for case name pattern
                    has_case_name = bool(re.search(r'\bv\.?\s*\w', citation_text, re.IGNORECASE))
                    # Only filter if no year AND no case name (true short-form)
                    if not has_year and not has_case_name:
                        return True
                # Filter citation object representations
                if "IdCitation(" in str(citation_text) or "ShortCaseCitation(" in str(citation_text):
                    return True
                # Filter law journals and law reviews
                import re
                law_journal_pattern = r'\b\d+\s+[A-Z][a-z]*\.?\s*(L\.J\.|Law\s+Rev\.|L\.\s*Rev\.|J\.|Rev\.)\s+\d+'
                if re.search(law_journal_pattern, citation_text, re.IGNORECASE):
                    return True
                return False
            
            # Filter citations within each cluster
            filtered_clusters = []
            for cluster in clusters:
                # Filter the citations list
                if "citations" in cluster and cluster["citations"]:
                    filtered_citations = [
                        cit for cit in cluster["citations"]
                        if not should_filter_citation(cit.get("citation", ""))
                    ]
                    cluster["citations"] = filtered_citations
                    
                # Filter the cluster_members list
                if "cluster_members" in cluster and cluster["cluster_members"]:
                    filtered_members = [
                        member for member in cluster["cluster_members"]
                        if not should_filter_citation(member.get("citation", "") if isinstance(member, dict) else member)
                    ]
                    cluster["cluster_members"] = filtered_members
                    cluster["cluster_size"] = len(filtered_members)
                
                # Only keep clusters that have citations left after filtering
                if cluster.get("citations") or cluster.get("cluster_members"):
                    filtered_clusters.append(cluster)
            
            clusters = filtered_clusters

            # FILTER: Also remove Id. and short-form citations from the main citations list
            original_count = len(citation_dicts)
            citation_dicts = [
                cit for cit in citation_dicts
                if not should_filter_citation(cit.get("citation", ""))
            ]

            # Create single-citation clusters for unclustered citations with valid ecn
            # This ensures slip opinions like "584 U. S. ___, ___" (Oil States) get their own cluster
            def _norm_ct(s):
                """Normalize citation text for comparison (collapse whitespace, strip)."""
                return re.sub(r"\s+", " ", s).strip() if s else ""

            clustered_citations = set()
            clustered_citations_norm = set()  # normalized versions for fuzzy matching
            for cluster in clusters:
                for member in cluster.get("cluster_members", []):
                    ct = member.get("citation", "") if isinstance(member, dict) else (member if isinstance(member, str) else str(member))
                    if ct:
                        clustered_citations.add(ct)
                        clustered_citations_norm.add(_norm_ct(ct))
                for cit in cluster.get("citations", []):
                    if isinstance(cit, dict):
                        ct = cit.get("citation", "")
                    else:
                        ct = getattr(cit, "citation", "")
                    if ct:
                        clustered_citations.add(ct)
                        clustered_citations_norm.add(_norm_ct(ct))

            for cit_dict in citation_dicts:
                ct = cit_dict.get("citation", "")
                ecn = cit_dict.get("extracted_case_name", "") or ""
                ct_norm = _norm_ct(ct)
                if ct and ct not in clustered_citations and ct_norm not in clustered_citations_norm and ecn and ecn != "N/A" and " v. " in ecn:
                    logger.info(f"[ORPHAN-CLUSTER] Creating orphan for: {ct[:60]} ecn={ecn[:40]}")
                    # When canonical URL exists, use only canonical_date for cluster_year (never extracted_date)
                    orphan_year = cit_dict.get("canonical_date") if cit_dict.get("canonical_url") else (cit_dict.get("canonical_date") or cit_dict.get("extracted_date", ""))
                    new_cluster = {
                        "cluster_id": f"cluster_orphan_{len(clusters) + 1}",
                        "cluster_key": ct,
                        "cluster_case_name": ecn,
                        "cluster_year": orphan_year,
                        "submitted_display_name": ecn,
                        "extracted_case_name": ecn,
                        "canonical_name": cit_dict.get("canonical_name", ""),
                        "canonical_url": cit_dict.get("canonical_url", ""),
                        "canonical_date": cit_dict.get("canonical_date", ""),
                        "extracted_date": cit_dict.get("extracted_date", ""),
                        "verified": cit_dict.get("verified", False),
                        "verification_status": "verified" if cit_dict.get("verified", False) else "unverified",
                        "cluster_members": [ct],
                        "size": 1,
                        "cluster_size": 1,
                        "citations": [cit_dict],
                        "confidence": 1.0,
                        "metadata": {},
                    }
                    clusters.append(new_cluster)
                    clustered_citations.add(ct)
                    logger.info(f"[ORPHAN-CLUSTER] Created cluster for unclustered citation: {ct[:50]} ecn={ecn[:40]}")

            # SECOND MERGE: Orphan clusters may duplicate existing clusters when citation
            # text strings don't exactly match cluster_members.  Re-run merge to fix.
            clusters = self._merge_clusters_by_canonical_name(clusters)
            clusters = self._apply_post_verify_cluster_splits(clusters, trace_id=context.trace_id)

            # Build citation to cluster mapping (exact + normalized keys)
            citation_to_cluster = {}
            for i, cluster in enumerate(clusters):
                for member in cluster.get("cluster_members", []):
                    citation_key = member.get("citation", "") if isinstance(member, dict) else member
                    if citation_key:
                        citation_to_cluster[citation_key] = i
                        citation_to_cluster[_norm_ct(citation_key)] = i
                for cit in cluster.get("citations", []):
                    if isinstance(cit, dict):
                        ct = cit.get("citation", "")
                    else:
                        ct = getattr(cit, "citation", "")
                    if ct:
                        citation_to_cluster[ct] = i
                        citation_to_cluster[_norm_ct(ct)] = i

            # Update citations with cluster information
            for cit_dict in citation_dicts:
                cluster_index = citation_to_cluster.get(cit_dict["citation"]) or citation_to_cluster.get(_norm_ct(cit_dict["citation"]))
                if cluster_index is not None:
                    # Add cluster information from clustering master
                    cluster = clusters[cluster_index]
                    # CRITICAL FIX: Use the cluster's original ID instead of generating a new one
                    # This preserves spatial_* and spatial_split_* IDs from spatial clustering
                    cit_dict["cluster_id"] = cluster.get("cluster_id", f"cluster_{cluster_index + 1}")
                    cluster_case_name = cluster.get("cluster_case_name")
                    
                    # USER FIX 2026-01-12: Reject contaminated cluster_case_name (newlines, excessive length)
                    # This prevents "Ibid.\n\nThese statements..." from being copied to citations
                    if cluster_case_name and ("\n" in cluster_case_name or len(cluster_case_name) > 200):
                        logger.warning(f"[CLUSTER-COPY-CONTAMINATION] Rejecting contaminated cluster_case_name: '{cluster_case_name[:50]}...'")
                        # Try to get a clean name from the cluster's citations
                        cluster_citations = cluster.get("citations", [])
                        clean_name = None
                        for cit in cluster_citations:
                            if isinstance(cit, dict):
                                name = cit.get("canonical_name") or cit.get("extracted_case_name")
                                if name and "\n" not in name and len(name) <= 200:
                                    clean_name = name
                                    break
                        cluster_case_name = clean_name or "N/A"
                        logger.warning(f"[CLUSTER-COPY-CONTAMINATION] Replaced with: '{cluster_case_name}'")
                        # CRITICAL: Update the cluster object itself so the clusters section uses the clean name
                        cluster["cluster_case_name"] = cluster_case_name
                    
                    # CRITICAL FIX: Strip signal phrases from cluster_case_name before assigning
                    # The clustering master may include signal phrases like "See", "Cf.", etc.
                    if cluster_case_name and cluster_case_name != "N/A":
                        signal_phrase_patterns = [
                            r"^See,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," or "See e.g.," or "See, e.g"
                            r"^See\s+also\s+",  # "See also"
                            r"^See\s+generally\s+",  # "See generally"
                            r"^But\s+see\s+",  # "But see"
                            r"^See\s+",  # "See " (standalone signal word)
                            r"^Accord\s+",  # "Accord "
                            r"^Compare\s+",  # "Compare "
                            r"^Cf\.?\s+",  # "Cf."
                            r"^E\.?g\.?\s*,?\s*",  # "E.g.,"
                            r"^I\.?e\.?\s*,?\s*",  # "I.e.,"
                        ]
                        original_name = cluster_case_name
                        for pattern in signal_phrase_patterns:
                            cluster_case_name = re.sub(pattern, "", cluster_case_name, flags=re.IGNORECASE).strip()
                    
                    # USER FIX 2026-02-03: DO NOT overwrite cluster_case_name with canonical_name
                    # This prevents contamination when verification APIs return wrong cases
                    # Example: 592 U.S. ___ should be "Uzuegbunam v. Preczewski", not "Trump v. Useche" from CaseMine
                    # Keep the original cluster_case_name from spatial clustering or extracted data
                    cit_dict["cluster_case_name"] = cluster_case_name
                    
                    # CRITICAL FIX: Log potential contamination for debugging
                    if (cit_dict.get("verified") and 
                        cit_dict.get("canonical_name") and 
                        cit_dict.get("canonical_name") != "N/A" and
                        cit_dict.get("extracted_case_name") and
                        cit_dict.get("extracted_case_name") != "N/A"):
                        
                        extracted_clean = cit_dict["extracted_case_name"].strip().lower()
                        canonical_clean = cit_dict["canonical_name"].strip().lower()
                        
                        # Check if names are completely different (possible wrong verification)
                        if (extracted_clean not in canonical_clean and 
                            canonical_clean not in extracted_clean and
                            len(extracted_clean) > 10 and len(canonical_clean) > 10):
                            
                            logger.warning(
                                f"[CONTAMINATION-BLOCK] Blocked name contamination: "
                                f"extracted='{cit_dict['extracted_case_name']}' vs "
                                f"canonical='{cit_dict['canonical_name']}' for {cit_dict.get('citation', 'unknown')}"
                            )
                    cit_dict["cluster_year"] = cluster.get("cluster_year")
                    cit_dict["cluster_size"] = cluster.get("cluster_size")
                    # CRITICAL: Derive cluster_members from this cluster's citations only (avoids Amcast/Cintas cross-assignment)
                    cluster_cits = cluster.get("citations", []) or cluster.get("citation_objects", [])
                    cluster_member_texts = []
                    for c in cluster_cits:
                        ct = c.get("citation", "") if isinstance(c, dict) else (getattr(c, "citation", None) or "")
                        if ct:
                            cluster_member_texts.append(str(ct))
                    cit_text = cit_dict.get("citation", "") or ""
                    cit_dict["cluster_members"] = [m for m in cluster_member_texts if m != cit_text]
                    cit_dict["is_in_cluster"] = True
                else:
                    cit_dict["cluster_id"] = None
                    cit_dict["cluster_case_name"] = None
                    cit_dict["cluster_year"] = None
                    cit_dict["cluster_size"] = 1
                    cit_dict["cluster_members"] = []
                    cit_dict["is_in_cluster"] = False

            # USER FIX 2026-01-12: Final cleanup - ensure all clusters have clean cluster_case_name
            # This is needed because the clusters section reads from the original cluster objects
            # USER FIX 2026-02-03: When all citations in a cluster have the same verified canonical_name,
            # use that for cluster_case_name so we never show the wrong case (e.g. Simon under TransUnion).
            logger.info(f"[CLUSTER-FINAL-CLEANUP] Starting cleanup for {len(clusters)} clusters")
            for i, cluster in enumerate(clusters):
                cluster_case_name = cluster.get("cluster_case_name")
                canonical_name = cluster.get("canonical_name")
                extracted_name = cluster.get("extracted_name")
                # Prefer common verified canonical_name over region/extracted name
                cluster_citations = cluster.get("citations", [])
                common_canonical = None
                common_canonical_url = None
                for cit in cluster_citations:
                    if not isinstance(cit, dict):
                        continue
                    if cit.get("verified") and cit.get("canonical_name") and cit.get("canonical_name") != "N/A":
                        cn = (cit.get("canonical_name") or "").strip().lower()
                        if common_canonical is None:
                            common_canonical = cit.get("canonical_name")
                            common_canonical_url = cit.get("canonical_url") or cit.get("url")
                        elif cn != (common_canonical or "").strip().lower():
                            common_canonical = None
                            common_canonical_url = None
                            break
                # USER FIX 2026-02-03: DO NOT overwrite cluster_case_name with common canonical_name
                # EXCEPTION: When cluster_case_name is truncated (e.g. "Corporation v. Detrex Corporation")
                # and we have verified canonical_name, use canonical to fix Amcast-style truncation.
                if common_canonical:
                    from src.utils.cluster_display_utils import _looks_truncated_extracted_name
                    if cluster_case_name and _looks_truncated_extracted_name(cluster_case_name):
                        cluster["cluster_case_name"] = common_canonical
                        for c in cluster_citations:
                            if isinstance(c, dict):
                                c["cluster_case_name"] = common_canonical
                        logger.info(
                            f"[CLUSTER-TRUNCATION-FIX] cluster_id={cluster.get('cluster_id')} "
                            f"replaced truncated '{cluster_case_name[:40]}...' with canonical"
                        )
                    else:
                        logger.info(
                            f"[CLUSTER-CONTAMINATION-BLOCK] cluster_id={cluster.get('cluster_id')} "
                            f"keeping cluster_case_name='{cluster_case_name[:50] if cluster_case_name else None}', "
                            f"canonical='{common_canonical[:50]}'"
                        )
                    if common_canonical_url:
                        cluster["canonical_url"] = common_canonical_url
                        cluster["url"] = common_canonical_url
                logger.info(f"[CLUSTER-FINAL-CLEANUP] Cluster {i}: cluster_case_name='{cluster.get('cluster_case_name', '')[:50] if cluster.get('cluster_case_name') else None}...', canonical_name='{canonical_name[:50] if canonical_name else None}...', extracted_name='{extracted_name[:50] if extracted_name else None}...'")
                
                # Check all three fields for contamination (use current cluster_case_name after common_canonical fix)
                cluster_case_name = cluster.get("cluster_case_name")
                if cluster_case_name and ("\n" in cluster_case_name or len(cluster_case_name) > 200):
                    logger.warning(f"[CLUSTER-FINAL-CLEANUP] Rejecting contaminated cluster_case_name in clusters section")
                    # Get clean name from cluster's citations
                    clean_name = None
                    for cit in cluster_citations:
                        if isinstance(cit, dict):
                            name = cit.get("canonical_name") or cit.get("extracted_case_name")
                            if name and "\n" not in name and len(name) <= 200:
                                clean_name = name
                                break
                    cluster["cluster_case_name"] = clean_name or "N/A"
                    logger.warning(f"[CLUSTER-FINAL-CLEANUP] Replaced with: '{cluster['cluster_case_name']}'")
                
                # Also clean canonical_name and extracted_name if they're contaminated
                if canonical_name and ("\n" in canonical_name or len(canonical_name) > 200):
                    logger.warning(f"[CLUSTER-FINAL-CLEANUP] Rejecting contaminated canonical_name")
                    # Use clean cluster_case_name as replacement, or get from citations
                    replacement_name = cluster_case_name
                    if not replacement_name or ("\n" in replacement_name or len(replacement_name) > 200):
                        # Get clean name from cluster's citations
                        cluster_citations = cluster.get("citations", [])
                        for cit in cluster_citations:
                            if isinstance(cit, dict):
                                name = cit.get("canonical_name") or cit.get("extracted_case_name")
                                if name and "\n" not in name and len(name) <= 200:
                                    replacement_name = name
                                    break
                    cluster["canonical_name"] = replacement_name or "N/A"
                    logger.warning(f"[CLUSTER-FINAL-CLEANUP] Replaced canonical_name with: '{cluster['canonical_name']}'")
                    
                if extracted_name and ("\n" in extracted_name or len(extracted_name) > 200):
                    logger.warning(f"[CLUSTER-FINAL-CLEANUP] Rejecting contaminated extracted_name")
                    # Use clean cluster_case_name as replacement, or get from citations
                    replacement_name = cluster_case_name
                    if not replacement_name or ("\n" in replacement_name or len(replacement_name) > 200):
                        # Get clean name from cluster's citations
                        cluster_citations = cluster.get("citations", [])
                        for cit in cluster_citations:
                            if isinstance(cit, dict):
                                name = cit.get("canonical_name") or cit.get("extracted_case_name")
                                if name and "\n" not in name and len(name) <= 200:
                                    replacement_name = name
                                    break
                    cluster["extracted_name"] = replacement_name or "N/A"
                    logger.warning(f"[CLUSTER-FINAL-CLEANUP] Replaced extracted_name with: '{cluster['extracted_name']}'")

            # USER FIX 2026-01-12: Add display fields to clusters for frontend compatibility
            # The frontend expects submitted_display_name and verifying_display_name fields
            from src.utils.cluster_display_utils import _repair_truncated_llc
            for cluster in clusters:
                # Use clean canonical_name for verifying_display_name
                # FIX 2026-01-20: Handle None values - cluster.get() returns None if key exists with None value
                canonical_name = cluster.get("canonical_name") or ""
                # USER FIX 2026-01-12: Enhanced contamination detection including descriptive text
                is_contaminated = canonical_name and (
                    ("\n" in canonical_name) or
                    (len(canonical_name) > 200) or
                    any(word in canonical_name.lower() for word in ['these statements', 'has been upheld', 'numerous courts', 'eighth amendment', 'court has chosen', 'by overriding'])
                )
                if canonical_name and is_contaminated:
                    logger.warning(f"[DISPLAY-FIELD-CLEANUP] Rejecting contaminated canonical_name: '{canonical_name[:50]}...'")
                    # Get clean name from cluster's citations
                    clean_name = None
                    for cit in cluster.get("citations", []):
                        if isinstance(cit, dict):
                            name = cit.get("canonical_name") or cit.get("extracted_case_name")
                            if name and "\n" not in name and len(name) <= 200 and not any(word in name.lower() for word in ['these statements', 'has been upheld', 'numerous courts', 'eighth amendment', 'court has chosen', 'by overriding']):
                                clean_name = name
                                break
                    canonical_name = clean_name or "N/A"
                    logger.warning(f"[DISPLAY-FIELD-CLEANUP] Replaced with: '{canonical_name}'")
                # FIX: Repair truncated LLC (e.g. "Consumer First Legal Group, LL" -> "LLC")
                canonical_name = _repair_truncated_llc(canonical_name or "")
                cluster["verifying_display_name"] = canonical_name

                # Use clean extracted_name for submitted_display_name
                # FIX 2026-01-20: Handle None values
                extracted_name = cluster.get("extracted_name") or ""
                # CRITICAL FIX: Clean extracted_name to remove trailing years (like ", 2020") BEFORE contamination check
                if extracted_name and extracted_name != "N/A":
                    from src.utils.case_name_cleaner import clean_extracted_case_name
                    extracted_name = clean_extracted_case_name(extracted_name)
                # USER FIX 2026-01-12: Enhanced contamination detection including descriptive text
                is_contaminated = extracted_name and (
                    ("\n" in extracted_name) or
                    (len(extracted_name) > 200) or
                    any(word in extracted_name.lower() for word in ['these statements', 'has been upheld', 'numerous courts', 'eighth amendment', 'court has chosen', 'by overriding'])
                )
                if extracted_name and is_contaminated:
                    logger.warning(f"[DISPLAY-FIELD-CLEANUP] Rejecting contaminated extracted_name: '{extracted_name[:50]}...'")
                    # Get clean name from cluster's citations
                    clean_name = None
                    for cit in cluster.get("citations", []):
                        if isinstance(cit, dict):
                            name = cit.get("canonical_name") or cit.get("extracted_case_name")
                            if name and "\n" not in name and len(name) <= 200 and not any(word in name.lower() for word in ['these statements', 'has been upheld', 'numerous courts', 'eighth amendment', 'court has chosen', 'by overriding']):
                                # CRITICAL: Also clean the name from citations
                                from src.utils.case_name_cleaner import clean_extracted_case_name
                                clean_cit_name = clean_extracted_case_name(name)
                                if clean_cit_name and clean_cit_name != "N/A":
                                    clean_name = clean_cit_name
                                    break
                    extracted_name = clean_name or "N/A"
                    logger.warning(f"[DISPLAY-FIELD-CLEANUP] Replaced with: '{extracted_name}'")
                # USER FIX 2026-01-29: Never show citation fragments "(10 Tenn.), 1831" or statute names as extracted
                if extracted_name and extracted_name != "N/A":
                    from src.utils.strict_context_isolator import is_citation_fragment_not_case_name
                    if is_citation_fragment_not_case_name(extracted_name):
                        extracted_name = "N/A"
                    elif _is_statute_name(extracted_name):
                        extracted_name = (cluster.get("canonical_name") or "").strip() or "N/A"
                # FIX: When extraction failed (empty/N/A) but canonical_name exists, use canonical
                if not extracted_name or extracted_name == "N/A":
                    canonical_fallback = (cluster.get("canonical_name") or "").strip()
                    if not canonical_fallback or canonical_fallback == "N/A":
                        for cit in cluster.get("citations", []):
                            if isinstance(cit, dict):
                                cn = (cit.get("canonical_name") or "").strip()
                                if cn and cn != "N/A":
                                    canonical_fallback = cn
                                    break
                    if canonical_fallback and canonical_fallback != "N/A":
                        extracted_name = canonical_fallback
                cluster["submitted_display_name"] = extracted_name
                cluster["extracted_case_name"] = cluster.get("extracted_case_name") or extracted_name
                
                # Add display dates - sanitize when canonical is clearly wrong (e.g. 2026-01-27 for Thole 2020)
                submitted_date_str = cluster.get("extracted_date", "") or ""
                if not submitted_date_str:
                    for c in (cluster.get("citations") or []):
                        if isinstance(c, dict) and c.get("extracted_date"):
                            submitted_date_str = str(c.get("extracted_date", ""))
                            break
                verifying_date_val = cluster.get("canonical_date", "") or ""
                from src.utils.date_utils import extract_year_value as _extract_yr
                ext_yr_str = _extract_yr(submitted_date_str) if submitted_date_str else None
                ext_yr = int(ext_yr_str) if ext_yr_str else None
                can_yr_str = _extract_yr(verifying_date_val) if verifying_date_val else None
                can_yr = int(can_yr_str) if can_yr_str else None
                if ext_yr is not None and can_yr is not None:
                    try:
                        if "-" in str(verifying_date_val) and len(str(verifying_date_val)) >= 10:
                            from datetime import datetime as _dt
                            parsed_d = _dt.strptime(str(verifying_date_val)[:10], "%Y-%m-%d").date()
                            if parsed_d >= date.today() and ext_yr < date.today().year:
                                verifying_date_val = str(ext_yr)
                                cluster["has_date_mismatch"] = False
                                for c in (cluster.get("citations") or []):
                                    if isinstance(c, dict) and c.get("canonical_date"):
                                        c["canonical_date"] = verifying_date_val
                        elif abs(can_yr - ext_yr) > 15 or (can_yr < 1950 and ext_yr >= 1990):
                            verifying_date_val = str(ext_yr)
                            cluster["has_date_mismatch"] = False
                            for c in (cluster.get("citations") or []):
                                if isinstance(c, dict) and c.get("canonical_date"):
                                    c["canonical_date"] = verifying_date_val
                    except Exception:
                        pass
                cluster["verifying_display_date"] = verifying_date_val
                cluster["submitted_display_date"] = cluster.get("extracted_date", "")
                # If the two dates we display have the same year, do not show "Different date"
                final_sub_yr = _extract_yr(cluster.get("extracted_date", "") or submitted_date_str)
                final_ver_yr = _extract_yr(verifying_date_val)
                if final_sub_yr and final_ver_yr and final_sub_yr == final_ver_yr:
                    cluster["has_date_mismatch"] = False
                    # Clear citation-level date_mismatch so cluster stays out of date_mismatch section
                    for _c in (cluster.get("citations") or []):
                        if isinstance(_c, dict):
                            _c["date_mismatch"] = False
                        elif hasattr(_c, "date_mismatch"):
                            setattr(_c, "date_mismatch", False)

                # Finalize with shared backend display semantics so sync/async/unified
                # paths converge on one source of truth for display identity.
                finalize_cluster_for_response(
                    cluster,
                    clean_names=True,
                    clear_unverified_canonical=True,
                    clear_unverified_citations=True,
                )

            # Normalize Unicode (ff, fi ligatures) and comma spacing before response
            try:
                from src.utils.extraction_cleaner import normalize_to_ascii_display, normalize_citation_text
                from src.utils.cluster_display_utils import _normalize_display_name_comma_spacing
                for cit in citation_dicts:
                    if isinstance(cit, dict):
                        if cit.get("citation"):
                            cit["citation"] = normalize_citation_text(normalize_to_ascii_display(str(cit["citation"])))
                        if cit.get("context"):
                            cit["context"] = normalize_to_ascii_display(str(cit["context"]))
                        if cit.get("cluster_members"):
                            cit["cluster_members"] = [
                                normalize_citation_text(normalize_to_ascii_display(str(m))) for m in cit["cluster_members"]
                            ]
                        if cit.get("cluster_case_name"):
                            cit["cluster_case_name"] = _normalize_display_name_comma_spacing(str(cit["cluster_case_name"]))
                        if cit.get("canonical_name"):
                            cit["canonical_name"] = _repair_truncated_llc(str(cit["canonical_name"]))
                        if cit.get("case_name"):
                            cit["case_name"] = _repair_truncated_llc(str(cit["case_name"]))
                for cluster in clusters:
                    if isinstance(cluster, dict):
                        if cluster.get("cluster_members"):
                            cluster["cluster_members"] = [
                                normalize_citation_text(normalize_to_ascii_display(str(m))) for m in cluster["cluster_members"]
                            ]
                        if cluster.get("cluster_case_name"):
                            cluster["cluster_case_name"] = _normalize_display_name_comma_spacing(str(cluster["cluster_case_name"]))
                        if cluster.get("cluster_key"):
                            cluster["cluster_key"] = _normalize_display_name_comma_spacing(str(cluster["cluster_key"]))
                        if cluster.get("canonical_name"):
                            cluster["canonical_name"] = _repair_truncated_llc(str(cluster["canonical_name"]))
            except Exception as norm_err:
                logger.warning(f"[PIPELINE] Response normalization skipped: {norm_err}")

            # Build final response with UNIFIED PIPELINE metadata
            response = {
                "citations": citation_dicts,
                "clusters": clusters,  # Use proper clusters from clustering master
                "metadata": {
                    # Core pipeline metadata
                    "processing_mode": context.processing_mode,
                    "trace_id": context.trace_id,
                    "processing_time_ms": int((time.time() - context.start_time) * 1000),
                    "stages_completed": context.stages_completed,
                    # UNIFIED PIPELINE IDENTIFIER
                    "processing_path": "unified_pipeline",
                    # Clustering version (bump in unified_clustering_master_optimized when logic changes)
                    "clustering_version": _get_clustering_version(),
                    # Processing results
                    "parallel_verifications_applied": context.metadata.get("parallel_verifications", 0),
                    "cluster_count": context.metadata.get("cluster_count", 0),
                    "extraction_count": context.metadata.get("extraction_count", 0),
                    "verification_count": context.metadata.get("verification_count", 0),
                    "errors": context.errors,
                    "status": "completed" if not context.errors else "completed_with_errors",
                },
            }

            return response

        except Exception as e:
            context.add_error(str(e), "formatting")
            raise

    def _create_clusters_from_parallel_citations(self, citation_dicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create clusters from parallel_citations metadata when clustering master fails.

        This fallback method groups citations that reference each other in their
        parallel_citations arrays into clusters.
        """
        if not citation_dicts:
            return []

        # Build a mapping of citation text to citation dict (support both "citation" and missing key)
        def _cit_key(cit):
            if isinstance(cit, dict):
                return cit.get("citation", cit.get("citation_text", "")) or str(cit)
            return str(getattr(cit, "citation", cit))
        citation_map = {}
        for cit in citation_dicts:
            k = _cit_key(cit)
            if k:
                citation_map[k] = cit
        if not citation_map:
            return []

        # Build graph of parallel relationships using union-find approach
        # This handles transitive relationships: if A references B and B references C,
        # then A, B, and C should all be in the same cluster
        parent = {}

        def find(citation_text):
            """Find root of citation's cluster"""
            if citation_text not in parent:
                parent[citation_text] = citation_text
            if parent[citation_text] != citation_text:
                parent[citation_text] = find(parent[citation_text])
            return parent[citation_text]

        def union(citation1, citation2):
            """Merge two citations into the same cluster"""
            root1 = find(citation1)
            root2 = find(citation2)
            if root1 != root2:
                parent[root2] = root1

        # Build relationships: if citation A has citation B in parallel_citations,
        # they should be in the same cluster
        for cit_dict in citation_dicts:
            citation_text = _cit_key(cit_dict)
            if not citation_text or citation_text not in citation_map:
                continue
            parallel_citations = cit_dict.get("parallel_citations", [])

            # Union this citation with all its parallel citations
            for parallel in parallel_citations:
                if parallel in citation_map:
                    union(citation_text, parallel)

        # Group citations by their root cluster
        clusters_by_citation = {}
        for cit_dict in citation_dicts:
            citation_text = _cit_key(cit_dict)
            if not citation_text or citation_text not in citation_map:
                continue
            root = find(citation_text)
            clusters_by_citation[citation_text] = root

        # Group citations by cluster
        clusters_dict = {}
        cluster_id_map = {}  # Map root to sequential cluster_id
        cluster_id_counter = 1

        for citation_text, root in clusters_by_citation.items():
            # Assign sequential cluster IDs
            if root not in cluster_id_map:
                cluster_id_map[root] = f"cluster_{cluster_id_counter}"
                cluster_id_counter += 1

            cluster_id = cluster_id_map[root]
            if cluster_id not in clusters_dict:
                clusters_dict[cluster_id] = []
            if citation_text in citation_map:
                clusters_dict[cluster_id].append(citation_map[citation_text])

        # Year extraction from date strings and citation text (single source: date_utils)
        def _year_from_date(date_str):
            return extract_year_value(date_str)

        def _year_from_citation_text(citation_text):
            y = extract_year_from_citation(citation_text or "")
            return str(y) if y is not None else None

        # Create cluster dictionaries with required fields
        final_clusters = []
        for cluster_id, citations in clusters_dict.items():
            if not citations:
                continue

            # Remove bogus same-reporter citations (e.g. 67 S.E.2d 289 when 431 S.E.2d 289 present - Va. page bleed)
            citations = remove_bogus_same_reporter_citations(citations)
            if not citations:
                continue

            # Get cluster metadata from first citation (prefer verified ones)
            verified_citations = [c for c in citations if c.get("verified", False)]
            primary_citation = verified_citations[0] if verified_citations else citations[0]

            # Build cluster_members list (all citations in this cluster)
            # Include parallel_citations (e.g. 517 U.S. 559, 116 S. Ct. 1589, 134 L. Ed. 2d 809 for BMW v. Gore)
            raw_members = list({_cit_key(c) for c in citations if _cit_key(c)})
            for c in citations:
                for p in (c.get("parallel_citations") or []):
                    pt = (p.get("citation", p) if isinstance(p, dict) else p) if p else ""
                    if isinstance(pt, str) and pt.strip():
                        raw_members.append(pt.strip())
            raw_members = list(dict.fromkeys(m for m in raw_members if m))  # dedupe, preserve order
            # CRITICAL FIX: Filter out placeholder citations and same-reporter/different-volume
            if raw_members:
                first_member = raw_members[0]
                cluster_members = filter_cluster_members_by_reporter(first_member, raw_members)
            else:
                cluster_members = []

            # CRITICAL FIX: Find the best extracted case name from ALL citations in cluster
            # This matches the frontend logic in getClusterSubmittedName()
            # Prefer the longest, most complete name that's not truncated or generic
            def is_generic_or_truncated(name):
                """Check if a case name is generic or obviously truncated"""
                if not name or name == "N/A":
                    return True
                # Skip names starting with common truncation patterns
                if re.match(r"^(Co\.|Inc\.|LLC|Ltd\.|Corp\.)\s+v\.", name, re.IGNORECASE):
                    return True
                # Skip very short names (likely incomplete)
                if len(name.strip()) < 10:
                    return True
                return False

            best_extracted_name = None
            best_extracted_name_length = 0
            # USER FIX 2026-01-29: Never use citation fragments (e.g. "(10 Tenn.), 1831") as extracted name
            # Document has "10 Tenn. 581 (1831)" - parens only around year; we must not show short form as name
            from src.utils.strict_context_isolator import is_citation_fragment_not_case_name
            for cit in citations:
                extracted_name = cit.get("extracted_case_name") or cit.get("submitted_display_name")
                # USER FIX 2026-01-12: Reject contaminated names (newlines, excessive length)
                # This prevents "Ibid.\n\nThese statements..." from being selected as best name
                if extracted_name and not is_generic_or_truncated(extracted_name):
                    # Reject citation fragments like "(10 Tenn.), 1831" (not case names)
                    if is_citation_fragment_not_case_name(extracted_name):
                        continue
                    # Reject statute names like "Administrative Procedure Act"
                    if _is_statute_name(extracted_name):
                        continue
                    # Reject if contains newlines or is excessively long (>200 chars)
                    if "\n" in extracted_name or len(extracted_name) > 200:
                        continue
                    if len(extracted_name) > best_extracted_name_length:
                        best_extracted_name = extracted_name
                        best_extracted_name_length = len(extracted_name)

            # Fallback to primary citation's extracted name if no better name found
            if not best_extracted_name:
                extracted_name = primary_citation.get("submitted_display_name") or primary_citation.get(
                    "extracted_case_name"
                )
                # USER FIX 2026-01-12: If fallback is also contaminated, use canonical name instead
                if extracted_name and ("\n" in extracted_name or len(extracted_name) > 200):
                    best_extracted_name = primary_citation.get("canonical_name") or "N/A"
                elif extracted_name and (is_citation_fragment_not_case_name(extracted_name) or _is_statute_name(extracted_name)):
                    best_extracted_name = primary_citation.get("canonical_name") or "N/A"
                else:
                    best_extracted_name = extracted_name
            
            # CRITICAL FIX: Strip signal phrases from best_extracted_name
            # This ensures submitted_display_name doesn't contain signal phrases
            if best_extracted_name and best_extracted_name != "N/A":
                signal_phrase_patterns = [
                    r"^See,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," or "See e.g.," or "See, e.g"
                    r"^See\s+also\s+",  # "See also"
                    r"^See\s+generally\s+",  # "See generally"
                    r"^But\s+see\s+",  # "But see"
                    r"^See\s+",  # "See " (standalone signal word)
                    r"^Accord\s+",  # "Accord "
                    r"^Compare\s+",  # "Compare "
                    r"^Cf\.?\s+",  # "Cf."
                    r"^E\.?g\.?\s*,?\s*",  # "E.g.,"
                    r"^I\.?e\.?\s*,?\s*",  # "I.e.,"
                ]
                original_best = best_extracted_name
                for pattern in signal_phrase_patterns:
                    best_extracted_name = re.sub(pattern, "", best_extracted_name, flags=re.IGNORECASE).strip()
                
                # CRITICAL FIX: Remove trailing years from best_extracted_name
                # This prevents document publication years (like "2020") from appearing in case names
                from src.utils.case_name_cleaner import clean_extracted_case_name
                cleaned_best = clean_extracted_case_name(best_extracted_name)
                if cleaned_best != best_extracted_name:
                    best_extracted_name = cleaned_best

            # Get case name and date (prefer canonical if verified, otherwise extracted)
            cluster_case_name = None
            cluster_year = None
            if primary_citation.get("verified", False):
                cluster_case_name = primary_citation.get("canonical_name") or primary_citation.get(
                    "extracted_case_name"
                )
                # When canonical URL exists, use only canonical_date - never fall back to extracted_date.
                # Using extracted_date as fallback confuses users (hides real date mismatch).
                cluster_year = primary_citation.get("canonical_date")
            else:
                cluster_case_name = primary_citation.get("extracted_case_name")
                # For unverified citations, use extracted_date for display, but don't call it canonical
                cluster_year = primary_citation.get("extracted_date")
            
            # CRITICAL FIX: Strip citation signal phrases from cluster_case_name
            # These should never appear in case names (e.g., "See New Hampshire..." -> "New Hampshire...")
            logger.info(f"[SIGNAL-STRIP-CHECK] cluster_case_name BEFORE: '{cluster_case_name}'")
            if cluster_case_name and cluster_case_name != "N/A":
                original_cluster_name = cluster_case_name
                signal_phrase_patterns = [
                    r"^See,?\s+e\.?g\.?\s*,?\s*",  # "See, e.g.," or "See e.g.," or "See, e.g"
                    r"^See\s+also\s+",  # "See also"
                    r"^See\s+generally\s+",  # "See generally"
                    r"^But\s+see\s+",  # "But see"
                    r"^See\s+",  # "See " (standalone signal word)
                    r"^Accord\s+",  # "Accord "
                    r"^Compare\s+",  # "Compare "
                    r"^Cf\.?\s*",  # "Cf." (fixed: removed \s+ to just \s*)
                    r"^E\.?g\.?\s*,?\s*",  # "E.g.,"
                    r"^I\.?e\.?\s*,?\s*",  # "I.e.,"
                ]
                for pattern in signal_phrase_patterns:
                    cluster_case_name = re.sub(pattern, "", cluster_case_name, flags=re.IGNORECASE).strip()
                
                logger.info(f"[SIGNAL-STRIP-CHECK] cluster_case_name AFTER: '{cluster_case_name}'")
                if cluster_case_name != original_cluster_name:
                    logger.info(
                        f"[FORMAT-RESPONSE-CLUSTER-SIGNAL] Removed signal phrase from cluster_case_name: '{original_cluster_name}' -> '{cluster_case_name}'"
                    )

            # Apply citation-text-year override: if citation text contains year that matches canonical, clear date_mismatch
            for cit in citations:
                cit_date_mismatch = cit.get("date_mismatch", False)
                if not cit_date_mismatch and cit.get("verified", False):
                    citation_text = cit.get("citation", "")
                    citation_year = _year_from_citation_text(citation_text)
                    if citation_year:
                        canonical_date = cit.get("canonical_date")
                        canonical_year = _year_from_date(canonical_date)
                        if canonical_year and citation_year != canonical_year:
                            cit["date_mismatch"] = True
                        elif canonical_year and citation_year == canonical_year:
                            cit["date_mismatch"] = False
                elif cit_date_mismatch:
                    citation_text = cit.get("citation", "")
                    citation_year = _year_from_citation_text(citation_text)
                    if citation_year:
                        canonical_date = cit.get("canonical_date")
                        canonical_year = _year_from_date(canonical_date)
                        if canonical_year and citation_year == canonical_year:
                            cit["date_mismatch"] = False

            # USER FIX: Use canonical data from the citation that has canonical_url (the one we link to).
            # This ensures verifying_display_name always matches the link (e.g. 418 U.S. 323 -> Gertz, not Milkovich).
            # CRITICAL: Prefer the citation whose canonical_name matches the cluster's identity (cluster_case_name
            # or best_extracted_name), so we never show a link to the wrong case (e.g. Illinois National v. Harman
            # when the cluster is Thole v. U.S. Bank).
            def _norm_for_match(s: str) -> str:
                if not s or s == "N/A":
                    return ""
                return re.sub(r"\s+", " ", str(s).lower().strip())

            cluster_norm = _norm_for_match(cluster_case_name) or _norm_for_match(best_extracted_name)
            best_canonical_name = None
            best_canonical_date = None
            best_canonical_url = None
            # Pass 1: prefer citation whose canonical_name matches cluster identity
            if cluster_norm:
                for cit in citations:
                    cn = cit.get("canonical_name")
                    if not cn or not cit.get("canonical_url"):
                        continue
                    if _norm_for_match(cn) == cluster_norm:
                        best_canonical_name = cn
                        best_canonical_date = cit.get("canonical_date")
                        best_canonical_url = cit.get("canonical_url")
                        break
            # Pass 2: first citation with canonical_url and canonical_name
            if best_canonical_name is None:
                for cit in citations:
                    if cit.get("canonical_url") and cit.get("canonical_name"):
                        best_canonical_name = cit.get("canonical_name")
                        best_canonical_date = cit.get("canonical_date")
                        best_canonical_url = cit.get("canonical_url")
                        break
            # Pass 3: first verified citation with canonical_name
            if best_canonical_name is None:
                for cit in citations:
                    if cit.get("verified", False) and cit.get("canonical_name"):
                        best_canonical_name = cit.get("canonical_name")
                        best_canonical_date = cit.get("canonical_date")
                        best_canonical_url = cit.get("canonical_url")
                        break

            # USER FIX 2026-01-12: Reject contaminated cluster_case_name (newlines, excessive length)
            # This prevents "Ibid.\n\nThese statements..." from being used as cluster name
            # MUST be done AFTER best_canonical_name is calculated so we can use it as fallback
            if cluster_case_name and ("\n" in cluster_case_name or len(cluster_case_name) > 200):
                logger.warning(f"[CLUSTER-NAME-CONTAMINATION] Rejecting contaminated cluster_case_name: '{cluster_case_name[:50]}...'")
                # Use best_extracted_name or canonical name instead
                cluster_case_name = best_extracted_name or best_canonical_name or "N/A"
                logger.warning(f"[CLUSTER-NAME-CONTAMINATION] Replaced with: '{cluster_case_name}'")

            # USER FIX 2026-01-12: Apply contamination cleanup to display fields before creating cluster
            # Clean verifying_display_name - prefer canonical_name, fallback to extracted only if canonical unavailable
            clean_verifying_name = best_canonical_name or cluster_case_name
            if clean_verifying_name and ("\n" in clean_verifying_name or len(clean_verifying_name) > 200):
                # Get clean name from citations
                clean_verifying_name = None
                for c in citations:
                    if isinstance(c, dict):
                        name = c.get("canonical_name") or c.get("extracted_case_name")
                        if name and "\n" not in name and len(name) <= 200:
                            clean_verifying_name = name
                            break
                clean_verifying_name = clean_verifying_name or "N/A"
            
            # Clean submitted_display_name
            # CRITICAL FIX: If extracted name is generic fallback and we have canonical_name, use canonical
            # This fixes cases where extraction failed but verification succeeded
            # CRITICAL FIX: Ensure best_extracted_name is cleaned (remove trailing years)
            if best_extracted_name and best_extracted_name != "N/A":
                from src.utils.case_name_cleaner import clean_extracted_case_name
                best_extracted_name = clean_extracted_case_name(best_extracted_name)
            clean_submitted_name = best_extracted_name
            # USER FIX 2026-01-29: Never show citation fragments or statute names as "extracted"
            if clean_submitted_name and clean_submitted_name != "N/A":
                from src.utils.strict_context_isolator import is_citation_fragment_not_case_name
                if is_citation_fragment_not_case_name(clean_submitted_name):
                    clean_submitted_name = best_canonical_name or "N/A"
                elif _is_statute_name(clean_submitted_name):
                    clean_submitted_name = best_canonical_name or "N/A"
            if _is_generic_fallback_name(clean_submitted_name) and best_canonical_name:
                # Extraction failed (generic name), but verification succeeded - use canonical for display
                logger.info(
                    f"[DISPLAY-FIX] Extracted name '{clean_submitted_name}' is generic fallback, "
                    f"using canonical_name '{best_canonical_name}' for submitted_display_name"
                )
                clean_submitted_name = best_canonical_name
            # Strip TOA header prefixes
            if clean_submitted_name:
                clean_submitted_name = re.sub(
                    r'^(?:TABLE\s+OF\s+AUTHORITIES\s+)?(?:(?:I{1,3}V?|V?I{0,3})\s+)?Cases(?:[-]Continued)?(?:\s*:\s*|\s+)(?:Page\s+)?',
                    '', clean_submitted_name, flags=re.IGNORECASE
                ).strip() or clean_submitted_name
                clean_submitted_name = re.sub(r'^Page\s+(?=[A-Z])', '', clean_submitted_name).strip() or clean_submitted_name
            # Strip trailing citation fragments from extracted names
            if clean_submitted_name:
                clean_submitted_name = re.sub(r',?\s*\d+\s+(?:U\.S\.|F\.\d*d?|S\.\s*Ct\.|L\.\s*Ed|Tex\.|Pet\.|Cranch|Wall\.|Wheat\.|How\.|Barb\.|A\.).*$', '', clean_submitted_name).strip() or clean_submitted_name
                clean_submitted_name = re.sub(r',\s*(?:19|20)\d{2}\s*$', '', clean_submitted_name).strip() or clean_submitted_name
                clean_submitted_name = re.sub(r',?\s*,?\s*No\.?\s*,?\s*(?:CIV\.?\s+|CV\s+)?(?:\d[\d\-]*)?\s*$', '', clean_submitted_name).strip() or clean_submitted_name
            # Truncate at real sentence boundaries only.
            # Require 2+ lowercase letters before period AND a common sentence-starting word after.
            if clean_submitted_name:
                sentence_end = re.search(r'(?<=[a-z]{2})\.\s+(?:From|The|This|That|These|Those|It|In|On|At|By|For|And|But|Or|An|As|If|So|No|To|We|He|She|Such|Under|After|Before|During|However|Moreover|Furthermore|Indeed|Rather|Thus|Therefore|Accordingly|Here|There|Where|When|While|Although|Because|Since|Until|Unless|Whether)\b', clean_submitted_name)
                if sentence_end:
                    clean_submitted_name = clean_submitted_name[:sentence_end.start()].strip()
            if clean_submitted_name and ("\n" in clean_submitted_name or len(clean_submitted_name) > 120):
                # Get clean name from citations
                clean_submitted_name = None
                for c in citations:
                    if isinstance(c, dict):
                        name = c.get("canonical_name") or c.get("extracted_case_name")
                        if name and "\n" not in name and len(name) <= 120:
                            clean_submitted_name = name
                            break
                clean_submitted_name = clean_submitted_name or "N/A"

            # Format cluster with all fields; mismatch flags set via compute_cluster_mismatch_flags below
            cluster = {
                "cluster_id": cluster_id,
                "cluster_members": cluster_members,
                "cluster_case_name": cluster_case_name,
                "cluster_year": cluster_year,
                "cluster_size": len(citations),
                "citations": citations,
                "case_name": cluster_case_name,  # For backward compatibility
                "date": cluster_year,  # For backward compatibility
                "canonical_name": best_canonical_name,  # USER FIX: Use best canonical from any verified citation
                "canonical_date": best_canonical_date,
                "extracted_case_name": best_extracted_name,  # USER FIX: Use best extracted name, not just primary
                "extracted_date": primary_citation.get("extracted_date"),
                "verified": any(c.get("verified", False) for c in citations),
                "canonical_url": best_canonical_url,
                # Frontend-expected fields for display - USER FIX 2026-01-12: Use cleaned names
                "verifying_display_name": clean_verifying_name,  # USER FIX: Clean canonical name
                "verifying_display_date": best_canonical_date or cluster_year,  # Updated after date overrides
                "submitted_display_name": clean_submitted_name,  # USER FIX: Clean extracted name
                "submitted_display_date": primary_citation.get("submitted_display_date")
                or primary_citation.get("extracted_date"),
                "has_name_mismatch": False,
                "has_date_mismatch": False,
                "mismatch_indices": [],
            }
            compute_cluster_mismatch_flags(cluster)

            # Centralized "clearly wrong canonical date" overrides (date_utils.apply_canonical_date_overrides)
            submitted_date_str = (
                primary_citation.get("submitted_display_date")
                or primary_citation.get("extracted_date")
                or ""
            )
            verifying_display_date_val = best_canonical_date or cluster_year
            corrected_canonical_date, has_date_mismatch = apply_canonical_date_overrides(
                citations,
                verifying_display_date_val,
                submitted_date_str,
                cluster["has_date_mismatch"],
                today=date.today(),
            )
            if corrected_canonical_date:
                verifying_display_date_val = corrected_canonical_date
            cluster["has_date_mismatch"] = has_date_mismatch
            cluster["verifying_display_date"] = verifying_display_date_val or cluster_year

            # If the two dates we display have the same year, do not show "Different date"
            from src.utils.date_utils import extract_year_value
            disp_ext = extract_year_value(submitted_date_str)
            disp_ver = extract_year_value(verifying_display_date_val)
            if disp_ext and disp_ver and disp_ext == disp_ver:
                cluster["has_date_mismatch"] = False
                # Clear citation-level date_mismatch so cluster stays out of date_mismatch section
                for _c in (cluster.get("citations") or []):
                    if isinstance(_c, dict):
                        _c["date_mismatch"] = False
                    elif hasattr(_c, "date_mismatch"):
                        setattr(_c, "date_mismatch", False)

            final_clusters.append(cluster)

        logger.info(f"[PIPELINE] Created {len(final_clusters)} clusters from parallel_citations metadata")

        # POST-PROCESSING: Run shared-citation merge FIRST (strongest signal - same citation = same case)
        # Catches "Erickson v. Pharmacia 2025" + "Kerry L. Erickson v. Pharmacia 2024" when both cite 31 Wn. App. 2d 100
        try:
            from src.utils.response_enrichment import merge_clusters_by_shared_citation
            before = len(final_clusters)
            final_clusters = merge_clusters_by_shared_citation(final_clusters)
            if len(final_clusters) < before:
                logger.info(f"[PIPELINE] Shared-citation merge: {before} -> {len(final_clusters)} clusters")
        except Exception as e:
            logger.warning(f"[PIPELINE] Shared-citation merge skipped: {e}")

        # Merge clusters with the same canonical_name to reduce duplicates
        # This handles cases where the same case (e.g., "Clarke v. Tri-Cities") appears
        # multiple times with different citation formats that weren't grouped by proximity
        final_clusters = merge_clusters_by_canonical_name(final_clusters)

        # Run shared-citation merge AGAIN after canonical merge - catches duplicates that
        # canonical merge missed (different years: "Erickson 2025" vs "Kerry L. Erickson 2024")
        try:
            before2 = len(final_clusters)
            final_clusters = merge_clusters_by_shared_citation(final_clusters)
            if len(final_clusters) < before2:
                logger.info(f"[PIPELINE] Shared-citation merge (post-canonical): {before2} -> {len(final_clusters)} clusters")
        except Exception as e2:
            logger.warning(f"[PIPELINE] Shared-citation merge (post-canonical) skipped: {e2}")

        final_clusters = self._apply_post_verify_cluster_splits(final_clusters, trace_id="cluster-build")

        return final_clusters

    def _split_clusters_by_canonical(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split any cluster that contains citations from different canonical cases."""
        return split_clusters_by_canonical(clusters)

    def _merge_clusters_by_canonical_name(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge clusters that have the same canonical_name or represent the same case."""
        return merge_clusters_by_canonical_name(clusters)

    def _merge_cluster_group(self, clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple clusters into a single cluster."""
        return merge_cluster_group(clusters)

    def _apply_post_verify_cluster_splits(
        self,
        clusters: List[Dict[str, Any]],
        *,
        trace_id: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Apply deterministic post-verification split passes so mixed court/doc clusters
        (e.g., WL + F. Supp. or Supreme + lower federal) are consistently separated.
        """
        return apply_post_verify_cluster_splits(clusters, run_id=trace_id)

    def _format_error_response(self, context: ProcessingContext, error: str) -> Dict[str, Any]:
        """Format error response with debugging information"""
        return {
            "citations": [],
            "clusters": [],
            "metadata": {
                "processing_mode": context.processing_mode,
                "trace_id": context.trace_id,
                "processing_time_ms": int((time.time() - context.start_time) * 1000),
                "stages_completed": context.stages_completed,
                "errors": context.errors,
                "status": "failed",
                "error": error,
            },
            "error": error,
        }

    def _build_clusters(self, citations: List[CitationResult]) -> tuple[list[list[str]], dict[str, int]]:
        """Build clusters from parallel links and proximity; include singletons."""
        return pipeline_build_clusters(citations)


# SINGLETON INSTANCE - Use this for all processing
unified_pipeline = UnifiedProcessingPipeline()


async def process_citations_unified(
    text: str,
    processing_mode: str = "enhanced_sync",
    enable_parallel_verification: bool = True,
    enable_verification: bool = True,
    trace_id: Optional[str] = None,
    progress_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    CONVENIENCE FUNCTION - Main entry point for all citation processing

    This function replaces all the different entry points:
    - ``UnifiedCitationProcessorV2.process_text()``
    - ``UnifiedInputProcessor.process_any_input()``
    - ``extract_citations_clean()`` / ``extract_citations_production()``

    **This is the ONLY supported entry point going forward.**
    """
    # Store progress callback in pipeline instance so processor can access it
    if progress_callback:
        setattr(unified_pipeline, "_progress_callback", progress_callback)

    return await unified_pipeline.process_citations(
        text=text,
        processing_mode=processing_mode,
        enable_parallel_verification=enable_parallel_verification,
        enable_verification=enable_verification,
        trace_id=trace_id,
    )


if __name__ == "__main__":
    # Test the unified pipeline
    async def test():
        test_text = "Gresser v. Banner Health, 2023 COA 108, 543 P.3d 1059."
        result = await process_citations_unified(test_text, trace_id="TEST")
        print(f"Result: {len(result.get('citations', []))} citations")
        for cit in result.get("citations", []):
            print(
                f"  {cit.get('citation')}: verified={cit.get('verified')}, true_by_parallel={cit.get('true_by_parallel')}"
            )
        print(f"Metadata: {result.get('metadata')}")

    asyncio.run(test())
