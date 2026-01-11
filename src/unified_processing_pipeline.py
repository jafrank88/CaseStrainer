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
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from src.models import CitationResult
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Import clustering function from correct module
try:
    from src.unified_clustering_master import cluster_citations_unified_master
except ImportError:
    # Fallback: define stub if import fails
    cluster_citations_unified_master = None

logger = logging.getLogger(__name__)


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
        logger.info(f"[PIPELINE-{self.trace_id}] Stage: {stage_name} (t+{elapsed:.2f}s)")
        if data is not None:
            logger.debug(f"[PIPELINE-{self.trace_id}] {stage_name} data: {str(data)}")

    def add_error(self, error: str, stage: Optional[str] = None):
        """Record error for debugging"""
        error_msg = f"Error in {stage or self.current_stage}: {error}"
        self.errors.append(error_msg)
        logger.error(f"[PIPELINE-{self.trace_id}] {error_msg}")


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

        # CRITICAL FIX: Extract document primary case name for contamination filtering
        from src.unified_clustering_master import UnifiedClusteringMaster

        clustering_master = UnifiedClusteringMaster()
        document_primary_case_name = clustering_master._extract_document_primary_case_name(text)

        if document_primary_case_name:
            logger.info(f"[PIPELINE-{context.trace_id}] Document primary case detected: '{document_primary_case_name}'")
            self.processor.document_primary_case_name = document_primary_case_name
        else:
            logger.info(f"[PIPELINE-{context.trace_id}] No document primary case name detected")

        logger.info(f"[PIPELINE-{context.trace_id}] Starting unified processing for {len(text)} chars")
        logger.info(f"[PIPELINE-{context.trace_id}] Verification enabled: {enable_verification}")

        try:
            # STAGE 1: Citation Extraction
            context.trace_stage("extraction")
            extraction_result = await self._extract_citations(text, context)
            citations = extraction_result.get("citations", [])

            # STAGE 2: Citation Verification (only if enabled)
            context.trace_stage("verification")
            if enable_verification:
                logger.info(f"[PIPELINE-{context.trace_id}] Verification enabled, running verification...")
                verified_citations = await self._verify_citations(citations, text, context)
            else:
                logger.info(f"[PIPELINE-{context.trace_id}] Verification disabled, skipping verification")
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
            result = await self._format_response(citations, context)

            # SUCCESS - Complete processing
            context.trace_stage("completed")
            elapsed = time.time() - context.start_time
            logger.info(f"[PIPELINE-{context.trace_id}] Processing completed in {elapsed:.2f}s")

            return result

        except Exception as e:
            context.add_error(str(e), "pipeline_error")
            logger.error(f"[PIPELINE-{context.trace_id}] Pipeline failed: {e}", exc_info=True)
            return self._format_error_response(context, str(e))

    async def _extract_citations(self, text: str, context: ProcessingContext) -> Dict[str, Any]:
        """Stage 1: Extract citations using the clean pipeline"""
        try:
            # Use the proven UnifiedCitationProcessorV2
            result = await self.processor.process_text(text)
            context.metadata["extraction_count"] = len(result.get("citations", []))
            return result
        except Exception as e:
            context.add_error(str(e), "extraction")
            raise

    async def _verify_citations(
        self, citations: List[CitationResult], text: str, context: ProcessingContext
    ) -> List[CitationResult]:
        """Stage 2: Verify citations and get canonical data with timeout protection"""
        try:
            logger.info(f"[PIPELINE-{context.trace_id}] Starting verification for {len(citations)} citations")

            # ASYNC VERIFICATION TIMEOUT GUARD
            # Add timeout protection to prevent hanging in async workers
            import asyncio

            async def verify_with_timeout():
                # Use the sync verification method (proven to work)
                return self.processor._verify_citations_sync(citations, text)

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
            logger.error(f"[PIPELINE-{context.trace_id}] VERIFICATION FAILED: {str(e)}", exc_info=True)
            context.add_error(str(e), "verification")
            # Return original citations if verification fails
            return citations

    async def _apply_parallel_verification(
        self, citations: List[CitationResult], context: ProcessingContext
    ) -> List[CitationResult]:
        """Stage 3: Apply parallel verification - GUARANTEED EXECUTION"""
        try:
            print(f"[DEBUG] UNIFIED PIPELINE: Applying parallel verification to {len(citations)} citations")
            logger.info(f"[PIPELINE-{context.trace_id}] Applying parallel verification to {len(citations)} citations")

            # Ensure proximity-based parallel links are present, then propagate
            try:
                self.processor.ensure_bidirectional_parallels(citations)
            except Exception:
                pass
            self.processor.propagate_canonical_to_cluster(citations)

            # Count parallel verifications
            parallel_count = sum(1 for c in citations if getattr(c, "true_by_parallel", False))
            context.metadata["parallel_verifications"] = parallel_count

            print(f"[DEBUG] UNIFIED PIPELINE: Parallel verification completed - {parallel_count} citations marked")
            logger.info(
                f"[PIPELINE-{context.trace_id}] Parallel verification completed - {parallel_count} citations marked"
            )

            return citations

        except Exception as e:
            context.add_error(str(e), "parallel_verification")
            logger.warning(f"[PIPELINE-{context.trace_id}] Parallel verification failed (non-critical): {e}")
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

                    # CRITICAL FIX: When extraction fails (N/A) but verification succeeded,
                    # use canonical_name as extracted_case_name for better user experience
                    # This prevents showing "N/A" when we actually know the case name
                    if (cleaned_name == "N/A" or not cleaned_name) and canonical_name and canonical_name != "N/A":
                        logger.info(
                            f"[FORMAT-RESPONSE] Using canonical_name '{canonical_name}' as extracted_case_name (extraction returned N/A)"
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
                        else:
                            logger.debug(
                                f"[POST-PROCESS-CONTAMINATION] ✓ Keeping name '{cleaned_name}' (does not match primary '{document_primary_case_name}')"
                            )

                    # CRITICAL: Do NOT replace extracted_case_name with canonical_name
                    # This was previously causing contamination by overwriting extracted data with canonical data
                    # Instead, just flag the mismatch - the comparison logic will handle it properly
                    # The extracted_case_name must ONLY come from document extraction
                    if cleaned_name and cleaned_name != "N/A" and canonical_name and canonical_name != "N/A":
                        if cleaned_name.lower() != canonical_name.lower():
                            # Log the mismatch but do NOT overwrite extracted with canonical
                            logger.info(
                                f"[DATA-SEPARATION] Extracted '{cleaned_name}' differs from canonical '{canonical_name}' - keeping both separate"
                            )
                            cit_dict["name_mismatch"] = True

                    cit_dict["extracted_case_name"] = cleaned_name

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
                logger.warning(f"[PIPELINE-{context.trace_id}] Failed to annotate mismatch flags: {e}", exc_info=True)

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
                    clusters = cluster_citations_unified_master(
                        citation_dicts, original_text=context.input_text, enable_verification=False  # Already verified
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

            # FIX DEC 2025: ALWAYS merge clusters with same canonical_name to reduce duplicates
            # This catches cases like Clarke v. Tri-Cities appearing 4 times
            clusters = self._merge_clusters_by_canonical_name(clusters)
            context.metadata["cluster_count"] = len(clusters)

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
                # Filter short-form citations (e.g., "346 F.R.D. at 105")
                if " at " in citation_text:
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
            logger.info(f"[PIPELINE-{context.trace_id}] After filtering Id./short-form from clusters: {len(clusters)} clusters remain")

            # FILTER: Also remove Id. and short-form citations from the main citations list
            original_count = len(citation_dicts)
            citation_dicts = [
                cit for cit in citation_dicts
                if not should_filter_citation(cit.get("citation", ""))
            ]
            logger.info(f"[PIPELINE-{context.trace_id}] After filtering Id./short-form from main list: {len(citation_dicts)}/{original_count} citations remain")

            # Build citation to cluster mapping
            citation_to_cluster = {}
            for i, cluster in enumerate(clusters):
                f"cluster_{i + 1}"
                for member in cluster.get("cluster_members", []):
                    # Extract citation text from member (could be dict or string)
                    citation_key = member.get("citation", "") if isinstance(member, dict) else member
                    if citation_key:
                        citation_to_cluster[citation_key] = i

            # Update citations with cluster information
            for cit_dict in citation_dicts:
                cluster_index = citation_to_cluster.get(cit_dict["citation"])
                if cluster_index is not None:
                    cit_dict["cluster_id"] = f"cluster_{cluster_index + 1}"
                    # Add cluster information from clustering master
                    cluster = clusters[cluster_index]
                    cit_dict["cluster_case_name"] = cluster.get("cluster_case_name")
                    cit_dict["cluster_year"] = cluster.get("cluster_year")
                    cit_dict["cluster_size"] = cluster.get("cluster_size")
                    cit_dict["is_in_cluster"] = True
                else:
                    cit_dict["cluster_id"] = None
                    cit_dict["cluster_case_name"] = None
                    cit_dict["cluster_year"] = None
                    cit_dict["cluster_size"] = 1
                    cit_dict["is_in_cluster"] = False

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
            cluster_members = [c["citation"] for c in citations]

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
            for cit in citations:
                extracted_name = cit.get("extracted_case_name") or cit.get("submitted_display_name")
                if extracted_name and not is_generic_or_truncated(extracted_name):
                    if len(extracted_name) > best_extracted_name_length:
                        best_extracted_name = extracted_name
                        best_extracted_name_length = len(extracted_name)

            # Fallback to primary citation's extracted name if no better name found
            if not best_extracted_name:
                best_extracted_name = primary_citation.get("submitted_display_name") or primary_citation.get(
                    "extracted_case_name"
                )

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

            # USER FIX: Find best canonical data from ANY verified citation in the cluster
            # The primary_citation might not be verified, so we need to check all citations
            best_canonical_name = None
            best_canonical_date = None
            best_canonical_url = None
            for cit in citations:
                if cit.get("verified", False) and cit.get("canonical_name"):
                    best_canonical_name = cit.get("canonical_name")
                    best_canonical_date = cit.get("canonical_date")
                    best_canonical_url = cit.get("canonical_url")
                    break  # Use first verified citation's canonical data

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
                # Frontend-expected fields for display
                "verifying_display_name": best_canonical_name or cluster_case_name,  # USER FIX: Use best canonical
                "verifying_display_date": best_canonical_date or cluster_year,
                "submitted_display_name": best_extracted_name,  # Use best extracted name from all citations
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

        # Group clusters by canonical_name
        canonical_to_clusters = {}
        for cluster in clusters:
            canonical_name = cluster.get("canonical_name")
            if canonical_name and canonical_name != "N/A":
                # Normalize the canonical name for comparison
                norm_name = canonical_name.lower().strip()
                if norm_name not in canonical_to_clusters:
                    canonical_to_clusters[norm_name] = []
                canonical_to_clusters[norm_name].append(cluster)

        # Merge clusters with the same canonical name
        merged_clusters = []
        merged_canonical_names = set()

        for cluster in clusters:
            canonical_name = cluster.get("canonical_name")
            if canonical_name and canonical_name != "N/A":
                norm_name = canonical_name.lower().strip()

                # Skip if we've already merged this canonical name
                if norm_name in merged_canonical_names:
                    continue

                # Get all clusters with this canonical name
                same_case_clusters = canonical_to_clusters.get(norm_name, [cluster])

                if len(same_case_clusters) > 1:
                    # Merge multiple clusters into one
                    logger.info(f"[MERGE-CLUSTERS] Merging {len(same_case_clusters)} clusters for '{canonical_name}'")
                    merged_cluster = self._merge_cluster_group(same_case_clusters)
                    merged_clusters.append(merged_cluster)
                else:
                    merged_clusters.append(cluster)

                merged_canonical_names.add(norm_name)
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
                canonical_date = cluster.get("canonical_date", "")
                canonical_name = cluster.get("canonical_name", "")
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
