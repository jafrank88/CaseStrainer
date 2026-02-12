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
import time
import uuid
import logging
import re
from datetime import date
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from src.models import CitationResult
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Import helper for filtering cluster members
from src.utils.cluster_filter import filter_cluster_members_by_reporter

# Import placeholder resolver
from src.utils.placeholder_resolver import resolve_placeholder_citations, is_placeholder_citation

# Import clustering function from correct module
try:
    from src.unified_clustering_master_optimized import cluster_citations_optimized as cluster_citations_unified_master
except ImportError:
    # Fallback to regular clustering if optimized not available
    try:
        from src.unified_clustering_master import cluster_citations_unified_master
    except ImportError:
        cluster_citations_unified_master = None

logger = logging.getLogger(__name__)


def _is_statute_name(name: str) -> bool:
    """Return True if name is a statute/act (e.g. Administrative Procedure Act), not a case name."""
    if not name or len(name.strip()) < 5:
        return False
    n = name.strip().lower()
    if not n.endswith((" act", " code", " statute", " regulation", " rule")):
        return False
    statute_phrases = [
        "administrative procedure",
        "freedom of information",
        "civil rights",
        "voting rights",
        "fair housing",
    ]
    return any(p in n for p in statute_phrases)


_GENERIC_FALLBACK_NAMES = [
    "U.S. Supreme Court Case",
    "Federal Appeals Case",
    "Federal District Case",
    "Washington State Case",
    "Pacific Reporter Case",
    "Unknown Case",
    "Case (",
    "Legal Citation (",
]


def _is_generic_fallback_name(name: str) -> bool:
    """Check if name is a generic fallback (extraction failed)"""
    if not name or name == "N/A":
        return True
    return any(name.startswith(gen) or name == gen for gen in _GENERIC_FALLBACK_NAMES)


@dataclass
class ProcessingContext:
    """Context object to track processing state and enable debugging"""

    trace_id: str
    start_time: float
    input_text: str
    processing_mode: str
    current_stage: str = "initialized"
    stages_completed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Nothing needed; defaults handled by default_factory
        pass

    def trace_stage(self, stage_name: str, data: Any = None):
        """Track processing stage for debugging"""
        self.current_stage = stage_name
        self.stages_completed.append(stage_name)
        elapsed = time.time() - self.start_time

    def add_error(self, error: str, stage: Optional[str] = None):
        """Record error for debugging"""
        error_msg = f"Error in {stage or self.current_stage}: {error}"
        self.errors.append(error_msg)


class UnifiedProcessingPipeline:
    """
    SINGLE ENTRY POINT for all citation processing in CaseStrainer.

    This replaces the multiple fragmented pathways:
    - unified_citation_processor_v2.py → process_text()
    - unified_input_processor.py → process_any_input()
    - clean_extraction_pipeline.py → extract_citations()
    - citation_extraction_endpoint.py → extract_citations_production()

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

            # SKIP SECOND VERIFICATION PASS - it overwrites fallback verification results!
            # process_text() already does: extraction -> verification -> clustering -> fallback
            # Running _verify_citations again would call CourtListener lookup which returns 404
            # for citations that were verified via CourtListener_Search (different API endpoint)
            if enable_verification and already_verified_count > 0:
                verified_citations = citations
            elif enable_verification:
                logger.info(
                    f"[PIPELINE-{context.trace_id}] ✅ Verification ENABLED, running verification for {len(citations)} citations..."
                )
                import os
                courtlistener_key = os.environ.get("COURTLISTENER_API_KEY", "")
                if courtlistener_key:
                    logger.info(
                        f"[PIPELINE-{context.trace_id}] CourtListener API key configured (length: {len(courtlistener_key)})"
                    )
                else:
                    logger.warning(
                        f"[PIPELINE-{context.trace_id}] ⚠️ WARNING: No CourtListener API key found! Verification may fail."
                    )
                verified_citations = await self._verify_citations(citations, text, context)
            else:
                logger.warning(
                    f"[PIPELINE-{context.trace_id}] ❌ Verification DISABLED, skipping verification for {len(citations)} citations"
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
            context.add_error(str(e), "pipeline_error")
            return self._format_error_response(context, str(e))

    async def _extract_citations(self, text: str, context: ProcessingContext) -> Dict[str, Any]:
        """Stage 1: Extract citations using the clean pipeline"""
        try:
            # Use the proven UnifiedCitationProcessorV2
            result = await self.processor.process_text(text)
            citations_count = len(result.get("citations", []))
            context.metadata["extraction_count"] = citations_count
            return result
        except Exception as e:
            context.add_error(str(e), "extraction")
            raise

    async def _verify_citations(
        self, citations: List[CitationResult], text: str, context: ProcessingContext
    ) -> List[CitationResult]:
        """Stage 2: Verify citations and get canonical data with timeout protection"""
        try:

            # ASYNC VERIFICATION TIMEOUT GUARD
            # Add timeout protection to prevent hanging in async workers
            import asyncio

            async def verify_with_timeout():
                # Use the sync verification method (proven to work)
                result = self.processor._verify_citations_sync(citations, text)
                return result

            # Set progressive timeout based on citation count
            # Base timeout + per-citation scaling with reasonable cap
            base_timeout = 30  # 30 seconds base
            per_citation_timeout = 3  # 3 seconds per citation
            max_timeout = 120  # 2 minutes max to allow for many citations

            timeout_seconds = min(max_timeout, max(base_timeout, len(citations) * per_citation_timeout))
            logger.info(
                f"[PIPELINE-{context.trace_id}] Progressive verification timeout: {timeout_seconds}s for {len(citations)} citations"
            )

            try:
                # Run verification with timeout
                verified_citations = await asyncio.wait_for(verify_with_timeout(), timeout=timeout_seconds)
                context.metadata["verification_count"] = len(verified_citations)
                logger.info(
                    f"[PIPELINE-{context.trace_id}] Verification completed, returned {len(verified_citations)} citations"
                )
                return verified_citations
            except asyncio.TimeoutError:
                logger.warning(
                    f"[PIPELINE-{context.trace_id}] Verification timed out after {timeout_seconds}s, returning original citations"
                )
                context.add_warning(f"Verification timed out after {timeout_seconds}s", "verification")
                # Return original citations if verification times out
                return citations

        except Exception as e:
            logger.error(
                f"[PIPELINE-{context.trace_id}] Verification error details: "
                f"Citations count: {len(citations)}, "
                f"Error type: {type(e).__name__}, "
                f"Error message: {str(e)}"
            )
            # Check for common verification issues
            import os
            courtlistener_key = os.environ.get("COURTLISTENER_API_KEY", "")
            if not courtlistener_key:
                logger.error(
                    f"[PIPELINE-{context.trace_id}] ⚠️ CRITICAL: COURTLISTENER_API_KEY is not set! "
                    "Verification requires a valid CourtListener API key."
                )
            else:
                logger.info(
                    f"[PIPELINE-{context.trace_id}] CourtListener API key is set (length: {len(courtlistener_key)})"
                )
            context.add_error(str(e), "verification")
            # Return original citations if verification fails
            return citations

    async def _apply_parallel_verification(
        self, citations: List[CitationResult], context: ProcessingContext
    ) -> List[CitationResult]:
        """Stage 3: Apply parallel verification - GUARANTEED EXECUTION"""
        try:

            # Ensure proximity-based parallel links are present, then propagate
            try:
                self.processor.ensure_bidirectional_parallels(citations)
            except Exception:
                pass
            self.processor.propagate_canonical_to_cluster(citations)

            # Count parallel verifications
            parallel_count = sum(1 for c in citations if getattr(c, "true_by_parallel", False))
            context.metadata["parallel_verifications"] = parallel_count

            logger.info(
                f"[PIPELINE-{context.trace_id}] Parallel verification completed - {parallel_count} citations marked"
            )

            return citations

        except Exception as e:
            context.add_error(str(e), "parallel_verification")
            # Return original citations if parallel verification fails
            return citations

    def _clean_case_name_contamination(self, extracted_name: str, canonical_name: str = None) -> str:
        """
        Clean obvious contamination from extracted case names.

        Args:
            extracted_name: The potentially contaminated extracted case name
            canonical_name: The verified canonical case name (optional)

        Returns:
            Cleaned case name
        """
        if not extracted_name or extracted_name == "N/A":
            return extracted_name

        # CRITICAL FIX: Detect and clean procedural/court text contamination
        # These patterns indicate text that is NOT a case name
        procedural_contamination_patterns = [
            # Court procedural text (common in briefs)
            r"^(?:Wash\.|Washington|Or\.|Oregon|Cal\.|California)\s+(?:Sup\.|Supreme)\s+(?:Ct\.|Court)\s+(?:oral\s+arg\.|argument)",
            r"^(?:oral\s+arg(?:ument)?\.?|argument)\s*,?\s*",
            r"^(?:We\s+interpret|The\s+court|This\s+court|As\s+stated)",
            r"^(?:quoting|citing|following|accord|see\s+also|but\s+see)",
            # Strip leading sentence fragments
            r"^[a-z][^A-Z]*\s+([A-Z][a-zA-Z\s\'&\-\.,]+\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]+)",
        ]

        cleaned = extracted_name

        # First pass: detect if the entire name is procedural text (return N/A)
        for pattern in procedural_contamination_patterns[:3]:  # First 3 patterns indicate total rejection
            if re.match(pattern, cleaned, re.IGNORECASE):
                logger.warning(f"[CLEANUP] Detected procedural contamination, rejecting: '{extracted_name}'")
                return "N/A"

        # Second pass: try to extract case name from contaminated text
        for pattern in procedural_contamination_patterns[3:]:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match and match.lastindex:
                cleaned = match.group(1).strip()
                logger.info(f"[CLEANUP] Extracted case name from contamination: '{extracted_name}' → '{cleaned}'")
                break

        # Common signal word contamination patterns
        signal_patterns = [
            r"^(?:this\s+case\s+involves|the\s+case\s+involves|case\s+involves)\s+(.+)$",
            r"^(?:see\s+the\s+case|see\s+case|the\s+case|case)\s+(?:of\s+)?(.+)$",
            r"^(?:in\s+this\s+case|in\s+the\s+case|in\s+case),?\s+(.+)$",
            r"^(?:cf|e\.g\.|i\.e\.|see\s+also|see|compare|accord|but\s+see|but\s+cf|contra)\.?\s+(.+)$",
            r"^(?:if|when|where|while|although|though|unless|until|since|because|as)\s+(?:in\s+)?(.+)$",
        ]

        for pattern in signal_patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                cleaned = match.group(1).strip()
                logger.info(f"[CLEANUP] Removed signal word: '{extracted_name}' → '{cleaned}'")
                break

        # Final validation: ensure it looks like a case name (has "v." or is "In re")
        if cleaned and cleaned != "N/A":
            has_v = " v. " in cleaned or " v " in cleaned.lower()
            is_in_re = cleaned.lower().startswith("in re ") or cleaned.lower().startswith("in the matter")
            if not has_v and not is_in_re:
                # Check if it's truncated (missing party)
                if len(cleaned) < 15 or not re.search(r"[A-Z][a-z]+", cleaned):
                    logger.warning(f"[CLEANUP] Name doesn't look like a case name: '{cleaned}' - keeping but flagging")

        return cleaned

    def _is_document_case_contamination_post_process(
        self, extracted_name: str, document_primary_case_name: str
    ) -> bool:
        """
        Post-processing contamination check: Detect if extracted case name matches document's primary case name.

        This is called AFTER extraction to catch any contamination that slipped through.

        Args:
            extracted_name: The extracted case name to check
            document_primary_case_name: The document's primary case name

        Returns:
            True if contaminated (should be rejected), False if clean
        """
        if not document_primary_case_name or not extracted_name or extracted_name == "N/A":
            return False

        # Use the same similarity-based contamination detection as unified_case_name_extractor
        # This ensures consistent behavior across all contamination checks and handles
        # cases where different systems have different case names (abbreviations vs full names)
        from src.utils.unified_case_name_extractor import _is_document_case_contamination

        return _is_document_case_contamination(extracted_name, document_primary_case_name, similarity_threshold=0.95)

    async def _format_response(self, citations: List[CitationResult], context: ProcessingContext) -> Dict[str, Any]:
        """Stage 4: Format final response using clustering master"""
        try:
            # CRITICAL FIX: Use the clustering master instead of building simple clusters
            # Convert citations to dicts for clustering master
            citation_dicts = []

            # Get document primary case name for contamination filtering
            document_primary_case_name = getattr(self.processor, "document_primary_case_name", None)

            for cit in citations:
                cit_dict = cit.to_dict()

                if "extracted_case_name" in cit_dict:
                    original_name = cit_dict["extracted_case_name"]
                    canonical_name = cit_dict.get("canonical_name")
                    cleaned_name = self._clean_case_name_contamination(original_name, canonical_name or "")
                    
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

                    # CRITICAL: Check for document primary case contamination on ALL citations
                    # The primary case name can appear in headers/footers on any page, not just the beginning
                    if cleaned_name and cleaned_name != "N/A" and document_primary_case_name:
                        is_contaminated = self._is_document_case_contamination_post_process(
                            cleaned_name, document_primary_case_name
                        )
                        if is_contaminated:
                            logger.error(
                                f"[POST-PROCESS-CONTAMINATION] ❌ REJECTING contaminated name '{cleaned_name}' for citation '{cit_dict.get('citation', 'unknown')}' (matches document primary '{document_primary_case_name}')"
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
                        from src.citation_extraction_endpoint import _names_equivalent
                        equiv = _names_equivalent(
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
                from src.citation_extraction_endpoint import _annotate_mismatch_flags

                # Create empty clusters list for now - will be populated by clustering master
                # NOTE: Threshold lowered from 0.6 to 0.4 to reduce false positives
                _annotate_mismatch_flags(citation_dicts, [], name_threshold=0.4, year_tolerance=0)
                logger.info(
                    f"[PIPELINE-{context.trace_id}] Annotated mismatch flags for {len(citation_dicts)} citations"
                )
            except Exception as e:
                pass

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

            print(f"[CLUSTERING-TRACE] Final source: {clustering_source}, clusters: {len(clusters)}", flush=True)
            # DEBUG: Log first cluster's fields
            if clusters:
                first = clusters[0]
                print(f"[CLUSTERING-TRACE] First cluster keys: {list(first.keys())}", flush=True)
                print(f"[CLUSTERING-TRACE] First cluster canonical_name: {first.get('canonical_name')}", flush=True)
                print(f"[CLUSTERING-TRACE] First cluster verified: {first.get('verified')}", flush=True)

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
                from src.citation_extraction_endpoint import _annotate_mismatch_flags

                # NOTE: Threshold lowered from 0.6 to 0.4 to reduce false positives
                _annotate_mismatch_flags(citation_dicts, clusters, name_threshold=0.4, year_tolerance=0)
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
                    new_cluster = {
                        "cluster_id": f"cluster_orphan_{len(clusters) + 1}",
                        "cluster_key": ct,
                        "cluster_case_name": ecn,
                        "cluster_year": cit_dict.get("extracted_date", ""),
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
                                f"🚫 [CONTAMINATION-BLOCK] Blocked name contamination: "
                                f"extracted='{cit_dict['extracted_case_name']}' vs "
                                f"canonical='{cit_dict['canonical_name']}' for {cit_dict.get('citation', 'unknown')}"
                            )
                    cit_dict["cluster_year"] = cluster.get("cluster_year")
                    cit_dict["cluster_size"] = cluster.get("cluster_size")
                    cit_dict["is_in_cluster"] = True
                else:
                    cit_dict["cluster_id"] = None
                    cit_dict["cluster_case_name"] = None
                    cit_dict["cluster_year"] = None
                    cit_dict["cluster_size"] = 1
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
                # This prevents contamination when verification APIs return wrong cases
                # Keep the original cluster_case_name from spatial clustering or extracted data
                if common_canonical:
                    logger.warning(
                        f"🚫 [CLUSTER-CONTAMINATION-BLOCK] cluster_id={cluster.get('cluster_id')} "
                        f"would have set cluster_case_name to '{common_canonical[:50]}...' "
                        f"but keeping original '{cluster_case_name[:50] if cluster_case_name else None}...'"
                    )
                    # Only update URLs, not names
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
                
                # Add display dates — sanitize when canonical is clearly wrong (e.g. 2026-01-27 for Thole 2020)
                submitted_date_str = cluster.get("extracted_date", "") or ""
                if not submitted_date_str:
                    for c in (cluster.get("citations") or []):
                        if isinstance(c, dict) and c.get("extracted_date"):
                            submitted_date_str = str(c.get("extracted_date", ""))
                            break
                verifying_date_val = cluster.get("canonical_date", "") or ""
                ext_yr_m = re.search(r"(19|20)\d{2}", str(submitted_date_str)) if submitted_date_str else None
                ext_yr = int(ext_yr_m.group(0)) if ext_yr_m else None
                can_yr_m = re.search(r"(19|20)\d{2}", str(verifying_date_val)) if verifying_date_val else None
                can_yr = int(can_yr_m.group(0)) if can_yr_m else None
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

        # Build a mapping of citation text to citation dict
        citation_map = {cit["citation"]: cit for cit in citation_dicts}

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
            citation_text = cit_dict["citation"]
            parallel_citations = cit_dict.get("parallel_citations", [])

            # Union this citation with all its parallel citations
            for parallel in parallel_citations:
                if parallel in citation_map:
                    union(citation_text, parallel)

        # Group citations by their root cluster
        clusters_by_citation = {}
        for cit_dict in citation_dicts:
            citation_text = cit_dict["citation"]
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

        # Helper function to extract year from date string
        def _extract_year(date_str):
            """Extract 4-digit year from date string"""
            if not date_str:
                return None
            import re

            match = re.search(r"(19|20)\d{2}", str(date_str))
            return match.group(0) if match else None

        # Helper function to extract year from citation text (for year-in-format citations)
        def _extract_year_from_citation(citation_text):
            """Extract year from citation text for year-in-format citations like '2002 WY 183'"""
            if not citation_text:
                return None
            import re

            # Match year-in-format patterns: "2002 WY 183", "2020 ND 123", etc.
            year_in_format_match = re.match(
                r"^(\d{4})\s+(?:WY|ND|OK|SD|UT|WI|MT|AL|AK|AR|AZ|CA|CO|CT|DE|FL|GA|HI|ID|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|NE|NV|NH|NJ|NM|NY|NC|OH|OR|PA|RI|SC|TN|TX|VT|VA|WA|WV|DC)\s+\d+",
                citation_text,
                re.IGNORECASE,
            )
            if year_in_format_match:
                return year_in_format_match.group(1)
            # Match WL citations: "2006 WL 3801910"
            wl_match = re.match(r"^(\d{4})\s+WL\s+\d+", citation_text)
            if wl_match:
                return wl_match.group(1)
            return None

        # Create cluster dictionaries with required fields
        final_clusters = []
        for cluster_id, citations in clusters_dict.items():
            if not citations:
                continue

            # Get cluster metadata from first citation (prefer verified ones)
            verified_citations = [c for c in citations if c.get("verified", False)]
            primary_citation = verified_citations[0] if verified_citations else citations[0]

            # Build cluster_members list (all citations in this cluster)
            # CRITICAL FIX: Filter out placeholder citations and same-reporter/different-volume
            raw_members = [c["citation"] for c in citations]
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
            # Document has "10 Tenn. 581 (1831)" — parens only around year; we must not show short form as name
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
                # CRITICAL: Only use canonical_date if citation is verified
                # Never use extracted_date as canonical_date (memory rule)
                cluster_year = primary_citation.get("canonical_date") or primary_citation.get("extracted_date")
            else:
                cluster_case_name = primary_citation.get("extracted_case_name")
                # For unverified citations, use extracted_date for display, but don't call it canonical
                cluster_year = primary_citation.get("extracted_date")
            
            # CRITICAL FIX: Strip citation signal phrases from cluster_case_name
            # These should never appear in case names (e.g., "See New Hampshire..." → "New Hampshire...")
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
                        f"[FORMAT-RESPONSE-CLUSTER-SIGNAL] Removed signal phrase from cluster_case_name: '{original_cluster_name}' → '{cluster_case_name}'"
                    )

            # Compute mismatch flags for cluster
            # Check if any citation has name or date mismatch
            has_name_mismatch = False
            has_date_mismatch = False
            mismatch_indices = []

            for idx, cit in enumerate(citations):
                cit_name_mismatch = cit.get("name_mismatch", False)
                cit_date_mismatch = cit.get("date_mismatch", False)

                # For date mismatch: if citation has year-in-format, extract year from citation text
                # and compare with canonical date year to determine if there's a real mismatch
                if not cit_date_mismatch and cit.get("verified", False):
                    citation_text = cit.get("citation", "")
                    citation_year = _extract_year_from_citation(citation_text)
                    if citation_year:
                        # Citation has year in format - use it for comparison
                        canonical_date = cit.get("canonical_date")
                        canonical_year = _extract_year(canonical_date)
                        if canonical_year and citation_year != canonical_year:
                            cit_date_mismatch = True
                        elif canonical_year and citation_year == canonical_year:
                            # Years match, so no mismatch even if extracted_date was wrong
                            cit_date_mismatch = False
                elif cit_date_mismatch:
                    # Check if we should override based on citation text year
                    citation_text = cit.get("citation", "")
                    citation_year = _extract_year_from_citation(citation_text)
                    if citation_year:
                        canonical_date = cit.get("canonical_date")
                        canonical_year = _extract_year(canonical_date)
                        if canonical_year and citation_year == canonical_year:
                            # Citation text year matches canonical - override the mismatch
                            cit_date_mismatch = False

                # CRITICAL FIX: Only count mismatches for VERIFIED citations
                # Unverified citations shouldn't trigger mismatch warnings
                is_verified = cit.get("verified", False)
                if is_verified and (cit_name_mismatch or cit_date_mismatch):
                    mismatch_indices.append(idx)
                if is_verified:
                    has_name_mismatch = has_name_mismatch or cit_name_mismatch
                    has_date_mismatch = has_date_mismatch or cit_date_mismatch

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
            elif clean_submitted_name and ("\n" in clean_submitted_name or len(clean_submitted_name) > 200):
                # Get clean name from citations
                clean_submitted_name = None
                for c in citations:
                    if isinstance(c, dict):
                        name = c.get("canonical_name") or c.get("extracted_case_name")
                        if name and "\n" not in name and len(name) <= 200:
                            clean_submitted_name = name
                            break
                clean_submitted_name = clean_submitted_name or "N/A"

            # USER FIX 2026-01-27: Sanitize verifying_display_date when canonical is clearly wrong
            # (e.g. "2026-01-27" from date_modified/today for Thole 2020, or "1917" for TransUnion 2016).
            # Also correct each citation's canonical_date so the frontend (getClusterVerifyingDate uses rep.canonical_date) shows the right date.
            submitted_date_str = (
                primary_citation.get("submitted_display_date") or primary_citation.get("extracted_date") or ""
            )
            verifying_display_date_val = best_canonical_date or cluster_year
            extracted_year_match = re.search(r"(19|20)\d{2}", str(submitted_date_str)) if submitted_date_str else None
            extracted_year_int = int(extracted_year_match.group(0)) if extracted_year_match else None
            can_year_match = re.search(r"(19|20)\d{2}", str(verifying_display_date_val)) if verifying_display_date_val else None
            can_year_int = int(can_year_match.group(0)) if can_year_match else None
            today = date.today()
            corrected_canonical_date = None  # set to str(extracted_year_int) when we override
            if extracted_year_int is not None and can_year_int is not None:
                # Canonical is "today" or future -> likely date_modified; use extracted year
                try:
                    if "-" in str(verifying_display_date_val) and len(str(verifying_display_date_val)) >= 10:
                        from datetime import datetime as dt
                        parsed = dt.strptime(str(verifying_display_date_val)[:10], "%Y-%m-%d").date()
                        if parsed >= today and extracted_year_int < today.year:
                            corrected_canonical_date = str(extracted_year_int)
                            verifying_display_date_val = corrected_canonical_date
                            has_date_mismatch = False
                except Exception:
                    pass
                # Canonical year absurdly different from extracted (e.g. 1917 vs 2016) -> use extracted
                if has_date_mismatch and abs(can_year_int - extracted_year_int) > 15:
                    corrected_canonical_date = str(extracted_year_int)
                    verifying_display_date_val = corrected_canonical_date
                    has_date_mismatch = False
                # Pre-1950 canonical with post-1990 extracted -> treat as wrong canonical
                if has_date_mismatch and can_year_int < 1950 and extracted_year_int >= 1990:
                    corrected_canonical_date = str(extracted_year_int)
                    verifying_display_date_val = corrected_canonical_date
                    has_date_mismatch = False
            if corrected_canonical_date:
                for c in citations:
                    if isinstance(c, dict) and c.get("canonical_date"):
                        c["canonical_date"] = corrected_canonical_date
                    elif hasattr(c, "canonical_date"):
                        c.canonical_date = corrected_canonical_date

            # Format cluster with all fields expected by frontend
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
                "verifying_display_date": verifying_display_date_val or cluster_year,
                "submitted_display_name": clean_submitted_name,  # USER FIX: Clean extracted name
                "submitted_display_date": primary_citation.get("submitted_display_date")
                or primary_citation.get("extracted_date"),
                # Mismatch flags
                "has_name_mismatch": has_name_mismatch,
                "has_date_mismatch": has_date_mismatch,
                "mismatch_indices": mismatch_indices,
            }

            final_clusters.append(cluster)

        logger.info(f"[PIPELINE] Created {len(final_clusters)} clusters from parallel_citations metadata")

        # POST-PROCESSING: Merge clusters with the same canonical_name to reduce duplicates
        # This handles cases where the same case (e.g., "Clarke v. Tri-Cities") appears
        # multiple times with different citation formats that weren't grouped by proximity
        final_clusters = self._merge_clusters_by_canonical_name(final_clusters)

        return final_clusters

    def _split_clusters_by_canonical(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split any cluster that contains citations from different canonical cases
        (different canonical_name and/or year). Ensures Davis/2008 and Meese/1987
        never remain in the same cluster regardless of clustering source.

        FIX 2026-02-10: Also detect when a citation's TEXT contains a different
        case name than its canonical_name metadata (e.g., citation text says
        "Trichell v. Midland" but canonical_name says "Simon v. Eastern Kentucky").
        """
        if not clusters:
            return clusters
        result: List[Dict[str, Any]] = []

        def _norm_name(name: str) -> str:
            if not name:
                return ""
            n = re.sub(r"^See,?\s+e\.?g\.?,?\s*", "", str(name), flags=re.IGNORECASE)
            n = re.sub(r"^See\s+also\s+", "", n, flags=re.IGNORECASE)
            n = re.sub(r"^See\s+generally\s+", "", n, flags=re.IGNORECASE)
            n = re.sub(r"^But\s+see\s+", "", n, flags=re.IGNORECASE)
            return re.sub(r"\s+", " ", n).strip().lower()

        def _extract_first_party_from_text(cit_text: str) -> str:
            """Extract first party name from citation text like 'Trichell v. Midland...'"""
            if not cit_text:
                return ""
            m = re.match(r"^([A-Z][A-Za-z'\-]+(?:\.\s*)?(?:\s+[A-Za-z'\-]+\.?)*)\s+v\.\s+", cit_text)
            return m.group(1).strip().rstrip(",. ").split()[-1].lower() if m else ""

        for cluster in clusters:
            citations = cluster.get("citations") or cluster.get("citation_objects") or []
            if len(citations) <= 1:
                result.append(cluster)
                continue
            canonical_groups: Dict[Any, List[Any]] = {}
            unassigned: List[Any] = []
            for cit in citations:
                # Handle both dict and CitationResult objects
                if isinstance(cit, dict):
                    can_name = cit.get("canonical_name")
                    can_date = cit.get("canonical_date")
                    is_verified = cit.get("verified", False) or cit.get("is_verified", False)
                    cit_text = cit.get("citation", "")
                else:
                    can_name = getattr(cit, "canonical_name", None)
                    can_date = getattr(cit, "canonical_date", None)
                    is_verified = getattr(cit, "verified", False)
                    cit_text = getattr(cit, "citation", "")

                # FIX 2026-02-10: Check if citation text has a different case name
                # than the canonical_name metadata. If so, use the citation text name
                # as the grouping key to prevent merging unrelated cases.
                cit_text_party = _extract_first_party_from_text(cit_text)
                if cit_text_party and can_name and " v. " in can_name.lower():
                    can_party = _norm_name(can_name).split(" v. ")[0].strip().split()[-1] if " v. " in _norm_name(can_name) else ""
                    if can_party and cit_text_party != can_party:
                        # Citation text says different case — extract name from text
                        text_name_m = re.match(
                            r"^((?:[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)"
                            r"\s+v\.\s+"
                            r"(?:[A-Z][A-Za-z'\-]+\.?(?:[\s,]+[A-Za-z'\-]+\.?)*))",
                            cit_text,
                        )
                        if text_name_m:
                            text_name = _norm_name(text_name_m.group(1).rstrip(","))
                            # Extract year from citation text parenthetical
                            year_m = re.search(r"\((?:[A-Za-z0-9.\s]*?)(\d{4})\)", cit_text)
                            year_int = int(year_m.group(1)) if year_m else 0
                            key = (text_name, year_int)
                            canonical_groups.setdefault(key, []).append(cit)
                            logger.info(
                                f"[PIPELINE-CANONICAL-SPLIT] Citation text '{cit_text[:60]}' has different name "
                                f"than canonical '{can_name}' — grouping by text name '{text_name}'"
                            )
                            continue

                if is_verified and can_name and can_date:
                    norm = _norm_name(can_name)
                    year_m = re.search(r"(19|20)\d{2}", str(can_date))
                    if norm and year_m:
                        year_int = int(year_m.group(0))
                        key = (norm, year_int)
                        canonical_groups.setdefault(key, []).append(cit)
                    else:
                        unassigned.append(cit)
                else:
                    unassigned.append(cit)
            # Process unassigned citations BEFORE the early-return check.
            # Unassigned citations with distinct ecns should create new groups,
            # potentially turning a single-group cluster into a multi-group one.
            if unassigned:
                logger.warning(
                    f"[PIPELINE-CANONICAL-SPLIT] {len(unassigned)} unassigned citations in cluster "
                    f"'{cluster.get('cluster_id', '?')}' with {len(canonical_groups)} canonical groups. "
                    f"Unassigned ecns: {[((c.get('extracted_case_name') or '')[:40] if isinstance(c, dict) else (getattr(c, 'extracted_case_name', '') or '')[:40]) for c in unassigned]}"
                )
            if unassigned:
                keys_before = list(canonical_groups.keys())
                for ua_cit in unassigned:
                    if isinstance(ua_cit, dict):
                        ua_ecn = ua_cit.get("extracted_case_name") or ""
                        ua_date_str = str(ua_cit.get("extracted_date", "") or ua_cit.get("canonical_date", "") or "")
                    else:
                        ua_ecn = getattr(ua_cit, "extracted_case_name", "") or ""
                        ua_date_str = str(getattr(ua_cit, "extracted_date", "") or getattr(ua_cit, "canonical_date", "") or "")
                    ua_ecn_norm = _norm_name(ua_ecn) if ua_ecn and ua_ecn != "N/A" and " v. " in ua_ecn else ""
                    assigned = False
                    if ua_ecn_norm:
                        # Try to match to an existing canonical group by first-party overlap
                        ua_parts = ua_ecn_norm.split(" v. ")
                        ua_first = ua_parts[0].strip().split()[-1] if ua_parts else ""
                        for key in list(canonical_groups.keys()):
                            key_parts = key[0].split(" v. ") if " v. " in key[0] else [key[0]]
                            key_first = key_parts[0].strip().split()[-1] if key_parts else ""
                            if ua_first and key_first and ua_first == key_first:
                                canonical_groups[key].append(ua_cit)
                                assigned = True
                                break
                        if not assigned:
                            # Distinct ecn — create a new group
                            ua_year_m = re.search(r"(19|20)\d{2}", ua_date_str)
                            ua_year = int(ua_year_m.group(0)) if ua_year_m else 0
                            new_key = (ua_ecn_norm, ua_year)
                            canonical_groups.setdefault(new_key, []).append(ua_cit)
                            assigned = True
                            logger.info(
                                f"[PIPELINE-CANONICAL-SPLIT] Unassigned citation with ecn='{ua_ecn}' "
                                f"created new group '{new_key}' instead of dumping into primary"
                            )
                    if not assigned:
                        # No ecn — fall back to first canonical group (or keep in cluster as-is)
                        if canonical_groups:
                            first_key = sorted(canonical_groups.keys())[0]
                            canonical_groups[first_key].append(ua_cit)
                        # else: will be handled by the <= 1 check below

            if len(canonical_groups) <= 1:
                result.append(cluster)
                continue
            keys = sorted(canonical_groups.keys(), key=lambda k: (k[0], k[1]))
            logger.info(
                f"[PIPELINE-CANONICAL-SPLIT] Splitting cluster with mixed cases {[(k[0], k[1]) for k in keys]} into {len(keys)} clusters"
            )
            base_id = cluster.get("cluster_id", "cluster_0")
            for ki, (norm_name, year_int) in enumerate(keys):
                group_cits = canonical_groups[(norm_name, year_int)]
                group_cit_texts = {(c.get("citation", "") if isinstance(c, dict) else getattr(c, "citation", "")) for c in group_cits}
                new_cluster = dict(cluster)
                new_cluster["cluster_id"] = f"{base_id}_canonical_split_{ki}" if len(keys) > 1 else base_id
                new_cits = [c for c in (cluster.get("citations") or []) if (c.get("citation", "") if isinstance(c, dict) else getattr(c, "citation", "")) in group_cit_texts]
                new_members = [
                    m for m in (cluster.get("cluster_members") or [])
                    if (m.get("citation", "") if isinstance(m, dict) else m) in group_cit_texts
                ]
                new_cluster["citations"] = new_cits or group_cits
                new_cluster["cluster_members"] = new_members
                new_cluster["cluster_size"] = len(new_cluster["citations"])
                new_cluster["cluster_year"] = str(year_int)
                # FIX: Only use canonical_name from citations whose canonical first-party
                # matches the group's norm_name first-party. This prevents a Susan B. Anthony
                # citation (split by text) from inheriting "Spokeo, Inc. v. Robins" as display_name
                # just because its canonical_name metadata still says Spokeo.
                group_first = norm_name.split(" v. ")[0].strip().split()[-1].lower() if " v. " in norm_name else norm_name.lower()
                display_name = None
                for c in group_cits:
                    cn = c.get("canonical_name", "") if isinstance(c, dict) else (getattr(c, "canonical_name", "") or "")
                    if not cn:
                        continue
                    cn_norm = _norm_name(cn)
                    cn_first = cn_norm.split(" v. ")[0].strip().split()[-1].lower() if " v. " in cn_norm else cn_norm.lower()
                    if cn_first == group_first:
                        display_name = cn
                        break
                def _get_ecn(c):
                    return c.get("extracted_case_name", "") if isinstance(c, dict) else (getattr(c, "extracted_case_name", "") or "")
                ext_name_for_display = next((_get_ecn(c) for c in group_cits if _get_ecn(c) and _get_ecn(c) != "N/A"), None)
                new_cluster["cluster_case_name"] = display_name or ext_name_for_display or cluster.get("cluster_case_name")
                new_cluster["canonical_name"] = display_name or ""
                # Also clear canonical_url if no display_name (prevents rq_worker from re-inheriting)
                if not display_name:
                    new_cluster["canonical_url"] = None
                    new_cluster["canonical_date"] = None
                    new_cluster["verified"] = False
                    new_cluster["verification_status"] = None
                    # Clear cluster_key too — it's inherited from parent
                    if ext_name_for_display:
                        new_cluster["cluster_key"] = ext_name_for_display.lower()
                    logger.warning(
                        f"[PIPELINE-CANONICAL-SPLIT] Cleared inherited canonical data for split cluster "
                        f"'{new_cluster['cluster_id']}' (no verified canonical_name in group). "
                        f"Using ecn='{ext_name_for_display}' for display."
                    )
                def _cit_get(c, key):
                    return c.get(key) if isinstance(c, dict) else getattr(c, key, None)
                new_cluster["canonical_date"] = new_cluster.get("canonical_date") or next((_cit_get(c, "canonical_date") for c in group_cits if _cit_get(c, "canonical_date")), cluster.get("canonical_date"))
                ext_name = next((_cit_get(c, "extracted_case_name") for c in group_cits if _cit_get(c, "extracted_case_name")), None)
                new_cluster["extracted_name"] = ext_name or cluster.get("extracted_name")
                new_cluster["extracted_date"] = next((_cit_get(c, "extracted_date") for c in group_cits if _cit_get(c, "extracted_date")), cluster.get("extracted_date"))
                result.append(new_cluster)
        return result

    def _merge_clusters_by_canonical_name(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge clusters that have the same canonical_name or represent the same case.

        This fixes duplicate clusters that appear when the same case is cited multiple
        times with different citation formats that weren't grouped by proximity detection.
        Also handles abbreviations like "TCAC" vs "Tri-Cities Animal Care & Control".
        """
        if not clusters or len(clusters) <= 1:
            return clusters

        def extract_first_party(name: str) -> str:
            """Extract first party name before 'v.' for comparison."""
            if not name:
                return ""
            # Handle "v." or "v" separator
            parts = re.split(r"\s+v\.?\s+", name, maxsplit=1, flags=re.IGNORECASE)
            return parts[0].lower().strip() if parts else name.lower().strip()

        def names_match(name1: str, name2: str) -> bool:
            """Check if two case names likely refer to the same case."""
            if not name1 or not name2:
                return False
            # Exact match after normalization
            n1 = name1.lower().strip()
            n2 = name2.lower().strip()
            if n1 == n2:
                return True
            # First party match (handles abbreviations)
            p1 = extract_first_party(name1)
            p2 = extract_first_party(name2)
            # Check if one contains the other or they share significant words
            if p1 and p2:
                # Same first party (e.g., "Clarke" in both)
                p1_words = set(re.findall(r"\b[a-z]+\b", p1))
                p2_words = set(re.findall(r"\b[a-z]+\b", p2))
                common = {"inc", "llc", "corp", "co", "the", "of", "and", "v"}
                p1_key = p1_words - common
                p2_key = p2_words - common
                if p1_key and p2_key and (p1_key & p2_key):
                    return True
            return False

        # PRE-PASS: Promote citation-level canonical data to cluster level when missing.
        # After verification, citations have canonical_name/canonical_url but the cluster
        # may not (clustering happens before verification).  Without this, clusters with
        # verified citations but no cluster-level canonical_name are invisible to the merge.
        for cluster in clusters:
            if (not cluster.get("canonical_name") or cluster.get("canonical_name") == "N/A"):
                for cit in cluster.get("citations", []):
                    if isinstance(cit, dict):
                        cn = cit.get("canonical_name")
                        cu = cit.get("canonical_url")
                        verified = cit.get("verified", False)
                        cd = cit.get("canonical_date")
                    else:
                        cn = getattr(cit, "canonical_name", None)
                        cu = getattr(cit, "canonical_url", None)
                        verified = getattr(cit, "verified", False)
                        cd = getattr(cit, "canonical_date", None)
                    if cn and cn != "N/A" and verified:
                        cluster["canonical_name"] = cn
                        if cu:
                            cluster["canonical_url"] = cu
                        cluster["canonical_date"] = cd or cluster.get("canonical_date")
                        logger.info(
                            f"[MERGE-PROMOTE] Promoted canonical_name='{cn}' from citation to "
                            f"cluster_id={cluster.get('cluster_id')}"
                        )
                        break

        # POST-PROMOTE diagnostic: show clusters still missing canonical_name
        for cluster in clusters:
            cn = cluster.get("canonical_name")
            if not cn or cn == "N/A":
                cit_texts = []
                for cit in cluster.get("citations", [])[:3]:
                    if isinstance(cit, dict):
                        cit_texts.append(cit.get("citation", "?")[:60])
                    else:
                        cit_texts.append(getattr(cit, "citation", "?")[:60])
                logger.info(
                    f"[MERGE-NO-CN] cluster_id={cluster.get('cluster_id')} has no canonical_name. "
                    f"Citations: {cit_texts}"
                )

        # Group clusters by canonical_name.  Clusters with the same name are
        # candidates for merging.  We only refuse to merge when both clusters
        # have DIFFERENT non-empty canonical_urls (different opinions).
        name_to_clusters: Dict[str, List[Dict[str, Any]]] = {}
        for cluster in clusters:
            cn = cluster.get("canonical_name")
            cu = cluster.get("canonical_url")
            if cn and cn != "N/A":
                logger.info(f"[MERGE-DIAG] cluster_id={cluster.get('cluster_id')} canonical_name='{cn}' canonical_url='{cu}' verified={cluster.get('verified')}")
        for cluster in clusters:
            canonical_name = cluster.get("canonical_name")
            if canonical_name and canonical_name != "N/A":
                norm_name = canonical_name.lower().strip()
                if norm_name not in name_to_clusters:
                    name_to_clusters[norm_name] = []
                name_to_clusters[norm_name].append(cluster)

        # Sub-group each name group by canonical_url so we never merge
        # clusters that point to genuinely different opinions.
        # Empty/None URLs are treated as compatible with any URL.
        def _split_by_url(group: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
            """Split a same-name group into sub-groups that are safe to merge."""
            url_groups: List[List[Dict[str, Any]]] = []
            no_url: List[Dict[str, Any]] = []
            url_map: Dict[str, List[Dict[str, Any]]] = {}
            for c in group:
                cu = (c.get("canonical_url") or "").strip()
                if not cu:
                    no_url.append(c)
                else:
                    url_map.setdefault(cu, []).append(c)
            # Attach no-url clusters to the first url group (or make their own)
            if url_map:
                first_key = next(iter(url_map))
                url_map[first_key].extend(no_url)
            elif no_url:
                url_groups.append(no_url)
            for url_key, members in url_map.items():
                url_groups.append(members)
            return url_groups

        # Merge clusters with the same canonical name
        merged_clusters = []
        merged_norm_names: set = set()

        for cluster in clusters:
            canonical_name = cluster.get("canonical_name")
            if canonical_name and canonical_name != "N/A":
                norm_name = canonical_name.lower().strip()

                # Skip if we've already processed this name
                if norm_name in merged_norm_names:
                    continue
                merged_norm_names.add(norm_name)

                same_name_clusters = name_to_clusters.get(norm_name, [cluster])
                # Split by URL to avoid merging different opinions
                url_subgroups = _split_by_url(same_name_clusters)
                for subgroup in url_subgroups:
                    if len(subgroup) > 1:
                        logger.warning(f"[MERGE-CLUSTERS] Merging {len(subgroup)} clusters for '{canonical_name}'")
                        merged_clusters.append(self._merge_cluster_group(subgroup))
                    else:
                        merged_clusters.append(subgroup[0])
            else:
                # No canonical name - keep as is
                merged_clusters.append(cluster)

        logger.info(f"[MERGE-CLUSTERS] After exact match: {len(clusters)} to {len(merged_clusters)} clusters")

        # SECOND PASS: Merge clusters with same date + similar first party names
        # This catches abbreviations like "Clarke v. TCAC" vs "Clarke v. Tri-Cities"
        if len(merged_clusters) > 1:
            # Group by (first_party, canonical_date) for similarity matching
            date_party_groups = {}
            for i, cluster in enumerate(merged_clusters):
                # FIX 2026-01-20: Handle None values properly
                canonical_date = cluster.get("canonical_date") or ""
                canonical_name = cluster.get("canonical_name") or ""
                first_party = extract_first_party(canonical_name)
                # Only group verified clusters with valid dates
                if canonical_date and first_party and cluster.get("verified", False):
                    key = (first_party, canonical_date)
                    if key not in date_party_groups:
                        date_party_groups[key] = []
                    date_party_groups[key].append(i)

            # Find clusters to merge (same first party + same date)
            indices_to_merge = {}  # Maps cluster index to group leader index
            for key, indices in date_party_groups.items():
                if len(indices) > 1:
                    leader = indices[0]
                    for idx in indices[1:]:
                        indices_to_merge[idx] = leader
                        logger.info(f"[MERGE-CLUSTERS] Will merge cluster {idx} into {leader} (same date+party: {key})")

            if indices_to_merge:
                # Group clusters by their leader
                leader_to_clusters = {}
                for i, cluster in enumerate(merged_clusters):
                    leader = indices_to_merge.get(i, i)
                    if leader not in leader_to_clusters:
                        leader_to_clusters[leader] = []
                    leader_to_clusters[leader].append(cluster)

                # Merge each group
                final_merged = []
                processed = set()
                for i, cluster in enumerate(merged_clusters):
                    leader = indices_to_merge.get(i, i)
                    if leader in processed:
                        continue
                    processed.add(leader)
                    group = leader_to_clusters.get(leader, [cluster])
                    if len(group) > 1:
                        final_merged.append(self._merge_cluster_group(group))
                    else:
                        final_merged.append(cluster)

                merged_clusters = final_merged
                logger.info(f"[MERGE-CLUSTERS] After similarity pass: {len(merged_clusters)} clusters")

        logger.info(f"[MERGE-CLUSTERS] Final: reduced from {len(clusters)} to {len(merged_clusters)} clusters")
        return merged_clusters

    def _merge_cluster_group(self, clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple clusters into a single cluster."""
        if not clusters:
            return {}
        if len(clusters) == 1:
            return clusters[0]

        # Use the first verified cluster as the base
        verified_clusters = [c for c in clusters if c.get("verified", False)]
        base_cluster = verified_clusters[0] if verified_clusters else clusters[0]

        # Collect all citations and members from all clusters
        all_citations = []
        all_members = []
        for cluster in clusters:
            all_citations.extend(cluster.get("citations", []))
            all_members.extend(cluster.get("cluster_members", []))

        # Remove duplicates from members while preserving order
        seen_members = set()
        unique_members = []
        for member in all_members:
            # Extract citation text as the deduplication key (dicts are unhashable)
            member_key = member.get("citation", "") if isinstance(member, dict) else member
            if member_key not in seen_members:
                seen_members.add(member_key)
                unique_members.append(member)

        # Remove duplicate citations by citation text
        seen_citations = set()
        unique_citations = []
        for cit in all_citations:
            cit_text = cit.get("citation", str(cit))
            if cit_text not in seen_citations:
                seen_citations.add(cit_text)
                unique_citations.append(cit)

        # Create merged cluster
        merged = base_cluster.copy()
        merged["cluster_members"] = unique_members
        merged["citations"] = unique_citations
        merged["cluster_size"] = len(unique_citations)
        merged["merged_from"] = len(clusters)  # Track that this was merged

        logger.info(f"[MERGE-CLUSTER] Merged {len(clusters)} clusters into 1 with {len(unique_citations)} citations")

        return merged

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
        """Build clusters from parallel links and proximity; include singletons.
        Returns (clusters_as_lists_of_citation_strings, citation_to_cluster_index).
        """
        # Build adjacency based on current parallel_citations
        adj: dict[str, set[str]] = {}

        def add_edge(a: str, b: str) -> None:
            if not a or not b or a == b:
                return
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)

        # Seed nodes
        for c in citations:
            adj.setdefault(c.citation, set())

        # Use declared parallel links where both endpoints are real citations
        citation_set = {c.citation for c in citations}
        for c in citations:
            for p in c.parallel_citations or []:
                if p in citation_set:
                    add_edge(c.citation, p)

        # Connected components
        visited: set[str] = set()
        clusters: list[list[str]] = []
        citation_to_cluster: dict[str, int] = {}
        for node in adj.keys():
            if node in visited:
                continue
            stack = [node]
            comp: list[str] = []
            visited.add(node)
            while stack:
                v = stack.pop()
                comp.append(v)
                for w in adj.get(v, ()):
                    if w not in visited:
                        visited.add(w)
                        stack.append(w)
            # Always include singleton clusters to avoid "missing cluster" warnings
            comp_sorted = sorted(comp)
            idx = len(clusters)
            clusters.append(comp_sorted)
            for cit in comp_sorted:
                citation_to_cluster[cit] = idx
        return clusters, citation_to_cluster


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
    - processor.process_text()
    - process_any_input()
    - extract_citations_clean()
    - extract_citations_production()

    ALL requests should use this function going forward.
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


# BACKWARD COMPATIBILITY WRAPPERS
async def process_text_legacy(text: str) -> Dict[str, Any]:
    """Legacy wrapper for UnifiedCitationProcessorV2.process_text()"""
    return await process_citations_unified(text, processing_mode="legacy")


def process_any_input_legacy(input_data: Any) -> Dict[str, Any]:
    """Legacy wrapper for unified_input_processor.process_any_input()"""
    if isinstance(input_data, str):
        # Run the async function in event loop
        return asyncio.run(process_citations_unified(input_data, processing_mode="sync"))
    else:
        raise ValueError("Only text input is supported in unified pipeline")


def extract_citations_clean_legacy(text: str) -> List[CitationResult]:
    """Legacy wrapper for clean_extraction_pipeline.extract_citations_clean()"""
    result = asyncio.run(process_citations_unified(text, processing_mode="clean"))
    # Convert back to CitationResult objects if needed
    from src.models import CitationResult

    citations = []
    for cit_dict in result.get("citations", []):
        citations.append(
            CitationResult(
                citation=cit_dict.get("citation", ""),
                extracted_case_name=cit_dict.get("extracted_case_name", ""),
                extracted_date=cit_dict.get("extracted_date", ""),
                canonical_name=cit_dict.get("canonical_name", ""),
                canonical_date=cit_dict.get("canonical_date", ""),
                verified=cit_dict.get("verified", False),
                true_by_parallel=cit_dict.get("true_by_parallel", False),
                start_index=cit_dict.get("start_index"),
                end_index=cit_dict.get("end_index"),
                method=cit_dict.get("method", ""),
                confidence=cit_dict.get("confidence", 0.0),
            )
        )
    return citations


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
