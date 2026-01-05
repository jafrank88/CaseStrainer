"""
Unified Clustering Master
=========================

This module provides THE SINGLE, AUTHORITATIVE clustering implementation
that consolidates the best features from all 45+ duplicate clustering functions.

ALL OTHER CLUSTERING FUNCTIONS SHOULD BE DEPRECATED AND REPLACED WITH THIS ONE.

Key Features Consolidated:
- Parallel citation detection (proximity + pattern-based)
- Case name and year extraction from clusters
- Metadata propagation within clusters
- Cluster merging and deduplication
- Verification integration
- Comprehensive validation
- Performance optimization
- Detailed logging and debugging
"""

import re
import logging
import time
from typing import Dict, Any, Optional, List, Set, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter, deque

logger = logging.getLogger(__name__)


class ClusterType(Enum):
    """Types of citation clusters."""

    PARALLEL = "parallel"
    CANONICAL = "canonical"
    EXTRACTED = "extracted"
    MIXED = "mixed"


@dataclass
class ClusterResult:
    """Standardized result from clustering."""

    cluster_id: str
    cluster_type: ClusterType
    case_name: Optional[str] = None
    case_year: Optional[str] = None
    citations: List[Any] = None
    size: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    verification_status: Optional[str] = None


class UnifiedClusteringMaster:
    """
    THE SINGLE, AUTHORITATIVE clustering implementation.

    This class consolidates the best features from:
    - unified_citation_clustering.py (7+ functions)
    - enhanced_clustering.py (8+ functions)
    - services/citation_clusterer.py (7+ functions)
    - citation_clustering.py (3+ functions)
    - enhanced_sync_processor.py (5+ functions)
    - All other duplicate clustering functions

    ALL clustering should go through this class.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the master clustering engine."""
        self.config = config or {}
        self.debug_mode = self.config.get("debug_mode", False)
        self.min_cluster_size = self.config.get("min_cluster_size", 1)
        self.case_name_similarity_threshold = self.config.get(
            "case_name_similarity_threshold", 0.95
        )  # FIX #58E: Raised from 0.6 to prevent different cases from clustering
        self.proximity_threshold = self.config.get(
            "proximity_threshold", 150
        )  # CRITICAL FIX: Increased from 50 to 150 for dense legal documents (Nov 2025)
        self.enable_verification = self.config.get("enable_verification", True)

        self._setup_patterns()
        logger.info("UnifiedClusteringMaster initialized - all duplicate clusterers deprecated")

    def _setup_patterns(self):
        """Setup regex patterns for clustering."""
        self.patterns = {
            # Parallel citation patterns
            "washington_parallel": re.compile(r"(\d+)\s+(?:Wn\.|Wash\.)\d*d\s+\d+.*?(\d+)\s+(?:P\.|A\.)\d*d\s+\d+"),
            "federal_parallel": re.compile(r"(\d+)\s+F\.\d*d\s+\d+.*?(\d+)\s+U\.S\.\s+\d+"),
            "supreme_parallel": re.compile(r"(\d+)\s+S\.\s*Ct\.\s+\d+.*?(\d+)\s+L\.\s*Ed\.\d*d\s+\d+"),
            "generic_parallel": re.compile(r"(\d+)\s+[A-Z][a-z]*\.\d*d?\s+\d+.*?(\d+)\s+[A-Z][a-z]*\.\d*d?\s+\d+"),
            # Citation separators
            "separator_patterns": re.compile(r"[;,]\s*(?:see\s+)?(?:also\s+)?"),
            "case_name_v": re.compile(r"([A-Z][A-Za-z0-9&\'\\s-]+)\\s+v\\.\\s+([A-Z][A-Za-z0-9&\'\\s-]+)"),
            "case_name_in_re": re.compile(r"(In\\s+re\\s+[A-Z][a-zA-Z\\s\'&\\-\\.]{2,80})", re.IGNORECASE),
            "case_name_state": re.compile(
                r"(State|People|Commonwealth)\\s+v\\.\\s+([A-Z][a-zA-Z\\s\'&\\-\\.]{2,80})", re.IGNORECASE
            ),
            # Year patterns
            "year_patterns": re.compile(r"\((\d{4})\)|\b(19|20)\d{2}\b"),
        }

    # -----------------------
    # Helper Scoring Methods
    # -----------------------

    def _select_best_case_name(self, group: List[Any]) -> Optional[str]:
        """Return the highest-quality case name available in the group."""
        candidates: List[Tuple[float, str]] = []

        for citation in group:
            if isinstance(citation, dict):
                possible_names = [
                    citation.get("canonical_name"),
                    citation.get("extracted_case_name"),
                    citation.get("cluster_case_name"),
                ]
            else:
                possible_names = [
                    getattr(citation, "canonical_name", None),
                    getattr(citation, "extracted_case_name", None),
                    getattr(citation, "cluster_case_name", None),
                ]

            for name in possible_names:
                if not name or not isinstance(name, str):
                    continue
                # FIX: Skip truncated names like "Noem v. Nat", "Inc. v. Ball Corp.", "Scott Timber Co. v. United Sta"
                # These are from eyecite and are incomplete
                if self._is_truncated_name(name):
                    logger.info(f"[CLUSTERING-SKIP-TRUNCATED] Skipping truncated name: '{name}'")
                    continue
                # CRITICAL FIX: Clean the case name to remove sentence fragments
                cleaned = self._clean_case_name_from_extraction(name.strip())
                if cleaned and cleaned not in ("N/A", "Unknown", "Unknown Case"):
                    candidates.append((self._score_case_name(cleaned), cleaned))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _is_truncated_name(self, name: str) -> bool:
        """Check if a case name appears truncated."""
        if not name or name == "N/A":
            return False

        # Check for truncation patterns
        # Pattern 1: Ends with "v. [1-3 letters]" like "Noem v. Nat"
        if re.search(r"v\.\s+[A-Z][a-z]{0,2}$", name):
            return True

        # Pattern 2: Starts with short word like "Inc. v." without full company name
        if re.match(r"^(Inc\.|LLC|Corp\.|Co\.|Ltd\.)\s+v\.", name):
            return True

        # Pattern 3: Ends mid-word (no punctuation at end, last word < 4 chars)
        words = name.split()
        if words and len(words[-1]) < 4 and not name[-1] in ".,:;)":
            return True

        return False

    def _clean_case_name_from_extraction(self, case_name: str) -> str:
        """Clean case name by removing sentence fragments and other contamination."""
        if not case_name or case_name in ("N/A", "Unknown", "Unknown Case"):
            return case_name

        # Remove sentence fragments that appear before the actual case name
        # Look for patterns like "scheme as a whole. Ass'n of..." and keep only "Ass'n of..."
        # Match: sentence-ending period followed by spaces, then case name with "v."
        case_name_match = re.search(r"\.\s+([A-Z].+?\s+v\.\s+.+?)$", case_name)
        if case_name_match and " v. " in case_name_match.group(1):
            case_name = case_name_match.group(1).strip()

        # Normalize whitespace
        case_name = re.sub(r"\s+", " ", case_name)

        return case_name

    def _score_case_name(self, name: str) -> float:
        """Score case name quality for comparison."""
        score = 0.0
        lowered = name.lower()

        if " v. " in lowered or lowered.startswith("state v") or lowered.startswith("people v"):
            score += 2.0
        if lowered.startswith("in re") or lowered.startswith("ex parte"):
            score += 1.5

        score += min(len(name) / 25.0, 2.0)

        if "unknown" in lowered:
            score -= 1.0

        return score

    def _select_best_extracted_name(self, group: List[Any]) -> Optional[str]:
        """
        Select the best EXTRACTED case name for cluster-level naming.

        CRITICAL: This function prioritizes extracted_case_name (from the document)
        over canonical_name (from APIs) because:
        1. Extracted names represent what's actually written in the document
        2. Canonical names from APIs may be wrong or N/A
        3. Cluster naming should reflect document content, not API data

        This is specifically for cluster.extracted_case_name field.
        For individual citation verification, use canonical_name.
        """
        candidates: List[Tuple[float, str]] = []

        for citation in group:
            if isinstance(citation, dict):
                # PRIORITY ORDER: extracted > cluster > canonical
                # Canonical is last because it's from APIs and may not match document
                possible_names = [
                    citation.get("extracted_case_name"),  # Priority 1: From document
                    citation.get("cluster_case_name"),  # Priority 2: Cluster aggregate
                    citation.get("canonical_name"),  # Priority 3: From API (may be wrong)
                ]
            else:
                possible_names = [
                    getattr(citation, "extracted_case_name", None),
                    getattr(citation, "cluster_case_name", None),
                    getattr(citation, "canonical_name", None),
                ]

            for name in possible_names:
                if not name or not isinstance(name, str):
                    continue
                # Skip truncated names
                if self._is_truncated_name(name):
                    logger.info(f"[CLUSTERING-SKIP-TRUNCATED] Skipping truncated name: '{name}'")
                    continue
                # Clean the case name
                cleaned = self._clean_case_name_from_extraction(name.strip())
                if cleaned and cleaned not in ("N/A", "Unknown", "Unknown Case"):
                    candidates.append((self._score_case_name(cleaned), cleaned))
                    break  # Use first valid name from priority list

        if not candidates:
            logger.warning(f"[CLUSTER-NAME] No valid extracted names found in group of {len(group)} citations")
            return None

        # Sort by score and return best
        candidates.sort(key=lambda item: item[0], reverse=True)
        best_name = candidates[0][1]
        logger.info(f"[CLUSTER-NAME] Selected best extracted name: '{best_name}' from {len(candidates)} candidates")
        return best_name

    def _select_best_case_year(self, group: List[Any]) -> Optional[str]:
        """Return the most consistent year across the group."""
        year_sources = ["canonical_date", "extracted_date", "cluster_year"]

        for source in year_sources:
            values: List[str] = []
            for citation in group:
                if isinstance(citation, dict):
                    raw_value = citation.get(source)
                else:
                    raw_value = getattr(citation, source, None)

                year = self._extract_year_value(raw_value)
                if year:
                    values.append(year)

            if values:
                most_common_year, _ = Counter(values).most_common(1)[0]
                return most_common_year

        return None

    def _extract_year_value(self, value: Optional[Any]) -> Optional[str]:
        if not value or value in ("N/A", "Unknown", ""):
            return None

        if isinstance(value, int):
            return str(value)

        if isinstance(value, str):
            match = re.search(r"(19|20)\d{2}", value)
            if match:
                return match.group(0)

        return None

    def _should_replace_case_name(self, existing: Optional[str], candidate: Optional[str]) -> bool:
        if not candidate:
            return False
        if not existing or existing in ("", "N/A", "Unknown", "Unknown Case"):
            return True
        return self._score_case_name(candidate) > self._score_case_name(existing)

    def cluster_citations(
        self, citations: List[Any], original_text: str = "", enable_verification: bool = None, request_id: str = "", progress_callback: Optional[Callable[[int, str, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        THE MASTER CLUSTERING FUNCTION

        This is THE ONLY function that should be used for citation clustering.
        It consolidates all the best features from duplicate functions.

        Args:
            citations: List of citation objects to cluster
            original_text: Original text for context (optional)
            enable_verification: Whether to verify citations (optional)
            request_id: Request ID for logging (optional)

        Returns:
            List of cluster dictionaries with comprehensive metadata
        """
        start_time = time.time()

        # Use instance setting if not explicitly overridden
        if enable_verification is None:
            enable_verification = self.enable_verification

        # FIX: Extract document's primary case name for contamination filtering
        self.document_primary_case_name = self._extract_document_primary_case_name(original_text)
        if self.document_primary_case_name:
            logger.warning(
                f"[CONTAMINATION-FILTER] Document primary case detected: '{self.document_primary_case_name}'"
            )

        # CRITICAL: Use ERROR level to ensure this appears in logs
        logger.error(
            f"[CLUSTER-ENTRY] Starting clustering: {len(citations)} citations, verification={enable_verification}"
        )
        logger.info(
            f"[MASTER_CLUSTER] Starting clustering for {len(citations)} citations (verification: {enable_verification})"
        )
        # print(f"CLUSTER ENTRY POINT HIT - {len(citations)} citations", flush=True)  # DISABLED

        # CRITICAL FIX: Apply verification paradox fix before clustering
        # CRITICAL FIX: If verified=False, clear canonical data (opposite of old "paradox fix")
        # Unverified citations CANNOT have canonical data unless true_by_parallel=True
        canonical_data_cleared = 0
        for citation in citations:
            if isinstance(citation, dict):
                is_verified = citation.get("verified", False)
                has_true_by_parallel = citation.get("true_by_parallel", False)
                has_canonical_data = (
                    citation.get("canonical_name") or citation.get("canonical_date") or citation.get("canonical_url")
                )
                # CRITICAL: Clear canonical data if unverified AND not true_by_parallel AND not year_mismatch_rejected
                # year_mismatch_rejected citations PRESERVE canonical data for cluster splitting by year
                is_year_mismatch = citation.get("source") == "year_mismatch_rejected"
                if not is_verified and not has_true_by_parallel and not is_year_mismatch and has_canonical_data:
                    citation["canonical_name"] = None
                    citation["canonical_date"] = None
                    citation["canonical_url"] = None
                    canonical_data_cleared += 1
                    logger.warning(
                        f"[CLUSTER-CLEANUP] {citation.get('citation')}: Cleared canonical data (verified=False, true_by_parallel=False)"
                    )
            elif hasattr(citation, "__dict__"):
                is_verified = getattr(citation, "verified", False)
                has_true_by_parallel = getattr(citation, "true_by_parallel", False)
                has_canonical_data = (
                    getattr(citation, "canonical_name", None)
                    or getattr(citation, "canonical_date", None)
                    or getattr(citation, "canonical_url", None)
                )
                # CRITICAL: Clear canonical data if unverified AND not true_by_parallel AND not year_mismatch_rejected
                # year_mismatch_rejected citations PRESERVE canonical data for cluster splitting by year
                is_year_mismatch = getattr(citation, "source", None) == "year_mismatch_rejected"
                if not is_verified and not has_true_by_parallel and not is_year_mismatch and has_canonical_data:
                    citation.canonical_name = None
                    citation.canonical_date = None
                    citation.canonical_url = None
                    canonical_data_cleared += 1
                    logger.warning(
                        f"[CLUSTER-CLEANUP] {citation.citation}: Cleared canonical data (verified=False, true_by_parallel=False)"
                    )

        if canonical_data_cleared > 0:
            logger.info(f"[CLUSTER-CLEANUP] Cleared canonical data from {canonical_data_cleared} unverified citations")

        if not citations:
            logger.warning("MASTER_CLUSTER: No citations provided")
            return []

        try:
            # Step 1: Detect parallel citations and create initial groups
            logger.info("MASTER_CLUSTER: Step 1 - Detecting parallel citations")
            logger.error(f"[CLUSTER-DEBUG] Input: {len(citations)} citations")
            
            # Update progress for parallel detection
            if progress_callback:
                progress_callback(72, "Clustering", "Detecting parallel citations...")

            # Sample first 3 citations to see their structure
            for i, cit in enumerate(citations[:3]):
                cit_text = getattr(cit, "citation", str(cit)) if hasattr(cit, "citation") else str(cit)
                has_position = hasattr(cit, "start_index") or (isinstance(cit, dict) and "start_index" in cit)
                position = (
                    getattr(cit, "start_index", None)
                    if hasattr(cit, "start_index")
                    else (cit.get("start_index") if isinstance(cit, dict) else None)
                )
                logger.error(
                    f"[CLUSTER-DEBUG] Citation {i+1}: {cit_text}, has_position={has_position}, position={position}"
                )

            parallel_groups = self._detect_parallel_citations(citations, original_text)
            logger.info(f"MASTER_CLUSTER: Created {len(parallel_groups)} parallel groups")
            logger.error(
                f"[CLUSTER-DEBUG] Output: {len(parallel_groups)} parallel groups (expected < {len(citations)} if parallels detected)"
            )

            # Show size of first few groups
            for i, group in enumerate(parallel_groups[:5]):
                logger.error(f"[CLUSTER-DEBUG] Group {i+1} size: {len(group)} citations")

            # DEBUG: Find Hamaatsa citations and see if they're grouped together
            for i, group in enumerate(parallel_groups):
                hamaatsa_in_group = []
                for cit in group:
                    cit_text = getattr(cit, "citation", str(cit)) if hasattr(cit, "citation") else str(cit)
                    if "388 P.3d 977" in cit_text or "2017-NM-007" in cit_text:
                        hamaatsa_in_group.append(cit_text)
                if hamaatsa_in_group:
                    logger.error(
                        f"[ERROR] [HAMAATSA-CLUSTER] Group {i+1} contains {len(hamaatsa_in_group)} Hamaatsa citation(s): {hamaatsa_in_group}"
                    )
                    logger.error(f"[ERROR] [HAMAATSA-CLUSTER] Group {i+1} total size: {len(group)} citations")

            # Step 2: Extract and propagate metadata within groups
            logger.info("MASTER_CLUSTER: Step 2 - Extracting and propagating metadata")
            if progress_callback:
                progress_callback(75, "Clustering", "Extracting citation metadata...")
            enhanced_citations = self._extract_and_propagate_metadata(citations, parallel_groups, original_text)
            logger.info(f"MASTER_CLUSTER: Enhanced {len(enhanced_citations)} citations")

            # Step 3: Create final clusters by metadata similarity
            logger.info("MASTER_CLUSTER: Step 3 - Creating final clusters")
            if progress_callback:
                progress_callback(80, "Clustering", "Creating citation clusters...")
            final_clusters = self._create_final_clusters(enhanced_citations)
            logger.info(f"MASTER_CLUSTER: Created {len(final_clusters)} final clusters")

            # DEBUG: Check Hamaatsa citations in final clusters
            for i, cluster in enumerate(final_clusters):
                cluster_cits = cluster.get("citations", [])
                hamaatsa_in_cluster = []
                for cit in cluster_cits:
                    cit_text = (
                        getattr(cit, "citation", str(cit))
                        if hasattr(cit, "citation")
                        else (cit.get("citation") if isinstance(cit, dict) else str(cit))
                    )
                    if "388 P.3d 977" in cit_text or "2017-NM-007" in cit_text:
                        hamaatsa_in_cluster.append(cit_text)
                if hamaatsa_in_cluster:
                    logger.error(
                        f"[SUCCESS] [HAMAATSA-FINAL] Cluster {i+1} contains {len(hamaatsa_in_cluster)} Hamaatsa citation(s): {hamaatsa_in_cluster}"
                    )
                    logger.error(f"[SUCCESS] [HAMAATSA-FINAL] Cluster {i+1} total size: {len(cluster_cits)} citations")

            # Step 4: Apply verification if enabled
            if enable_verification:
                logger.info("MASTER_CLUSTER: Step 4 - Applying verification")
                if progress_callback:
                    progress_callback(85, "Clustering", "Verifying citations...")
                # CRITICAL FIX: Set instance variable before calling verification
                # so _apply_verification_to_clusters uses the correct value
                self.enable_verification = enable_verification
                self._apply_verification_to_clusters(final_clusters)

            # Step 4.5: FIX #22 - Validate canonical consistency
            # CRITICAL: This runs EVEN IF enable_verification=False because verification
            # may have been done externally (before clustering). We check for canonical data.
            logger.info("MASTER_CLUSTER: Step 4.5 - Validating canonical consistency (Fix #22)")
            if progress_callback:
                progress_callback(88, "Clustering", "Validating cluster consistency...")
            final_clusters = self._validate_canonical_consistency(final_clusters)
            logger.info(f"MASTER_CLUSTER: After canonical validation: {len(final_clusters)} clusters")

            # Step 4.6: Enrich extracted dates from canonical dates
            logger.info("MASTER_CLUSTER: Step 4.6 - Enriching dates from canonical data")
            self._enrich_dates_from_canonical(final_clusters)
            logger.info(f"MASTER_CLUSTER: Date enrichment complete")

            # Step 5: Merge and deduplicate clusters
            logger.info("MASTER_CLUSTER: Step 5 - Merging and deduplicating")
            merged_clusters = self._merge_and_deduplicate_clusters(final_clusters)
            logger.info(f"MASTER_CLUSTER: Final result: {len(merged_clusters)} clusters")

            # Step 5.5: Validate cluster integrity
            logger.info("MASTER_CLUSTER: Step 5.5 - Validating cluster integrity")
            validated_clusters = self._validate_clusters(merged_clusters, original_text)
            logger.info(f"MASTER_CLUSTER: Validated {len(validated_clusters)} clusters")

            # Step 6: Format clusters for output
            formatted_clusters = self._format_clusters_for_output(validated_clusters)

            elapsed_time = time.time() - start_time
            logger.info(
                f"[SUCCESS] MASTER_CLUSTER: Completed clustering in {elapsed_time:.2f}s - {len(formatted_clusters)} clusters"
            )

            return formatted_clusters

        except Exception as e:
            logger.error(f"[MASTER_CLUSTER] Clustering failed: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _detect_parallel_citations(self, citations: List[Any], text: str) -> List[List[Any]]:
        """Detect parallel citations using reporter heuristics and proximity analysis."""
        if not citations:
            return []

        parallel_groups: List[List[Any]] = []
        processed_ids: Set[int] = set()
        total = len(citations)

        adjacency: Dict[int, Set[int]] = {i: set() for i in range(total)}
        for i in range(total):
            for j in range(i + 1, total):
                if self._are_citations_parallel_pair(citations[i], citations[j], text):
                    adjacency[i].add(j)
                    adjacency[j].add(i)

        visited: Set[int] = set()
        for idx in range(total):
            if idx in visited:
                continue
            stack = [idx]
            component: List[int] = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        stack.append(neighbor)

            if len(component) > 1:
                group = [citations[i] for i in component]
                parallel_groups.append(group)
                for citation in group:
                    processed_ids.add(id(citation))

        remaining = [citation for citation in citations if id(citation) not in processed_ids]
        if remaining:
            proximity_groups = self._group_by_proximity(remaining, text)
            for group in proximity_groups:
                if len(group) >= 2 and self._are_parallel_citations(group, text):
                    parallel_groups.append(group)
                    for citation in group:
                        processed_ids.add(id(citation))

        # DISABLED 2025-11-09: Name-year-window grouping TOO AGGRESSIVE
        # Problem: Groups ALL citations between case name and year, even if they're different cases
        # Example: "Kammerer... 618 P.2d 1330... 879 F. Supp. 2d 1214... (1980)"
        #   - Both get grouped as Kammerer
        #   - But F. Supp. 2d didn't exist until 1998, can't be from 1980!
        # Solution: DISABLED this grouping method - too many false positives

        # remaining = [citation for citation in citations if id(citation) not in processed_ids]
        # if remaining:
        #     nyw_groups = self._group_by_name_year_window(remaining, text)
        #     for group in nyw_groups:
        #         if len(group) >= 2:
        #             logger.info(f"[NAME-YEAR-WINDOW] Found {len(group)} citations in same window (name..year)")
        #             parallel_groups.append(group)
        #             for citation in group:
        #                 processed_ids.add(id(citation))

        logger.info("[NAME-YEAR-WINDOW] DISABLED - was causing false groupings of unrelated citations")

        # DISABLED 2025-11-09 (Round 3): Canonical-based clustering CAUSES MORE HARM THAN GOOD
        # Problem: Groups citations by canonical data from verification
        # But verification can be WRONG or assign wrong canonical names
        # This causes "Erickson" to contaminate "Env't Def Fund" citations
        # Solution: DISABLE canonical-based grouping entirely

        # remaining = [citation for citation in citations if id(citation) not in processed_ids]
        # if remaining:
        #     canonical_groups = self._group_by_canonical_data(remaining)
        #     for group in canonical_groups:
        #         if len(group) >= 2:
        #             logger.info(f"CANONICAL-GROUPING: Found {len(group)} parallel citations by canonical data")
        #             parallel_groups.append(group)
        #             for citation in group:
        #                 processed_ids.add(id(citation))

        logger.info(
            "[CANONICAL-GROUPING] DISABLED - was causing wrong canonical names to propagate (e.g., Erickson → Env't Def Fund)"
        )

        for citation in citations:
            if id(citation) not in processed_ids:
                parallel_groups.append([citation])

        return parallel_groups

    def _group_by_proximity(self, citations: List[Any], text: str) -> List[List[Any]]:
        """Group citations by proximity in the text."""
        if not citations or not text:
            return [[citation] for citation in citations]

        # Sort citations by position
        sorted_citations = sorted(citations, key=lambda c: getattr(c, "start_index", 0))

        groups = []
        current_group = [sorted_citations[0]]

        logger.error(f"[PROXIMITY-DEBUG] Starting proximity grouping for {len(sorted_citations)} citations")
        logger.error(f"[PROXIMITY-DEBUG] Proximity threshold: {self.proximity_threshold} chars")

        for i in range(1, len(sorted_citations)):
            current_citation = sorted_citations[i]
            previous_citation = sorted_citations[i - 1]

            # Calculate distance
            current_start = getattr(current_citation, "start_index", 0)
            previous_end = getattr(previous_citation, "end_index", 0)
            distance = current_start - previous_end

            # Get citation text for logging
            prev_text = getattr(previous_citation, "citation", "Unknown")
            curr_text = getattr(current_citation, "citation", "Unknown")

            logger.error(f"[PROXIMITY-DEBUG] Comparing: '{prev_text}' → '{curr_text}'")
            logger.error(
                f"[PROXIMITY-DEBUG] Distance: {distance} chars (prev_end={previous_end}, curr_start={current_start})"
            )

            # USER FIX 2024-10-16: Check for semicolon boundary
            # Semicolons separate different cases, even if close together
            # Example: "...562 U.S. 42 (2011); Hamaatsa, Inc. v. Pueblo of San Felipe..."
            has_semicolon_boundary = False
            has_case_history_signal = False
            if text and previous_end < len(text) and current_start < len(text):
                text_between = text[previous_end:current_start]
                logger.error(f"[PROXIMITY-DEBUG] Text between: '{text_between}'")

                if ";" in text_between:
                    has_semicolon_boundary = True
                    logger.error(f"[PROXIMITY-DEBUG] SEMICOLON BOUNDARY - citations separated")

                # CRITICAL FIX 2024-12-21: Check for case history signals
                # aff'd, rev'd, affirmed, reversed, etc. indicate different court proceedings
                # Example: "63 Conn. App. 695, aff'd, 47 Conn. Supp. 113"
                case_history_patterns = [
                    r"\baff'?d\b",
                    r"\baffirmed\b",
                    r"\brev'?d\b",
                    r"\breversed\b",
                    r"\bvacated\b",
                    r"\bremanded\b",
                    r"\bmodified\b",
                    r"\boverruled\b",
                    r"\bcert\.\s*denied\b",
                    r"\bcert\.\s*granted\b",
                    r"\bappeal\s+from\b",
                    r"\bon\s+appeal\b",
                ]
                text_between_lower = text_between.lower()
                for pattern in case_history_patterns:
                    if re.search(pattern, text_between_lower):
                        has_case_history_signal = True
                        logger.error(f"[PROXIMITY-DEBUG] CASE HISTORY SIGNAL - citations from different proceedings")

            # CRITICAL FIX: Check if citations are from the same case before grouping by proximity
            are_same_case = self._are_citations_parallel_pair(previous_citation, current_citation, text)

            # CRITICAL FIX 2025-11-09 (Round 3): Even if proximity is close, check extracted names
            # Prevents grouping citations that happen to be close but are different cases
            # BUG FIX: Don't skip validation if one name is N/A - be MORE strict!
            names_compatible = True
            if distance <= self.proximity_threshold and not has_semicolon_boundary:
                # Get extracted names
                if isinstance(previous_citation, dict):
                    prev_name = previous_citation.get("extracted_case_name")
                else:
                    prev_name = getattr(previous_citation, "extracted_case_name", None)

                if isinstance(current_citation, dict):
                    curr_name = current_citation.get("extracted_case_name")
                else:
                    curr_name = getattr(current_citation, "extracted_case_name", None)

                # STRICTER VALIDATION: Check if we CAN validate
                prev_valid = prev_name and prev_name != "N/A"
                curr_valid = curr_name and curr_name != "N/A"

                if prev_valid and curr_valid:
                    # Both have names - check similarity
                    from difflib import SequenceMatcher

                    similarity = SequenceMatcher(None, prev_name.lower(), curr_name.lower()).ratio()

                    if similarity < 0.6:  # Less than 60% similar
                        names_compatible = False
                        logger.error(f"[PROXIMITY-DEBUG] ❌ REJECTING proximity group - names too different:")
                        logger.error(f"  Prev: '{prev_name}'")
                        logger.error(f"  Curr: '{curr_name}'")
                        logger.error(f"  Similarity: {similarity:.2%} < 60%")
                elif prev_valid and not curr_valid:
                    # Previous has name, current doesn't
                    # USER FIX: Allow grouping if VERY close (< 100 chars) - likely same citation string
                    if distance < 100:
                        names_compatible = True
                        logger.error(
                            f"[PROXIMITY-DEBUG] ✅ ALLOWING proximity group despite N/A (very close: {distance} chars):"
                        )
                        logger.error(f"  Prev: '{prev_name}' (valid)")
                        logger.error(f"  Curr: N/A (will inherit name from prev)")
                    else:
                        names_compatible = False
                        logger.error(f"[PROXIMITY-DEBUG] ❌ REJECTING proximity group - current has no name:")
                        logger.error(f"  Prev: '{prev_name}' (valid)")
                        logger.error(f"  Curr: N/A (invalid)")
                        logger.error(f"  REASON: Don't group N/A with valid names when far apart")
                elif not prev_valid and curr_valid:
                    # Current has name, previous doesn't
                    # USER FIX: Allow grouping if VERY close (< 100 chars) - likely same citation string
                    if distance < 100:
                        names_compatible = True
                        logger.error(
                            f"[PROXIMITY-DEBUG] ✅ ALLOWING proximity group despite N/A (very close: {distance} chars):"
                        )
                        logger.error(f"  Prev: N/A (will inherit name from curr)")
                        logger.error(f"  Curr: '{curr_name}' (valid)")
                    else:
                        names_compatible = False
                        logger.error(f"[PROXIMITY-DEBUG] ❌ REJECTING proximity group - previous has no name:")
                        logger.error(f"  Prev: N/A (invalid)")
                        logger.error(f"  Curr: '{curr_name}' (valid)")
                        logger.error(f"  REASON: Don't group N/A with valid names when far apart")
                # else: both N/A - allow grouping (they're both unknown)

            if (
                distance <= self.proximity_threshold
                and not has_semicolon_boundary
                and not has_case_history_signal
                and names_compatible
            ):
                if are_same_case:
                    logger.error(
                        f"[PROXIMITY-DEBUG] ✅ GROUPING citations (distance={distance} <= {self.proximity_threshold}) - same case"
                    )
                    current_group.append(current_citation)
                else:
                    # FIX DEC 2025: Even if are_same_case returns False, check if reporters are compatible parallel pairs
                    # This fixes cases like Ohio St. + N.E.2d where the parallel detection fails due to name validation
                    prev_text = getattr(previous_citation, "citation", "")
                    curr_text = getattr(current_citation, "citation", "")
                    reporters_compatible = (
                        self._match_parallel_patterns(prev_text, curr_text) if prev_text and curr_text else False
                    )

                    if reporters_compatible and distance < 100:  # Very close + compatible reporters = likely parallel
                        logger.error(
                            f"[PROXIMITY-DEBUG] ✅ GROUPING via reporter fallback (distance={distance}, compatible reporters)"
                        )
                        current_group.append(current_citation)
                    else:
                        logger.error(
                            f"[PROXIMITY-DEBUG] NOT GROUPING - different cases despite proximity (distance={distance})"
                        )
                        groups.append(current_group)
                        current_group = [current_citation]
            else:
                reason = (
                    "distance too large"
                    if distance > self.proximity_threshold
                    else (
                        "semicolon boundary"
                        if has_semicolon_boundary
                        else ("case history signal" if has_case_history_signal else "names incompatible")
                    )
                )
                logger.error(f"[PROXIMITY-DEBUG] NEW GROUP ({reason})")
                groups.append(current_group)
                current_group = [current_citation]

        if current_group:
            groups.append(current_group)

        logger.error(f"[PROXIMITY-DEBUG] Final result: {len(groups)} group(s)")
        for idx, group in enumerate(groups):
            citations_str = ", ".join([getattr(c, "citation", "Unknown") for c in group])
            logger.error(f"[PROXIMITY-DEBUG] Group {idx+1}: {len(group)} citation(s) - {citations_str}")

        return groups

    def _find_preceding_case_name(self, text: str, index: int) -> Optional[Tuple[int, int, str]]:
        """Find the nearest preceding case-name pattern before index.
        Returns (start, end, name_text) or None."""
        if not text or index is None or index <= 0:
            return None
        window_start = max(0, index - 1500)
        segment = text[window_start:index]
        # Patterns: "X v. Y", "In re ...", "Ex parte ..."
        patterns = [
            r"([A-Z][A-Za-z0-9&\.'\s-]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\.'\s-]+?)",
            r"(In\s+re\s+[A-Z][A-Za-z0-9&\.'\s-]+)",
            r"(Ex\s+parte\s+[A-Z][A-Za-z0-9&\.'\s-]+)",
        ]
        best = None
        for pat in patterns:
            try:
                for m in re.finditer(pat, segment, re.IGNORECASE | re.DOTALL):
                    s = window_start + m.start()
                    e = window_start + m.end()
                    # prefer the closest (largest start)
                    if not best or s > best[0]:
                        if m.lastindex and m.lastindex >= 2 and " v" in m.group(0).lower():
                            nm = f"{m.group(1).strip()} v. {m.group(2).strip()}"
                        else:
                            nm = m.group(1).strip()
                        nm = re.sub(r"\s+", " ", nm).strip()
                        best = (s, e, nm)
            except Exception:
                continue
        return best

    def _find_following_year_boundary(self, text: str, index: int) -> Optional[Tuple[int, int, str]]:
        """Find the first year after index, prefer (YYYY) and return (year_start, boundary_end, year_text).
        boundary_end is the index after ')' if parenthetical found, else year end index."""
        if not text or index is None:
            return None
        window_end = min(len(text), index + 600)
        segment = text[index:window_end]
        # Prefer year in parentheses
        m = re.search(r"\(\s*((?:19|20)\d{2})\s*\)", segment)
        if m:
            y = m.group(1)
            y_start = index + m.start(1)
            b_end = index + m.end(0)
            return (y_start, b_end, y)
        # Fallback: bare year
        m2 = re.search(r"(?:19|20)\d{2}", segment)
        if m2:
            y = m2.group(0)
            y_start = index + m2.start(0)
            y_end = index + m2.end(0)
            return (y_start, y_end, y)
        return None

    def _group_by_name_year_window(self, citations: List[Any], text: str) -> List[List[Any]]:
        """Group citations that share the same (preceding case-name .. following year) window.
        All citations that follow the case name and precede the year belong to one cluster."""
        if not citations or not text:
            return [[c] for c in citations]

        # Build window keys
        def get_pos(cit, key):
            if isinstance(cit, dict):
                return cit.get(key)
            return getattr(cit, key, None)

        groups: Dict[Tuple[int, int], List[Any]] = {}
        singles: List[Any] = []
        for cit in citations:
            start = get_pos(cit, "start_index")
            end = get_pos(cit, "end_index") or start
            if start is None:
                singles.append(cit)
                continue
            name_span = self._find_preceding_case_name(text, start)
            if not name_span:
                singles.append(cit)
                continue
            year_span = self._find_following_year_boundary(text, end or start)
            if not year_span:
                singles.append(cit)
                continue
            name_start, _, _ = name_span
            _, boundary_end, year_text = year_span
            # Keyed by exact boundary indices to keep windows distinct even for same name/year repeated
            key = (name_start, boundary_end)
            groups.setdefault(key, []).append(cit)
        result: List[List[Any]] = []
        for _, arr in groups.items():
            if len(arr) >= 2:
                result.append(arr)
            else:
                singles.extend(arr)
        for cit in singles:
            result.append([cit])
        logger.info(f"[NAME-YEAR-WINDOW] Grouped into {len(result)} group(s)")
        return result

    def _group_by_canonical_data(self, citations: List[Any]) -> List[List[Any]]:
        """Group citations by verified canonical identifiers (URL preferred) as a fallback.
        Returns a list of groups; groups with a single member are returned as singletons.

        CRITICAL FIX (Nov 2025): Now validates that extracted names are similar before grouping.
        This prevents completely different cases from being clustered just because they share a year.
        """
        if not citations:
            return []

        canonical_groups: Dict[tuple, List[Any]] = {}
        singletons: List[Any] = []

        for cit in citations:
            if isinstance(cit, dict):
                verified = cit.get("verified", False)
                c_name = cit.get("canonical_name")
                c_date = cit.get("canonical_date")
                c_url = cit.get("canonical_url")
                cit.get("extracted_case_name")
            else:
                verified = getattr(cit, "verified", False)
                c_name = getattr(cit, "canonical_name", None)
                c_date = getattr(cit, "canonical_date", None)
                c_url = getattr(cit, "canonical_url", None)
                getattr(cit, "extracted_case_name", None)

            # Only group verified citations with stable canonical identifiers
            if not verified or (not c_url and (not c_name or not c_date)):
                singletons.append(cit)
                continue

            if c_url:
                key = ("url", str(c_url).strip())
            else:
                import re

                m = re.search(r"(\d{4})", str(c_date))
                year = m.group(1) if m else str(c_date)
                norm_name = self._normalize_case_name_for_clustering(str(c_name)) if c_name else ""
                key = ("name_year", norm_name, year)

            canonical_groups.setdefault(key, []).append(cit)

        # CRITICAL FIX: Validate groups before accepting them
        # Split groups where extracted names are too different
        validated_groups: List[List[Any]] = []
        multi_count = 0

        for key, group in canonical_groups.items():
            if len(group) >= 2:
                # Extract all extracted_case_names from this group
                extracted_names = []
                for cit in group:
                    if isinstance(cit, dict):
                        ext_name = cit.get("extracted_case_name")
                    else:
                        ext_name = getattr(cit, "extracted_case_name", None)

                    if ext_name and ext_name != "N/A":
                        extracted_names.append(ext_name)

                # CRITICAL VALIDATION: Check if extracted names are similar
                # If we have multiple extracted names, they should match
                if len(extracted_names) >= 2:
                    unique_names = list(set(extracted_names))

                    if len(unique_names) > 1:
                        # Check similarity between extracted names
                        from difflib import SequenceMatcher

                        all_similar = True
                        base_name = unique_names[0].lower()

                        for other_name in unique_names[1:]:
                            similarity = SequenceMatcher(None, base_name, other_name.lower()).ratio()

                            if similarity < 0.6:  # Less than 60% similar
                                all_similar = False
                                logger.warning(
                                    f"[CANONICAL-GROUPING] ❌ REJECTING group - extracted names too different:"
                                )
                                logger.warning(f"  Base: '{unique_names[0]}'")
                                logger.warning(f"  Other: '{other_name}'")
                                logger.warning(f"  Similarity: {similarity:.2%} < 60%")
                                logger.warning(f"  Key: {key}")
                                break

                        if not all_similar:
                            # Don't group these citations - return them as singletons
                            logger.warning(
                                f"[CANONICAL-GROUPING] Splitting group of {len(group)} citations due to name mismatch"
                            )
                            for cit in group:
                                validated_groups.append([cit])
                            continue

                # Group passed validation
                multi_count += 1
                logger.info(f"[CANONICAL-GROUPING] ✅ Validated {len(group)} parallel citations for {key}")
                validated_groups.append(group)
            else:
                singletons.extend(group)

        for cit in singletons:
            validated_groups.append([cit])

        logger.info(
            f"[CANONICAL-GROUPING] Result: {len(validated_groups)} total groups ({multi_count} multi-citation, {len(singletons)} singleton)"
        )
        return validated_groups

    def _normalize_case_name_for_clustering(self, name: str) -> str:
        """Normalize case name for clustering comparison."""
        if not name:
            return ""

        # Convert to lowercase and remove common variations
        normalized = name.lower().strip()

        # FIX: Expand common abbreviations BEFORE other normalization
        # This allows "Rice v. Dow Chem. Co." to match "Rice v. Dow Chemical Co."
        abbreviation_map = {
            r"\bco\.\b": "company",
            r"\bcorp\.\b": "corporation",
            r"\binc\.\b": "incorporated",
            r"\bltd\.\b": "limited",
            r"\battys?\.\b": "attorney",
            r"\bchem\.\b": "chemical",
            r"\bmfg\.\b": "manufacturing",
            r"\bgen\.\b": "general",
            r"\bnat\'?l\.\b": "national",
            r"\bint\'?l\.\b": "international",
            r"\bassocs?\.\b": "association",
            r"\bassn\.\b": "association",
            r"\bdept\.\b": "department",
            r"\bsec\.\b": "secretary",
            r"\badm\'?r\.\b": "administrator",
            r"\bcomm\'?r\.\b": "commissioner",
            r"\bgov\.\b": "governor",
            r"\bcons\.\b": "consolidated",
            r"\bw\.\b": "west",
            r"\be\.\b": "east",
            r"\bn\.\b": "north",
            r"\bs\.\b": "south",
        }

        import re

        for abbrev_pattern, expansion in abbreviation_map.items():
            normalized = re.sub(abbrev_pattern, expansion, normalized)

        # Remove common legal suffixes (after expansion, so we catch both forms)
        suffixes_to_remove = [
            ", incorporated",
            ", corporation",
            ", company",
            ", limited",
            ", inc.",
            ", inc",
            ", corp.",
            ", corp",
            ", co.",
            ", co",
            ", llc",
            ", ltd.",
            ", ltd",
        ]

        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)].strip()

        # Remove caption-role/docket tokens that pollute party names
        # Examples: "et al", "petitioners", "respondent", "appellant", "appellee", "plaintiff", "defendant", "no", "aka"
        tokens = ["et al", "petitioners", "respondent", "appellant", "appellee", "plaintiff", "defendant", "no", "aka"]
        for t in tokens:
            normalized = re.sub(r"\b" + re.escape(t) + r"\b", " ", normalized)

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def _calculate_case_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        if not name1 or not name2:
            return 0.0

        # Simple word-based similarity
        words1 = set(name1.split())
        words2 = set(name2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    # State-specific reporters that cannot be parallel with each other
    STATE_REPORTERS = {
        "ohio": ["Ohio St.", "Ohio App.", "Ohio Misc.", "N.E.", "N.E.2d", "N.E.3d"],
        "nebraska": ["Neb.", "Neb. App.", "N.W.", "N.W.2d"],
        "washington": ["Wash.", "Wn.", "Wn.2d", "Wn. App.", "Wn. App. 2d", "P.", "P.2d", "P.3d"],
        "connecticut": ["Conn.", "Conn. App.", "Conn. Supp.", "A.", "A.2d", "A.3d"],
        "california": ["Cal.", "Cal.2d", "Cal.3d", "Cal.4th", "Cal.5th", "Cal. App.", "Cal. Rptr."],
        "new_york": ["N.Y.", "N.Y.2d", "N.Y.3d", "A.D.", "A.D.2d", "A.D.3d", "N.Y.S.", "N.Y.S.2d", "N.Y.S.3d"],
        "federal": [
            "U.S.",
            "S. Ct.",
            "L. Ed.",
            "L. Ed. 2d",
            "F.",
            "F.2d",
            "F.3d",
            "F.4th",
            "F. Supp.",
            "F. Supp. 2d",
            "F. Supp. 3d",
        ],
    }

    def _get_citation_jurisdiction(self, citation_text: str) -> str:
        """Determine which state/jurisdiction a citation belongs to."""
        if not citation_text:
            return "unknown"
        cit_upper = citation_text.upper()
        for state, reporters in self.STATE_REPORTERS.items():
            for reporter in reporters:
                if reporter.upper() in cit_upper:
                    return state
        return "unknown"

    def _citations_compatible_jurisdiction(self, cit1: str, cit2: str) -> bool:
        """Check if two citations could be parallel (same jurisdiction)."""
        state1 = self._get_citation_jurisdiction(cit1)
        state2 = self._get_citation_jurisdiction(cit2)
        # Unknown states can be parallel with anything
        if state1 == "unknown" or state2 == "unknown":
            return True
        # Same state = compatible
        return state1 == state2

    def _are_parallel_citations(self, citations: List[Any], text: str) -> bool:
        """Check if citations are parallel (refer to the same case)."""
        if len(citations) < 2:
            return False

        citation_texts = []
        citation_lookup = {}
        for citation in citations:
            if hasattr(citation, "citation"):
                citation_text = citation.citation
            elif isinstance(citation, dict):
                citation_text = citation.get("citation", "")
            else:
                citation_text = str(citation)
            citation_texts.append(citation_text)
            citation_lookup[citation_text] = citation

        # Respect explicit parallel_citations metadata when present
        for citation in citations:
            if isinstance(citation, dict):
                parallels = citation.get("parallel_citations", []) or []
            else:
                parallels = getattr(citation, "parallel_citations", []) or []
            for parallel_text in parallels:
                if parallel_text in citation_lookup:
                    return True

        # Check for regex-based parallel patterns
        for pattern_name, pattern in self.patterns.items():
            if "parallel" in pattern_name:
                for text_segment in citation_texts:
                    if pattern.search(text_segment):
                        return True

        # Reporter-based heuristic comparisons
        for i in range(len(citations)):
            for j in range(i + 1, len(citations)):
                if self._are_citations_parallel_pair(citations[i], citations[j], text):
                    return True

        # USER FIX 2024-10-17: PRIORITIZE case name + year matching
        # Parallel citations ARE the same case, so they SHOULD have:
        # 1. Same (or very similar) extracted case name
        # 2. Same year
        # 3. Different reporters (U.S. vs S.Ct vs L.Ed, etc.)
        #
        # CRITICAL FIX: Use ONLY extracted names/years for clustering, NEVER canonical!
        # Canonical data comes from APIs and may not match what's in the user's document.
        # Clustering must be based on what the user actually wrote, not what APIs return.
        case_names = []
        case_years = []
        for citation in citations:
            # CRITICAL: Use ONLY extracted_case_name for clustering
            # Never use canonical_name - it comes from APIs and may not match the document
            case_name = getattr(
                citation, "extracted_case_name", None
            ) or getattr(  # PRIMARY: Use extracted from document
                citation, "cluster_case_name", None
            )  # Fallback to cluster-level extracted

            # CRITICAL: Use ONLY extracted_date for clustering
            # Never use canonical_date - it comes from APIs and may not match the document
            case_year = getattr(citation, "extracted_date", None) or getattr(  # PRIMARY: Use extracted from document
                citation, "cluster_year", None
            )  # Fallback to cluster-level extracted
            if case_name and case_name != "N/A":
                case_names.append(case_name)
            else:
                case_names.append(None)  # Keep index alignment

            if case_year:
                # Extract just the year if it's a full date
                year_match = re.search(r"\b(19|20)\d{2}\b", str(case_year))
                case_years.append(year_match.group(0) if year_match else str(case_year))
            else:
                case_years.append(None)

        if len(case_names) >= 2:
            for i in range(len(case_names)):
                if not case_names[i]:
                    continue
                for j in range(i + 1, len(case_names)):
                    if not case_names[j]:
                        continue

                    # CRITICAL FIX: Check if they're in the same reporter first
                    reporter_i = self._extract_reporter_type(citation_texts[i])
                    reporter_j = self._extract_reporter_type(citation_texts[j])

                    # If same reporter, they CANNOT be parallel (must have different reporters)
                    if reporter_i == reporter_j:
                        logger.debug(
                            f"PARALLEL_CHECK Rejected name similarity - same reporter: {reporter_i} | {citation_texts[i]} vs {citation_texts[j]}"
                        )
                        continue  # Don't cluster same-reporter citations even with matching names

                    # Check case name similarity
                    similarity = self._calculate_name_similarity(case_names[i], case_names[j])

                    # NEW: Also check year similarity
                    year_match = False
                    if case_years[i] and case_years[j]:
                        year_match = case_years[i] == case_years[j]

                    # CRITICAL FIX: Require EXTREMELY high similarity (>98%) + year match to prevent cross-contamination
                    # Two citations from different cases (like Fischer 2024 vs Sulzbach 2022) should NEVER be parallel
                    if similarity >= 0.98 and year_match:  # Ultra-strict: >98% similarity AND same year
                        logger.error(
                            f"[SUCCESS] [PARALLEL-MATCH] Clustering via name+year: {case_names[i][:40]} ({case_years[i]}) ↔ {case_names[j][:40]} ({case_years[j]})"
                        )
                        logger.error(f"   Citations: {citation_texts[i]} ↔ {citation_texts[j]}")
                        logger.error(f"   Similarity: {similarity:.2%}, Years match: {year_match}")
                        return True
                    elif similarity >= 0.98:  # Only if similarity is extremely high (same case name)
                        logger.error(
                            f"PARALLEL_CHECK Accepted via ultra-high name similarity ({similarity:.2f}): {case_names[i][:30]} | {citation_texts[i]} ↔ {citation_texts[j]}"
                        )
                        return True

        return False

    def _citations_separated_by_parenthetical(self, citation1: Any, citation2: Any, text: str) -> bool:
        """
        Check if two citations are separated by a parenthetical boundary.

        Returns True if the citations are in different nesting levels of parentheses,
        which means they should NOT be clustered together.

        Example:
            "State v. M.Y.G., 199 Wn.2d 528, 509 P.3d 818 (2022) (quoting Am. Legion, 116 Wn.2d 1 (1991))"
             ^-----------Citation 1 (509 P.3d 818)-----------^         ^--Citation 2 (116 Wn.2d 1)--^

             These should NOT cluster because Citation 2 is inside a parenthetical.
        """

        def get_start_index(cit: Any) -> int:
            if isinstance(cit, dict):
                return cit.get("start_index", cit.get("start", 0))
            return getattr(cit, "start_index", getattr(cit, "start", 0))

        start1 = get_start_index(citation1)
        start2 = get_start_index(citation2)

        # Make sure start1 < start2
        if start1 > start2:
            start1, start2 = start2, start1

        # Get the text between the two citations
        between_text = text[start1:start2]

        # Count parentheses in the text between the citations
        paren_depth = 0
        crossed_boundary = False

        for char in between_text:
            if char == "(":
                paren_depth += 1
                if paren_depth > 0:
                    crossed_boundary = True
            elif char == ")":
                paren_depth -= 1
                if paren_depth < 0:
                    # Closing paren before opening - definitely crossed a boundary
                    return True

        # If paren_depth != 0, we crossed into or out of a parenthetical
        # If crossed_boundary is True and paren_depth > 0, we're inside a parenthetical
        if paren_depth != 0 or (crossed_boundary and paren_depth > 0):
            return True

        return False

    def _are_citations_parallel_pair(self, citation1: Any, citation2: Any, text: str) -> bool:
        """Determine if two citations are likely parallel citations."""
        # Extract citation text
        if isinstance(citation1, dict):
            citation1_text = citation1.get("citation", "")
            citation1_meta = citation1
        else:
            citation1_text = getattr(citation1, "citation", str(citation1))
            citation1_meta = citation1.__dict__ if hasattr(citation1, "__dict__") else {}

        if isinstance(citation2, dict):
            citation2_text = citation2.get("citation", "")
            citation2_meta = citation2
        else:
            citation2_text = getattr(citation2, "citation", str(citation2))
            citation2_meta = citation2.__dict__ if hasattr(citation1, "__dict__") else {}

        # Skip identical citations to prevent infinite loops
        if citation1_text == citation2_text:
            if self.debug_mode:
                logger.debug("PARALLEL_CHECK skipped: identical citations")
            return False

        # PHASE 5 DEBUG: DISABLED - was causing 5000+ print statements for 102 citations
        # print(f"[PHASE5-START] Comparing: {citation1_text[:40]} <-> {citation2_text[:40]}", flush=True)

        # Check for known parallel citations from metadata first
        def get_parallel_citations(citation_meta):
            if isinstance(citation_meta, dict):
                return citation_meta.get("parallel_citations", []) or []
            return getattr(citation_meta, "parallel_citations", []) or []

        get_parallel_citations(citation1_meta)
        get_parallel_citations(citation2_meta)

        # USER FIX: Always use EXTRACTED names for clustering, never canonical
        def get_clustering_name_for_validation(cit: Any) -> Optional[str]:
            """Get name for clustering - always use extracted_case_name"""
            extracted_name = None

            if isinstance(cit, dict):
                extracted_name = cit.get("extracted_case_name")
            else:
                extracted_name = getattr(cit, "extracted_case_name", None)

            if extracted_name and extracted_name != "N/A":
                return extracted_name
            return None

        case_name1 = get_clustering_name_for_validation(citation1)
        case_name2 = get_clustering_name_for_validation(citation2)
        # print(f"[PHASE5] Names: '{case_name1}' vs '{case_name2}'", flush=True)  # DISABLED - too many calls

        # If BOTH have names, they MUST match
        if case_name1 and case_name2 and case_name1 != "N/A" and case_name2 != "N/A":
            name_similarity = self._calculate_name_similarity(case_name1, case_name2)
            # DISABLED - too many log calls in O(n²) loop (5000+ for 102 citations)
            # logger.error(f"[FIX #58D DEBUG] Eyecite parallel validation: similarity={name_similarity:.2f}")
            if name_similarity < self.case_name_similarity_threshold:
                # logger.error(f"[FIX #58D] REJECTED eyecite parallel - name mismatch")
                return False
            # else:
            #     logger.error(f"[SUCCESS] [FIX #58D] ACCEPTED eyecite parallel - name match")

            # Get extracted years (never canonical!)
            def get_year(cit: Any) -> Optional[str]:
                if isinstance(cit, dict):
                    return cit.get("extracted_date")
                return getattr(cit, "extracted_date", None)

            year1 = get_year(citation1)
            year2 = get_year(citation2)
            # print(f"  [PHASE5] Years: '{year1}' vs '{year2}'", flush=True)  # DISABLED - too many calls

            # FIX #6: ALLOW clustering if at least one citation has a year
            # P.3d citations don't have years in text, they get them from cluster partners
            has_year1 = year1 and year1 != "N/A"
            has_year2 = year2 and year2 != "N/A"

            if not has_year1 and not has_year2:
                # print(f"  [PHASE5-EYECITE] REJECTED - both missing year!", flush=True)  # DISABLED
                # logger.error(f"[REJECTED] [FIX #6] REJECTED eyecite parallel - both missing year: '{year1}' vs '{year2}'")
                return False

            # If both have years, they MUST match exactly
            if has_year1 and has_year2 and year1 != year2:
                # print(f"  [PHASE5-EYECITE] REJECTED - year mismatch!", flush=True)  # DISABLED
                # logger.error(f"[REJECTED] [FIX #6] REJECTED eyecite parallel - year mismatch: {year1} vs {year2}")
                return False

            # If at least one has a year, accept clustering (date will be propagated later)
            # if has_year1 or has_year2:
            #     print(f"  [SUCCESS] [PHASE5-EYECITE] ACCEPTED - at least one has year and names match!", flush=True)  # DISABLED

            # Validation passed - accept the parallel relationship
            if self.debug_mode:
                logger.debug(
                    f"PARALLEL_CHECK ACCEPTED eyecite parallel after validation: '{case_name1[:30] if case_name1 else 'N/A'}' ({year1})"
                )
            return True

        reporter1 = self._extract_reporter_type(citation1_text)
        reporter2 = self._extract_reporter_type(citation2_text)

        # PHASE 5 DEBUG: DISABLED - too many calls in O(n²) loop (5000+ for 102 citations)
        # logger.error(f"[PHASE5-DEBUG] PARALLEL_CHECK: {citation1_text} <-> {citation2_text}")
        # logger.error(f"   Reporters: {reporter1} vs {reporter2}")
        # print(f"[PHASE5] CHECK: {citation1_text} <-> {citation2_text}, reporters: {reporter1} vs {reporter2}", flush=True)

        if self.debug_mode:
            logger.debug(
                "PARALLEL_CHECK start | %s (%s) <-> %s (%s)",
                citation1_text,
                reporter1,
                citation2_text,
                reporter2,
            )

        # Check if either citation is explicitly marked as parallel to the other
        def get_cluster_id(cit: Any) -> Optional[str]:
            if isinstance(cit, dict):
                return cit.get("cluster_id") or cit.get("clusterid")
            return getattr(cit, "cluster_id", getattr(cit, "clusterid", None))

        cluster_id1 = get_cluster_id(citation1)
        cluster_id2 = get_cluster_id(citation2)
        if cluster_id1 and cluster_id2 and cluster_id1 == cluster_id2:
            if self.debug_mode:
                logger.debug(
                    "PARALLEL_CHECK cluster-id match %s | %s ↔ %s",
                    cluster_id1,
                    citation1_text,
                    citation2_text,
                )
            return True

        # P5 FIX: If same reporter, they can't be parallel (must be different reporters)
        # Additionally, even if different reporters, same reporter + different volumes = DIFFERENT CASES
        if reporter1 == reporter2:
            if self.debug_mode:
                logger.debug(
                    "PARALLEL_CHECK rejected: same reporter type | reporter=%s",
                    reporter1,
                )
            return False

        # P5 FIX: CRITICAL - Even if they have similar case names, validate reporter/volume combinations
        # Same reporter + different volumes = CANNOT be parallel (different cases entirely)
        # Example: "506 U.S. 224" and "546 U.S. 418" cannot both be same case
        parsed1 = self._parse_citation_components(citation1_text)
        parsed2 = self._parse_citation_components(citation2_text)

        if parsed1 and parsed2:
            vol1, rep1 = parsed1.get("volume"), parsed1.get("reporter")
            vol2, rep2 = parsed2.get("volume"), parsed2.get("reporter")

            # If SAME reporter but DIFFERENT volumes, they CANNOT be parallel
            if rep1 and rep2 and rep1 == rep2 and vol1 != vol2:
                logger.warning(
                    f"[REJECTED] P5_FIX: Prevented false clustering - same reporter '{rep1}' but different volumes {vol1} vs {vol2} | "
                    f"{citation1_text} ↔ {citation2_text}"
                )
                return False

        # If either reporter is unknown, we can't reliably determine if they're parallel
        if "unknown" in (reporter1, reporter2):
            if self.debug_mode:
                logger.debug("PARALLEL_CHECK rejected: unknown reporter type")
            return False

        # CRITICAL FIX: Check proximity FIRST before any other heuristics
        # This prevents citations that are far apart from being grouped together
        # even if they have similar case names or other matching attributes
        def get_start_index(cit: Any) -> int:
            if isinstance(cit, dict):
                return cit.get("start_index", cit.get("start", 0))
            return getattr(cit, "start_index", getattr(cit, "start", 0))

        start1 = get_start_index(citation1)
        start2 = get_start_index(citation2)
        distance = abs(start1 - start2)

        # CRITICAL FIX #13: Check for parenthetical boundaries between citations
        # Citations in parentheticals (e.g., "quoting Am. Legion...") should NOT cluster
        # with the main citation, even if they're within proximity.
        # Example: "State v. M.Y.G., 199 Wn.2d 528, 509 P.3d 818 (quoting Am. Legion, 116 Wn.2d 1)"
        #          Main: 199 Wn.2d 528, 509 P.3d 818
        #          Parenthetical: 116 Wn.2d 1
        if text and self._citations_separated_by_parenthetical(citation1, citation2, text):
            if self.debug_mode:
                logger.debug(
                    "PARALLEL_CHECK rejected by parenthetical boundary | %s ↔ %s",
                    citation1_text[:50],
                    citation2_text[:50],
                )
            return False

        # Adjust proximity threshold based on citation types
        proximity_threshold = self.proximity_threshold
        if "U.S." in citation1_text or "U.S." in citation2_text:
            # Be more lenient with US Supreme Court citations
            proximity_threshold = max(proximity_threshold, 500)

        # REJECT IMMEDIATELY if citations are too far apart
        # This prevents false clustering of unrelated citations
        if distance > proximity_threshold:
            # PHASE 5 DEBUG: DISABLED - too many calls in O(n²) loop
            # logger.error(f"[PHASE5-DEBUG] REJECTED by proximity: distance={distance} > threshold={proximity_threshold}")
            # logger.error(f"   Positions: {start1} vs {start2}")
            # print(f"[PHASE5] REJECTED proximity: {citation1_text[:30]} <-> {citation2_text[:30]}, distance={distance} > {proximity_threshold}", flush=True)

            if self.debug_mode:
                logger.debug(
                    "PARALLEL_CHECK rejected by proximity | distance=%s threshold=%s | %s ↔ %s",
                    distance,
                    proximity_threshold,
                    citation1_text[:50],
                    citation2_text[:50],
                )
            return False

        # Now that we know citations are close together, check parallel patterns
        if not self._match_parallel_patterns(citation1_text, citation2_text):
            # PHASE 5 DEBUG: DISABLED - too many calls in O(n²) loop
            # logger.error(f"[WARNING]  [PHASE5-DEBUG] Pattern matching failed, trying name fallback...")

            if self.debug_mode:
                logger.debug("PARALLEL_CHECK reporter pair not recognized as parallel")

            # FIX #58F: If patterns don't match, try case name similarity as a fallback
            # BUT ONLY if they're already within proximity (which we checked above)

            # USER FIX: Always use EXTRACTED names for clustering, never canonical
            # Clustering should reflect what's in the user's document, not API data
            def get_clustering_name(cit: Any) -> Optional[str]:
                """Get name for clustering decision - always use extracted_case_name"""
                extracted_name = None

                if isinstance(cit, dict):
                    extracted_name = cit.get("extracted_case_name")
                else:
                    extracted_name = getattr(cit, "extracted_case_name", None)

                # Always use extracted name for clustering
                if extracted_name and extracted_name != "N/A":
                    return extracted_name
                return None

            case_name1 = get_clustering_name(citation1)
            case_name2 = get_clustering_name(citation2)

            # logger.error(f"   Names: '{case_name1}' vs '{case_name2}'")  # DISABLED - O(n²)

            if case_name1 and case_name2 and case_name1 != "N/A" and case_name2 != "N/A":
                similarity = self._calculate_name_similarity(case_name1, case_name2)
                # logger.error(f"[DEBUG] [FIX #58F] Fallback name similarity check: {similarity:.2f} vs threshold {self.case_name_similarity_threshold:.2f} | '{case_name1[:30]}' vs '{case_name2[:30]}'")  # DISABLED
                if (
                    similarity >= self.case_name_similarity_threshold
                ):  # FIX #58F: Use configured threshold, not hardcoded 0.8!
                    # logger.error(f"[SUCCESS] [FIX #58F] ACCEPTED via fallback - name similarity {similarity:.2f} >= {self.case_name_similarity_threshold:.2f}")  # DISABLED
                    return True
                # else:
                # logger.error(f"[REJECTED] [FIX #58F] REJECTED via fallback - name similarity {similarity:.2f} < {self.case_name_similarity_threshold:.2f}")  # DISABLED
            # else:
            # logger.error(f"[PHASE5-DEBUG] REJECTED - missing case names for fallback")  # DISABLED

            return False

        # Washington-specific handling
        if "wash" in reporter1 or "wash" in reporter2:
            if not self._check_washington_parallel_patterns(citation1_text, citation2_text):
                if self.debug_mode:
                    logger.debug("PARALLEL_CHECK Washington reporter validation failed")
                return False

        # FIX #58C: STRICT validation - BOTH citations MUST have extracted names AND years
        # This prevents citations from different cases clustering together
        case_name1 = self._get_case_name(citation1)
        case_name2 = self._get_case_name(citation2)

        # STRICT: Reject if either citation lacks extracted name
        if not case_name1 or not case_name2 or case_name1 == "N/A" or case_name2 == "N/A":
            if self.debug_mode:
                logger.debug(f"PARALLEL_CHECK rejected - missing extracted names: '{case_name1}' vs '{case_name2}'")
            return False

        # STRICT: Names must match
        name_similarity = self._calculate_name_similarity(case_name1, case_name2)
        if name_similarity < self.case_name_similarity_threshold:
            if self.debug_mode:
                logger.debug(
                    f"PARALLEL_CHECK rejected - name mismatch ({name_similarity:.2f}): '{case_name1}' vs '{case_name2}'"
                )
            return False

        # FIX #58C: STRICT year validation
        def get_year(cit: Any) -> Optional[str]:
            """Get ONLY extracted year for clustering - never canonical!"""
            if isinstance(cit, dict):
                return cit.get("extracted_date")
            return getattr(cit, "extracted_date", None)

        year1 = get_year(citation1)
        year2 = get_year(citation2)

        # FIX #58C: Allow year validation if at least one citation has a year
        # P.3d citations don't have years in text, they get them from cluster partners
        has_year1 = year1 and year1 != "N/A"
        has_year2 = year2 and year2 != "N/A"

        # If neither has a year, reject clustering
        if not has_year1 and not has_year2:
            if self.debug_mode:
                logger.debug(f"PARALLEL_CHECK rejected - both missing extracted years: '{year1}' vs '{year2}'")
            return False

        # If both have years, they MUST match exactly
        if has_year1 and has_year2 and year1 != year2:
            if self.debug_mode:
                logger.debug(f"PARALLEL_CHECK rejected - year mismatch: {year1} vs {year2}")
            return False

        # If we get here, the citations are parallel AND have matching names
        # At least one has a year (dates will be propagated later)
        # PHASE 5 DEBUG: DISABLED - too many calls in O(n²) loop
        # logger.error(f"[SUCCESS] [PHASE5-DEBUG] ACCEPTED as parallel citations!")
        # logger.error(f"   Names match: '{case_name1[:40]}' ≈ '{case_name2[:40]}'")
        # logger.error(f"   Years: year1={year1}, year2={year2} (at least one valid)")
        # logger.error(f"   Distance: {distance}")
        # print(f"[SUCCESS] [PHASE5] ACCEPTED: {citation1_text[:30]} ↔ {citation2_text[:30]}, names={case_name1[:30]}, years=({year1}, {year2})", flush=True)

        if self.debug_mode:
            logger.debug(
                "PARALLEL_CHECK ACCEPTED | %s ↔ %s | distance=%s | name=%s | year=%s",
                citation1_text,
                citation2_text,
                distance,
                case_name1[:30],
                year1,
            )

        return True

    def _get_case_name(self, citation: Any) -> Optional[str]:
        """
        CRITICAL FIX: Get case name for clustering - USE ONLY EXTRACTED, NEVER CANONICAL!

        Clustering MUST use extracted names from the user's document, NOT canonical names from APIs.
        Using canonical names causes citations that verify to different cases to cluster together.
        The extracted name is what the user actually wrote in their document.

        Priority order:
        1. extracted_case_name (from user's document - PRIMARY)
        2. cluster_case_name (cluster-level extracted name - fallback)
        3. Never use canonical_name for clustering!
        """
        if isinstance(citation, dict):
            # CRITICAL: Use ONLY extracted_case_name, never canonical_name
            extracted = citation.get("extracted_case_name")
            if extracted and extracted != "N/A":
                return extracted
            # Fallback to cluster_case_name (which should also be extracted)
            return citation.get("cluster_case_name")

        # Object citation format
        # CRITICAL: Use ONLY extracted_case_name, never canonical_name
        extracted = getattr(citation, "extracted_case_name", None)
        if extracted and extracted != "N/A":
            return extracted
        # Fallback to cluster_case_name (which should also be extracted)
        return getattr(citation, "cluster_case_name", None)

    def _extract_reporter_type(self, citation_text: str) -> str:
        """Extract a simplified reporter type token from citation text with enhanced Washington state support."""
        if not citation_text or not isinstance(citation_text, str):
            return "unknown"

        normalized = citation_text.lower()

        # Washington Court of Appeals (Div. I, II, III)
        if any(
            token in normalized
            for token in (
                "wn. app.",
                "wn. app",
                "wn.app.",
                "wn app",
                "wash. app.",
                "wash. app",
                "wash.app.",
                "wash app",
                "wa. app.",
                "wa app",
                "w.a.",
                "wa.",
                "wac",
                "wn. app. 2d",
                "wn. app.2d",
                "wn app 2d",
                "wn app.2d",
                "wash. app. 2d",
                "wash. app.2d",
                "wash app 2d",
                "wash app.2d",
                "div. i",
                "div. ii",
                "div. iii",
                "div i",
                "div ii",
                "div iii",
                "division i",
                "division ii",
                "division iii",
            )
        ):
            return "wash_app"

        # Washington Supreme Court (Wash. 2d, Wn.2d, etc.)
        if any(
            token in normalized
            for token in (
                "wn.2d",
                "wn. 2d",
                "wn2d",
                "wn 2d",
                "wash.2d",
                "wash. 2d",
                "wash2d",
                "wash 2d",
                "w n.2d",
                "w n 2d",
                "wn. 2d",
                "wn.2d",
                "washington 2d",
                "washington.2d",
                "washington. 2d",
            )
        ):
            return "wash2d"

        # General Washington reporters (catch-all for other variations)
        if any(
            token in normalized
            for token in (
                "wash.",
                "wn.",
                "wash ",
                "wn ",
                "wa.",
                "wa ",
                "washington reports",
                "washington supreme court",
                "wsc",
            )
        ):
            # If we've already identified it as a specific type, return that
            if "app" in normalized or "div" in normalized:
                return "wash_app"
            if "2d" in normalized or "ii" in normalized.lower():
                return "wash2d"
            return "wash"

        # Pacific Reporter (P., P.2d, P.3d)
        if "p.3d" in normalized or "p3d" in normalized or "p. 3d" in normalized:
            return "p3d"
        if "p.2d" in normalized or "p2d" in normalized or "p. 2d" in normalized:
            return "p2d"
        if " p. " in normalized or " p " in normalized:
            # Only return 'p' if it's not part of another word
            if not any(w in normalized for w in ("supra", "sup.", "para", "page", "part")):
                return "p"

        # US Supreme Court
        if "u.s." in normalized or "us " in normalized:
            return "us"
        if "s. ct." in normalized or "s.ct." in normalized or "s ct" in normalized or "supreme court" in normalized:
            return "sct"
        if "l. ed." in normalized or "l.ed." in normalized or "l ed " in normalized:
            return "led"

        # Federal Reporters
        if "f.3d" in normalized or "f3d" in normalized or "f. 3d" in normalized:
            return "f3d"
        if "f.2d" in normalized or "f2d" in normalized or "f. 2d" in normalized:
            return "f2d"
        if " f. " in normalized or " f " in normalized:
            # Only return 'f' if it's not part of another word
            if not any(w in normalized for w in ("of ", "if ", "for ", "from ")):
                return "f"

        # =================================================================
        # COMPLETE STATE REPORTER EXTRACTION (All 50 States)
        # =================================================================

        # ATLANTIC STATES (CT, DE, DC, ME, MD, NH, NJ, PA, RI, VT)
        if "conn. supp" in normalized or "conn supp" in normalized:
            return "conn_supp"
        if "conn. app" in normalized or "conn app" in normalized:
            return "conn_app"
        if " conn." in normalized or " conn " in normalized or "conn. " in normalized:
            return "conn"
        if " del." in normalized or " del " in normalized:
            return "del"
        if " d.c." in normalized or " d.c " in normalized:
            return "dc"
        if " me " in normalized or " me." in normalized:
            return "me"
        if " md." in normalized or " md " in normalized:
            return "md"
        if " n.h." in normalized or " nh " in normalized:
            return "nh"
        if " n.j." in normalized or " nj " in normalized:
            return "nj"
        if " pa." in normalized or " pa " in normalized:
            if "app" not in normalized:
                return "pa"
        if " r.i." in normalized or " ri " in normalized:
            return "ri"
        if " vt." in normalized or " vt " in normalized:
            return "vt"

        # NORTH EASTERN STATES (IL, IN, MA, NY, OH)
        if "ohio st." in normalized or "ohio st " in normalized:
            if "3d" in normalized:
                return "ohio_st3d"
            return "ohio_st"
        if " ill." in normalized or " ill " in normalized:
            if "app" in normalized:
                return "ill"  # Ill. App. still uses 'ill'
            return "ill"
        if " ind." in normalized or " ind " in normalized:
            return "ind"
        if " mass." in normalized or " mass " in normalized:
            return "mass"
        if " n.y." in normalized or " ny " in normalized:
            if "app" not in normalized and "misc" not in normalized:
                return "ny"

        # NORTH WESTERN STATES (IA, MI, MN, NE, ND, SD, WI)
        if " neb." in normalized or " neb " in normalized:
            return "neb"
        if " iowa " in normalized or " iowa." in normalized:
            return "iowa"
        if " mich." in normalized or " mich " in normalized:
            return "mich"
        if " minn." in normalized or " minn " in normalized:
            return "minn"
        if " n.d." in normalized or " nd " in normalized:
            return "nd"
        if " s.d." in normalized or " sd " in normalized:
            return "sd"
        if " wis." in normalized or " wis " in normalized:
            return "wis"

        # PACIFIC STATES (AK, AZ, CA, CO, HI, ID, KS, MT, NV, NM, OK, OR, UT, WY)
        if " alaska " in normalized or " alaska." in normalized:
            return "alaska"
        if " ariz." in normalized or " ariz " in normalized:
            return "ariz"
        if "cal. app" in normalized or "cal.app" in normalized or "cal app" in normalized:
            return "cal_app"
        if "cal. rptr" in normalized or "cal.rptr" in normalized:
            if "3d" in normalized:
                return "cal_rptr3d"
            return "cal_rptr"
        if " cal." in normalized or " cal " in normalized:
            if "4th" in normalized:
                return "cal4th"
            return "cal"
        if " colo." in normalized or " colo " in normalized:
            return "colo"
        if " haw." in normalized or " haw " in normalized:
            return "haw"
        if " idaho " in normalized or " idaho." in normalized:
            return "idaho"
        if " kan." in normalized or " kan " in normalized:
            return "kan"
        if " mont." in normalized or " mont " in normalized:
            return "mont"
        if " nev." in normalized or " nev " in normalized:
            return "nev"
        if " n.m." in normalized or " nm " in normalized:
            return "nm"
        if " okla." in normalized or " okla " in normalized:
            return "okla"
        if " or." in normalized or " or " in normalized:
            if "app" not in normalized:
                return "or"
        if " utah " in normalized or " utah." in normalized:
            return "utah"
        if " wyo." in normalized or " wyo " in normalized:
            return "wyo"

        # SOUTH EASTERN STATES (GA, NC, SC, VA, WV)
        if " ga." in normalized or " ga " in normalized:
            return "ga"
        if " n.c." in normalized or " nc " in normalized:
            return "nc"
        if " s.c." in normalized or " sc " in normalized:
            return "sc"
        if " va." in normalized or " va " in normalized:
            if "w." not in normalized and "west" not in normalized:
                return "va"
        if " w.va." in normalized or " w. va." in normalized or " wva " in normalized:
            return "wva"

        # SOUTH WESTERN STATES (AR, KY, MO, TN, TX)
        if " ark." in normalized or " ark " in normalized:
            return "ark"
        if " ky." in normalized or " ky " in normalized:
            return "ky"
        if " mo." in normalized or " mo " in normalized:
            return "mo"
        if " tenn." in normalized or " tenn " in normalized:
            return "tenn"
        if " tex." in normalized or " tex " in normalized:
            return "tex"

        # SOUTHERN STATES (AL, FL, LA, MS)
        if " ala." in normalized or " ala " in normalized:
            return "ala"
        if " fla." in normalized or " fla " in normalized:
            return "fla"
        if " la." in normalized or " la " in normalized:
            return "la"
        if " miss." in normalized or " miss " in normalized:
            return "miss"

        # =================================================================
        # REGIONAL REPORTERS
        # =================================================================

        # N.E.2d, N.E.3d (North Eastern Reporter)
        if "n.e.2d" in normalized or "ne2d" in normalized or "n.e. 2d" in normalized:
            return "ne2d"
        if "n.e.3d" in normalized or "ne3d" in normalized or "n.e. 3d" in normalized:
            return "ne3d"

        # N.W.2d (North Western Reporter)
        if "n.w.2d" in normalized or "nw2d" in normalized or "n.w. 2d" in normalized:
            return "nw2d"
        if "n.w." in normalized or " nw " in normalized:
            return "nw"

        # S.E.2d (South Eastern Reporter)
        if "s.e.2d" in normalized or "se2d" in normalized or "s.e. 2d" in normalized:
            return "se2d"
        if "s.e." in normalized or " se " in normalized:
            return "se"

        # S.W.2d, S.W.3d (South Western Reporter)
        if "s.w.3d" in normalized or "sw3d" in normalized or "s.w. 3d" in normalized:
            return "sw3d"
        if "s.w.2d" in normalized or "sw2d" in normalized or "s.w. 2d" in normalized:
            return "sw2d"

        # So.2d, So.3d (Southern Reporter)
        if "so.3d" in normalized or "so3d" in normalized or "so. 3d" in normalized:
            return "so3d"
        if "so.2d" in normalized or "so2d" in normalized or "so. 2d" in normalized:
            return "so2d"

        # A.2d, A.3d (Atlantic Reporter)
        if "a.2d" in normalized or "a2d" in normalized or "a. 2d" in normalized:
            return "a2d"
        if "a.3d" in normalized or "a3d" in normalized or "a. 3d" in normalized:
            return "a3d"

        # L. Ed., L. Ed. 2d (Lawyer's Edition)
        if "l. ed. 2d" in normalized or "l.ed.2d" in normalized or "l ed 2d" in normalized:
            return "led2d"
        if "l. ed." in normalized or "l.ed." in normalized or "l ed " in normalized:
            return "led"

        # Westlaw
        if " wl " in normalized or " w.l." in normalized or "wl." in normalized:
            return "wl"

        return "unknown"

    def _match_parallel_patterns(self, citation1: str, citation2: str) -> bool:
        """Check if two citation texts match known parallel citation reporter combinations."""
        # First check Washington-specific patterns which have special handling
        if self._check_washington_parallel_patterns(citation1, citation2):
            return True

        reporter1 = self._extract_reporter_type(citation1)
        reporter2 = self._extract_reporter_type(citation2)

        # DEBUG: Log reporter extraction for non-Washington pairs
        if (
            "ohio" in citation1.lower()
            or "n.e." in citation1.lower()
            or "ohio" in citation2.lower()
            or "n.e." in citation2.lower()
        ):
            logger.error(f"[REPORTER-DEBUG] '{citation1}' -> '{reporter1}' | '{citation2}' -> '{reporter2}'")

        if reporter1 == reporter2 or "unknown" in (reporter1, reporter2):
            return False

        # Check for known parallel reporter pairs
        reporter_pair = frozenset({reporter1, reporter2})
        valid_pairs = {
            # Washington State
            frozenset({"wash", "p3d"}),
            frozenset({"wash", "p2d"}),
            frozenset({"wash", "p"}),
            frozenset({"wash2d", "p3d"}),
            frozenset({"wash2d", "p2d"}),
            frozenset({"wash2d", "p"}),
            frozenset({"wash_app", "p3d"}),
            frozenset({"wash_app", "p2d"}),
            frozenset({"wash_app", "p"}),
            # US Supreme Court
            frozenset({"us", "sct"}),
            frozenset({"us", "led"}),
            frozenset({"us", "l_ed"}),
            frozenset({"sct", "led"}),
            frozenset({"sct", "l_ed"}),
            frozenset({"led", "l_ed"}),
            # Federal Reporters
            frozenset({"f3d", "us"}),
            frozenset({"f3d", "sct"}),
            frozenset({"f2d", "us"}),
            frozenset({"f2d", "sct"}),
            frozenset({"f", "us"}),
            frozenset({"f", "sct"}),
            # =================================================================
            # COMPLETE STATE-REGIONAL REPORTER MAPPINGS (Bluebook Reference)
            # https://libguides.uakron.edu/c.php?g=627783&p=4379905
            # =================================================================
            # ATLANTIC REPORTER (A., A.2d, A.3d): CT, DE, DC, ME, MD, NH, NJ, PA, RI, VT
            frozenset({"conn", "a2d"}),
            frozenset({"conn", "a3d"}),
            frozenset({"conn_app", "a2d"}),
            frozenset({"conn_app", "a3d"}),
            frozenset({"conn_supp", "a2d"}),
            frozenset({"conn_supp", "a3d"}),
            frozenset({"del", "a2d"}),
            frozenset({"del", "a3d"}),
            frozenset({"dc", "a2d"}),
            frozenset({"dc", "a3d"}),
            frozenset({"me", "a2d"}),
            frozenset({"me", "a3d"}),
            frozenset({"md", "a2d"}),
            frozenset({"md", "a3d"}),
            frozenset({"nh", "a2d"}),
            frozenset({"nh", "a3d"}),
            frozenset({"nj", "a2d"}),
            frozenset({"nj", "a3d"}),
            frozenset({"pa", "a2d"}),
            frozenset({"pa", "a3d"}),
            frozenset({"ri", "a2d"}),
            frozenset({"ri", "a3d"}),
            frozenset({"vt", "a2d"}),
            frozenset({"vt", "a3d"}),
            # NORTH EASTERN REPORTER (N.E., N.E.2d, N.E.3d): IL, IN, MA, NY, OH
            frozenset({"ill", "ne2d"}),
            frozenset({"ill", "ne3d"}),
            frozenset({"ind", "ne2d"}),
            frozenset({"ind", "ne3d"}),
            frozenset({"mass", "ne2d"}),
            frozenset({"mass", "ne3d"}),
            frozenset({"ny", "ne2d"}),
            frozenset({"ny", "ne3d"}),
            frozenset({"ohio_st", "ne2d"}),
            frozenset({"ohio_st", "ne3d"}),
            frozenset({"ohio_st3d", "ne2d"}),
            frozenset({"ohio_st3d", "ne3d"}),
            # NORTH WESTERN REPORTER (N.W., N.W.2d): IA, MI, MN, NE, ND, SD, WI
            frozenset({"iowa", "nw2d"}),
            frozenset({"iowa", "nw"}),
            frozenset({"mich", "nw2d"}),
            frozenset({"mich", "nw"}),
            frozenset({"minn", "nw2d"}),
            frozenset({"minn", "nw"}),
            frozenset({"neb", "nw2d"}),
            frozenset({"neb", "nw"}),
            frozenset({"nd", "nw2d"}),
            frozenset({"nd", "nw"}),
            frozenset({"sd", "nw2d"}),
            frozenset({"sd", "nw"}),
            frozenset({"wis", "nw2d"}),
            frozenset({"wis", "nw"}),
            # PACIFIC REPORTER (P., P.2d, P.3d): AK, AZ, CA, CO, HI, ID, KS, MT, NV, NM, OK, OR, UT, WA, WY
            frozenset({"alaska", "p2d"}),
            frozenset({"alaska", "p3d"}),
            frozenset({"ariz", "p2d"}),
            frozenset({"ariz", "p3d"}),
            frozenset({"cal", "p2d"}),
            frozenset({"cal", "p3d"}),
            frozenset({"cal4th", "p3d"}),
            frozenset({"cal_app", "p3d"}),
            frozenset({"cal_rptr", "p3d"}),
            frozenset({"cal_rptr3d", "p3d"}),
            frozenset({"colo", "p2d"}),
            frozenset({"colo", "p3d"}),
            frozenset({"haw", "p2d"}),
            frozenset({"haw", "p3d"}),
            frozenset({"idaho", "p2d"}),
            frozenset({"idaho", "p3d"}),
            frozenset({"kan", "p2d"}),
            frozenset({"kan", "p3d"}),
            frozenset({"mont", "p2d"}),
            frozenset({"mont", "p3d"}),
            frozenset({"nev", "p2d"}),
            frozenset({"nev", "p3d"}),
            frozenset({"nm", "p2d"}),
            frozenset({"nm", "p3d"}),
            frozenset({"okla", "p2d"}),
            frozenset({"okla", "p3d"}),
            frozenset({"or", "p2d"}),
            frozenset({"or", "p3d"}),
            frozenset({"utah", "p2d"}),
            frozenset({"utah", "p3d"}),
            frozenset({"wyo", "p2d"}),
            frozenset({"wyo", "p3d"}),
            # SOUTH EASTERN REPORTER (S.E., S.E.2d): GA, NC, SC, VA, WV
            frozenset({"ga", "se2d"}),
            frozenset({"ga", "se"}),
            frozenset({"nc", "se2d"}),
            frozenset({"nc", "se"}),
            frozenset({"sc", "se2d"}),
            frozenset({"sc", "se"}),
            frozenset({"va", "se2d"}),
            frozenset({"va", "se"}),
            frozenset({"wva", "se2d"}),
            frozenset({"wva", "se"}),
            # SOUTH WESTERN REPORTER (S.W., S.W.2d, S.W.3d): AR, KY, MO, TN, TX
            frozenset({"ark", "sw2d"}),
            frozenset({"ark", "sw3d"}),
            frozenset({"ky", "sw2d"}),
            frozenset({"ky", "sw3d"}),
            frozenset({"mo", "sw2d"}),
            frozenset({"mo", "sw3d"}),
            frozenset({"tenn", "sw2d"}),
            frozenset({"tenn", "sw3d"}),
            frozenset({"tex", "sw2d"}),
            frozenset({"tex", "sw3d"}),
            # SOUTHERN REPORTER (So., So.2d, So.3d): AL, FL, LA, MS
            frozenset({"ala", "so2d"}),
            frozenset({"ala", "so3d"}),
            frozenset({"fla", "so2d"}),
            frozenset({"fla", "so3d"}),
            frozenset({"la", "so2d"}),
            frozenset({"la", "so3d"}),
            frozenset({"miss", "so2d"}),
            frozenset({"miss", "so3d"}),
            # FEDERAL - U.S. Supreme Court parallel citations
            frozenset({"us", "led"}),
            frozenset({"us", "led2d"}),
            frozenset({"sct", "led"}),
            frozenset({"sct", "led2d"}),
            # Regional reporter cross-series
            frozenset({"a3d", "a2d"}),
            frozenset({"ne3d", "ne2d"}),
            frozenset({"nw2d", "nw"}),
            frozenset({"se2d", "se"}),
            frozenset({"sw3d", "sw2d"}),
            frozenset({"so3d", "so2d"}),
            frozenset({"p3d", "p2d"}),
        }

        if reporter_pair in valid_pairs:
            return True

        # Check for volume and page number matches as a fallback
        return self._check_volume_page_match(citation1, citation2)

    def _check_volume_page_match(self, citation1: str, citation2: str) -> bool:
        """Check if two citations have matching volume and page numbers."""
        # Extract volume and page numbers using regex
        import re

        def extract_volume_page(citation: str) -> tuple:
            # Match patterns like "123 Wash.2d 456" or "123 Wn.2d 456" or "123 P.3d 789"
            match = re.search(r"(\d+)\s+(?:Wash\.?2d?|Wn\.?2d?|P\.?3?d?)\s+(\d+)", citation, re.IGNORECASE)
            if match:
                return (int(match.group(1)), int(match.group(2)))
            return (None, None)

        vol1, page1 = extract_volume_page(citation1)
        vol2, page2 = extract_volume_page(citation2)

        # If we couldn't extract both volume and page, can't confirm they're parallel
        if not all([vol1, page1, vol2, page2]):
            return False

        # Check if volumes and pages match
        return vol1 == vol2 and page1 == page2

    def _check_washington_parallel_patterns(self, citation1: str, citation2: str) -> bool:
        """
        Specifically validate Washington reporter pairings (Wn./Wash. with P. reporters).
        Handles various formats of Washington state citations and their Pacific Reporter counterparts.
        """
        import re

        def normalize_citation(cite):
            """Normalize citation text for consistent matching."""
            if not cite or not isinstance(cite, str):
                return ""
            # Remove any non-alphanumeric characters except spaces, dots, and numbers
            normalized = re.sub(r"[^a-z0-9\s.]", " ", cite.lower())
            # Collapse multiple spaces and standardize variations
            normalized = re.sub(r"\s+", " ", normalized).strip()
            # Standardize variations
            normalized = normalized.replace("pacific", "p").replace("pacific reporter", "p")
            normalized = normalized.replace("washington", "wash").replace("wn ", "wash ").replace("wn. ", "wash. ")
            # Handle cases like 'Wn. App. 2d' -> 'wash app 2d' (must be before general app pattern)
            normalized = re.sub(r"wash\.?\s+app\.?\s+(\d*)d", r"wash app \1d", normalized)
            # Handle cases like 'Wn. App.' -> 'wash app'
            normalized = re.sub(r"wash(?:ington)?\s+app(?:\.?\s*\w*)?", "wash app", normalized)
            # Handle cases like 'Wash.2d' -> 'wash2d'
            normalized = re.sub(r"wash(?:ington)?\.?\s*(\d*)d", r"wash\1d", normalized)
            # Handle cases like 'Wn.2d' -> 'wash2d'
            normalized = re.sub(r"wn\.?\s*(\d*)d", r"wash\1d", normalized)
            # Handle cases like 'P.3d' -> 'p3d'
            normalized = re.sub(r"p\.?\s*(\d*)d", r"p\1d", normalized)
            return normalized

        norm1 = normalize_citation(citation1)
        norm2 = normalize_citation(citation2)

        if self.debug_mode:
            logger.debug(f"WA_PARALLEL_CHECK: Normalized citations: '{norm1}' and '{norm2}'")

        # Check if we have one Washington citation and one Pacific Reporter citation
        def is_wash_citation(cite):
            return (
                any(
                    term in cite
                    for term in [
                        "wash ",
                        "wash. ",
                        "wn ",
                        "wn. ",
                        "washington",
                        "wash app",
                        "wash. app",
                        "wn app",
                        "wn. app",
                        "wac",
                        "wash2d",
                        "wash 2d",
                        "wash. 2d",
                        "wn2d",
                        "wn 2d",
                        "wn. 2d",
                        "wash.app",
                        "wn.app",
                        "washapp",
                        "wnapp",
                        "wash app 2d",  # Added this pattern
                        "wash. app. 2d",
                        "wn. app. 2d",
                        "wac ",  # Additional patterns
                    ]
                )
                or re.search(r"wash(?:ington)?\s*\d*d", cite)
                or re.search(r"wn\.?\s*\d*d", cite)
                or re.search(r"wac\s*\d+", cite)
                or re.search(r"wash\s+app\s*\d*d", cite)  # Added regex pattern
            )

        def is_p_citation(cite):
            return any(
                term in cite
                for term in [
                    " p ",
                    " p. ",
                    "p2d",
                    "p.2d",
                    "p 2d",
                    "p. 2d",
                    "p3d",
                    "p.3d",
                    "p 3d",
                    "p. 3d",
                    "pacific",
                    "p.2d",
                    "p.3d",
                    "p. 2d",
                    "p. 3d",
                    "p2d",
                    "p3d",
                    "p. 2d",
                    "p. 3d",
                    "p.2d",
                    "p.3d",  # Additional patterns
                ]
            ) or re.search(r"p\.?\s*\d*d", cite)

        has_wash = is_wash_citation(norm1) or is_wash_citation(norm2)
        has_p = is_p_citation(norm1) or is_p_citation(norm2)

        if self.debug_mode:
            logger.debug(f"WA_PARALLEL_CHECK: has_wash={has_wash}, has_p={has_p}")

        # If we have one of each type, they might be parallel
        if has_wash and has_p:
            # Enhanced volume and page extraction with multiple patterns
            def extract_volume_page(cite):
                patterns = [
                    # Standard patterns: 123 Wash.2d 456, 123 P.3d 789
                    r"(\d+)\s+(?:wash\.?\s*\d*d|wn\.?\s*\d*d|p\.?\s*\d*d)\s+(\d+)",
                    # Patterns with 'v.' or 'vol.'
                    r"(?:v\.?|vol\.?)\s*(\d+)\s+(?:wash|wn|p)\.?\s*\d*d\s+(\d+)",
                    # Patterns with parentheses: (123 Wash.2d 456)
                    r"\((\d+)\s+(?:wash|wn|p)\.?\s*\d*d\s+(\d+)\)",
                    # Just numbers: 123 456 (last two numbers)
                    r"(\d+)\s+\d+\s+(\d+)",
                    # Any two numbers (last resort)
                    r"(\d+)\s+(\d+)",
                ]

                for pattern in patterns:
                    match = re.search(pattern, cite, re.IGNORECASE)
                    if match:
                        try:
                            vol = int(match.group(1))
                            page = int(match.group(2))
                            if 1 <= vol <= 9999 and 1 <= page <= 99999:  # Sanity check
                                return (vol, page)
                        except (ValueError, IndexError):
                            continue
                return (None, None)

            # Get volume and page for both citations
            vol1, page1 = extract_volume_page(norm1)
            vol2, page2 = extract_volume_page(norm2)

            if self.debug_mode:
                logger.debug(f"WA_PARALLEL_CHECK: Extracted - {vol1}:{page1} and {vol2}:{page2}")

            # If we have both volumes and pages, check if they match
            if all(v is not None for v in [vol1, page1, vol2, page2]):
                # FOR WASHINGTON PARALLEL CITATIONS: Volume/page numbers are ALWAYS different
                # Washington reporter and Pacific Reporter use different numbering systems
                # So we DON'T check for matching volumes/pages for Washington citations
                if has_wash and has_p:
                    if self.debug_mode:
                        logger.debug(f"[SUCCESS] WASHINGTON PARALLEL MATCH (different volumes expected): {citation1} ↔ {citation2}")
                    return True
                
                # For non-Washington citations, require matching volumes/pages
                # Exact match
                if vol1 == vol2 and page1 == page2:
                    if self.debug_mode:
                        logger.debug(f"[SUCCESS] NON-WASHINGTON PARALLEL MATCH (exact): {citation1} ↔ {citation2}")
                    return True

                # Allow for small page differences (same volume, pages within 5)
                if vol1 == vol2 and abs(page1 - page2) <= 5:
                    if self.debug_mode:
                        logger.debug(f"[SUCCESS] NON-WASHINGTON PARALLEL MATCH (close pages): {citation1} ↔ {citation2}")
                    return True

            # If volume/page extraction failed, try to extract just page numbers
            def extract_just_pages(cite):
                # Look for 2-4 digit numbers that could be page numbers
                pages = [int(m) for m in re.findall(r"\b(\d{2,4})\b", cite)]
                return pages[-2:] if len(pages) >= 2 else []

            pages1 = extract_just_pages(norm1)
            pages2 = extract_just_pages(norm2)

            if pages1 and pages2:
                # Check if any page numbers are close (within 5)
                for p1 in pages1[-2:]:  # Check last 2 numbers in each citation
                    for p2 in pages2[-2:]:
                        if abs(p1 - p2) <= 5:
                            if self.debug_mode:
                                logger.debug(
                                    f"[SUCCESS] WASHINGTON PARALLEL MATCH (page numbers close): {citation1} ↔ {citation2}"
                                )
                            return True

            # Check for case name similarity as a last resort
            def get_case_name(citation):
                if hasattr(citation, "case_name"):
                    return getattr(citation, "case_name")
                if hasattr(citation, "canonical_name"):
                    return getattr(citation, "canonical_name")
                if hasattr(citation, "extracted_case_name"):
                    return getattr(citation, "extracted_case_name")
                return None

            name1 = get_case_name(citation1)
            name2 = get_case_name(citation2)

            if name1 and name2 and name1 != "N/A" and name2 != "N/A":
                similarity = self._calculate_name_similarity(name1, name2)
                if similarity >= 0.7:  # 70% similarity threshold
                    if self.debug_mode:
                        logger.debug(
                            f"[SUCCESS] WASHINGTON PARALLEL MATCH (similar case names {similarity:.1%}): {name1} ↔ {name2}"
                        )
                    return True

            # If we get here, the citations don't appear to be parallel
            if self.debug_mode:
                logger.debug(f"No match for: {citation1} <-> {citation2}")
            return False

        return False

    def _are_citations_in_proximity(self, cite1: str, cite2: str, max_distance: int = 50) -> bool:
        """Check if two citations appear in close proximity in the text."""
        # This is a simplified version - in a real implementation, you'd need the full text
        # and positions of the citations. This is just a placeholder.
        # In a real implementation, you'd compare the character offsets.
        return True  # Placeholder - always return True for now

    def _extract_and_propagate_metadata(
        self, citations: List[Any], parallel_groups: List[List[Any]], text: str
    ) -> List[Any]:
        """Extract metadata from clusters and propagate to all members."""
        enhanced_citations = []

        for group in parallel_groups:
            if not group:
                continue

            canonical_names: List[str] = []
            canonical_years: List[str] = []
            for citation in group:
                if isinstance(citation, dict):
                    verified = citation.get("verified", False)
                    canonical_name = citation.get("canonical_name")
                    canonical_date = citation.get("canonical_date")
                else:
                    verified = getattr(citation, "verified", False)
                    canonical_name = getattr(citation, "canonical_name", None)
                    canonical_date = getattr(citation, "canonical_date", None)

                if verified and canonical_name and canonical_name != "N/A":
                    canonical_names.append(canonical_name)
                if verified and canonical_date and canonical_date != "N/A":
                    year_value = self._extract_year_value(canonical_date) or canonical_date
                    canonical_years.append(year_value)

            case_name = (
                max(canonical_names, key=self._score_case_name)
                if canonical_names
                else self._select_best_case_name(group)
            )
            if canonical_years:
                from collections import Counter

                case_year = Counter(canonical_years).most_common(1)[0][0]
            else:
                case_year = self._select_best_case_year(group)

            # CRITICAL LOGGING: Track what canonical names were found in this group
            if canonical_names:
                logger.info(
                    f"[CLUSTER-CANONICAL] Group has {len(canonical_names)} verified canonical names: {canonical_names[:3]}... -> selected: '{case_name}'"
                )

            # FIX: Clear truncated extracted_case_names and re-extract from document
            # This prevents truncated names from eyecite from being used anywhere
            for citation in group:
                extracted_name = getattr(citation, "extracted_case_name", None)
                if extracted_name and self._is_truncated_name(extracted_name):
                    logger.info(
                        f"[CLUSTERING-CLEAR-TRUNCATED] Clearing truncated name '{extracted_name}' - will re-extract"
                    )

                    # Re-extract the case name from document text
                    try:
                        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

                        # Get citation details for extraction
                        if isinstance(citation, dict):
                            citation_text = citation.get("citation", "")
                            start_idx = citation.get("start_index") or citation.get("start")
                            end_idx = citation.get("end_index") or citation.get("end")
                        else:
                            citation_text = getattr(citation, "citation", "")
                            start_idx = getattr(citation, "start_index", None) or getattr(citation, "start", None)
                            end_idx = getattr(citation, "end_index", None) or getattr(citation, "end", None)

                        # Call unified extraction with contamination filtering
                        result = extract_case_name_and_date_unified_master(
                            text=text,
                            citation=citation_text,
                            start_index=start_idx,
                            end_index=end_idx,
                            document_primary_case_name=getattr(self, "document_primary_case_name", None),
                        )

                        # Set the re-extracted name (result is a dict)
                        if result and result.get("case_name") and result.get("case_name") != "N/A":
                            new_name = result.get("case_name")

                            # CRITICAL: Filter out header patterns before overwriting
                            # Check if new_name contains header patterns (ET AL + role word, or role word + NO)
                            new_name_upper = new_name.upper()
                            has_et_al = "ET AL" in new_name_upper or "ETAL" in new_name_upper.replace(" ", "")
                            has_role_word = any(
                                role in new_name_upper
                                for role in [
                                    "PETITIONER",
                                    "RESPONDENT",
                                    "APPELLANT",
                                    "APPELLEE",
                                    "PLAINTIFF",
                                    "DEFENDANT",
                                ]
                            )
                            has_no = (
                                "NO." in new_name_upper or " NO " in new_name_upper or new_name_upper.endswith(" NO")
                            )

                            # Skip if it's clearly a header (ET AL + role word, or role word + NO)
                            if (has_et_al and has_role_word) or (has_role_word and has_no):
                                logger.warning(
                                    f"[CLUSTERING-REEXTRACTED] REJECTED header pattern: '{new_name}' - keeping original '{extracted_name}'"
                                )
                                # Keep the original extracted_name instead of overwriting with header
                                continue

                            logger.info(
                                f"[CLUSTERING-REEXTRACTED] '{extracted_name}' -> '{new_name}' for {citation_text}"
                            )
                            if isinstance(citation, dict):
                                citation["extracted_case_name"] = new_name
                            else:
                                citation.extracted_case_name = new_name
                        else:
                            # Re-extraction failed, KEEP the truncated name (it's better than N/A)
                            # but mark it with a prefix to indicate it may be incomplete
                            logger.warning(
                                f"[CLUSTERING-REEXTRACT-FAILED] Could not re-extract for {citation_text}, keeping truncated name: '{extracted_name}'"
                            )
                            if isinstance(citation, dict):
                                citation["extracted_case_name"] = extracted_name  # Keep original truncated name
                                citation["metadata"] = citation.get("metadata", {})
                                citation["metadata"]["name_may_be_truncated"] = True
                            else:
                                citation.extracted_case_name = extracted_name  # Keep original truncated name
                                if not hasattr(citation, "metadata"):
                                    citation.metadata = {}
                                citation.metadata["name_may_be_truncated"] = True
                    except Exception as e:
                        logger.error(f"[CLUSTERING-REEXTRACT-ERROR] {e}")
                        if isinstance(citation, dict):
                            citation["extracted_case_name"] = "N/A"
                        else:
                            citation.extracted_case_name = "N/A"

            if not case_name:
                for citation in group:
                    extracted_name = getattr(citation, "extracted_case_name", None)
                    fallback_name = getattr(citation, "canonical_name", None)
                    # FIX: Skip truncated names in fallback too
                    if extracted_name and extracted_name != "N/A" and not self._is_truncated_name(extracted_name):
                        case_name = extracted_name
                        logger.info(f"[CLUSTERING-FALLBACK] Using non-truncated extracted name: '{extracted_name}'")
                        break
                    elif extracted_name and self._is_truncated_name(extracted_name):
                        logger.info(f"[CLUSTERING-FALLBACK-SKIP] Skipping truncated fallback name: '{extracted_name}'")
                    if fallback_name and fallback_name != "N/A" and not self._is_truncated_name(fallback_name):
                        case_name = fallback_name
                        logger.info(f"[CLUSTERING-FALLBACK] Using non-truncated canonical name: '{fallback_name}'")
                        break

            if not case_year:
                for citation in group:
                    extracted_date = getattr(citation, "extracted_date", None)
                    fallback_date = getattr(citation, "canonical_date", None)
                    year_value = self._extract_year_value(extracted_date) if extracted_date else None
                    if year_value:
                        case_year = year_value
                        break
                    year_value = self._extract_year_value(fallback_date) if fallback_date else None
                    if year_value:
                        case_year = year_value
                        break

            # CRITICAL FIX: Standardize extracted names within cluster to prevent validation splits
            # BUT FIRST: Validate that citations actually belong together!
            # Collect all extracted names and pick the best one (longest, most complete)
            extracted_names = []
            extracted_dates = []
            for citation in group:
                if isinstance(citation, dict):
                    extracted_name = citation.get("extracted_case_name")
                    extracted_date = citation.get("extracted_date")
                else:
                    extracted_name = getattr(citation, "extracted_case_name", None)
                    extracted_date = getattr(citation, "extracted_date", None)

                if extracted_name and extracted_name != "N/A":
                    extracted_names.append(extracted_name)
                if extracted_date and extracted_date != "N/A":
                    extracted_dates.append(extracted_date)

            # URGENT FIX 2024-10-17: Check if extracted names are actually similar
            # If we have multiple different case names, these citations don't belong together!
            skip_standardization = False
            if len(extracted_names) > 1:
                unique_names = list(set(extracted_names))
                if len(unique_names) > 1:
                    # Check if names are similar (not just longest)
                    from difflib import SequenceMatcher

                    base_name = unique_names[0]
                    for other_name in unique_names[1:]:
                        similarity = SequenceMatcher(None, base_name.lower(), other_name.lower()).ratio()
                        if similarity < 0.5:  # Less than 50% similar
                            logger.error(
                                f"[BAD-CLUSTER] Citations have VERY different names - should NOT be clustered!"
                            )
                            logger.error(f"   Name 1: '{base_name}'")
                            logger.error(f"   Name 2: '{other_name}'")
                            logger.error(f"   Similarity: {similarity:.2%}")
                            logger.error(f"   [WARNING]  SKIPPING cluster standardization to prevent contamination")
                            # Don't standardize - keep each citation's own extracted name
                            skip_standardization = True
                            break

            # Pick best extracted name (longest, most complete)
            # USER FIX 2024-10-17: Detect and clean contaminated names BEFORE selecting best
            best_extracted_name = None
            if extracted_names and not skip_standardization:
                from src.utils.name_contamination_detector import (
                    is_contaminated_case_name,
                    clean_contaminated_case_name,
                )

                # Clean all contaminated names first
                cleaned_names = []
                for name in extracted_names:
                    if is_contaminated_case_name(name):
                        logger.error(f"🚨 [CLUSTERING-CONTAMINATION] Detected: '{name}'")
                        cleaned = clean_contaminated_case_name(name)
                        if cleaned and cleaned != name:
                            logger.error(f"[SUCCESS] [CLUSTERING-CLEANED] '{name}' → '{cleaned}'")
                            cleaned_names.append(cleaned)
                        else:
                            logger.error(f"[CLUSTERING-SKIP] Could not clean, skipping")
                            # Don't add contaminated name
                    else:
                        cleaned_names.append(name)

                # USER FIX 2024-10-21: Remove signal words from ALL cleaned names before selection
                # This prevents "See Martin v. Lessee" from beating "Martin v. Lessee" in longest-wins logic
                if cleaned_names:
                    # Note: 're' is already imported at module level - do NOT re-import here
                    # as it causes UnboundLocalError in other branches of this function
                    final_cleaned = []
                    signal_patterns = [
                        r"^(?:see also|see|compare|cf|e\.g\.|i\.e\.|accord|but see|but cf|contra)\s+",
                        r"^(?:if|when|where|while|although|though|unless|until|since|because|as)\s+(?:in\s+)?",
                    ]
                    for name in cleaned_names:
                        cleaned = name
                        for pattern in signal_patterns:
                            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
                        if cleaned and len(cleaned) >= 5:  # Keep only valid names
                            final_cleaned.append(cleaned)
                    cleaned_names = final_cleaned if final_cleaned else cleaned_names

                # CRITICAL: Filter out header patterns from best_extracted_name before using it
                # Check if best_extracted_name contains header patterns (ET AL + role word, or role word + NO)
                if cleaned_names:
                    # Filter out any names that are clearly headers
                    non_header_names = []
                    for name in cleaned_names:
                        name_upper = name.upper()
                        has_et_al = "ET AL" in name_upper or "ETAL" in name_upper.replace(" ", "").replace(
                            ".", ""
                        ).replace(",", "")
                        has_role_word = any(
                            role in name_upper
                            for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                        )
                        has_no = "NO." in name_upper or " NO " in name_upper or name_upper.endswith(" NO")

                        # CRITICAL: Check for the exact Erickson header pattern
                        erickson_pattern = re.search(
                            r"ERICKSON\s+ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                            name_upper,
                        )
                        generic_header_pattern = re.search(
                            r"ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                            name_upper,
                        )

                        # Skip if it's clearly a header (ET AL + role word, or role word + NO, or matches header patterns)
                        if (
                            (has_et_al and has_role_word)
                            or (has_role_word and has_no)
                            or erickson_pattern
                            or generic_header_pattern
                        ):
                            logger.error(f"[STANDARDIZE-CLUSTER] REJECTED header pattern from cluster names: '{name}'")
                            continue
                        non_header_names.append(name)

                    if non_header_names:
                        # CRITICAL: Filter out document primary case name contamination
                        # The primary case name can appear in headers/footers throughout the document
                        document_primary_case_name = getattr(self, "document_primary_case_name", None)
                        # CRITICAL FIX: Sanity check - valid case names are short (<50 chars)
                        # If document_primary_case_name is too long, it was extracted incorrectly
                        # and should not be used for contamination filtering
                        # 50 chars is reasonable for "Party A v. Party B" format
                        if document_primary_case_name and len(document_primary_case_name) > 50:
                            logger.warning(
                                f"[STANDARDIZE-CLUSTER] Skipping contamination filter - document_primary_case_name too long ({len(document_primary_case_name)} chars)"
                            )
                            document_primary_case_name = None
                        if document_primary_case_name:

                            def normalize_for_comparison(name):
                                normalized = name.lower()
                                # Remove "et al" and role words (Petitioners, Respondents, etc.) - these are document header artifacts
                                normalized = re.sub(r"\bet\s+al\.?\b", "", normalized)
                                normalized = re.sub(
                                    r"\b(?:petitioners?|appellants?|plaintiffs?|appellees?|respondents?|defendants?)\b",
                                    "",
                                    normalized,
                                )
                                normalized = re.sub(r"\bno\.?\s*\d+", "", normalized)  # Remove docket numbers
                                # Normalize common variations
                                normalized = re.sub(r"\bllc\b", "llc", normalized)
                                normalized = re.sub(r"\bll\.?c\.?\b", "llc", normalized)
                                normalized = re.sub(r"\binc\.?\b", "inc", normalized)
                                normalized = re.sub(r"\bcorp\.?\b", "corp", normalized)
                                normalized = re.sub(r"\bco\.?\b", "co", normalized)
                                normalized = re.sub(r"[,\.\s]+", " ", normalized)
                                normalized = normalized.strip()
                                return normalized

                            primary_normalized = normalize_for_comparison(document_primary_case_name)
                            filtered_names = []
                            for name in non_header_names:
                                name_normalized = normalize_for_comparison(name)
                                # Reject if it matches the document's primary case name (bidirectional check)
                                if (
                                    name_normalized == primary_normalized
                                    or primary_normalized in name_normalized
                                    or name_normalized in primary_normalized
                                ):
                                    logger.error(
                                        f"[STANDARDIZE-CLUSTER] REJECTED primary case contamination: '{name}' (matches document primary '{document_primary_case_name}')"
                                    )
                                    continue
                                filtered_names.append(name)

                            if filtered_names:
                                non_header_names = filtered_names
                            else:
                                logger.error(
                                    f"[WARNING] [STANDARDIZE-CLUSTER] All names were primary case contamination and were rejected!"
                                )
                                non_header_names = []  # Clear the list so we don't select a contaminated name

                        if non_header_names:
                            best_extracted_name = max(non_header_names, key=lambda n: (len(n), n))
                            logger.error(
                                f"🔧 [STANDARDIZE-CLUSTER] Group has {len(non_header_names)} non-header names → using best: '{best_extracted_name}'"
                            )
                            if len(set(non_header_names)) > 1:
                                logger.error(f"   Variations: {list(set(non_header_names))}")
                        else:
                            best_extracted_name = None
                    else:
                        logger.error(f"[WARNING] [STANDARDIZE-CLUSTER] All names were headers and were rejected!")
                        best_extracted_name = None
                else:
                    logger.error(
                        f"[WARNING] [STANDARDIZE-CLUSTER] All names were contaminated and couldn't be cleaned!"
                    )
                    best_extracted_name = None

            # Pick best extracted year (most common)
            best_extracted_year = None
            if extracted_dates:
                from collections import Counter

                # Extract years from all dates
                years = [self._extract_year_value(d) for d in extracted_dates]
                years = [y for y in years if y]  # Remove None values
                if years:
                    best_extracted_year = Counter(years).most_common(1)[0][0]
                    logger.error(
                        f"🔧 [STANDARDIZE-CLUSTER] Group has {len(years)} extracted years → using best: '{best_extracted_year}'"
                    )

            # PROPAGATE best extracted name and year to ALL citations in cluster
            # This ensures validation won't split the cluster due to extraction variations
            # USER FIX: All citations in a cluster refer to the same case, so they should all have the same extracted_case_name
            # Overwrite all extracted_case_name values with the best one to ensure consistency
            if best_extracted_name:
                # CRITICAL: Final check - reject header patterns before propagating
                best_name_upper = best_extracted_name.upper()
                has_et_al = "ET AL" in best_name_upper or "ETAL" in best_name_upper.replace(" ", "").replace(
                    ".", ""
                ).replace(",", "")
                has_role_word = any(
                    role in best_name_upper
                    for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                )
                has_no = "NO." in best_name_upper or " NO " in best_name_upper or best_name_upper.endswith(" NO")

                # CRITICAL: Check for the exact Erickson header pattern
                erickson_pattern_best = re.search(
                    r"ERICKSON\s+ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                    best_name_upper,
                )
                header_pattern_match = re.search(
                    r"ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                    best_name_upper,
                )

                if (
                    (has_et_al and has_role_word)
                    or (has_role_word and has_no)
                    or erickson_pattern_best
                    or header_pattern_match
                ):
                    logger.error(
                        f"[CLUSTERING-PROPAGATE] REJECTED header pattern: '{best_extracted_name}' - cannot propagate"
                    )
                    best_extracted_name = None  # Don't propagate a header
                else:
                    # Propagate best name to ALL citations in cluster
                    for citation in group:
                        existing_name = (
                            citation.get("extracted_case_name")
                            if isinstance(citation, dict)
                            else getattr(citation, "extracted_case_name", None)
                        )

                        if isinstance(citation, dict):
                            citation["extracted_case_name"] = best_extracted_name
                        else:
                            citation.extracted_case_name = best_extracted_name

                        if existing_name and existing_name != best_extracted_name and existing_name != "N/A":
                            logger.debug(f"   📝 Overwrote '{existing_name}' with best: '{best_extracted_name}'")
                        else:
                            logger.debug(f"   📝 Set extracted_case_name to best: '{best_extracted_name}'")
            else:
                # No best name available - check each citation for headers and clear them
                for citation in group:
                    existing_name = (
                        citation.get("extracted_case_name")
                        if isinstance(citation, dict)
                        else getattr(citation, "extracted_case_name", None)
                    )

                    if existing_name and existing_name != "N/A":
                        existing_name_upper = existing_name.upper()
                        has_et_al_existing = "ET AL" in existing_name_upper or "ETAL" in existing_name_upper.replace(
                            " ", ""
                        ).replace(".", "").replace(",", "")
                        has_role_word_existing = any(
                            role in existing_name_upper
                            for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                        )
                        has_no_existing = (
                            "NO." in existing_name_upper
                            or " NO " in existing_name_upper
                            or existing_name_upper.endswith(" NO")
                        )

                        # CRITICAL: Check for the exact Erickson header pattern
                        erickson_pattern_existing = re.search(
                            r"ERICKSON\s+ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                            existing_name_upper,
                        )
                        header_pattern_existing = re.search(
                            r"ET\s+AL\.?\s*,?\s*(?:PETITIONER|RESPONDENT|APPELLANT|APPELLEE|PLAINTIFF|DEFENDANT)",
                            existing_name_upper,
                        )

                        if (
                            (has_et_al_existing and has_role_word_existing)
                            or (has_role_word_existing and has_no_existing)
                            or erickson_pattern_existing
                            or header_pattern_existing
                        ):
                            logger.error(
                                f"[CLUSTERING-PROPAGATE] REJECTED header pattern: '{existing_name}' - clearing it"
                            )
                            # Clear the header
                            if isinstance(citation, dict):
                                citation["extracted_case_name"] = "N/A"
                            else:
                                citation.extracted_case_name = "N/A"

            # PROPAGATE best extracted year to ALL citations in cluster (same logic as name)
            # All citations in a cluster refer to the same case, so they should all have the same extracted_date
            if best_extracted_year:
                for citation in group:
                    existing_date = (
                        citation.get("extracted_date")
                        if isinstance(citation, dict)
                        else getattr(citation, "extracted_date", None)
                    )

                    if isinstance(citation, dict):
                        citation["extracted_date"] = best_extracted_year
                    else:
                        citation.extracted_date = best_extracted_year

                    if existing_date and existing_date != best_extracted_year and existing_date != "N/A":
                        logger.debug(f"   📅 Overwrote '{existing_date}' with best: '{best_extracted_year}'")
                    else:
                        logger.debug(f"   📅 Set extracted_date to best: '{best_extracted_year}'")

            for citation in group:
                enhanced_citation = self._create_enhanced_citation(citation, case_name, case_year, group)
                enhanced_citations.append(enhanced_citation)

        return enhanced_citations

    def _create_enhanced_citation(
        self, citation: Any, case_name: Optional[str], case_year: Optional[str], group: List[Any]
    ) -> Any:
        """Create an enhanced citation object with propagated metadata."""
        if hasattr(citation, "__dict__"):
            import copy

            enhanced = copy.copy(citation)
        elif isinstance(citation, dict):
            enhanced = citation.copy()
        else:
            enhanced = citation

        if isinstance(citation, dict):
            canonical_name = citation.get("canonical_name")
            canonical_date = citation.get("canonical_date")
            verified_flag = citation.get("verified", False)
            original_citation_text = citation.get("citation", str(citation))
        else:
            canonical_name = getattr(citation, "canonical_name", None)
            canonical_date = getattr(citation, "canonical_date", None)
            verified_flag = getattr(citation, "verified", False)
            original_citation_text = getattr(citation, "citation", str(citation))

        if verified_flag and canonical_name and canonical_name != "N/A" and not case_name:
            case_name = canonical_name
        if verified_flag and canonical_date and canonical_date != "N/A" and not case_year:
            case_year = self._extract_year_value(canonical_date) or canonical_date

        # CRITICAL FIX: Extract citation text properly from different object types
        members = []
        for c in group:
            if isinstance(c, dict):
                # For dict objects, get the 'citation' field first, then 'text'
                cit_text = c.get("citation") or c.get("text") or str(c)
            else:
                # For object attributes, get 'citation' first, then convert to string
                cit_text = getattr(c, "citation", None) or str(c)

            # Ensure we're getting clean citation text, not dict representations
            if isinstance(cit_text, str) and not cit_text.startswith("{"):
                members.append(cit_text)
            else:
                # Fallback: try to extract citation from dict string or use string representation
                if isinstance(cit_text, str):
                    import re

                    # Try to extract citation from dict string like "{'citation': '123 F.3d 456', ...}"
                    citation_match = re.search(r"'citation':\s*'([^']+)'", cit_text)
                    if citation_match:
                        members.append(citation_match.group(1))
                    else:
                        members.append(str(cit_text))
                else:
                    members.append(str(cit_text))
        parallel = len(group) > 1

        if hasattr(enhanced, "__dict__"):
            enhanced.cluster_case_name = case_name
            enhanced.cluster_year = case_year
            enhanced.cluster_size = len(group)
            enhanced.is_in_cluster = parallel
            enhanced.cluster_members = members

            # FIX #29: CRITICAL DATA INTEGRITY FIX
            # NEVER overwrite extracted_case_name or extracted_date with cluster-level data!
            # Each citation must preserve its OWN extracted data from the document.
            # Overwriting it with cluster-level data (which comes from the FIRST citation)
            # destroys data integrity and causes contamination.
            #
            # Example bug this caused:
            #   - Citation "183 Wn.2d 649" extracted "Lopez Demetrio" (correct!)
            #   - Citation "192 Wn.2d 453" extracted "Spokane County" (correct!)
            #   - Both clustered together (bug in clustering)
            #   - Cluster case_name set to "Spokane County" (from first citation)
            #   - "183 Wn.2d 649"'s extracted_case_name overwritten to "Spokane County" (WRONG!)
            #
            # REMOVED: Code that was contaminating extracted_case_name and extracted_date
            # The cluster_case_name and cluster_year fields exist for cluster-level info.
            # Each citation's extracted_case_name and extracted_date must remain unchanged.

            enhanced.is_parallel = parallel
            enhanced.parallel_citations = [member for member in members if member != original_citation_text]
        elif isinstance(enhanced, dict):
            enhanced["cluster_case_name"] = case_name
            enhanced["cluster_year"] = case_year
            enhanced["cluster_size"] = len(group)
            enhanced["is_in_cluster"] = parallel
            enhanced["cluster_members"] = members

            # FIX #29: CRITICAL DATA INTEGRITY FIX (dict path)
            # NEVER overwrite extracted_case_name or extracted_date with cluster-level data!
            # Each citation must preserve its OWN extracted data from the document.
            # REMOVED: Code that was contaminating extracted_case_name and extracted_date

            enhanced["is_parallel"] = parallel
            enhanced["parallel_citations"] = [member for member in members if member != original_citation_text]

        return enhanced

    def _create_final_clusters(self, enhanced_citations: List[Any]) -> List[Dict[str, Any]]:
        """Create final clusters from proximity-based parallel groups.

        CRITICAL: This should PRESERVE the parallel groups from _detect_parallel_citations()
        which are stored in citation.cluster_members. We should NOT re-cluster here!

        The clustering has ALREADY happened based on:
        - Proximity in document (citations close together)
        - Same case name before citations
        - Same date after citations

        This function just converts those groups into cluster dictionaries.
        """
        # Use cluster_members to identify which citations belong together
        # Each citation has cluster_members = list of citations in the same parallel group
        processed = set()
        cluster_groups = []

        for citation in enhanced_citations:
            citation_id = id(citation)
            if citation_id in processed:
                continue

            # FIX 2024-11-08: CRITICAL CLUSTERING FIX
            # Use parallel_citations array (populated by verification) in addition to cluster_members
            # This fixes the bug where parallel citations are detected but not clustered
            member_texts = []

            # Try parallel_citations first (populated by verification/eyecite)
            if hasattr(citation, "parallel_citations"):
                parallel_cits = getattr(citation, "parallel_citations", [])
                if parallel_cits:
                    # Add self citation to the list
                    self_citation = (
                        getattr(citation, "citation", str(citation)) if hasattr(citation, "citation") else str(citation)
                    )
                    member_texts = [self_citation] + list(parallel_cits)
            elif isinstance(citation, dict):
                parallel_cits = citation.get("parallel_citations", [])
                if parallel_cits:
                    # Add self citation to the list
                    self_citation = citation.get("citation", str(citation))
                    member_texts = [self_citation] + list(parallel_cits)

            # Fallback to cluster_members if parallel_citations not available
            if not member_texts:
                if hasattr(citation, "cluster_members"):
                    member_texts = getattr(citation, "cluster_members", [])
                elif isinstance(citation, dict):
                    member_texts = citation.get("cluster_members", [])
                else:
                    member_texts = []

            # Find all citations that share the same parallel_citations or cluster_members
            if len(member_texts) > 1:
                # This is a parallel group - find all citations with the same members
                group = []
                for other_citation in enhanced_citations:
                    other_id = id(other_citation)
                    if other_id in processed:
                        continue

                    # FIX 2024-11-08: Check both parallel_citations and cluster_members
                    other_members = set()

                    # Try parallel_citations first
                    if hasattr(other_citation, "parallel_citations"):
                        parallel_cits = getattr(other_citation, "parallel_citations", [])
                        if parallel_cits:
                            other_self_citation = (
                                getattr(other_citation, "citation", str(other_citation))
                                if hasattr(other_citation, "citation")
                                else str(other_citation)
                            )
                            other_members = set([other_self_citation] + list(parallel_cits))
                    elif isinstance(other_citation, dict):
                        parallel_cits = other_citation.get("parallel_citations", [])
                        if parallel_cits:
                            other_self_citation = other_citation.get("citation", str(other_citation))
                            other_members = set([other_self_citation] + list(parallel_cits))

                    # Fallback to cluster_members
                    if not other_members:
                        if hasattr(other_citation, "cluster_members"):
                            other_members = set(getattr(other_citation, "cluster_members", []))
                        elif isinstance(other_citation, dict):
                            other_members = set(other_citation.get("cluster_members", []))

                    # If this citation shares the same parallel_citations/cluster_members, it's in the same group
                    if other_members and set(member_texts) == other_members:
                        group.append(other_citation)
                        processed.add(other_id)

                if group:
                    cluster_groups.append(group)
            else:
                # Single citation (not in a parallel group)
                cluster_groups.append([citation])
                processed.add(citation_id)

        # Convert cluster groups to cluster dictionaries
        # FIX #17: Use ONLY extracted data for clustering - never canonical data
        # This prevents contamination of document-sourced information
        final_clusters = []
        for i, citations in enumerate(cluster_groups):
            if not citations:
                continue

            # CRITICAL FIX (NOV 10): Fallback through ALL citations in cluster to find valid extracted name
            # Don't just use first citation - it might have 'N/A' while others have valid names
            extracted_name = None
            extracted_date = None

            for citation in citations:
                # Try to get extracted_case_name
                if hasattr(citation, "extracted_case_name"):
                    name = citation.extracted_case_name
                elif hasattr(citation, "get"):
                    name = citation.get("extracted_case_name", None)
                else:
                    name = None

                # Use first valid name found
                if not extracted_name and name and name not in ("N/A", None, "", "Unknown"):
                    extracted_name = name

                # Try to get extracted_date
                if hasattr(citation, "extracted_date"):
                    date = citation.extracted_date
                elif hasattr(citation, "get"):
                    date = citation.get("extracted_date", None)
                else:
                    date = None

                # Use first valid date found
                if not extracted_date and date and date not in ("N/A", None, "", "Unknown"):
                    extracted_date = date

                # Stop if we have both
                if extracted_name and extracted_date:
                    break

            # Create cluster key using ONLY extracted data
            if extracted_name and extracted_name != "N/A":
                normalized_name = self._normalize_case_name(extracted_name)
            else:
                normalized_name = "unknown"

            if extracted_date and extracted_date != "N/A":
                year_match = re.search(r"(19|20)\d{2}", str(extracted_date))
                normalized_year = year_match.group(0) if year_match else str(extracted_date)[:4]
            else:
                normalized_year = "unknown"

            cluster_key = f"{normalized_name}_{normalized_year}"

            # CRITICAL FIX: Deduplicate citations within the cluster
            # Same citation can appear multiple times in document, leading to duplicates in cluster
            deduplicated_citations = self._deduplicate_cluster_citations(citations)

            # CRITICAL FIX: Ensure cluster_members is a list of citation strings, not objects or JSON strings
            cluster_members_list = []
            for cit in deduplicated_citations:
                if isinstance(cit, dict):
                    cit_text = cit.get("citation", str(cit))
                elif hasattr(cit, "citation"):
                    cit_text = cit.citation
                else:
                    cit_text = str(cit)
                cluster_members_list.append(cit_text)

            # USER FIX: Populate canonical data from verified citations for DISPLAY purposes
            # (not used for clustering logic, but needed by frontend)
            best_canonical_name = None
            best_canonical_date = None
            best_canonical_url = None
            any_verified = False
            for cit in deduplicated_citations:
                cit_verified = cit.get("verified", False) if isinstance(cit, dict) else getattr(cit, "verified", False)
                if cit_verified:
                    any_verified = True
                    cit_canonical = (
                        cit.get("canonical_name") if isinstance(cit, dict) else getattr(cit, "canonical_name", None)
                    )
                    if cit_canonical and not best_canonical_name:
                        best_canonical_name = cit_canonical
                        best_canonical_date = (
                            cit.get("canonical_date") if isinstance(cit, dict) else getattr(cit, "canonical_date", None)
                        )
                        best_canonical_url = (
                            cit.get("canonical_url") if isinstance(cit, dict) else getattr(cit, "canonical_url", None)
                        )
                        break

            # USER FIX 2024-12-24: Propagate the best extracted_date to all citations in the cluster
            # This ensures consistency between cluster-level extracted_date and citation-level extracted_date
            # (e.g., "2000" from boundary detection instead of "2001" from initial extraction)
            if extracted_date and extracted_date not in ("N/A", None, "", "Unknown"):
                for cit in deduplicated_citations:
                    if isinstance(cit, dict):
                        old_date = cit.get("extracted_date")
                        cit["extracted_date"] = extracted_date
                        if old_date and old_date != extracted_date and old_date != "N/A":
                            logger.debug(
                                f"[CLUSTER-DATE-FIX] Updated citation extracted_date: {old_date} -> {extracted_date}"
                            )
                    elif hasattr(cit, "extracted_date"):
                        old_date = cit.extracted_date
                        cit.extracted_date = extracted_date
                        if old_date and old_date != extracted_date and old_date != "N/A":
                            logger.debug(
                                f"[CLUSTER-DATE-FIX] Updated citation extracted_date: {old_date} -> {extracted_date}"
                            )

            cluster = {
                "cluster_id": f"cluster_{i+1}",
                "cluster_key": cluster_key,
                "citations": deduplicated_citations,
                "size": len(deduplicated_citations),
                # FIX #17: Store ONLY extracted data for CLUSTERING decisions
                # But still populate canonical data for DISPLAY purposes (USER FIX)
                "cluster_case_name": extracted_name,  # Pure extracted from document
                "cluster_year": extracted_date,  # Pure extracted from document
                "canonical_name": best_canonical_name,  # USER FIX: For display, not clustering
                "canonical_date": best_canonical_date,  # USER FIX: For display, not clustering
                "canonical_url": best_canonical_url,  # USER FIX: For display
                "extracted_case_name": extracted_name,  # USER FIX: Explicit extracted name field
                "cluster_members": cluster_members_list,  # List of citation strings, not objects
                "confidence": self._calculate_cluster_confidence(deduplicated_citations),
                "verified": any_verified,  # USER FIX: Track if any citation is verified
                # Frontend display fields
                "verifying_display_name": best_canonical_name or extracted_name,
                "submitted_display_name": extracted_name,
                "metadata": {
                    "cluster_type": "proximity_based",  # Clustering by proximity in document (NOT by metadata!)
                    "created_by": "unified_master",
                    "cluster_key": cluster_key,
                    "cluster_members_preserved": True,  # Indicates we preserved parallel groups from Step 1
                    "data_source": "extracted_only",  # Flag indicating clustering used extracted data only
                },
                "verification_status": "verified" if any_verified else "not_verified",
                "verification_source": None,
            }
            final_clusters.append(cluster)

        # USER FIX: Split clusters where citations have different canonical dates
        # This fixes cases like Meri-Weather where Superior Court (2000) and Appellate Court (2001)
        # are incorrectly merged based on proximity but are actually different cases
        split_clusters = self._split_clusters_by_canonical_date(final_clusters)

        return split_clusters

    def _split_clusters_by_canonical_date(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split clusters where citations have significantly different canonical dates.

        USER FIX: This handles cases like Meri-Weather where:
        - Superior Court case (2000-03-27) with citations 47 Conn. Supp. 113, 778 A.2d 1006
        - Appellate Court case (2001-06-12) with citations 63 Conn. App. 695, 778 A.2d 1038

        These were merged based on proximity (same case name) but are different proceedings
        with different canonical dates. We split them based on canonical_date differences.
        """
        result_clusters = []

        for cluster in clusters:
            citations = cluster.get("citations", [])

            # Group citations by canonical year
            year_groups = {}
            for cit in citations:
                canonical_date = (
                    cit.get("canonical_date") if isinstance(cit, dict) else getattr(cit, "canonical_date", None)
                )
                if canonical_date:
                    year_match = re.search(r"(19|20)\d{2}", str(canonical_date))
                    if year_match:
                        year = year_match.group(0)
                        if year not in year_groups:
                            year_groups[year] = []
                        year_groups[year].append(cit)
                    else:
                        # No year found, put in 'unknown' group
                        if "unknown" not in year_groups:
                            year_groups["unknown"] = []
                        year_groups["unknown"].append(cit)
                else:
                    # No canonical date, put in 'unknown' group
                    if "unknown" not in year_groups:
                        year_groups["unknown"] = []
                    year_groups["unknown"].append(cit)

            # If all citations are in the same year group (or unknown), keep cluster as-is
            known_years = [y for y in year_groups.keys() if y != "unknown"]
            if len(known_years) <= 1:
                result_clusters.append(cluster)
                continue

            # USER REQUEST: Split appellate history into separate clusters
            # e.g., "75 Wash. 581 (1913), aff'd, 243 U.S. 219 (1917)" should be TWO clusters:
            # - Cluster 1: Washington Supreme Court (1913) with 75 Wash. 581, 135 P. 645
            # - Cluster 2: U.S. Supreme Court (1917) with 243 U.S. 219, 37 S. Ct. 260, 61 L. Ed. 685
            # Each court's opinion is verified independently with its own canonical date
            years_int = sorted([int(y) for y in known_years])
            max_diff = years_int[-1] - years_int[0] if len(years_int) > 1 else 0

            if max_diff == 0:
                # All citations have same canonical year - keep cluster as-is
                result_clusters.append(cluster)
                continue

            # Split the cluster by canonical year
            logger.warning(
                f"⚠️ SPLITTING cluster '{cluster.get('cluster_case_name', 'Unknown')}' - citations have different canonical years: {known_years}"
            )

            for year, year_cits in year_groups.items():
                if not year_cits:
                    continue

                # Create a new cluster for this year group
                new_cluster = cluster.copy()
                new_cluster["citations"] = year_cits
                new_cluster["size"] = len(year_cits)
                new_cluster["cluster_id"] = f"{cluster.get('cluster_id', 'cluster')}_year_{year}"

                # Update cluster_members
                cluster_members_list = []
                for cit in year_cits:
                    if isinstance(cit, dict):
                        cit_text = cit.get("citation", str(cit))
                    elif hasattr(cit, "citation"):
                        cit_text = cit.citation
                    else:
                        cit_text = str(cit)
                    cluster_members_list.append(cit_text)
                new_cluster["cluster_members"] = cluster_members_list

                # Update canonical data from this year group
                for cit in year_cits:
                    cit_verified = (
                        cit.get("verified", False) if isinstance(cit, dict) else getattr(cit, "verified", False)
                    )
                    if cit_verified:
                        cit_canonical = (
                            cit.get("canonical_name") if isinstance(cit, dict) else getattr(cit, "canonical_name", None)
                        )
                        if cit_canonical:
                            new_cluster["canonical_name"] = cit_canonical
                            new_cluster["canonical_date"] = (
                                cit.get("canonical_date")
                                if isinstance(cit, dict)
                                else getattr(cit, "canonical_date", None)
                            )
                            new_cluster["canonical_url"] = (
                                cit.get("canonical_url")
                                if isinstance(cit, dict)
                                else getattr(cit, "canonical_url", None)
                            )
                            new_cluster["verifying_display_name"] = cit_canonical
                            break

                # Update cluster key with year
                new_cluster["cluster_key"] = f"{cluster.get('cluster_key', 'unknown')}_{year}"
                new_cluster["metadata"] = {
                    **cluster.get("metadata", {}),
                    "split_by_canonical_date": True,
                    "original_cluster_id": cluster.get("cluster_id"),
                }

                logger.info(
                    f"  Created split cluster: {new_cluster['cluster_id']} with {len(year_cits)} citations for year {year}"
                )
                result_clusters.append(new_cluster)

        return result_clusters

    def _parse_citation_components(self, citation_text: str) -> Optional[Dict[str, str]]:
        """Parse citation into volume, reporter, and page components.

        P5 FIX: Helper function for preventing false clustering.

        Examples:
            "506 U.S. 224" -> {'volume': '506', 'reporter': 'U.S.', 'page': '224'}
            "100 F.3d 123" -> {'volume': '100', 'reporter': 'F.3d', 'page': '123'}
            "783 F.3d 1328" -> {'volume': '783', 'reporter': 'F.3d', 'page': '1328'}
        """
        if not citation_text:
            return None

        import re

        # Pattern: volume reporter page
        # CRITICAL FIX: Handle reporters like "F.3d", "F.2d", "P.3d" where the second part starts with a digit
        # Pattern breakdown:
        #   (\d+) - volume (one or more digits)
        #   \s+ - whitespace
        #   ([A-Z][\w\.]+(?:\s+[\w\.]+)*) - reporter (starts with uppercase, then letters/digits/periods, optionally with spaces)
        #   \s+ - whitespace
        #   (\d+) - page (one or more digits)
        pattern = r"(\d+)\s+([A-Z][\w\.]+(?:\s+[\w\.]+)*?)\s+(\d+)"
        match = re.search(pattern, citation_text)

        if match:
            return {"volume": match.group(1), "reporter": match.group(2).strip(), "page": match.group(3)}

        return None

    def _deduplicate_cluster_citations(self, citations: List[Any]) -> List[Any]:
        """
        Deduplicate citations within a cluster.

        The same citation can appear multiple times in a document (e.g., "3 Wn.3d 179" cited twice).
        This method removes exact duplicates while preserving the best quality version.

        Deduplication key: citation text
        Quality preference: verified > unverified, has extracted_case_name > N/A
        """
        if not citations or len(citations) <= 1:
            return citations

        seen = {}
        for citation in citations:
            # Get citation text (the unique key)
            if hasattr(citation, "citation"):
                cit_text = citation.citation
            elif hasattr(citation, "get"):
                cit_text = citation.get("citation", "")
            else:
                continue

            if not cit_text:
                continue

            # Check if we've seen this citation before
            if cit_text in seen:
                existing = seen[cit_text]

                # Prefer verified over unverified
                cit_verified = (
                    getattr(citation, "verified", False)
                    if hasattr(citation, "verified")
                    else citation.get("verified", False) if hasattr(citation, "get") else False
                )
                existing_verified = (
                    getattr(existing, "verified", False)
                    if hasattr(existing, "verified")
                    else existing.get("verified", False) if hasattr(existing, "get") else False
                )

                # Prefer citations with extracted case names
                cit_name = (
                    getattr(citation, "extracted_case_name", "N/A")
                    if hasattr(citation, "extracted_case_name")
                    else citation.get("extracted_case_name", "N/A") if hasattr(citation, "get") else "N/A"
                )
                existing_name = (
                    getattr(existing, "extracted_case_name", "N/A")
                    if hasattr(existing, "extracted_case_name")
                    else existing.get("extracted_case_name", "N/A") if hasattr(existing, "get") else "N/A"
                )

                # Quality score: verified (2 points) + has name (1 point)
                cit_score = (2 if cit_verified else 0) + (1 if cit_name and cit_name != "N/A" else 0)
                existing_score = (2 if existing_verified else 0) + (
                    1 if existing_name and existing_name != "N/A" else 0
                )

                # Keep the better quality citation
                if cit_score > existing_score:
                    logger.debug(f"[DEDUP_CLUSTER] Replacing '{cit_text}' (score {cit_score} > {existing_score})")
                    seen[cit_text] = citation
                else:
                    logger.debug(
                        f"[DEDUP_CLUSTER] Keeping existing '{cit_text}' (score {existing_score} >= {cit_score})"
                    )
            else:
                seen[cit_text] = citation

        deduplicated = list(seen.values())

        if len(deduplicated) < len(citations):
            logger.info(
                f"[DEDUP_CLUSTER] Removed {len(citations) - len(deduplicated)} duplicate citations within cluster ({len(citations)} → {len(deduplicated)})"
            )

        return deduplicated

    def _should_add_to_cluster(self, citation: Any, existing_citations: List[Any]) -> bool:
        """Validate if a citation should be added to an existing cluster.

        FIX #17: Use ONLY extracted data for clustering decisions.
        Canonical data should NEVER influence clustering - clustering is based on
        what's in the document, not what the API says.
        """
        if not existing_citations:
            return True

        # Get citation metadata - USE ONLY EXTRACTED DATA
        # FIX #17: Removed all canonical_name and canonical_date references
        cit_name = getattr(citation, "extracted_case_name", None)
        cit_year = getattr(citation, "extracted_date", None)

        # Extract year from date if needed
        def extract_year(date_str):
            if not date_str or date_str == "N/A":
                return None
            year_match = re.search(r"(19|20)\d{2}", str(date_str))
            return int(year_match.group(0)) if year_match else None

        cit_year_int = extract_year(cit_year)

        # Check against first citation in cluster - USE ONLY EXTRACTED DATA
        first_cit = existing_citations[0]
        first_name = getattr(first_cit, "extracted_case_name", None)
        first_year = getattr(first_cit, "extracted_date", None)

        first_year_int = extract_year(first_year)

        # VALIDATION 1: Year consistency check (EXTRACTED DATA ONLY)
        # If both have years, they must be within 2 years of each other
        if cit_year_int and first_year_int:
            year_diff = abs(cit_year_int - first_year_int)
            if year_diff > 2:
                logger.warning(
                    f"MASTER_CLUSTER: Extracted year mismatch: {cit_year_int} vs {first_year_int} (diff: {year_diff} years)"
                )
                return False

        # VALIDATION 2: Case name similarity (EXTRACTED DATA ONLY)
        # If both have case names, they must be similar
        if cit_name and cit_name != "N/A" and first_name and first_name != "N/A":
            similarity = self._calculate_name_similarity(cit_name, first_name)
            if similarity < self.case_name_similarity_threshold:
                logger.warning(
                    f"MASTER_CLUSTER: Extracted case name mismatch: '{cit_name}' vs '{first_name}' (similarity: {similarity:.2f})"
                )
                return False

        # P5 FIX: VALIDATION 3: Same reporter + different volumes = DIFFERENT CASES
        # This prevents false clustering like "506 U.S." and "546 U.S." being grouped
        # Same case can have DIFFERENT reporters (e.g., "100 F.3d 1" and "100 S.Ct. 1")
        # but CANNOT have same reporter with different volumes
        cit_text = getattr(citation, "citation", None) or getattr(citation, "text", "")
        first_text = getattr(first_cit, "citation", None) or getattr(first_cit, "text", "")

        if cit_text and first_text:
            # Extract reporter and volume from both citations
            cit_parsed = self._parse_citation_components(cit_text)
            first_parsed = self._parse_citation_components(first_text)

            if cit_parsed and first_parsed:
                cit_reporter = cit_parsed.get("reporter", "")
                cit_volume = cit_parsed.get("volume", "")
                first_reporter = first_parsed.get("reporter", "")
                first_volume = first_parsed.get("volume", "")

                # If both have same reporter but different volumes, they are DIFFERENT cases
                if cit_reporter and first_reporter and cit_reporter == first_reporter:
                    if cit_volume and first_volume and cit_volume != first_volume:
                        logger.warning(
                            f"P5_FIX: Preventing false cluster - same reporter '{cit_reporter}' but different volumes: {cit_volume} vs {first_volume}"
                        )
                        return False

        # FIX #17: Removed all canonical data validation
        # Clustering should be based ONLY on extracted data (from the document),
        # NOT on canonical data (from the API)

        return True

    def _apply_verification_to_clusters(self, clusters: List[Dict[str, Any]]) -> None:
        """Apply verification to clusters if enabled - OPTIMIZED WITH BATCH API."""
        logger.error(
            f"[DEBUG] [VERIFY-DEBUG] _apply_verification_to_clusters called: enable_verification={self.enable_verification}, clusters={len(clusters)}"
        )
        if not self.enable_verification:
            logger.error(f"[DEBUG] [VERIFY-DEBUG] Verification DISABLED - returning early")
            return

        logger.error(f"[DEBUG] [VERIFY-DEBUG] Verification ENABLED - proceeding with {len(clusters)} clusters")

        try:
            # OPTIMIZATION: Use batch verification instead of one-by-one
            # Collect all unique citations across all clusters
            all_citations = []
            citation_to_cluster_map = {}  # Map citation text -> (cluster_idx, citation_idx)

            for cluster_idx, cluster in enumerate(clusters):
                citations = cluster.get("citations", [])
                if not citations:
                    continue

                for cit_idx, citation_obj in enumerate(citations):
                    # Debug: Check what type of object we're working with
                    is_verified = False
                    source_info = "Unknown"

                    if isinstance(citation_obj, dict):
                        is_verified = citation_obj.get("verified", False)
                        source_info = citation_obj.get("verification_source", citation_obj.get("source", "Unknown"))
                    else:
                        is_verified = getattr(citation_obj, "verified", False)
                        source_info = getattr(citation_obj, "source", "Unknown")

                    logger.error(
                        f"[DEBUG] [VERIFY-DEBUG] Citation object type: {type(citation_obj)}, verified: {is_verified}, source: {source_info}"
                    )

                    # Handle both dict and object citation formats
                    if isinstance(citation_obj, dict):
                        citation_text = citation_obj.get("citation", str(citation_obj))
                        case_name = citation_obj.get("extracted_case_name", None)
                        case_date = citation_obj.get("extracted_date", None)
                        # Skip already verified citations to preserve source information
                        if is_verified:
                            logger.error(
                                f"[DEBUG] [VERIFY-DEBUG] Skipping already verified citation: {citation_text} (source: {source_info})"
                            )
                            continue
                    else:
                        citation_text = getattr(citation_obj, "citation", str(citation_obj))
                        case_name = getattr(citation_obj, "extracted_case_name", None)
                        case_date = getattr(citation_obj, "extracted_date", None)
                        # Skip already verified citations to preserve source information
                        if is_verified:
                            logger.error(
                                f"[DEBUG] [VERIFY-DEBUG] Skipping already verified citation: {citation_text} (source: {source_info})"
                            )
                            continue

                    # Skip citations that already have errors
                    if hasattr(citation_obj, "error") and citation_obj.error:
                        continue

                    all_citations.append(
                        {
                            "citation": citation_text,
                            "case_name": case_name,
                            "case_date": case_date,
                            "cluster_idx": cluster_idx,
                            "cit_idx": cit_idx,
                        }
                    )
                    citation_to_cluster_map[citation_text] = (cluster_idx, cit_idx)

            if not all_citations:
                logger.info("No citations to verify")
                return

            logger.info(f"🚀 BATCH VERIFICATION: Verifying {len(all_citations)} citations in single batch API call")

            # Use batch verification API
            from src.unified_verification_master import get_master_verifier

            verifier = get_master_verifier()

            # Prepare batch data
            citation_texts = [c["citation"] for c in all_citations]
            case_names = [c["case_name"] for c in all_citations]
            case_dates = [c["case_date"] for c in all_citations]

            # Call batch verification (async function, need to run in event loop)
            import asyncio

            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, create new loop in thread
                    from concurrent.futures import ThreadPoolExecutor

                    def run_batch():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(
                                verifier.verify_citations_batch(citation_texts, case_names, case_dates)
                            )
                        finally:
                            new_loop.close()

                    with ThreadPoolExecutor(max_workers=1) as executor:
                        batch_results = executor.submit(run_batch).result(timeout=60.0)
                else:
                    # No running loop, use this one
                    batch_results = loop.run_until_complete(
                        verifier.verify_citations_batch(citation_texts, case_names, case_dates)
                    )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    batch_results = loop.run_until_complete(
                        verifier.verify_citations_batch(citation_texts, case_names, case_dates)
                    )
                finally:
                    loop.close()

            logger.info(f"[SUCCESS] BATCH VERIFICATION: Received {len(batch_results)} results")

            # DEBUG: Log verification success rate
            verified_count = sum(1 for r in batch_results if r.verified)
            possible_match_count = sum(1 for r in batch_results if getattr(r, "possible_match", False))
            logger.error(
                f"[BATCH-VERIFY-DEBUG] Verified: {verified_count}/{len(batch_results)}, Possible Matches: {possible_match_count}/{len(batch_results)}"
            )
            for r in batch_results[:5]:
                possible_match = getattr(r, "possible_match", False)
                logger.error(
                    f"  - {r.citation}: verified={r.verified}, possible_match={possible_match}, source={r.source if (r.verified or possible_match) else r.error}"
                )

            # Apply results back to citations (match by citation text, not by list order)
            citation_to_queue = defaultdict(deque)
            for i, info in enumerate(all_citations):
                citation_to_queue[info["citation"]].append(i)

            for result in batch_results:
                # Get the citation text from the result
                res_text = getattr(result, "citation", None) or getattr(result, "text", None) or ""
                if not res_text or res_text not in citation_to_queue or not citation_to_queue[res_text]:
                    logger.warning(
                        f"[APPLY-VERIFICATION] Could not map verification result back to request for citation='{res_text}'"
                    )
                    continue

                req_idx = citation_to_queue[res_text].popleft()
                cit_info = all_citations[req_idx]
                cluster_idx = cit_info["cluster_idx"]
                cit_idx = cit_info["cit_idx"]
                cluster = clusters[cluster_idx]
                citations = cluster.get("citations", [])
                citation_obj = citations[cit_idx]
                citation_text = cit_info["citation"]

                if result.verified:
                    # USER FIX: Validate year match before setting verified=True
                    # Get extracted date from citation object
                    if hasattr(citation_obj, "__dict__"):
                        extracted_date = getattr(citation_obj, "extracted_date", None)
                    else:
                        extracted_date = citation_obj.get("extracted_date") if isinstance(citation_obj, dict) else None

                    canonical_date = result.canonical_date
                    year_match = True  # Default to True if no dates to compare
                    if extracted_date and canonical_date:
                        import re

                        ext_year = re.search(r"(19|20)\d{2}", str(extracted_date))
                        can_year = re.search(r"(19|20)\d{2}", str(canonical_date))
                        if ext_year and can_year:
                            year_match = ext_year.group(0) == can_year.group(0)

                    if not year_match:
                        # Year mismatch - reject verification
                        logger.warning(
                            f"❌ [APPLY-VERIFICATION] Citation: {citation_text} - REJECTED due to year mismatch"
                        )
                        logger.warning(f"   Extracted year: {extracted_date} vs Canonical year: {canonical_date}")
                        if hasattr(citation_obj, "__dict__"):
                            citation_obj.verified = False
                            citation_obj.verification_error = (
                                f"Year mismatch: extracted {extracted_date} vs canonical {canonical_date}"
                            )
                        elif isinstance(citation_obj, dict):
                            citation_obj["verified"] = False
                            citation_obj["verification_error"] = (
                                f"Year mismatch: extracted {extracted_date} vs canonical {canonical_date}"
                            )
                        continue  # Skip to next citation

                    # VERIFIED: Apply canonical data
                    logger.error(f"🔧 [APPLY-VERIFICATION] Citation: {citation_text} - VERIFIED")
                    logger.error(f"   📝 result.canonical_name = {result.canonical_name}")
                    logger.error(f"   📝 result.canonical_date = {result.canonical_date}")

                    if hasattr(citation_obj, "__dict__"):
                        citation_obj.verified = True
                        citation_obj.canonical_name = result.canonical_name
                        citation_obj.canonical_date = result.canonical_date
                        citation_obj.canonical_url = result.canonical_url
                        citation_obj.verification_source = result.source
                        citation_obj.possible_match = False
                        logger.error(
                            f"   [SUCCESS] AFTER (object): verified=True, canonical_name = {citation_obj.canonical_name}"
                        )
                    elif isinstance(citation_obj, dict):
                        citation_obj["verified"] = True
                        citation_obj["canonical_name"] = result.canonical_name
                        citation_obj["canonical_date"] = result.canonical_date
                        citation_obj["canonical_url"] = result.canonical_url
                        citation_obj["verification_source"] = result.source
                        citation_obj["possible_match"] = False
                        logger.error(
                            f"   [SUCCESS] AFTER (dict): verified=True, canonical_name = {citation_obj['canonical_name']}"
                        )
                elif getattr(result, "possible_match", False):
                    # POSSIBLE MATCH: Apply canonical data but mark as possible match
                    logger.error(f"🔶 [APPLY-VERIFICATION] Citation: {citation_text} - POSSIBLE MATCH")
                    logger.error(f"   📝 result.canonical_name = {result.canonical_name}")
                    logger.error(f"   📝 result.canonical_date = {result.canonical_date}")

                    # CRITICAL: possible_match=True but verified=False means we found a potential match
                    # but couldn't verify it. Per user rule: unverified citations CANNOT have canonical data.
                    # Store the potential match info in metadata but don't set canonical fields.
                    if hasattr(citation_obj, "__dict__"):
                        citation_obj.verified = False
                        citation_obj.possible_match = True
                        # CRITICAL: Don't set canonical_name/canonical_date for unverified citations
                        # Store potential match in metadata instead
                        citation_obj.canonical_name = None
                        citation_obj.canonical_date = None
                        citation_obj.canonical_url = None
                        citation_obj.verification_source = result.source
                        citation_obj.verification_error = result.error
                        # Store potential match in metadata for reference
                        if not hasattr(citation_obj, "metadata") or citation_obj.metadata is None:
                            citation_obj.metadata = {}
                        citation_obj.metadata["possible_match_name"] = result.canonical_name
                        citation_obj.metadata["possible_match_date"] = result.canonical_date
                        citation_obj.metadata["possible_match_url"] = result.canonical_url
                        logger.error(
                            f"   🔶 AFTER (object): verified=False, possible_match=True, canonical_name=None (stored in metadata)"
                        )
                    elif isinstance(citation_obj, dict):
                        citation_obj["verified"] = False
                        citation_obj["possible_match"] = True
                        # CRITICAL: Don't set canonical_name/canonical_date for unverified citations
                        citation_obj["canonical_name"] = None
                        citation_obj["canonical_date"] = None
                        citation_obj["canonical_url"] = None
                        citation_obj["verification_source"] = result.source
                        citation_obj["verification_error"] = result.error
                        # Store potential match in metadata for reference
                        if "metadata" not in citation_obj or citation_obj["metadata"] is None:
                            citation_obj["metadata"] = {}
                        citation_obj["metadata"]["possible_match_name"] = result.canonical_name
                        citation_obj["metadata"]["possible_match_date"] = result.canonical_date
                        citation_obj["metadata"]["possible_match_url"] = result.canonical_url
                        logger.error(
                            f"   🔶 AFTER (dict): verified=False, possible_match=True, canonical_name=None (stored in metadata)"
                        )
                else:
                    # UNVERIFIED: Mark as unverified, store error
                    # CRITICAL: Unverified citations CANNOT have canonical data
                    logger.error(f"[APPLY-VERIFICATION] Citation: {citation_text} - UNVERIFIED")
                    logger.error(f"   [WARNING] Error: {result.error}")

                    if hasattr(citation_obj, "__dict__"):
                        citation_obj.verified = False
                        citation_obj.possible_match = False
                        citation_obj.verification_error = result.error
                        # CRITICAL: Clear canonical data for unverified citations
                        citation_obj.canonical_name = None
                        citation_obj.canonical_date = None
                        citation_obj.canonical_url = None
                        logger.error(
                            f"   AFTER (object): verified=False, possible_match=False, canonical_name=None, canonical_date=None"
                        )
                    elif isinstance(citation_obj, dict):
                        citation_obj["verified"] = False
                        citation_obj["possible_match"] = False
                        citation_obj["verification_error"] = result.error
                        # CRITICAL: Clear canonical data for unverified citations
                        citation_obj["canonical_name"] = None
                        citation_obj["canonical_date"] = None
                        citation_obj["canonical_url"] = None
                        logger.error(f"   AFTER (dict): verified=False, canonical_name=None, canonical_date=None")

        except ImportError:
            logger.warning("MASTER_CLUSTER: Verification master not available, skipping verification")
        except Exception as e:
            logger.error(f"MASTER_CLUSTER: Error in verification: {e}")

    def _merge_and_deduplicate_clusters(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate clusters."""
        if not clusters:
            return []

        # Simple deduplication - remove clusters with identical citations
        seen_citations = set()
        unique_clusters = []

        for cluster in clusters:
            citations = cluster.get("citations", [])
            citation_texts = []

            for citation in citations:
                citation_text = getattr(citation, "citation", str(citation))
                citation_texts.append(citation_text)

            # Create a signature for this cluster
            cluster_signature = tuple(sorted(citation_texts))

            if cluster_signature not in seen_citations:
                seen_citations.add(cluster_signature)
                unique_clusters.append(cluster)

        return unique_clusters

    def _validate_clusters(self, clusters: List[Dict[str, Any]], original_text: str) -> List[Dict[str, Any]]:
        """
        Validate cluster integrity to catch incorrectly grouped citations.

        This method checks:
        1. All citations in a cluster are within proximity threshold
        2. Citations have consistent case names
        3. No citations from vastly different document locations are grouped

        If a cluster fails validation, it will be split or flagged with warnings.
        """
        validated_clusters = []

        for cluster in clusters:
            citations = cluster.get("citations", [])

            if len(citations) <= 1:
                # Single citation clusters are always valid
                validated_clusters.append(cluster)
                continue

            # CRITICAL FIX: Check proximity FIRST - if citations are close together, TRUST the clustering!
            # Parallel citations are typically within 50-200 characters of each other
            positions = []
            for citation in citations:
                pos = None
                if hasattr(citation, "start_index"):
                    pos = citation.start_index
                elif isinstance(citation, dict):
                    pos = citation.get("start_index")
                if pos is not None:
                    positions.append(pos)

            # If citations are in close proximity (<= 50 chars), they're LIKELY parallel
            # BUT still check canonical names to prevent grouping different cases!
            if len(positions) >= 2:
                sorted_positions = sorted(positions)
                max_distance = sorted_positions[-1] - sorted_positions[0]
                if max_distance <= 50:  # USER FIX: Reduced from 200 to 50 chars for stricter proximity
                    # Proximity suggests parallel, but verify EXTRACTED case names match
                    # CRITICAL FIX: Use extracted names, not canonical names, for clustering decisions
                    # Canonical names can be contaminated and shouldn't be used for clustering
                    extracted_names = set()
                    for citation in citations:
                        if hasattr(citation, "extracted_case_name"):
                            extracted = citation.extracted_case_name
                        elif isinstance(citation, dict):
                            extracted = citation.get("extracted_case_name")
                        else:
                            extracted = None

                        if extracted and extracted != "N/A" and extracted.strip():
                            # Normalize the extracted name for comparison
                            normalized = self._normalize_case_name_for_clustering(extracted)
                            if normalized:
                                extracted_names.add(normalized)

                    # If we have multiple different extracted names, these are DIFFERENT cases!
                    if len(extracted_names) > 1:
                        logger.error(
                            f"[REJECTED] [PROXIMITY-OVERRIDE-FAILED] Citations within {max_distance} chars BUT have different extracted names: {extracted_names}. "
                            f"These are DIFFERENT cases incorrectly grouped by proximity. Applying P5_FIX validation..."
                        )
                        # Continue to P5_FIX validation below
                    else:
                        logger.error(
                            f"[SUCCESS] [PROXIMITY-OVERRIDE] Cluster with {len(citations)} citations within {max_distance} chars and matching extracted names - definitely parallel"
                        )
                        validated_clusters.append(cluster)
                        continue
                else:
                    logger.error(
                        f"[WARNING] [PROXIMITY-CHECK] Cluster with {len(citations)} citations spread over {max_distance} chars - APPLYING P5_FIX validation"
                    )

            # P5 FIX ENHANCED: Comprehensive false clustering detection
            # Only run this for non-proximate citations
            # Collect citation metadata for validation
            citation_metadata = []
            reporter_volumes = {}  # {reporter: set of volumes}

            for citation in citations:
                if hasattr(citation, "citation"):
                    cit_text = citation.citation
                elif isinstance(citation, dict):
                    cit_text = citation.get("citation", "") or citation.get("text", "")
                else:
                    cit_text = str(citation)

                parsed = self._parse_citation_components(cit_text)

                # Extract year from citation object
                year = None
                if hasattr(citation, "extracted_date"):
                    year = citation.extracted_date
                elif isinstance(citation, dict):
                    year = citation.get("extracted_date")

                if parsed:
                    reporter = parsed.get("reporter")
                    volume = parsed.get("volume")

                    citation_metadata.append(
                        {"citation": cit_text, "reporter": reporter, "volume": volume, "year": year}
                    )

                    if reporter and volume:
                        if reporter not in reporter_volumes:
                            reporter_volumes[reporter] = set()
                        reporter_volumes[reporter].add(volume)

            # P5 VALIDATION 1: Check for incompatible reporter types
            # Federal vs State reporters should NEVER cluster
            # Supreme Court vs Circuit/District should NEVER cluster (different courts)
            supreme_court_reporters = set(["U.S.", "S.Ct.", "L.Ed.", "L.Ed.2d"])
            circuit_reporters = set(["F.2d", "F.3d", "F.4th"])
            district_reporters = set(["F.Supp.", "F.Supp.2d", "F.Supp.3d"])
            state_reporters = set(
                [
                    "P.2d",
                    "P.3d",
                    "A.2d",
                    "A.3d",
                    "N.E.2d",
                    "N.E.3d",
                    "N.W.2d",
                    "S.E.2d",
                    "S.W.2d",
                    "S.W.3d",
                    "So.2d",
                    "So.3d",
                ]
            )

            has_supreme = any(
                meta["reporter"] in supreme_court_reporters for meta in citation_metadata if meta.get("reporter")
            )
            has_circuit = any(
                meta["reporter"] in circuit_reporters for meta in citation_metadata if meta.get("reporter")
            )
            has_district = any(
                meta["reporter"] in district_reporters for meta in citation_metadata if meta.get("reporter")
            )
            has_state = any(meta["reporter"] in state_reporters for meta in citation_metadata if meta.get("reporter"))

            # Federal vs State = NEVER parallel
            if (has_supreme or has_circuit or has_district) and has_state:
                logger.error(
                    f"[REJECTED] P5_FIX: FALSE CLUSTERING DETECTED in cluster '{cluster.get('case_name', 'N/A')}' - "
                    f"Mixed federal and state reporters (cannot be parallel citations). "
                    f"Splitting cluster..."
                )
                split_clusters = self._split_cluster_by_reporter_volume(cluster, citations)
                validated_clusters.extend(split_clusters)
                continue

            # Supreme Court vs Circuit/District = NEVER parallel (different courts)
            if has_supreme and (has_circuit or has_district):
                logger.error(
                    f"[REJECTED] P5_FIX: FALSE CLUSTERING DETECTED in cluster '{cluster.get('case_name', 'N/A')}' - "
                    f"Mixed Supreme Court and Circuit/District reporters (different courts, cannot be parallel). "
                    f"Splitting cluster..."
                )
                # USER FIX 2024-10-21: Split by COURT TYPE, not by individual reporters
                # This keeps Supreme Court parallel citations (U.S., S. Ct., L. Ed.) together
                logger.error(f"[P5-DEBUG] About to call _split_cluster_by_court_type with {len(citations)} citations")
                try:
                    split_clusters = self._split_cluster_by_court_type(cluster, citations)
                    logger.error(f"[P5-DEBUG] _split_cluster_by_court_type returned {len(split_clusters)} clusters")
                    validated_clusters.extend(split_clusters)
                except Exception as e:
                    logger.error(f"[P5-ERROR] _split_cluster_by_court_type failed: {e}")
                    logger.exception(e)
                    validated_clusters.append(cluster)  # Keep original if split fails
                continue

            # P5 VALIDATION 2: Check for large year differences
            # Citations from different years (e.g., 1999 vs 2019) are unlikely to be parallel
            years = [meta["year"] for meta in citation_metadata if meta.get("year")]
            if len(years) >= 2:
                try:
                    year_ints = [int(str(y)[:4]) for y in years if y]  # Extract first 4 digits
                    if year_ints:
                        year_range = max(year_ints) - min(year_ints)
                        if year_range > 2:  # Allow 2 years difference for delayed publication
                            logger.error(
                                f"[REJECTED] P5_FIX: FALSE CLUSTERING DETECTED in cluster '{cluster.get('case_name', 'N/A')}' - "
                                f"Large year difference: {min(year_ints)} to {max(year_ints)} ({year_range} years). "
                                f"Splitting cluster..."
                            )
                            split_clusters = self._split_cluster_by_reporter_volume(cluster, citations)
                            validated_clusters.extend(split_clusters)
                            continue
                except (ValueError, TypeError) as e:
                    logger.debug(f"Year comparison error: {e}")

            # P5 VALIDATION 3: Check if any reporter has multiple different volumes
            false_clustering_detected = False
            for reporter, volumes in reporter_volumes.items():
                if len(volumes) > 1:
                    logger.error(
                        f"[REJECTED] P5_FIX: FALSE CLUSTERING DETECTED in cluster '{cluster.get('case_name', 'N/A')}' - "
                        f"same reporter '{reporter}' but different volumes: {sorted(volumes)}. "
                        f"Splitting cluster..."
                    )
                    false_clustering_detected = True
                    break

            if false_clustering_detected:
                # Split the cluster by reporter+volume
                split_clusters = self._split_cluster_by_reporter_volume(cluster, citations)
                validated_clusters.extend(split_clusters)
                continue

            # Get positions of all citations
            positions = []
            for citation in citations:
                if hasattr(citation, "start_index"):
                    pos = citation.start_index
                elif isinstance(citation, dict):
                    pos = citation.get("start_index", 0)
                else:
                    pos = 0
                positions.append(pos)

            # Check if all citations are within reasonable proximity
            if positions:
                min_pos = min(positions)
                max_pos = max(positions)
                span = max_pos - min_pos

                # If span exceeds 10x the proximity threshold, this is suspicious
                max_allowed_span = self.proximity_threshold * 10

                if span > max_allowed_span:
                    # CRITICAL FIX: Check if these are parallel citations (same case, different reporters)
                    # Parallel citations should NEVER be split even if far apart in document
                    case_names = []
                    for citation in citations:
                        case_name = getattr(citation, "extracted_case_name", None)
                        if case_name and case_name not in ("N/A", "Unknown", None):
                            case_names.append(case_name.lower().strip())

                    # If all citations have the same case name, they're parallel citations - DON'T split
                    unique_case_names = set(case_names) if case_names else set()
                    if len(unique_case_names) == 1 and len(citations) <= 5:  # Parallel citations typically 2-4 cites
                        logger.info(
                            f"[SUCCESS] CLUSTER_VALIDATION: Keeping parallel citations together despite span={span}. "
                            f"All {len(citations)} citations reference: {list(unique_case_names)[0]}"
                        )
                        validated_clusters.append(cluster)
                        continue

                    # Not parallel citations - proceed with split
                    logger.warning(
                        f"[WARNING] CLUSTER_VALIDATION: Suspicious cluster with span={span} chars "
                        f"(threshold={max_allowed_span}). This may indicate incorrect clustering. "
                        f"Cluster has {len(citations)} citations spanning {span} characters."
                    )

                    # Log the citations for debugging
                    for i, citation in enumerate(citations):
                        citation_text = getattr(citation, "citation", str(citation))[:60]
                        pos = positions[i]
                        logger.warning(f"  Citation {i+1}: {citation_text} @ position {pos}")

                    # Split the cluster by proximity
                    # Group citations that are actually close together
                    split_clusters = self._split_cluster_by_proximity(cluster, citations, positions)
                    validated_clusters.extend(split_clusters)
                    continue

            # Cluster passes validation
            validated_clusters.append(cluster)

        return validated_clusters

    def _split_cluster_by_proximity(
        self, original_cluster: Dict[str, Any], citations: List[Any], positions: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Split a cluster into multiple clusters based on citation proximity.

        Citations that are far apart should not be in the same cluster.
        """
        # Sort citations by position
        sorted_pairs = sorted(zip(positions, citations), key=lambda x: x[0])

        # Group citations by proximity
        groups = []
        current_group = [sorted_pairs[0]]

        for i in range(1, len(sorted_pairs)):
            current_pos, current_citation = sorted_pairs[i]
            last_pos, _ = current_group[-1]

            distance = current_pos - last_pos

            # Use the standard proximity threshold
            if distance <= self.proximity_threshold:
                current_group.append(sorted_pairs[i])
            else:
                # Start a new group
                groups.append(current_group)
                current_group = [sorted_pairs[i]]

        # Don't forget the last group
        if current_group:
            groups.append(current_group)

        # Create new clusters from groups
        new_clusters = []
        for group_idx, group in enumerate(groups):
            group_citations = [citation for _, citation in group]

            # Create a new cluster dict based on the original
            new_cluster = {
                "cluster_id": f"{original_cluster.get('cluster_id', 'unknown')}_split{group_idx+1}",
                "citations": group_citations,
                "size": len(group_citations),
                "case_name": original_cluster.get("case_name", "N/A"),
                "case_year": original_cluster.get("case_year", "N/A"),
                "confidence": original_cluster.get("confidence", 0.0) * 0.8,  # Lower confidence for split clusters
                "verification_status": original_cluster.get("verification_status", "not_verified"),
                "metadata": {
                    **original_cluster.get("metadata", {}),
                    "split_from": original_cluster.get("cluster_id", "unknown"),
                    "split_reason": "proximity_validation",
                },
            }

            logger.info(
                f"✂️ CLUSTER_VALIDATION: Split cluster {original_cluster.get('cluster_id')} "
                f"into subcluster {new_cluster['cluster_id']} with {len(group_citations)} citations"
            )

            new_clusters.append(new_cluster)

        return new_clusters

    def _split_cluster_by_reporter_volume(
        self, original_cluster: Dict[str, Any], citations: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        P5 FIX: Split a cluster that has same reporter + different volumes (false clustering).

        Each unique reporter+volume combination becomes its own cluster.
        Example: ["506 U.S. 224", "546 U.S. 345"] would be split into 2 clusters.
        """
        # Group citations by reporter+volume
        groups = {}  # {(reporter, volume): [citations]}

        for citation in citations:
            if hasattr(citation, "citation"):
                cit_text = citation.citation
            elif isinstance(citation, dict):
                cit_text = citation.get("citation", "") or citation.get("text", "")
            else:
                cit_text = str(citation)

            parsed = self._parse_citation_components(cit_text)
            if parsed:
                reporter = parsed.get("reporter")
                volume = parsed.get("volume")
                key = (reporter, volume)
            else:
                # Unparseable citation - put in its own group
                key = ("unknown", cit_text)

            if key not in groups:
                groups[key] = []
            groups[key].append(citation)

        # Create new clusters from groups
        new_clusters = []
        for group_idx, ((reporter, volume), group_citations) in enumerate(groups.items()):
            new_cluster = {
                "cluster_id": f"{original_cluster.get('cluster_id', 'unknown')}_vol{group_idx+1}",
                "citations": group_citations,
                "size": len(group_citations),
                "case_name": original_cluster.get("case_name", "N/A"),
                "case_year": original_cluster.get("case_year", "N/A"),
                "confidence": original_cluster.get("confidence", 0.0) * 0.7,  # Lower confidence for split clusters
                "verification_status": original_cluster.get("verification_status", "not_verified"),
                "metadata": {
                    **original_cluster.get("metadata", {}),
                    "split_from": original_cluster.get("cluster_id", "unknown"),
                    "split_reason": "false_clustering_same_reporter_different_volumes",
                    "reporter": reporter,
                    "volume": volume,
                },
            }

            logger.info(
                f"✂️ P5_FIX: Split false cluster '{original_cluster.get('case_name', 'N/A')}' - "
                f"created subcluster for {reporter} vol.{volume} with {len(group_citations)} citation(s)"
            )

            new_clusters.append(new_cluster)

        return new_clusters

    def _split_cluster_by_court_type(
        self, original_cluster: Dict[str, Any], citations: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        USER FIX 2024-10-21: Split cluster by COURT TYPE, keeping parallel citations together.

        This keeps Supreme Court parallel citations (U.S., S. Ct., L. Ed.) in ONE cluster,
        while separating Circuit/District courts into separate clusters.

        Court type groupings:
        - Supreme Court: U.S., S.Ct., S. Ct., L.Ed., L. Ed.
        - Circuit/District: F.2d, F.3d, F.Supp., F. Supp.
        - State: Wn.2d, P.3d, etc.
        """
        # Normalized reporters (spaces removed)
        supreme_court_reporters = {"U.S.", "S.Ct.", "L.Ed.", "L.Ed.2d"}
        circuit_reporters = {"F.2d", "F.3d", "F.Supp.", "F.Supp.2d", "F.Supp.3d"}

        # Group citations by court type
        supreme_citations = []
        circuit_citations = []
        other_citations = []

        logger.error(f"[COURT-TYPE-DEBUG] Starting classification of {len(citations)} citations")

        for citation in citations:
            if hasattr(citation, "citation"):
                cit_text = citation.citation
            elif isinstance(citation, dict):
                cit_text = citation.get("citation", "") or citation.get("text", "")
            else:
                cit_text = str(citation)

            parsed = self._parse_citation_components(cit_text)
            if parsed:
                reporter = parsed.get("reporter", "")
                # Normalize reporter for comparison - REMOVE spaces (don't add dots, they're already there!)
                reporter_normalized = reporter.replace(" ", "")

                logger.error(
                    f"[COURT-TYPE-DEBUG] {cit_text}: reporter='{reporter}', normalized='{reporter_normalized}'"
                )

                if reporter_normalized in supreme_court_reporters or any(
                    sc in reporter for sc in ["U.S.", "S.Ct", "L.Ed"]
                ):
                    supreme_citations.append(citation)
                    logger.error(f"   → Classified as SUPREME COURT")
                elif reporter_normalized in circuit_reporters or any(
                    cr in reporter for cr in ["F.2d", "F.3d", "F.Supp", "F. Supp"]
                ):
                    circuit_citations.append(citation)
                    logger.error(f"   → Classified as CIRCUIT/DISTRICT")
                else:
                    other_citations.append(citation)
                    logger.error(f"   → Classified as OTHER")
            else:
                other_citations.append(citation)
                logger.error(f"[COURT-TYPE-DEBUG] {cit_text}: FAILED TO PARSE → OTHER")

        # Create clusters by court type
        new_clusters = []

        logger.error(
            f"[COURT-TYPE-DEBUG] Classification complete: Supreme={len(supreme_citations)}, Circuit={len(circuit_citations)}, Other={len(other_citations)}"
        )

        if supreme_citations:
            supreme_cluster = {
                "cluster_id": f"{original_cluster.get('cluster_id', 'unknown')}_supreme",
                "citations": supreme_citations,
                "size": len(supreme_citations),
                "case_name": original_cluster.get("case_name", "N/A"),
                "case_year": original_cluster.get("case_year", "N/A"),
                "confidence": original_cluster.get("confidence", 0.0),
                "verification_status": original_cluster.get("verification_status", "not_verified"),
                "metadata": {
                    **original_cluster.get("metadata", {}),
                    "split_from": original_cluster.get("cluster_id", "unknown"),
                    "split_reason": "separated_by_court_type",
                    "court_type": "Supreme Court",
                },
            }
            new_clusters.append(supreme_cluster)
            logger.info(
                f"✂️ P5_FIX: Created Supreme Court cluster with {len(supreme_citations)} citation(s) - keeping parallels together"
            )

        if circuit_citations:
            circuit_cluster = {
                "cluster_id": f"{original_cluster.get('cluster_id', 'unknown')}_circuit",
                "citations": circuit_citations,
                "size": len(circuit_citations),
                "case_name": original_cluster.get("case_name", "N/A"),
                "case_year": original_cluster.get("case_year", "N/A"),
                "confidence": original_cluster.get("confidence", 0.0),
                "verification_status": original_cluster.get("verification_status", "not_verified"),
                "metadata": {
                    **original_cluster.get("metadata", {}),
                    "split_from": original_cluster.get("cluster_id", "unknown"),
                    "split_reason": "separated_by_court_type",
                    "court_type": "Circuit/District",
                },
            }
            new_clusters.append(circuit_cluster)
            logger.info(f"✂️ P5_FIX: Created Circuit/District cluster with {len(circuit_citations)} citation(s)")

        if other_citations:
            for citation in other_citations:
                single_cluster = {
                    "cluster_id": f"{original_cluster.get('cluster_id', 'unknown')}_other",
                    "citations": [citation],
                    "size": 1,
                    "case_name": original_cluster.get("case_name", "N/A"),
                    "case_year": original_cluster.get("case_year", "N/A"),
                    "confidence": original_cluster.get("confidence", 0.0) * 0.7,
                    "verification_status": original_cluster.get("verification_status", "not_verified"),
                    "metadata": {
                        **original_cluster.get("metadata", {}),
                        "split_from": original_cluster.get("cluster_id", "unknown"),
                        "split_reason": "separated_by_court_type",
                        "court_type": "Other",
                    },
                }
                new_clusters.append(single_cluster)

        return new_clusters

    def _format_clusters_for_output(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format clusters for final output and update citation objects with cluster IDs."""
        formatted_clusters = []

        for cluster in clusters:
            cluster_id = cluster.get("cluster_id", "unknown")
            citations = cluster.get("citations", [])
            # FINAL SAFEGUARD: Deduplicate citations within a cluster by citation text
            if citations:
                seen_texts = set()
                unique_citations = []
                for c in citations:
                    if hasattr(c, "citation"):
                        txt = getattr(c, "citation", "")
                    elif isinstance(c, dict):
                        txt = c.get("citation", "") or c.get("text", "")
                    else:
                        txt = str(c)
                    key = (txt or "").strip()
                    if key and key not in seen_texts:
                        seen_texts.add(key)
                        unique_citations.append(c)
                citations = unique_citations

            # CRITICAL FIX: Use _select_best_EXTRACTED_name() for cluster-level extracted name
            # This prioritizes extracted_case_name from document over canonical_name from APIs
            best_name = cluster.get("case_name", "N/A")
            if best_name in (None, "", "N/A", "Unknown", "Unknown Case"):
                inferred_name = self._select_best_extracted_name(citations)  # Changed from _select_best_case_name
                if inferred_name:
                    best_name = inferred_name
                    logger.info(f"[CLUSTER-FORMAT] Inferred cluster name from extracted data: '{best_name}'")
                else:
                    logger.warning(
                        f"[CLUSTER-FORMAT] Could not infer cluster name for cluster {cluster.get('cluster_id')} with {len(citations)} citations"
                    )

            best_year = cluster.get("case_year", "N/A")
            if best_year in (None, "", "N/A", "Unknown"):
                inferred_year = self._select_best_case_year(citations)
                if inferred_year:
                    best_year = inferred_year

            # CRITICAL FIX: Propagate canonical data to parallel citations
            # Find the first verified citation with canonical data
            best_verified = None
            for cit in citations:
                is_verified = getattr(cit, "verified", False)
                has_canonical = getattr(cit, "canonical_name", None) is not None
                logger.info(
                    f"[CLUSTER_FORMAT] Checking citation {getattr(cit, 'citation', str(cit))[:50]} - verified={is_verified}, has_canonical={has_canonical}"
                )
                if is_verified and has_canonical:
                    best_verified = cit
                    logger.info(
                        f"[SUCCESS] CLUSTER_FORMAT: Found best_verified citation: {best_verified.citation} with canonical_name={best_verified.canonical_name}"
                    )
                    break

            # Propagate canonical data to unverified parallel citations
            # IMPORTANT: Only propagate if citations are verified parallel pairs (true_by_parallel=True)
            # CRITICAL: Unverified citations without true_by_parallel CANNOT have canonical data
            if best_verified and len(citations) > 1:
                for cit in citations:
                    is_verified = getattr(cit, "verified", False)
                    if not is_verified:
                        # CRITICAL FIX: Only propagate canonical data if extracted names match
                        # This prevents wrong canonical data from being propagated to different cases
                        extracted_name_cit = getattr(cit, "extracted_case_name", None) or (
                            cit.get("extracted_case_name") if isinstance(cit, dict) else None
                        )
                        extracted_name_verified = getattr(best_verified, "extracted_case_name", None) or (
                            best_verified.get("extracted_case_name") if isinstance(best_verified, dict) else None
                        )

                        # Check if extracted names match (prevent wrong canonical data propagation)
                        # FIX DEC 2025: Allow propagation if either name is "N/A" AND citations have compatible reporters
                        # This handles cases where extraction failed but citations are clearly parallel (e.g., Wn.2d + P.3d)
                        names_match = False

                        # Get citation texts to check reporter compatibility
                        cit_text = getattr(cit, "citation", "") or (
                            cit.get("citation", "") if isinstance(cit, dict) else ""
                        )
                        verified_text = getattr(best_verified, "citation", "") or (
                            best_verified.get("citation", "") if isinstance(best_verified, dict) else ""
                        )

                        # Check if reporters are compatible parallel pairs
                        reporters_compatible = (
                            self._match_parallel_patterns(cit_text, verified_text)
                            if cit_text and verified_text
                            else False
                        )

                        if (
                            extracted_name_cit
                            and extracted_name_verified
                            and extracted_name_cit != "N/A"
                            and extracted_name_verified != "N/A"
                        ):
                            # Both names exist - check if they match
                            import re

                            def normalize_for_comparison(name):
                                if not name:
                                    return ""
                                # Remove punctuation, lowercase, normalize whitespace
                                normalized = re.sub(r"[^\w\s]", "", name.lower())
                                normalized = re.sub(r"\s+", " ", normalized).strip()
                                return normalized

                            norm_cit = normalize_for_comparison(extracted_name_cit)
                            norm_verified = normalize_for_comparison(extracted_name_verified)
                            # Match if exact match or one is substring of the other (handles abbreviations)
                            names_match = (
                                norm_cit == norm_verified or norm_cit in norm_verified or norm_verified in norm_cit
                            )
                        elif reporters_compatible:
                            # FIX DEC 2025: If either name is N/A but reporters are compatible parallel pairs,
                            # allow propagation (e.g., 160 Wn.2d 32 + 156 P.3d 185 for Ford Motor Co.)
                            names_match = True
                            logger.info(
                                f"[PARALLEL-FIX] Allowing propagation despite N/A name - reporters compatible: {cit_text} <-> {verified_text}"
                            )

                        if names_match:
                            # Mark as true_by_parallel - this allows canonical data propagation
                            # true_by_parallel means the citation is verified by association with a verified parallel citation
                            if hasattr(cit, "__dict__"):
                                cit.true_by_parallel = True
                                # Only set canonical data if we have a verified parallel citation
                                cit.canonical_name = getattr(best_verified, "canonical_name", None)
                                cit.canonical_date = getattr(best_verified, "canonical_date", None)
                                cit.canonical_url = getattr(best_verified, "canonical_url", None)
                                # Don't change verified status - keep it False, but true_by_parallel=True allows canonical data
                                logger.info(
                                    f"[SUCCESS] CLUSTER_FORMAT: Propagated canonical data from {best_verified.citation} to {getattr(cit, 'citation', str(cit))[:50]} (true_by_parallel=True, names match)"
                                )
                            elif isinstance(cit, dict):
                                cit["true_by_parallel"] = True
                                # Only set canonical data if we have a verified parallel citation
                                cit["canonical_name"] = getattr(best_verified, "canonical_name", None)
                                cit["canonical_date"] = getattr(best_verified, "canonical_date", None)
                                cit["canonical_url"] = getattr(best_verified, "canonical_url", None)
                                logger.info(
                                    f"[SUCCESS] CLUSTER_FORMAT: Propagated canonical data from {best_verified.citation} to {cit.get('citation', str(cit))[:50]} (true_by_parallel=True, names match)"
                                )
                        else:
                            # Citations are NOT parallel pairs OR names don't match - clear any canonical data
                            if hasattr(cit, "__dict__"):
                                cit.canonical_name = None
                                cit.canonical_date = None
                                cit.canonical_url = None
                                cit.true_by_parallel = False
                            elif isinstance(cit, dict):
                                cit["canonical_name"] = None
                                cit["canonical_date"] = None
                                cit["canonical_url"] = None
                                cit["true_by_parallel"] = False
                            logger.warning(
                                f"[WARNING] CLUSTER_FORMAT: Cleared canonical data (extracted names don't match): '{extracted_name_cit}' vs '{extracted_name_verified}' for citations {getattr(cit, 'citation', str(cit))[:50]} vs {best_verified.citation}"
                            )

            # CRITICAL FIX: Extract cluster-level canonical data ONLY from verified citations
            cluster_canonical_name = None
            cluster_canonical_date = None
            cluster_verification_source = None

            # Find first verified citation with canonical data
            # CRITICAL: Only set cluster-level canonical data if we have a verified citation
            if best_verified:
                is_best_verified = getattr(best_verified, "verified", False)
                if is_best_verified:
                    cluster_canonical_name = getattr(best_verified, "canonical_name", None)
                    cluster_canonical_date = getattr(best_verified, "canonical_date", None)
                    cluster_verification_source = getattr(
                        best_verified, "verification_source", getattr(best_verified, "source", None)
                    )
                    logger.info(
                        f"[SUMMARY] CLUSTER_FORMAT: Setting cluster canonical data - name={cluster_canonical_name}, date={cluster_canonical_date}, source={cluster_verification_source}"
                    )
                else:
                    logger.warning(
                        f"[WARNING] CLUSTER_FORMAT: best_verified citation is not actually verified, clearing cluster canonical data"
                    )
                    cluster_canonical_name = None
                    cluster_canonical_date = None
            else:
                logger.warning(
                    f"[WARNING] CLUSTER_FORMAT: No best_verified found for cluster {cluster_id} with {len(citations)} citations - no cluster canonical data"
                )

            # USER FIX: Serialize citation objects to dicts so Vue.js can access extracted_case_name
            # This matches the fix in unified_citation_clustering.py for async pathway
            serialized_citations = []
            for cit in citations:
                if isinstance(cit, dict):
                    # CRITICAL FIX: Only include canonical data if citation is verified OR true_by_parallel=True
                    is_verified = cit.get("verified", False)
                    has_true_by_parallel = cit.get("true_by_parallel", False)
                    can_have_canonical = is_verified or has_true_by_parallel

                    # Clear canonical data if unverified and not true_by_parallel
                    if not can_have_canonical:
                        cit["canonical_name"] = None
                        cit["canonical_date"] = None
                        cit["canonical_url"] = None

                    # Ensure mismatch flags exist in dict citations as well
                    cit.setdefault("name_mismatch", False)
                    cit.setdefault("date_mismatch", False)
                    cit.setdefault("mismatch_confidence", 0.0)
                    cit.setdefault("possible_match", False)
                    cit.setdefault("true_by_parallel", False)
                    serialized_citations.append(cit)
                else:
                    # Convert object to dict
                    # Debug: Check what source fields are available
                    verification_source = getattr(cit, "verification_source", None)
                    source = getattr(cit, "source", None)
                    logger.error(
                        f"[DEBUG] [SERIALIZE-DEBUG] Citation: {getattr(cit, 'citation', 'Unknown')}, verification_source: {verification_source}, source: {source}"
                    )

                    # CRITICAL FIX: Only include canonical data if citation is verified OR true_by_parallel=True
                    is_verified = getattr(cit, "verified", False)
                    has_true_by_parallel = getattr(cit, "true_by_parallel", False)
                    can_have_canonical = is_verified or has_true_by_parallel

                    cit_dict = {
                        "citation": getattr(cit, "citation", ""),
                        "extracted_case_name": getattr(cit, "extracted_case_name", None),
                        "extracted_date": getattr(cit, "extracted_date", None),
                        "start_index": getattr(cit, "start_index", None),
                        "end_index": getattr(cit, "end_index", None),
                        "method": getattr(cit, "method", "unified_processor"),
                        "confidence": getattr(cit, "confidence", 0.9),
                        "metadata": getattr(cit, "metadata", {}),
                        "verified": is_verified,
                        "canonical_name": getattr(cit, "canonical_name", None) if can_have_canonical else None,
                        "canonical_date": getattr(cit, "canonical_date", None) if can_have_canonical else None,
                        "canonical_url": getattr(cit, "canonical_url", None) if can_have_canonical else None,
                        "source": (
                            verification_source if verification_source else source
                        ),  # Prioritize verification_source but use source if not available
                        "error": getattr(cit, "error", None),
                        "true_by_parallel": has_true_by_parallel,
                        # Backend-driven mismatch flags
                        "name_mismatch": getattr(cit, "name_mismatch", False),
                        "date_mismatch": getattr(cit, "date_mismatch", False),
                        "mismatch_confidence": getattr(cit, "mismatch_confidence", 0.0),
                        "possible_match": getattr(cit, "possible_match", False),
                    }
                    serialized_citations.append(cit_dict)

            formatted_cluster = {
                "cluster_id": cluster_id,
                "cluster_case_name": best_name or "N/A",
                "cluster_year": best_year or "N/A",
                "cluster_size": cluster.get("size", 0),
                "citations": serialized_citations,  # USER FIX: Use serialized dicts instead of objects
                "confidence": cluster.get("confidence", 0.0),
                "verification_status": "verified" if best_verified else "not_verified",
                "verification_source": cluster_verification_source,
                # CRITICAL FIX: Add cluster-level extracted fields (from document)
                "extracted_case_name": best_name or "N/A",  # Extracted from document
                "extracted_date": best_year or "N/A",  # Extracted from document
                # Canonical fields (from API verification)
                "canonical_name": cluster_canonical_name,
                "canonical_date": cluster_canonical_date,
                "metadata": cluster.get("metadata", {}),
                "cluster_members": [],
                # Backend-driven cluster-level mismatch summary
                "has_name_mismatch": any(c.get("name_mismatch") for c in serialized_citations),
                "has_date_mismatch": any(c.get("date_mismatch") for c in serialized_citations),
                "mismatch_indices": [
                    idx
                    for idx, c in enumerate(serialized_citations)
                    if c.get("name_mismatch") or c.get("date_mismatch")
                ],
            }

            for citation in citations:
                citation_text = getattr(citation, "citation", str(citation))
                formatted_cluster["cluster_members"].append(citation_text)

                if hasattr(citation, "cluster_id"):
                    citation.cluster_id = cluster_id
                if hasattr(citation, "is_cluster"):
                    citation.is_cluster = len(citations) > 1
                if hasattr(citation, "cluster_case_name"):
                    citation.cluster_case_name = best_name or "N/A"
                if hasattr(citation, "cluster_year"):
                    citation.cluster_year = best_year or "N/A"

                if isinstance(citation, dict):
                    citation["cluster_case_name"] = best_name or "N/A"
                    citation["cluster_year"] = best_year or "N/A"

            formatted_clusters.append(formatted_cluster)

        return formatted_clusters

    def _normalize_case_name(self, case_name: str) -> str:
        """Normalize case name for clustering (uses comprehensive normalization)."""
        if not case_name:
            return "unknown"

        # FIX: Use the comprehensive normalization that includes abbreviation expansion
        # This ensures "Rice v. Dow Chem. Co." matches "Rice v. Dow Chemical Co."
        return self._normalize_case_name_for_clustering(case_name) or "unknown"

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        if not name1 or not name2:
            return 0.0

        # Normalize names
        norm1 = self._normalize_case_name(name1)
        norm2 = self._normalize_case_name(name2)

        # Simple word-based similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _validate_canonical_consistency(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        FIX #22/#47/#48: Validate cluster consistency using EXTRACTED data, not canonical data.

        FIX #48: CRITICAL CHANGE - Use extracted_case_name and extracted_date for validation!
        Different websites can return different canonical names for the same case.
        We should cluster based on what's in the USER'S DOCUMENT, not what the API says.

        Trust hierarchy:
        1. Proximity (close together = likely parallel)
        2. Extracted data (from user's document) ← PRIMARY
        3. Canonical data (from API) ← ONLY for display/verification

        Example:
        - Cluster: [148 Wn.2d 224, 59 P.3d 655]
        - Both extract "Fraternal Order" from document
        - API might return slightly different canonical names
        - → Keep together because extracted data matches!

        Only split when:
        - Extracted names are VERY different (not just abbreviations)
        - Extracted years differ by more than 2 years
        - AND citations are NOT in close proximity
        """
        validated_clusters = []

        for cluster in clusters:
            citations = cluster.get("citations", [])
            if len(citations) <= 1:
                # Single citation clusters don't need validation
                validated_clusters.append(cluster)
                continue

            # FIX #47: Check if citations are in close proximity (likely parallel)
            positions = []
            for citation in citations:
                pos = None
                if hasattr(citation, "start_index"):
                    pos = citation.start_index
                elif isinstance(citation, dict):
                    pos = citation.get("start_index")
                if pos is not None:
                    positions.append(pos)

            # DIAGNOSTIC: Check if positions were found
            if len(citations) > 1 and len(positions) == 0:
                logger.error(f"🚨 [PROXIMITY-BUG] Cluster has {len(citations)} citations but NO positions found!")
                logger.error(f"   First citation type: {type(citations[0])}")
                if hasattr(citations[0], "__dict__"):
                    logger.error(f"   First citation attrs: {list(vars(citations[0]).keys())[:10]}")
                elif isinstance(citations[0], dict):
                    logger.error(f"   First citation keys: {list(citations[0].keys())[:10]}")

            # If we have positions, check proximity
            is_close_proximity = False
            if len(positions) >= 2:
                sorted_positions = sorted(positions)
                max_distance = sorted_positions[-1] - sorted_positions[0]
                # FIX #47: If citations are within 200 chars, they're likely parallel
                is_close_proximity = max_distance <= 200
                logger.error(
                    f"[PROXIMITY-CHECK] {len(citations)} citations, distance={max_distance} chars, is_close={is_close_proximity}"
                )
            elif len(citations) > 1:
                logger.error(
                    f"[WARNING] [PROXIMITY-CHECK] {len(citations)} citations but only {len(positions)} positions - CANNOT determine proximity!"
                )

            # FIX #48: Group citations by EXTRACTED case name + year (from document)
            extracted_groups = {}
            no_extraction_citations = []

            for citation in citations:
                # FIX #48: Get EXTRACTED name and date (from document)
                extracted_name = None
                extracted_date = None

                if hasattr(citation, "extracted_case_name"):
                    extracted_name = citation.extracted_case_name
                    extracted_date = getattr(citation, "extracted_date", None)
                elif isinstance(citation, dict):
                    extracted_name = citation.get("extracted_case_name")
                    extracted_date = citation.get("extracted_date")

                # Skip citations without extraction data
                if not extracted_name or extracted_name == "N/A":
                    no_extraction_citations.append(citation)
                    continue

                # Normalize the extracted name
                normalized_name = self._normalize_case_name(extracted_name)

                # Extract year from extracted date
                year = None
                if extracted_date:
                    year_match = re.search(r"(19|20)\d{2}", str(extracted_date))
                    if year_match:
                        year = year_match.group(0)

                group_key = f"{normalized_name}_{year}" if year else normalized_name

                if group_key not in extracted_groups:
                    extracted_groups[group_key] = []
                extracted_groups[group_key].append(citation)

            # FIX #48: If all citations have the same extracted data, keep the cluster
            if len(extracted_groups) <= 1:
                logger.debug(
                    f"[SUCCESS] [FIX #48] Cluster validation: {len(extracted_groups)} extracted group(s) - keeping intact"
                )
                validated_clusters.append(cluster)
                continue

            # FIX #49: If citations are in CLOSE proximity, ALWAYS keep them together!
            # Proximity is the PRIMARY signal for parallel citations.
            # Extracted data is SECONDARY (can have extraction errors).
            if is_close_proximity:
                logger.info(
                    f"[SUCCESS] [FIX #49] PROXIMITY OVERRIDE - Keeping cluster intact despite {len(extracted_groups)} different extracted names"
                )
                logger.info(f"   Reason: Citations within 200 chars are likely parallel (extraction may have failed)")
                logger.info(f"   Extracted groups: {list(extracted_groups.keys())}")
                validated_clusters.append(cluster)
                continue

            # FIX #48: Check if we should trust similarity over minor name variations (for non-proximate citations)
            if len(extracted_groups) == 2:
                # Check if the extracted names are similar (slight variations vs completely different)
                group_keys = list(extracted_groups.keys())
                name1 = group_keys[0].split("_")[0] if "_" in group_keys[0] else group_keys[0]
                name2 = group_keys[1].split("_")[0] if "_" in group_keys[1] else group_keys[1]

                # Extract first word from each name (usually most important)
                words1 = name1.lower().split()
                words2 = name2.lower().split()

                first_word_match = words1 and words2 and words1[0] == words2[0]

                # Check for year mismatch (strong signal they're different cases)
                years = [key.split("_")[-1] for key in group_keys if "_" in key]
                year_mismatch = len(years) == 2 and years[0] != years[1] and abs(int(years[0]) - int(years[1])) > 2

                if first_word_match and not year_mismatch:
                    # Likely the same case with slight name variations - DON'T split
                    logger.info(
                        f"[SUCCESS] [FIX #48] Keeping cluster intact - close proximity + similar EXTRACTED names"
                    )
                    logger.info(f"   Extracted groups: {group_keys}")
                    validated_clusters.append(cluster)
                    continue
                elif year_mismatch:
                    logger.warning(
                        f"[WARNING]  [FIX #48] EXTRACTED year mismatch detected ({years}) - will split despite proximity"
                    )

            # SPLIT THE CLUSTER - citations have different EXTRACTED data!
            logger.warning(
                f"[ERROR] FIX #48: Splitting cluster - {len(extracted_groups)} different EXTRACTED cases detected (proximity={is_close_proximity})"
            )

            # DEBUG: Check if Hamaatsa citations are being split
            for group_key, group_citations in extracted_groups.items():
                hamaatsa_in_split = []
                for cit in group_citations:
                    cit_text = (
                        getattr(cit, "citation", str(cit))
                        if hasattr(cit, "citation")
                        else (cit.get("citation") if isinstance(cit, dict) else str(cit))
                    )
                    if "388 P.3d 977" in cit_text or "2017-NM-007" in cit_text:
                        hamaatsa_in_split.append(cit_text)
                if hamaatsa_in_split:
                    logger.error(f"💥 [HAMAATSA-SPLIT] SPLITTING Hamaatsa citations! Group key: {group_key}")
                    logger.error(f"💥 [HAMAATSA-SPLIT] Citations in this sub-cluster: {hamaatsa_in_split}")
                logger.warning(f"   Sub-cluster (extracted): {group_key} with {len(group_citations)} citations")

                # Create a new cluster for this extracted group
                new_cluster = {
                    "cluster_id": f"{cluster['cluster_id']}_split_{len(validated_clusters)}",
                    "cluster_key": cluster.get("cluster_key", ""),
                    "citations": group_citations,
                    "size": len(group_citations),
                    "case_name": cluster.get("case_name"),
                    "case_year": cluster.get("case_year"),
                    "confidence": self._calculate_cluster_confidence(group_citations),
                    "metadata": {
                        **cluster.get("metadata", {}),
                        "split_from": cluster["cluster_id"],
                        "split_reason": "extracted_data_mismatch",
                        "extracted_group_key": group_key,
                    },
                }
                validated_clusters.append(new_cluster)

            # Add citations without extraction as their own cluster if any exist
            if no_extraction_citations:
                logger.warning(f"   No-extraction sub-cluster: {len(no_extraction_citations)} citations")
                new_cluster = {
                    "cluster_id": f"{cluster['cluster_id']}_no_extraction",
                    "cluster_key": cluster.get("cluster_key", ""),
                    "citations": no_extraction_citations,
                    "size": len(no_extraction_citations),
                    "case_name": cluster.get("case_name"),
                    "case_year": cluster.get("case_year"),
                    "confidence": self._calculate_cluster_confidence(no_extraction_citations),
                    "metadata": {
                        **cluster.get("metadata", {}),
                        "split_from": cluster["cluster_id"],
                        "split_reason": "no_extraction_data",
                    },
                }
                validated_clusters.append(new_cluster)

        logger.info(
            f"[FIX #48] EXTRACTED data validation: {len(clusters)} input clusters → {len(validated_clusters)} output clusters"
        )
        return validated_clusters

    def _enrich_dates_from_canonical(self, clusters: List[Dict[str, Any]]) -> None:
        """
        DEPRECATED: This function violates the rule that extracted_date should NEVER
        be overwritten by verification API results.

        REMOVED: Enriching extracted_date from canonical_date causes cross-contamination.
        The extracted_date must only come from the user's document text, never from
        verification APIs. This prevents clustering logic from breaking because
        "2018" ≠ "2018-12-06" causes parallel citations to be split into separate clusters.

        This function is kept for backward compatibility but does nothing.
        """
        # CRITICAL FIX: Do NOT copy canonical_date to extracted_date
        # This violates the rule that extracted_date must only come from user's document
        # See memory:8688660 and memory:7901330
        logger.debug("[DATE-ENRICHMENT] Skipped - extracted_date should never be overwritten by canonical_date")
        return

    def _extract_document_primary_case_name(self, text: str) -> Optional[str]:
        """
        FIX: Extract the primary case name from the document.

        The primary case name typically appears at the beginning of legal documents in formats like:
        - "PLAINTIFF v. DEFENDANT"
        - "In the Matter of CASE NAME"
        - In briefs: "CASE NAME\nNo. 12-3456"

        This is used for contamination filtering to prevent cited case names from being
        incorrectly extracted as the document's own case name.

        Args:
            text: Full document text

        Returns:
            The document's primary case name, or None if not found
        """
        if not text or len(text) < 50:
            return None

        # Look at first 2000 characters (enough for case caption)
        header = text[:2000]

        # Strategy 1: Look for case name pattern before "No." (case number)
        # Enhanced to handle multi-plaintiff cases like "GOPHER MEDIA LLC, ...; AJAY THAKORE, ... v. DEFENDANT"
        # FIX: Updated pattern to handle case numbers like "103135-1" (6 digits before dash, 1 after)
        case_number_match = re.search(r"No\.\s+\d{4,7}-\d{1,3}", header, re.IGNORECASE)
        if case_number_match:
            # Look backwards from case number for case name
            before_case_num = header[: case_number_match.start()]

            # FIX P4: Look for "Plaintiffs" or "Plaintiff" marker to find all plaintiffs
            # This handles multi-plaintiff cases where multiple parties are listed before "v."
            plaintiffs_marker = re.search(r"Plaintiffs?\s*[-–]\s*Appellants?", before_case_num, re.IGNORECASE)
            if plaintiffs_marker:
                # Extract from start to plaintiffs marker
                plaintiff_section = before_case_num[: plaintiffs_marker.start()].strip()
                # Take last 500 chars to get the plaintiff names (handles long descriptions)
                plaintiff_section = plaintiff_section[-500:]

                # Find first complete party name (handles "COMPANY NAME, a corp; PERSON NAME, individual")
                # Look for pattern: ALL CAPS NAME followed by comma or semicolon
                first_party = re.search(r"([A-Z][A-Z\s&\.,\'-]{8,100?})(?:,|\;)", plaintiff_section)
                if first_party:
                    plaintiff_name = first_party.group(1).strip()
                    # Clean up trailing punctuation and descriptions
                    plaintiff_name = re.sub(r",\s*a\s+.*$", "", plaintiff_name)  # Remove ", a Nevada..."
                    plaintiff_name = re.sub(r",\s*an\s+.*$", "", plaintiff_name)  # Remove ", an individual..."
                    plaintiff_name = plaintiff_name.strip().strip(",").strip()

                    # Now find defendant after plaintiffs marker
                    after_plaintiffs = before_case_num[plaintiffs_marker.end() :]
                    v_match = re.search(r"v\.\s*([A-Z][A-Za-z\s\.,&\-\']{5,80})", after_plaintiffs, re.IGNORECASE)
                    if v_match:
                        defendant_name = v_match.group(1).strip()
                        # Clean defendant name
                        defendant_name = re.sub(
                            r",\s*(?:an?\s+)?individual.*$", "", defendant_name, flags=re.IGNORECASE
                        )
                        defendant_name = defendant_name.strip().strip(",").strip()

                        case_name = f"{plaintiff_name} v. {defendant_name}"
                        logger.warning(
                            f"[CONTAMINATION-FILTER] Found primary case (Strategy 1 Multi-Plaintiff): '{case_name}'"
                        )
                        return case_name

            # Original single-plaintiff logic as fallback
            # FIX: Look for case name pattern more specifically - find "v." and work backwards
            # This avoids matching from the beginning of the text (like "E SUPREME COURT")
            v_match = re.search(r"\s+v\.\s+", before_case_num, re.IGNORECASE)
            if v_match:
                # Extract text before "v." - look for the last 200 chars to get the plaintiff name
                before_v = before_case_num[max(0, v_match.start() - 200) : v_match.start()].strip()
                # Find the actual party name (skip court names, etc.)
                # NEW APPROACH: Look backwards from "Petitioners" to find the actual name
                # Find "Petitioners" or similar role word at the end (since before_v ends before "v.")
                role_match = re.search(r"(?:Petitioners?|Appellants?|Plaintiffs?)\s*,?\s*$", before_v, re.IGNORECASE)
                if role_match:
                    # Get text before the role word
                    before_role = before_v[: role_match.start()].strip()
                    # Now find the name - look for "ET AL" pattern first, then extract name before it
                    # This avoids matching from the beginning of the text
                    et_al_match = re.search(r"\s+ET\s+AL\.?\s*,?\s*$", before_role, re.IGNORECASE)
                    if et_al_match:
                        # Extract text before "ET AL"
                        before_et_al = before_role[: et_al_match.start()].strip()
                        # Now find the name - look for the last proper name (skip court words)
                        # Pattern: Look for a name that doesn't start with court words
                        plaintiff_match = re.search(r"([A-Z][A-Za-z\s\.,&\-\']{5,50})\s*$", before_et_al)
                        if plaintiff_match:
                            plaintiff_text = plaintiff_match.group(1).strip()
                            # Filter out if it starts with common court words
                            court_words = [
                                "THE SUPREME",
                                "THE COURT",
                                "IN THE",
                                "STATE OF",
                                "SUPREME COURT",
                                "WASHINGTON",
                                "F THE STATE",
                                "OF THE STATE",
                            ]
                            if any(
                                plaintiff_text.upper().startswith(word) or word in plaintiff_text.upper()
                                for word in court_words
                            ):
                                # Split and find the actual name
                                parts = re.split(
                                    r"\b(?:OF|THE|STATE|COURT|SUPREME|IN)\b", before_et_al, flags=re.IGNORECASE
                                )
                                if parts:
                                    # Filter out empty parts and find the last meaningful part
                                    non_empty_parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]
                                    if non_empty_parts:
                                        # Take the last part (should be the name)
                                        last_part = non_empty_parts[-1]
                                        # Extract just the name part - look for pattern like "KERRY L. ERICKSON"
                                        # Pattern: At least 2 capitalized words (person name pattern)
                                        name_match = re.search(
                                            r"([A-Z][A-Za-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][A-Za-z]+)", last_part
                                        )
                                        if name_match:
                                            name_text = name_match.group(1).strip()
                                        # Fallback: if no pattern match, take the last part if it has multiple words
                                        elif len(last_part.split()) >= 2:
                                            # Remove "WASHINGTON" if it's the first word
                                            words = last_part.split()
                                            if words[0].upper() == "WASHINGTON" and len(words) > 2:
                                                name_text = " ".join(words[1:])
                                            else:
                                                name_text = last_part
                                        else:
                                            name_text = None

                                        # Create a simple match-like object if we found a name
                                        if name_text:

                                            class SimpleMatch:
                                                def __init__(self, text):
                                                    self._text = text

                                                def group(self, n=1):
                                                    return self._text if n == 1 else None

                                            plaintiff_match = SimpleMatch(name_text)
                                else:
                                    plaintiff_match = None
                    else:
                        plaintiff_match = None
                    if not plaintiff_match:
                        # Fallback: just take the last reasonable name, but filter out court phrases
                        plaintiff_match = re.search(r"([A-Z][A-Za-z\s\.,&\-\']{5,50})\s*$", before_role)
                        if plaintiff_match:
                            plaintiff_text = plaintiff_match.group(1).strip()
                            # Filter out if it starts with common court words or contains them
                            court_words = [
                                "THE SUPREME",
                                "THE COURT",
                                "IN THE",
                                "STATE OF",
                                "SUPREME COURT",
                                "WASHINGTON",
                                "F THE STATE",
                                "OF THE STATE",
                            ]
                            if any(
                                plaintiff_text.upper().startswith(word) or word in plaintiff_text.upper()
                                for word in court_words
                            ):
                                # Try to find the actual name - look for a pattern like "KERRY L. ERICKSON"
                                # Split by common words and take the last part
                                parts = re.split(
                                    r"\b(?:OF|THE|STATE|COURT|SUPREME|IN|OF)\b", before_role, flags=re.IGNORECASE
                                )
                                if parts:
                                    # Find the last part that looks like a name (has letters, not just court words)
                                    for part in reversed(parts):
                                        part = part.strip()
                                        if part and len(part) > 5:
                                            # Check if it looks like a name (has letters, not all caps court words)
                                            name_match = re.search(r"([A-Z][A-Za-z\s\.,&\-\']{5,50})", part)
                                            if name_match:
                                                name_text = name_match.group(1).strip()
                                                # Make sure it's not a court word
                                                if not any(name_text.upper().startswith(word) for word in court_words):
                                                    plaintiff_match = name_match
                                                    break
                                    else:
                                        # If no good part found, try to extract just the name part
                                        # Look for pattern like "KERRY L. ERICKSON" or "ERICKSON"
                                        name_match = re.search(
                                            r"([A-Z][A-Z][A-Za-z\s\.,&\-\']{3,30})\s+(?:ET\s+AL\.?)?\s*$",
                                            before_role,
                                            re.IGNORECASE,
                                        )
                                        if name_match:
                                            plaintiff_match = name_match
                                        else:
                                            plaintiff_match = None
                                else:
                                    plaintiff_match = None
                else:
                    # No role word found, try original approach
                    plaintiff_match = re.search(
                        r"([A-Z][A-Za-z\s\.,&\-\']{3,50})\s+ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?)\s*$",
                        before_v,
                        re.IGNORECASE,
                    )
                    if not plaintiff_match:
                        plaintiff_match = re.search(
                            r"([A-Z][A-Za-z\s\.,&\-\']{3,50})\s+(?:Petitioners?|Appellants?|Plaintiffs?)\s*$",
                            before_v,
                            re.IGNORECASE,
                        )

                # Extract defendant after "v."
                after_v = before_case_num[v_match.end() :].strip()
                defendant_match = re.search(
                    r"^([A-Z][A-Za-z\s\.,&\-\']{3,60})(?:\s*,?\s*(?:Respondents?|Appellees?|Defendants?))?",
                    after_v,
                    re.IGNORECASE,
                )

                if plaintiff_match and defendant_match:
                    plaintiff_name = plaintiff_match.group(1).strip()
                    defendant_name = defendant_match.group(1).strip()
                    case_name = f"{plaintiff_name} v. {defendant_name}"
                else:
                    # Fallback to original pattern if new logic fails
                    v_pattern = re.search(
                        r"([A-Z][A-Za-z\s\.,&\-\']{5,80})\s+v\.\s+([A-Z][A-Za-z\s\.,&\-\']{5,80})",
                        before_case_num,
                        re.IGNORECASE,
                    )
                    if v_pattern:
                        case_name = f"{v_pattern.group(1).strip()} v. {v_pattern.group(2).strip()}"
                    else:
                        case_name = None
            else:
                case_name = None

            if case_name:
                # CRITICAL: Even if it has header patterns, extract and clean it for comparison
                # We need to detect "Erickson v. Pharmacia, LLC" even if it appears as "ERICKSON ET AL., Petitioners, v. PHARMACIA LLC, Respondent. NO"
                case_name_upper = case_name.upper()
                has_et_al = "ET AL" in case_name_upper or "ETAL" in case_name_upper.replace(" ", "")
                has_role_word = any(
                    role in case_name_upper
                    for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
                )
                has_no = "NO." in case_name_upper or " NO " in case_name_upper or case_name_upper.endswith(" NO")

                # If it has header patterns, clean them and extract the core case name
                if (has_et_al and has_role_word) or (has_role_word and has_no):
                    # Clean the header to get the core case name for comparison
                    # Remove "ET AL" and role words, normalize
                    cleaned = case_name
                    cleaned = re.sub(r"\bet\s+al\.?\b", "", cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(
                        r"\b(?:petitioners?|appellants?|plaintiffs?|appellees?|respondents?|defendants?)\b",
                        "",
                        cleaned,
                        flags=re.IGNORECASE,
                    )
                    cleaned = re.sub(r"\bno\.?\s*\d+", "", cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r"[,\.\s]+", " ", cleaned)
                    cleaned = cleaned.strip()

                    if cleaned and len(cleaned) > 10 and " v. " in cleaned:
                        logger.warning(
                            f"[CONTAMINATION-FILTER] Found primary case (Strategy 1, cleaned from header): '{cleaned}'"
                        )
                        return cleaned
                    else:
                        logger.debug(
                            f"[CONTAMINATION-FILTER] Skipping header pattern (Strategy 1): '{case_name}' (cleaned too short: '{cleaned}')"
                        )
                else:
                    logger.warning(f"[CONTAMINATION-FILTER] Found primary case (Strategy 1): '{case_name}'")
                    return case_name

        # Strategy 2: Look for case name in first few lines (typical brief format)
        lines = header.split("\n")
        for i, line in enumerate(lines[:15]):  # Check first 15 lines
            line = line.strip()
            if " v. " in line and len(line) > 10 and len(line) < 150:
                # Check if it looks like a case name (not a citation)
                # Case names usually don't have numbers before "v."
                if not re.search(r"\d+\s+\w+\.\s*\d*\s+\d+", line):  # Not "123 F.3d 456"
                    # Clean up common prefix/suffix patterns
                    cleaned = re.sub(r"^\s*(?:IN\s+THE\s+)?(?:MATTER\s+OF\s+)?", "", line, flags=re.IGNORECASE)
                    # ENHANCED: Clean role words from both ends
                    cleaned = re.sub(
                        r"\s*,?\s*(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*$",
                        "",
                        cleaned,
                        flags=re.IGNORECASE,
                    )
                    # Also clean role words at the beginning (e.g., "Appellant CARTER")
                    cleaned = re.sub(
                        r"^(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*,?\s*",
                        "",
                        cleaned,
                        flags=re.IGNORECASE,
                    )
                    # Clean extra commas and spaces
                    cleaned = re.sub(r"\s*,\s*,\s*", ", ", cleaned)  # Remove double commas
                    cleaned = re.sub(r"^\s*,\s*|\s*,\s*$", "", cleaned)  # Remove leading/trailing commas

                    if " v. " in cleaned and len(cleaned) > 10:
                        logger.warning(f"[CONTAMINATION-FILTER] Found primary case (Strategy 2): '{cleaned}'")
                        return cleaned

        # Strategy 3: Pattern match for common formats
        # "PLAINTIFF, v. DEFENDANT," or "PLAINTIFF v. DEFENDANT No."
        # ENHANCED: Handle role words in both positions
        pattern = r"([A-Z][A-Za-z\s\.,\&\-']{8,80})\s+v\.\s+([A-Za-z][A-Za-z\s\.,\&\-']{8,80})(?:\s*,|\s+No\.)"
        match = re.search(pattern, header)
        if match:
            case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            # ENHANCED: Clean role words from both parties
            # Clean plaintiff side
            plaintiff = match.group(1).strip()
            plaintiff = re.sub(r"\s*,?\s*(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*$", "", plaintiff, flags=re.IGNORECASE)
            plaintiff = re.sub(r"^(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*,?\s*", "", plaintiff, flags=re.IGNORECASE)
            # Clean defendant side
            defendant = match.group(2).strip()
            defendant = re.sub(r"\s*,?\s*(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*$", "", defendant, flags=re.IGNORECASE)
            defendant = re.sub(r"^(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*,?\s*", "", defendant, flags=re.IGNORECASE)
            
            case_name = f"{plaintiff.strip()} v. {defendant.strip()}"
            case_name = re.sub(r"\s*,\s*,\s*", ", ", case_name)  # Remove double commas
            case_name = re.sub(r"^\s*,\s*|\s*,\s*$", "", case_name)  # Remove leading/trailing commas
            # CRITICAL: Even if it has header patterns, extract and clean it for comparison
            case_name_upper = case_name.upper()
            has_et_al = "ET AL" in case_name_upper or "ETAL" in case_name_upper.replace(" ", "")
            has_role_word = any(
                role in case_name_upper
                for role in ["PETITIONER", "RESPONDENT", "APPELLANT", "APPELLEE", "PLAINTIFF", "DEFENDANT"]
            )
            has_no = "NO." in case_name_upper or " NO " in case_name_upper or case_name_upper.endswith(" NO")

            # If it has header patterns, clean them and extract the core case name
            if (has_et_al and has_role_word) or (has_role_word and has_no):
                # Clean the header to get the core case name for comparison
                cleaned = case_name
                cleaned = re.sub(r"\bet\s+al\.?\b", "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(
                    r"\b(?:petitioners?|appellants?|plaintiffs?|appellees?|respondents?|defendants?)\b",
                    "",
                    cleaned,
                    flags=re.IGNORECASE,
                )
                cleaned = re.sub(r"\bno\.?\s*\d+", "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"[,\.\s]+", " ", cleaned)
                cleaned = cleaned.strip()

                if cleaned and len(cleaned) > 10 and " v. " in cleaned:
                    logger.warning(
                        f"[CONTAMINATION-FILTER] Found primary case (Strategy 3, cleaned from header): '{cleaned}'"
                    )
                    return cleaned
                else:
                    logger.debug(
                        f"[CONTAMINATION-FILTER] Skipping header pattern (Strategy 3): '{case_name}' (cleaned too short: '{cleaned}')"
                    )
            else:
                logger.warning(f"[CONTAMINATION-FILTER] Found primary case (Strategy 3): '{case_name}'")
                return case_name

        logger.warning("[CONTAMINATION-FILTER] Could not extract document primary case name")
        return None

    def _calculate_cluster_confidence(self, citations: List[Any]) -> float:
        """Calculate confidence score for a cluster."""
        if not citations:
            return 0.0

        # Base confidence
        confidence = 0.5

        # Bonus for multiple citations
        if len(citations) > 1:
            confidence += 0.2

        # Bonus for consistent case names
        case_names = []
        for citation in citations:
            case_name = getattr(citation, "extracted_case_name", None) or getattr(citation, "canonical_name", None)
            if case_name and case_name != "N/A":
                case_names.append(case_name)

        if len(case_names) > 1:
            # Check consistency
            base_name = case_names[0]
            consistent_count = sum(
                1 for name in case_names[1:] if self._calculate_name_similarity(base_name, name) > 0.7
            )
            if consistent_count > 0:
                confidence += 0.2

        # Bonus for verification
        verified_count = sum(1 for citation in citations if getattr(citation, "verified", False))
        if verified_count > 0:
            confidence += 0.1

        return min(1.0, confidence)


# Global singleton instance
_master_clusterer = None


def get_master_clusterer(config: Optional[Dict[str, Any]] = None) -> UnifiedClusteringMaster:
    """Get the singleton master clusterer instance."""
    global _master_clusterer
    if _master_clusterer is None:
        _master_clusterer = UnifiedClusteringMaster(config)
    return _master_clusterer


def cluster_citations_unified_master(
    citations: List[Any],
    original_text: str = "",
    enable_verification: bool = None,
    request_id: str = "",
    config: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, str, str], None]] = None,
) -> List[Dict[str, Any]]:
    """
    THE SINGLE, UNIFIED CLUSTERING FUNCTION

    This function replaces ALL 45+ duplicate clustering functions.
    Use this instead of:
    - cluster_citations()
    - group_citations_into_clusters()
    - _cluster_citations_local()
    - _create_clusters()
    - All other duplicate clustering functions

    Returns:
        List of cluster dictionaries with comprehensive metadata
    """
    clusterer = get_master_clusterer(config)
    return clusterer.cluster_citations(citations, original_text, enable_verification, request_id, progress_callback)
