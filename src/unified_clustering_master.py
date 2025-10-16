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
from typing import Dict, Any, Optional, List, Union, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter

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
        self.debug_mode = self.config.get('debug_mode', False)
        self.min_cluster_size = self.config.get('min_cluster_size', 1)
        self.case_name_similarity_threshold = self.config.get('case_name_similarity_threshold', 0.95)  # FIX #58E: Raised from 0.6 to prevent different cases from clustering
        self.proximity_threshold = self.config.get('proximity_threshold', 200)  # characters
        self.enable_verification = self.config.get('enable_verification', False)
        
        self._setup_patterns()
        logger.info("UnifiedClusteringMaster initialized - all duplicate clusterers deprecated")
    
    def _setup_patterns(self):
        """Setup regex patterns for clustering."""
        self.patterns = {
            # Parallel citation patterns
            'washington_parallel': re.compile(r'(\d+)\s+(?:Wn\.|Wash\.)\d*d\s+\d+.*?(\d+)\s+(?:P\.|A\.)\d*d\s+\d+'),
            'federal_parallel': re.compile(r'(\d+)\s+F\.\d*d\s+\d+.*?(\d+)\s+U\.S\.\s+\d+'),
            'supreme_parallel': re.compile(r'(\d+)\s+S\.\s*Ct\.\s+\d+.*?(\d+)\s+L\.\s*Ed\.\d*d\s+\d+'),
            'generic_parallel': re.compile(r'(\d+)\s+[A-Z][a-z]*\.\d*d?\s+\d+.*?(\d+)\s+[A-Z][a-z]*\.\d*d?\s+\d+'),
            
            # Citation separators
            'separator_patterns': re.compile(r'[;,]\s*(?:see\s+)?(?:also\s+)?'),
            
            'case_name_v': re.compile(r'([A-Z][A-Za-z0-9&\'\\s-]+)\\s+v\\.\\s+([A-Z][A-Za-z0-9&\'\\s-]+)'),
            'case_name_in_re': re.compile(r'(In\\s+re\\s+[A-Z][a-zA-Z\\s\'&\\-\\.]{2,80})', re.IGNORECASE),
            'case_name_state': re.compile(r'(State|People|Commonwealth)\\s+v\\.\\s+([A-Z][a-zA-Z\\s\'&\\-\\.]{2,80})', re.IGNORECASE),
            
            # Year patterns
            'year_patterns': re.compile(r'\((\d{4})\)|\b(19|20)\d{2}\b'),
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
                    citation.get('canonical_name'),
                    citation.get('extracted_case_name'),
                    citation.get('cluster_case_name'),
                ]
            else:
                possible_names = [
                    getattr(citation, 'canonical_name', None),
                    getattr(citation, 'extracted_case_name', None),
                    getattr(citation, 'cluster_case_name', None),
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
                if cleaned and cleaned not in ('N/A', 'Unknown', 'Unknown Case'):
                    candidates.append((self._score_case_name(cleaned), cleaned))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]
    
    def _is_truncated_name(self, name: str) -> bool:
        """Check if a case name appears truncated."""
        if not name or name == 'N/A':
            return False
        
        # Check for truncation patterns
        # Pattern 1: Ends with "v. [1-3 letters]" like "Noem v. Nat"
        if re.search(r'v\.\s+[A-Z][a-z]{0,2}$', name):
            return True
        
        # Pattern 2: Starts with short word like "Inc. v." without full company name
        if re.match(r'^(Inc\.|LLC|Corp\.|Co\.|Ltd\.)\s+v\.', name):
            return True
        
        # Pattern 3: Ends mid-word (no punctuation at end, last word < 4 chars)
        words = name.split()
        if words and len(words[-1]) < 4 and not name[-1] in '.,:;)':
            return True
        
        return False
    
    def _clean_case_name_from_extraction(self, case_name: str) -> str:
        """Clean case name by removing sentence fragments and other contamination."""
        if not case_name or case_name in ('N/A', 'Unknown', 'Unknown Case'):
            return case_name
        
        # Remove sentence fragments that appear before the actual case name
        # Look for patterns like "scheme as a whole. Ass'n of..." and keep only "Ass'n of..."
        # Match: sentence-ending period followed by spaces, then case name with "v."
        case_name_match = re.search(r'\.\s+([A-Z].+?\s+v\.\s+.+?)$', case_name)
        if case_name_match and ' v. ' in case_name_match.group(1):
            case_name = case_name_match.group(1).strip()
        
        # Normalize whitespace
        case_name = re.sub(r'\s+', ' ', case_name)
        
        return case_name

    def _score_case_name(self, name: str) -> float:
        """Score case name quality for comparison."""
        score = 0.0
        lowered = name.lower()

        if ' v. ' in lowered or lowered.startswith('state v') or lowered.startswith('people v'):
            score += 2.0
        if lowered.startswith('in re') or lowered.startswith('ex parte'):
            score += 1.5

        score += min(len(name) / 25.0, 2.0)

        if 'unknown' in lowered:
            score -= 1.0

        return score

    def _select_best_case_year(self, group: List[Any]) -> Optional[str]:
        """Return the most consistent year across the group."""
        year_sources = ['canonical_date', 'extracted_date', 'cluster_year']

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
        if not value or value in ('N/A', 'Unknown', ''):
            return None

        if isinstance(value, int):
            return str(value)

        if isinstance(value, str):
            match = re.search(r'(19|20)\d{2}', value)
            if match:
                return match.group(0)

        return None

    def _should_replace_case_name(self, existing: Optional[str], candidate: Optional[str]) -> bool:
        if not candidate:
            return False
        if not existing or existing in ('', 'N/A', 'Unknown', 'Unknown Case'):
            return True
        return self._score_case_name(candidate) > self._score_case_name(existing)

    def cluster_citations(
        self,
        citations: List[Any],
        original_text: str = "",
        enable_verification: bool = None,
        request_id: str = ""
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
            logger.warning(f"[CONTAMINATION-FILTER] Document primary case detected: '{self.document_primary_case_name}'")
        
        # CRITICAL: Use ERROR level to ensure this appears in logs
        logger.error(f"🎯 [CLUSTER-ENTRY] Starting clustering: {len(citations)} citations, verification={enable_verification}")
        logger.info(f"🎯 MASTER_CLUSTER: Starting clustering for {len(citations)} citations (verification: {enable_verification})")
        
        if not citations:
            logger.warning("MASTER_CLUSTER: No citations provided")
            return []
        
        try:
            # Step 1: Detect parallel citations and create initial groups
            logger.info("MASTER_CLUSTER: Step 1 - Detecting parallel citations")
            logger.error(f"🔍 [CLUSTER-DEBUG] Input: {len(citations)} citations")
            
            # Sample first 3 citations to see their structure
            for i, cit in enumerate(citations[:3]):
                cit_text = getattr(cit, 'citation', str(cit)) if hasattr(cit, 'citation') else str(cit)
                has_position = hasattr(cit, 'start_index') or (isinstance(cit, dict) and 'start_index' in cit)
                position = getattr(cit, 'start_index', None) if hasattr(cit, 'start_index') else (cit.get('start_index') if isinstance(cit, dict) else None)
                logger.error(f"🔍 [CLUSTER-DEBUG] Citation {i+1}: {cit_text}, has_position={has_position}, position={position}")
            
            parallel_groups = self._detect_parallel_citations(citations, original_text)
            logger.info(f"MASTER_CLUSTER: Created {len(parallel_groups)} parallel groups")
            logger.error(f"🔍 [CLUSTER-DEBUG] Output: {len(parallel_groups)} parallel groups (expected < {len(citations)} if parallels detected)")
            
            # Show size of first few groups
            for i, group in enumerate(parallel_groups[:5]):
                logger.error(f"🔍 [CLUSTER-DEBUG] Group {i+1} size: {len(group)} citations")
            
            # Step 2: Extract and propagate metadata within groups
            logger.info("MASTER_CLUSTER: Step 2 - Extracting and propagating metadata")
            enhanced_citations = self._extract_and_propagate_metadata(citations, parallel_groups, original_text)
            logger.info(f"MASTER_CLUSTER: Enhanced {len(enhanced_citations)} citations")
            
            # Step 3: Create final clusters by metadata similarity
            logger.info("MASTER_CLUSTER: Step 3 - Creating final clusters")
            final_clusters = self._create_final_clusters(enhanced_citations)
            logger.info(f"MASTER_CLUSTER: Created {len(final_clusters)} final clusters")
            
            # Step 4: Apply verification if enabled
            if enable_verification:
                logger.info("MASTER_CLUSTER: Step 4 - Applying verification")
                # CRITICAL FIX: Set instance variable before calling verification
                # so _apply_verification_to_clusters uses the correct value
                self.enable_verification = enable_verification
                self._apply_verification_to_clusters(final_clusters)
            
            # Step 4.5: FIX #22 - Validate canonical consistency
            # CRITICAL: This runs EVEN IF enable_verification=False because verification
            # may have been done externally (before clustering). We check for canonical data.
            logger.info("MASTER_CLUSTER: Step 4.5 - Validating canonical consistency (Fix #22)")
            final_clusters = self._validate_canonical_consistency(final_clusters)
            logger.info(f"MASTER_CLUSTER: After canonical validation: {len(final_clusters)} clusters")
            
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
            logger.info(f"✅ MASTER_CLUSTER: Completed clustering in {elapsed_time:.2f}s - {len(formatted_clusters)} clusters")
            
            return formatted_clusters
            
        except Exception as e:
            logger.error(f"❌ MASTER_CLUSTER: Clustering failed: {e}")
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

        for citation in citations:
            if id(citation) not in processed_ids:
                parallel_groups.append([citation])

        return parallel_groups

    def _group_by_proximity(self, citations: List[Any], text: str) -> List[List[Any]]:
        """Group citations by proximity in the text."""
        if not citations or not text:
            return [[citation] for citation in citations]
        
        # Sort citations by position
        sorted_citations = sorted(citations, key=lambda c: getattr(c, 'start_index', 0))
        
        groups = []
        current_group = [sorted_citations[0]]
        
        for i in range(1, len(sorted_citations)):
            current_citation = sorted_citations[i]
            previous_citation = sorted_citations[i-1]
            
            # Calculate distance
            current_start = getattr(current_citation, 'start_index', 0)
            previous_end = getattr(previous_citation, 'end_index', 0)
            distance = current_start - previous_end
            
            if distance <= self.proximity_threshold:
                current_group.append(current_citation)
            else:
                groups.append(current_group)
                current_group = [current_citation]
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _are_parallel_citations(self, citations: List[Any], text: str) -> bool:
        """Check if citations are parallel (refer to the same case)."""
        if len(citations) < 2:
            return False

        citation_texts = []
        citation_lookup = {}
        for citation in citations:
            if hasattr(citation, 'citation'):
                citation_text = citation.citation
            elif isinstance(citation, dict):
                citation_text = citation.get('citation', '')
            else:
                citation_text = str(citation)
            citation_texts.append(citation_text)
            citation_lookup[citation_text] = citation

        # Respect explicit parallel_citations metadata when present
        for citation in citations:
            if isinstance(citation, dict):
                parallels = citation.get('parallel_citations', []) or []
            else:
                parallels = getattr(citation, 'parallel_citations', []) or []
            for parallel_text in parallels:
                if parallel_text in citation_lookup:
                    return True

        # Check for regex-based parallel patterns
        for pattern_name, pattern in self.patterns.items():
            if 'parallel' in pattern_name:
                for text_segment in citation_texts:
                    if pattern.search(text_segment):
                        return True

        # Reporter-based heuristic comparisons
        for i in range(len(citations)):
            for j in range(i + 1, len(citations)):
                if self._are_citations_parallel_pair(citations[i], citations[j], text):
                    return True

        # Fallback: compare available case names for similarity
        # CRITICAL: Only use this for citations in DIFFERENT reporters
        # Citations in the same reporter with different volumes CANNOT be parallel
        case_names = []
        for citation in citations:
            case_name = (
                getattr(citation, 'canonical_name', None)
                or getattr(citation, 'cluster_case_name', None)
                or getattr(citation, 'extracted_case_name', None)
            )
            if case_name and case_name != 'N/A':
                case_names.append(case_name)

        if len(case_names) >= 2:
            for i in range(len(case_names)):
                for j in range(i + 1, len(case_names)):
                    # CRITICAL FIX: Check if they're in the same reporter first
                    reporter_i = self._extract_reporter_type(citation_texts[i])
                    reporter_j = self._extract_reporter_type(citation_texts[j])
                    
                    # If same reporter, they CANNOT be parallel (must have different reporters)
                    if reporter_i == reporter_j:
                        logger.debug(f"PARALLEL_CHECK Rejected name similarity - same reporter: {reporter_i} | {citation_texts[i]} vs {citation_texts[j]}")
                        continue  # Don't cluster same-reporter citations even with matching names
                    
                    similarity = self._calculate_name_similarity(case_names[i], case_names[j])
                    if similarity >= self.case_name_similarity_threshold:
                        logger.debug(f"PARALLEL_CHECK Accepted via name similarity ({similarity:.2f}): {case_names[i][:30]} | {citation_texts[i]} ↔ {citation_texts[j]}")
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
                return cit.get('start_index', cit.get('start', 0))
            return getattr(cit, 'start_index', getattr(cit, 'start', 0))
        
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
            if char == '(':
                paren_depth += 1
                if paren_depth > 0:
                    crossed_boundary = True
            elif char == ')':
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
            citation1_text = citation1.get('citation', '')
            citation1_meta = citation1
        else:
            citation1_text = getattr(citation1, 'citation', str(citation1))
            citation1_meta = citation1.__dict__ if hasattr(citation1, '__dict__') else {}

        if isinstance(citation2, dict):
            citation2_text = citation2.get('citation', '')
            citation2_meta = citation2
        else:
            citation2_text = getattr(citation2, 'citation', str(citation2))
            citation2_meta = citation2.__dict__ if hasattr(citation2, '__dict__') else {}

        # Check for known parallel citations from metadata first
        def get_parallel_citations(citation_meta):
            if isinstance(citation_meta, dict):
                return citation_meta.get('parallel_citations', []) or []
            return getattr(citation_meta, 'parallel_citations', []) or []

        parallel1 = get_parallel_citations(citation1_meta)
        parallel2 = get_parallel_citations(citation2_meta)
        
        # FIX #58D: Even if marked as parallel by eyecite, VALIDATE extracted names/years!
        # Eyecite marks citations as parallel based on proximity, but doesn't check if they're the same case.
        is_marked_parallel = (citation1_text in parallel2 or citation2_text in parallel1)
        
        if is_marked_parallel:
            if self.debug_mode:
                logger.debug("PARALLEL_CHECK citations marked parallel by eyecite - VALIDATING names/years...")
            
            # STRICT: Get extracted names (never canonical!)
            case_name1 = self._get_case_name(citation1)
            case_name2 = self._get_case_name(citation2)
            
            # If BOTH have names, they MUST match
            if case_name1 and case_name2 and case_name1 != 'N/A' and case_name2 != 'N/A':
                name_similarity = self._calculate_name_similarity(case_name1, case_name2)
                logger.error(f"🔥 [FIX #58D DEBUG] Eyecite parallel validation: similarity={name_similarity:.2f}, threshold={self.case_name_similarity_threshold:.2f}, name1='{case_name1[:40]}', name2='{case_name2[:40]}'")
                if name_similarity < self.case_name_similarity_threshold:
                    logger.error(f"🚫 [FIX #58D] REJECTED eyecite parallel - name mismatch ({name_similarity:.2f}): '{case_name1[:30]}' vs '{case_name2[:30]}'")
                    return False
                else:
                    logger.error(f"✅ [FIX #58D] ACCEPTED eyecite parallel - name match ({name_similarity:.2f} >= {self.case_name_similarity_threshold:.2f})")
            
            # Get extracted years (never canonical!)
            def get_year(cit: Any) -> Optional[str]:
                if isinstance(cit, dict):
                    return cit.get('extracted_date')
                return getattr(cit, 'extracted_date', None)
            
            year1 = get_year(citation1)
            year2 = get_year(citation2)
            
            # If BOTH have years, they MUST match
            if year1 and year2 and year1 != 'N/A' and year2 != 'N/A':
                if year1 != year2:
                    if self.debug_mode:
                        logger.debug(f"PARALLEL_CHECK REJECTED eyecite parallel - year mismatch: {year1} vs {year2}")
                    return False
            
            # Validation passed - accept the parallel relationship
            if self.debug_mode:
                logger.debug(f"PARALLEL_CHECK ACCEPTED eyecite parallel after validation: '{case_name1[:30] if case_name1 else 'N/A'}' ({year1})")
            return True

        reporter1 = self._extract_reporter_type(citation1_text)
        reporter2 = self._extract_reporter_type(citation2_text)

        if self.debug_mode:
            logger.debug(
                "PARALLEL_CHECK start | %s (%s) ↔ %s (%s)",
                citation1_text,
                reporter1,
                citation2_text,
                reporter2,
            )

        # Check if either citation is explicitly marked as parallel to the other
        def get_cluster_id(cit: Any) -> Optional[str]:
            if isinstance(cit, dict):
                return cit.get('cluster_id') or cit.get('clusterid')
            return getattr(cit, 'cluster_id', getattr(cit, 'clusterid', None))

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
            vol1, rep1 = parsed1.get('volume'), parsed1.get('reporter')
            vol2, rep2 = parsed2.get('volume'), parsed2.get('reporter')
            
            # If SAME reporter but DIFFERENT volumes, they CANNOT be parallel
            if rep1 and rep2 and rep1 == rep2 and vol1 != vol2:
                logger.warning(
                    f"🚫 P5_FIX: Prevented false clustering - same reporter '{rep1}' but different volumes {vol1} vs {vol2} | "
                    f"{citation1_text} ↔ {citation2_text}"
                )
                return False

        # If either reporter is unknown, we can't reliably determine if they're parallel
        if 'unknown' in (reporter1, reporter2):
            if self.debug_mode:
                logger.debug("PARALLEL_CHECK rejected: unknown reporter type")
            return False

        # CRITICAL FIX: Check proximity FIRST before any other heuristics
        # This prevents citations that are far apart from being grouped together
        # even if they have similar case names or other matching attributes
        def get_start_index(cit: Any) -> int:
            if isinstance(cit, dict):
                return cit.get('start_index', cit.get('start', 0))
            return getattr(cit, 'start_index', getattr(cit, 'start', 0))

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
                    citation2_text[:50]
                )
            return False
        
        # Adjust proximity threshold based on citation types
        proximity_threshold = self.proximity_threshold
        if 'U.S.' in citation1_text or 'U.S.' in citation2_text:
            # Be more lenient with US Supreme Court citations
            proximity_threshold = max(proximity_threshold, 500)
            
        # REJECT IMMEDIATELY if citations are too far apart
        # This prevents false clustering of unrelated citations
        if distance > proximity_threshold:
            if self.debug_mode:
                logger.debug(
                    "PARALLEL_CHECK rejected by proximity | distance=%s threshold=%s | %s ↔ %s",
                    distance,
                    proximity_threshold,
                    citation1_text[:50],
                    citation2_text[:50]
                )
            return False
        
        # Now that we know citations are close together, check parallel patterns
        if not self._match_parallel_patterns(citation1_text, citation2_text):
            if self.debug_mode:
                logger.debug("PARALLEL_CHECK reporter pair not recognized as parallel")
            
            # FIX #58F: If patterns don't match, try case name similarity as a fallback
            # BUT ONLY if they're already within proximity (which we checked above)
            case_name1 = self._get_case_name(citation1)
            case_name2 = self._get_case_name(citation2)
            
            if case_name1 and case_name2 and case_name1 != 'N/A' and case_name2 != 'N/A':
                similarity = self._calculate_name_similarity(case_name1, case_name2)
                logger.error(f"🔥 [FIX #58F] Fallback name similarity check: {similarity:.2f} vs threshold {self.case_name_similarity_threshold:.2f} | '{case_name1[:30]}' vs '{case_name2[:30]}'")
                if similarity >= self.case_name_similarity_threshold:  # FIX #58F: Use configured threshold, not hardcoded 0.8!
                    logger.error(f"✅ [FIX #58F] ACCEPTED via fallback - name similarity {similarity:.2f} >= {self.case_name_similarity_threshold:.2f}")
                    return True
                else:
                    logger.error(f"🚫 [FIX #58F] REJECTED via fallback - name similarity {similarity:.2f} < {self.case_name_similarity_threshold:.2f}")
            
            return False

        # Washington-specific handling
        if 'wash' in reporter1 or 'wash' in reporter2:
            if not self._check_washington_parallel_patterns(citation1_text, citation2_text):
                if self.debug_mode:
                    logger.debug("PARALLEL_CHECK Washington reporter validation failed")
                return False

        # FIX #58C: STRICT validation - BOTH citations MUST have extracted names AND years
        # This prevents citations from different cases clustering together
        case_name1 = self._get_case_name(citation1)
        case_name2 = self._get_case_name(citation2)
        
        # STRICT: Reject if either citation lacks extracted name
        if not case_name1 or not case_name2 or case_name1 == 'N/A' or case_name2 == 'N/A':
            if self.debug_mode:
                logger.debug(f"PARALLEL_CHECK rejected - missing extracted names: '{case_name1}' vs '{case_name2}'")
            return False
        
        # STRICT: Names must match
        name_similarity = self._calculate_name_similarity(case_name1, case_name2)
        if name_similarity < self.case_name_similarity_threshold:
            if self.debug_mode:
                logger.debug(f"PARALLEL_CHECK rejected - name mismatch ({name_similarity:.2f}): '{case_name1}' vs '{case_name2}'")
            return False
        
        # FIX #58C: STRICT year validation
        def get_year(cit: Any) -> Optional[str]:
            """Get ONLY extracted year for clustering - never canonical!"""
            if isinstance(cit, dict):
                return cit.get('extracted_date')
            return getattr(cit, 'extracted_date', None)
        
        year1 = get_year(citation1)
        year2 = get_year(citation2)
        
        # STRICT: Reject if either citation lacks extracted year
        if not year1 or not year2 or year1 == 'N/A' or year2 == 'N/A':
            if self.debug_mode:
                logger.debug(f"PARALLEL_CHECK rejected - missing extracted years: '{year1}' vs '{year2}'")
            return False
        
        # STRICT: Years must match exactly
        if year1 != year2:
            if self.debug_mode:
                logger.debug(f"PARALLEL_CHECK rejected - year mismatch: {year1} vs {year2}")
            return False

        # If we get here, the citations are parallel AND have matching extracted names/years
        if self.debug_mode:
            logger.debug(
                "PARALLEL_CHECK ACCEPTED | %s ↔ %s | distance=%s | name=%s | year=%s",
                citation1_text,
                citation2_text,
                distance,
                case_name1[:30],
                year1
            )
            
        return True
        
    def _get_case_name(self, citation: Any) -> Optional[str]:
        """
        FIX #58C: Get case name for clustering - USE ONLY EXTRACTED, NEVER CANONICAL!
        
        CRITICAL: Clustering MUST use extracted names from the document, NOT canonical names from APIs.
        Using canonical names causes citations that verify to different cases to cluster together.
        """
        if isinstance(citation, dict):
            return (
                citation.get('extracted_case_name')  # FIX #58C: EXTRACTED ONLY!
                or citation.get('case_name')
            )
        return (
            getattr(citation, 'extracted_case_name', None)  # FIX #58C: EXTRACTED ONLY!
            or getattr(citation, 'case_name', None)
        )

    def _extract_reporter_type(self, citation_text: str) -> str:
        """Extract a simplified reporter type token from citation text with enhanced Washington state support."""
        if not citation_text or not isinstance(citation_text, str):
            return 'unknown'
            
        normalized = citation_text.lower()
        
        # Washington Court of Appeals (Div. I, II, III)
        if any(token in normalized for token in (
            'wn. app.', 'wn. app', 'wn.app.', 'wn app',
            'wash. app.', 'wash. app', 'wash.app.', 'wash app',
            'wa. app.', 'wa app', 'w.a.', 'wa.', 'wac',
            'wn. app. 2d', 'wn. app.2d', 'wn app 2d', 'wn app.2d',
            'wash. app. 2d', 'wash. app.2d', 'wash app 2d', 'wash app.2d',
            'div. i', 'div. ii', 'div. iii', 'div i', 'div ii', 'div iii',
            'division i', 'division ii', 'division iii'
        )):
            return 'wash_app'
            
        # Washington Supreme Court (Wash. 2d, Wn.2d, etc.)
        if any(token in normalized for token in (
            'wn.2d', 'wn. 2d', 'wn2d', 'wn 2d',
            'wash.2d', 'wash. 2d', 'wash2d', 'wash 2d',
            'w n.2d', 'w n 2d', 'wn. 2d', 'wn.2d',
            'washington 2d', 'washington.2d', 'washington. 2d'
        )):
            return 'wash2d'
            
        # General Washington reporters (catch-all for other variations)
        if any(token in normalized for token in (
            'wash.', 'wn.', 'wash ', 'wn ', 'wa.', 'wa ',
            'washington reports', 'washington supreme court', 'wsc'
        )):
            # If we've already identified it as a specific type, return that
            if 'app' in normalized or 'div' in normalized:
                return 'wash_app'
            if '2d' in normalized or 'ii' in normalized.lower():
                return 'wash2d'
            return 'wash'
            
        # Pacific Reporter (P., P.2d, P.3d)
        if 'p.3d' in normalized or 'p3d' in normalized or 'p. 3d' in normalized:
            return 'p3d'
        if 'p.2d' in normalized or 'p2d' in normalized or 'p. 2d' in normalized:
            return 'p2d'
        if ' p. ' in normalized or ' p ' in normalized:
            # Only return 'p' if it's not part of another word
            if not any(w in normalized for w in ('supra', 'sup.', 'para', 'page', 'part')):
                return 'p'
                
        # US Supreme Court
        if 'u.s.' in normalized or 'us ' in normalized:
            return 'us'
        if 's. ct.' in normalized or 's.ct.' in normalized or 's ct' in normalized or 'supreme court' in normalized:
            return 'sct'
        if 'l. ed.' in normalized or 'l.ed.' in normalized or 'l ed ' in normalized:
            return 'led'
            
        # Federal Reporters
        if 'f.3d' in normalized or 'f3d' in normalized or 'f. 3d' in normalized:
            return 'f3d'
        if 'f.2d' in normalized or 'f2d' in normalized or 'f. 2d' in normalized:
            return 'f2d'
        if ' f. ' in normalized or ' f ' in normalized:
            # Only return 'f' if it's not part of another word
            if not any(w in normalized for w in ('of ', 'if ', 'for ', 'from ')):
                return 'f'
                
        # Westlaw
        if ' wl ' in normalized or ' w.l.' in normalized or 'wl.' in normalized:
            if ' ' not in normalized.replace(' ', ''):  # Simple WL citation
                return 'wl'
                
        return 'unknown'

    def _match_parallel_patterns(self, citation1: str, citation2: str) -> bool:
        """Check if two citation texts match known parallel citation reporter combinations."""
        # First check Washington-specific patterns which have special handling
        if self._check_washington_parallel_patterns(citation1, citation2):
            return True
            
        reporter1 = self._extract_reporter_type(citation1)
        reporter2 = self._extract_reporter_type(citation2)
        
        if reporter1 == reporter2 or 'unknown' in (reporter1, reporter2):
            return False

        # Check for known parallel reporter pairs
        reporter_pair = frozenset({reporter1, reporter2})
        valid_pairs = {
            # Washington State
            frozenset({'wash', 'p3d'}),
            frozenset({'wash', 'p2d'}),
            frozenset({'wash', 'p'}),
            frozenset({'wash2d', 'p3d'}),
            frozenset({'wash2d', 'p2d'}),
            frozenset({'wash2d', 'p'}),
            frozenset({'wash_app', 'p3d'}),
            frozenset({'wash_app', 'p2d'}),
            frozenset({'wash_app', 'p'}),
            
            # US Supreme Court
            frozenset({'us', 'sct'}),
            frozenset({'us', 'led'}),
            frozenset({'us', 'l_ed'}),
            frozenset({'sct', 'led'}),
            frozenset({'sct', 'l_ed'}),
            frozenset({'led', 'l_ed'}),
            
            # Federal Reporters
            frozenset({'f3d', 'us'}),
            frozenset({'f3d', 'sct'}),
            frozenset({'f2d', 'us'}),
            frozenset({'f2d', 'sct'}),
            frozenset({'f', 'us'}),
            frozenset({'f', 'sct'}),
            
            # State-specific parallel citations
            frozenset({'cal4th', 'cal_rptr3d'}),
            frozenset({'cal4th', 'calrptr3d'}),
            frozenset({'cal_app4th', 'cal_rptr3d'}),
            frozenset({'cal_app4th', 'calrptr3d'}),
            
            # Other common parallel citations
            frozenset({'a3d', 'a2d'}),
            frozenset({'nw2d', 'nw'}),
            frozenset({'se2d', 'se'}),
            frozenset({'so3d', 'so2d'}),
            frozenset({'p3d', 'p2d'}),
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
            match = re.search(r'(\d+)\s+(?:Wash\.?2d?|Wn\.?2d?|P\.?3?d?)\s+(\d+)', citation, re.IGNORECASE)
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
            normalized = re.sub(r'[^a-z0-9\s.]', ' ', cite.lower())
            # Collapse multiple spaces and standardize variations
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            # Standardize variations
            normalized = normalized.replace('pacific', 'p').replace('pacific reporter', 'p')
            normalized = normalized.replace('washington', 'wash').replace('wn ', 'wash ').replace('wn. ', 'wash. ')
            # Handle cases like 'Wn. App.' -> 'wash app'
            normalized = re.sub(r'wash(?:ington)?\s+app(?:\.?\s*\w*)?', 'wash app', normalized)
            # Handle cases like 'Wash.2d' -> 'wash2d'
            normalized = re.sub(r'wash(?:ington)?\.?\s*(\d*)d', r'wash\1d', normalized)
            # Handle cases like 'Wn.2d' -> 'wash2d'
            normalized = re.sub(r'wn\.?\s*(\d*)d', r'wash\1d', normalized)
            # Handle cases like 'P.3d' -> 'p3d'
            normalized = re.sub(r'p\.?\s*(\d*)d', r'p\1d', normalized)
            return normalized
            
        norm1 = normalize_citation(citation1)
        norm2 = normalize_citation(citation2)
        
        if self.debug_mode:
            logger.debug(f"WA_PARALLEL_CHECK: Normalized citations: '{norm1}' and '{norm2}'")
        
        # Check if we have one Washington citation and one Pacific Reporter citation
        def is_wash_citation(cite):
            return any(term in cite for term in [
                'wash ', 'wash. ', 'wn ', 'wn. ', 'washington',
                'wash app', 'wash. app', 'wn app', 'wn. app', 'wac',
                'wash2d', 'wash 2d', 'wash. 2d', 'wn2d', 'wn 2d', 'wn. 2d',
                'wash.app', 'wn.app', 'washapp', 'wnapp', 'wash2d', 'wn2d',
                'wash. app. 2d', 'wn. app. 2d', 'wac '  # Additional patterns
            ]) or re.search(r'wash(?:ington)?\s*\d*d', cite) or \
               re.search(r'wn\.?\s*\d*d', cite) or \
               re.search(r'wac\s*\d+', cite)
            
        def is_p_citation(cite):
            return any(term in cite for term in [
                ' p ', ' p. ', 'p2d', 'p.2d', 'p 2d', 'p. 2d',
                'p3d', 'p.3d', 'p 3d', 'p. 3d', 'pacific',
                'p.2d', 'p.3d', 'p. 2d', 'p. 3d', 'p2d', 'p3d',
                'p. 2d', 'p. 3d', 'p.2d', 'p.3d'  # Additional patterns
            ]) or re.search(r'p\.?\s*\d*d', cite)
        
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
                    r'(\d+)\s+(?:wash\.?\s*\d*d|wn\.?\s*\d*d|p\.?\s*\d*d)\s+(\d+)',
                    # Patterns with 'v.' or 'vol.'
                    r'(?:v\.?|vol\.?)\s*(\d+)\s+(?:wash|wn|p)\.?\s*\d*d\s+(\d+)',
                    # Patterns with parentheses: (123 Wash.2d 456)
                    r'\((\d+)\s+(?:wash|wn|p)\.?\s*\d*d\s+(\d+)\)',
                    # Just numbers: 123 456 (last two numbers)
                    r'(\d+)\s+\d+\s+(\d+)',
                    # Any two numbers (last resort)
                    r'(\d+)\s+(\d+)'
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
                # Exact match
                if vol1 == vol2 and page1 == page2:
                    if self.debug_mode:
                        logger.debug(f"✅ WASHINGTON PARALLEL MATCH (exact): {citation1} ↔ {citation2}")
                    return True
                
                # Allow for small page differences (same volume, pages within 5)
                if vol1 == vol2 and abs(page1 - page2) <= 5:
                    if self.debug_mode:
                        logger.debug(f"✅ WASHINGTON PARALLEL MATCH (close pages): {citation1} ↔ {citation2}")
                    return True
            
            # If volume/page extraction failed, try to extract just page numbers
            def extract_just_pages(cite):
                # Look for 2-4 digit numbers that could be page numbers
                pages = [int(m) for m in re.findall(r'\b(\d{2,4})\b', cite)]
                return pages[-2:] if len(pages) >= 2 else []
                
            pages1 = extract_just_pages(norm1)
            pages2 = extract_just_pages(norm2)
            
            if pages1 and pages2:
                # Check if any page numbers are close (within 5)
                for p1 in pages1[-2:]:  # Check last 2 numbers in each citation
                    for p2 in pages2[-2:]:
                        if abs(p1 - p2) <= 5:
                            if self.debug_mode:
                                logger.debug(f"✅ WASHINGTON PARALLEL MATCH (page numbers close): {citation1} ↔ {citation2}")
                            return True
            
            # Check for case name similarity as a last resort
            def get_case_name(citation):
                if hasattr(citation, 'case_name'):
                    return getattr(citation, 'case_name')
                if hasattr(citation, 'canonical_name'):
                    return getattr(citation, 'canonical_name')
                if hasattr(citation, 'extracted_case_name'):
                    return getattr(citation, 'extracted_case_name')
                return None
                
            name1 = get_case_name(citation1)
            name2 = get_case_name(citation2)
            
            if name1 and name2 and name1 != 'N/A' and name2 != 'N/A':
                similarity = self._calculate_name_similarity(name1, name2)
                if similarity >= 0.7:  # 70% similarity threshold
                    if self.debug_mode:
                        logger.debug(f"✅ WASHINGTON PARALLEL MATCH (similar case names {similarity:.1%}): {name1} ↔ {name2}")
                    return True
            
            # If we get here, the citations don't appear to be parallel
            if self.debug_mode:
                logger.debug(f"❌ No match for: {citation1} ↔ {citation2}")
            return False
                
        return False
        
    def _are_citations_in_proximity(self, cite1: str, cite2: str, max_distance: int = 50) -> bool:
        """Check if two citations appear in close proximity in the text."""
        # This is a simplified version - in a real implementation, you'd need the full text
        # and positions of the citations. This is just a placeholder.
        # In a real implementation, you'd compare the character offsets.
        return True  # Placeholder - always return True for now
    
    def _extract_and_propagate_metadata(self, citations: List[Any], parallel_groups: List[List[Any]], text: str) -> List[Any]:
        """Extract metadata from clusters and propagate to all members."""
        enhanced_citations = []

        for group in parallel_groups:
            if not group:
                continue

            canonical_names: List[str] = []
            canonical_years: List[str] = []
            for citation in group:
                if isinstance(citation, dict):
                    verified = citation.get('verified', False)
                    canonical_name = citation.get('canonical_name')
                    canonical_date = citation.get('canonical_date')
                else:
                    verified = getattr(citation, 'verified', False)
                    canonical_name = getattr(citation, 'canonical_name', None)
                    canonical_date = getattr(citation, 'canonical_date', None)

                if verified and canonical_name and canonical_name != 'N/A':
                    canonical_names.append(canonical_name)
                if verified and canonical_date and canonical_date != 'N/A':
                    year_value = self._extract_year_value(canonical_date) or canonical_date
                    canonical_years.append(year_value)

            case_name = max(canonical_names, key=self._score_case_name) if canonical_names else self._select_best_case_name(group)
            if canonical_years:
                from collections import Counter
                case_year = Counter(canonical_years).most_common(1)[0][0]
            else:
                case_year = self._select_best_case_year(group)
            
            # CRITICAL LOGGING: Track what canonical names were found in this group
            if canonical_names:
                logger.info(f"[CLUSTER-CANONICAL] Group has {len(canonical_names)} verified canonical names: {canonical_names[:3]}... -> selected: '{case_name}'")

            # FIX: Clear truncated extracted_case_names and re-extract from document
            # This prevents truncated names from eyecite from being used anywhere
            for citation in group:
                extracted_name = getattr(citation, 'extracted_case_name', None)
                if extracted_name and self._is_truncated_name(extracted_name):
                    logger.info(f"[CLUSTERING-CLEAR-TRUNCATED] Clearing truncated name '{extracted_name}' - will re-extract")
                    
                    # Re-extract the case name from document text
                    try:
                        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
                        
                        # Get citation details for extraction
                        if isinstance(citation, dict):
                            citation_text = citation.get('citation', '')
                            start_idx = citation.get('start_index') or citation.get('start')
                            end_idx = citation.get('end_index') or citation.get('end')
                        else:
                            citation_text = getattr(citation, 'citation', '')
                            start_idx = getattr(citation, 'start_index', None) or getattr(citation, 'start', None)
                            end_idx = getattr(citation, 'end_index', None) or getattr(citation, 'end', None)
                        
                        # Call unified extraction with contamination filtering
                        result = extract_case_name_and_date_unified_master(
                            text=text,
                            citation=citation_text,
                            start_index=start_idx,
                            end_index=end_idx,
                            document_primary_case_name=getattr(self, 'document_primary_case_name', None)
                        )
                        
                        # Set the re-extracted name (result is a dict)
                        if result and result.get('case_name') and result.get('case_name') != 'N/A':
                            new_name = result.get('case_name')
                            logger.info(f"[CLUSTERING-REEXTRACTED] '{extracted_name}' -> '{new_name}' for {citation_text}")
                            if isinstance(citation, dict):
                                citation['extracted_case_name'] = new_name
                            else:
                                citation.extracted_case_name = new_name
                        else:
                            # Re-extraction failed, KEEP the truncated name (it's better than N/A)
                            # but mark it with a prefix to indicate it may be incomplete
                            logger.warning(f"[CLUSTERING-REEXTRACT-FAILED] Could not re-extract for {citation_text}, keeping truncated name: '{extracted_name}'")
                            if isinstance(citation, dict):
                                citation['extracted_case_name'] = extracted_name  # Keep original truncated name
                                citation['metadata'] = citation.get('metadata', {})
                                citation['metadata']['name_may_be_truncated'] = True
                            else:
                                citation.extracted_case_name = extracted_name  # Keep original truncated name
                                if not hasattr(citation, 'metadata'):
                                    citation.metadata = {}
                                citation.metadata['name_may_be_truncated'] = True
                    except Exception as e:
                        logger.error(f"[CLUSTERING-REEXTRACT-ERROR] {e}")
                        if isinstance(citation, dict):
                            citation['extracted_case_name'] = 'N/A'
                        else:
                            citation.extracted_case_name = 'N/A'
            
            if not case_name:
                for citation in group:
                    extracted_name = getattr(citation, 'extracted_case_name', None)
                    fallback_name = getattr(citation, 'canonical_name', None)
                    # FIX: Skip truncated names in fallback too
                    if extracted_name and extracted_name != 'N/A' and not self._is_truncated_name(extracted_name):
                        case_name = extracted_name
                        logger.info(f"[CLUSTERING-FALLBACK] Using non-truncated extracted name: '{extracted_name}'")
                        break
                    elif extracted_name and self._is_truncated_name(extracted_name):
                        logger.info(f"[CLUSTERING-FALLBACK-SKIP] Skipping truncated fallback name: '{extracted_name}'")
                    if fallback_name and fallback_name != 'N/A' and not self._is_truncated_name(fallback_name):
                        case_name = fallback_name
                        logger.info(f"[CLUSTERING-FALLBACK] Using non-truncated canonical name: '{fallback_name}'")
                        break

            if not case_year:
                for citation in group:
                    extracted_date = getattr(citation, 'extracted_date', None)
                    fallback_date = getattr(citation, 'canonical_date', None)
                    year_value = self._extract_year_value(extracted_date) if extracted_date else None
                    if year_value:
                        case_year = year_value
                        break
                    year_value = self._extract_year_value(fallback_date) if fallback_date else None
                    if year_value:
                        case_year = year_value
                        break

            # CRITICAL FIX: Standardize extracted names within cluster to prevent validation splits
            # Collect all extracted names and pick the best one (longest, most complete)
            extracted_names = []
            extracted_dates = []
            for citation in group:
                if isinstance(citation, dict):
                    extracted_name = citation.get('extracted_case_name')
                    extracted_date = citation.get('extracted_date')
                else:
                    extracted_name = getattr(citation, 'extracted_case_name', None)
                    extracted_date = getattr(citation, 'extracted_date', None)
                
                if extracted_name and extracted_name != 'N/A':
                    extracted_names.append(extracted_name)
                if extracted_date and extracted_date != 'N/A':
                    extracted_dates.append(extracted_date)
            
            # Pick best extracted name (longest, most complete)
            best_extracted_name = None
            if extracted_names:
                best_extracted_name = max(extracted_names, key=lambda n: (len(n), n))
                logger.error(f"🔧 [STANDARDIZE-CLUSTER] Group has {len(extracted_names)} extracted names → using best: '{best_extracted_name}'")
                if len(set(extracted_names)) > 1:
                    logger.error(f"   Variations: {list(set(extracted_names))}")
            
            # Pick best extracted year (most common)
            best_extracted_year = None
            if extracted_dates:
                from collections import Counter
                # Extract years from all dates
                years = [self._extract_year_value(d) for d in extracted_dates]
                years = [y for y in years if y]  # Remove None values
                if years:
                    best_extracted_year = Counter(years).most_common(1)[0][0]
                    logger.error(f"🔧 [STANDARDIZE-CLUSTER] Group has {len(years)} extracted years → using best: '{best_extracted_year}'")
            
            # PROPAGATE best extracted name and year to ALL citations in cluster
            # This ensures validation won't split the cluster due to extraction variations
            for citation in group:
                if best_extracted_name:
                    if isinstance(citation, dict):
                        old_name = citation.get('extracted_case_name')
                        citation['extracted_case_name'] = best_extracted_name
                        if old_name and old_name != best_extracted_name:
                            logger.error(f"   📝 Updated '{old_name}' → '{best_extracted_name}'")
                    else:
                        old_name = getattr(citation, 'extracted_case_name', None)
                        citation.extracted_case_name = best_extracted_name
                        if old_name and old_name != best_extracted_name:
                            logger.error(f"   📝 Updated '{old_name}' → '{best_extracted_name}'")
                
                if best_extracted_year:
                    if isinstance(citation, dict):
                        citation['extracted_date'] = best_extracted_year
                    else:
                        citation.extracted_date = best_extracted_year

            for citation in group:
                enhanced_citation = self._create_enhanced_citation(citation, case_name, case_year, group)
                enhanced_citations.append(enhanced_citation)

        return enhanced_citations

    def _create_enhanced_citation(self, citation: Any, case_name: Optional[str], case_year: Optional[str], group: List[Any]) -> Any:
        """Create an enhanced citation object with propagated metadata."""
        if hasattr(citation, '__dict__'):
            import copy
            enhanced = copy.copy(citation)
        elif isinstance(citation, dict):
            enhanced = citation.copy()
        else:
            enhanced = citation

        if isinstance(citation, dict):
            canonical_name = citation.get('canonical_name')
            canonical_date = citation.get('canonical_date')
            verified_flag = citation.get('verified', False)
            original_citation_text = citation.get('citation', str(citation))
        else:
            canonical_name = getattr(citation, 'canonical_name', None)
            canonical_date = getattr(citation, 'canonical_date', None)
            verified_flag = getattr(citation, 'verified', False)
            original_citation_text = getattr(citation, 'citation', str(citation))

        if verified_flag and canonical_name and canonical_name != 'N/A' and not case_name:
            case_name = canonical_name
        if verified_flag and canonical_date and canonical_date != 'N/A' and not case_year:
            case_year = self._extract_year_value(canonical_date) or canonical_date

        members = [getattr(c, 'citation', str(c)) for c in group]
        parallel = len(group) > 1

        if hasattr(enhanced, '__dict__'):
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
            enhanced['cluster_case_name'] = case_name
            enhanced['cluster_year'] = case_year
            enhanced['cluster_size'] = len(group)
            enhanced['is_in_cluster'] = parallel
            enhanced['cluster_members'] = members

            # FIX #29: CRITICAL DATA INTEGRITY FIX (dict path)
            # NEVER overwrite extracted_case_name or extracted_date with cluster-level data!
            # Each citation must preserve its OWN extracted data from the document.
            # REMOVED: Code that was contaminating extracted_case_name and extracted_date

            enhanced['is_parallel'] = parallel
            enhanced['parallel_citations'] = [member for member in members if member != original_citation_text]

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
            
            # Get the cluster members for this citation
            if hasattr(citation, 'cluster_members'):
                member_texts = getattr(citation, 'cluster_members', [])
            elif isinstance(citation, dict):
                member_texts = citation.get('cluster_members', [])
            else:
                member_texts = []
            
            # Find all citations that share the same cluster_members
            if len(member_texts) > 1:
                # This is a parallel group - find all citations with the same members
                group = []
                for other_citation in enhanced_citations:
                    other_id = id(other_citation)
                    if other_id in processed:
                        continue
                    
                    if hasattr(other_citation, 'cluster_members'):
                        other_members = set(getattr(other_citation, 'cluster_members', []))
                    elif isinstance(other_citation, dict):
                        other_members = set(other_citation.get('cluster_members', []))
                    else:
                        other_members = set()
                    
                    # If this citation shares the same cluster_members, it's in the same group
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
            
            # CRITICAL: Get ONLY extracted metadata from first citation in the group
            # Do NOT use cluster_case_name or cluster_year as they may be contaminated
            # with canonical data from verification!
            first_citation = citations[0]
            
            # Get ONLY extracted_case_name (from document)
            if hasattr(first_citation, 'extracted_case_name'):
                extracted_name = first_citation.extracted_case_name
            elif hasattr(first_citation, 'get'):
                extracted_name = first_citation.get('extracted_case_name', None)
            else:
                extracted_name = None
            
            # Get ONLY extracted_date (from document)
            if hasattr(first_citation, 'extracted_date'):
                extracted_date = first_citation.extracted_date
            elif hasattr(first_citation, 'get'):
                extracted_date = first_citation.get('extracted_date', None)
            else:
                extracted_date = None
            
            # Create cluster key using ONLY extracted data
            if extracted_name and extracted_name != 'N/A':
                normalized_name = self._normalize_case_name(extracted_name)
            else:
                normalized_name = 'unknown'
            
            if extracted_date and extracted_date != 'N/A':
                year_match = re.search(r'(19|20)\d{2}', str(extracted_date))
                normalized_year = year_match.group(0) if year_match else str(extracted_date)[:4]
            else:
                normalized_year = 'unknown'
            
            cluster_key = f"{normalized_name}_{normalized_year}"
            
            # CRITICAL FIX: Deduplicate citations within the cluster
            # Same citation can appear multiple times in document, leading to duplicates in cluster
            deduplicated_citations = self._deduplicate_cluster_citations(citations)
            
            cluster = {
                'cluster_id': f"cluster_{i+1}",
                'cluster_key': cluster_key,
                'citations': deduplicated_citations,
                'size': len(deduplicated_citations),
                # FIX #17: Store ONLY extracted data, NEVER canonical
                'case_name': extracted_name,  # Pure extracted from document
                'case_year': extracted_date,  # Pure extracted from document
                'confidence': self._calculate_cluster_confidence(citations),
                'metadata': {
                    'cluster_type': 'proximity_based',  # Clustering by proximity in document (NOT by metadata!)
                    'created_by': 'unified_master',
                    'cluster_key': cluster_key,
                    'cluster_members_preserved': True,  # Indicates we preserved parallel groups from Step 1
                    'data_source': 'extracted_only'  # Flag indicating pure extracted data
                }
            }
            final_clusters.append(cluster)
        
        return final_clusters
    
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
        pattern = r'(\d+)\s+([A-Z][\w\.]+(?:\s+[\w\.]+)*?)\s+(\d+)'
        match = re.search(pattern, citation_text)
        
        if match:
            return {
                'volume': match.group(1),
                'reporter': match.group(2).strip(),
                'page': match.group(3)
            }
        
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
            if hasattr(citation, 'citation'):
                cit_text = citation.citation
            elif hasattr(citation, 'get'):
                cit_text = citation.get('citation', '')
            else:
                continue
            
            if not cit_text:
                continue
            
            # Check if we've seen this citation before
            if cit_text in seen:
                existing = seen[cit_text]
                
                # Prefer verified over unverified
                cit_verified = getattr(citation, 'verified', False) if hasattr(citation, 'verified') else citation.get('verified', False) if hasattr(citation, 'get') else False
                existing_verified = getattr(existing, 'verified', False) if hasattr(existing, 'verified') else existing.get('verified', False) if hasattr(existing, 'get') else False
                
                # Prefer citations with extracted case names
                cit_name = getattr(citation, 'extracted_case_name', 'N/A') if hasattr(citation, 'extracted_case_name') else citation.get('extracted_case_name', 'N/A') if hasattr(citation, 'get') else 'N/A'
                existing_name = getattr(existing, 'extracted_case_name', 'N/A') if hasattr(existing, 'extracted_case_name') else existing.get('extracted_case_name', 'N/A') if hasattr(existing, 'get') else 'N/A'
                
                # Quality score: verified (2 points) + has name (1 point)
                cit_score = (2 if cit_verified else 0) + (1 if cit_name and cit_name != 'N/A' else 0)
                existing_score = (2 if existing_verified else 0) + (1 if existing_name and existing_name != 'N/A' else 0)
                
                # Keep the better quality citation
                if cit_score > existing_score:
                    logger.debug(f"[DEDUP_CLUSTER] Replacing '{cit_text}' (score {cit_score} > {existing_score})")
                    seen[cit_text] = citation
                else:
                    logger.debug(f"[DEDUP_CLUSTER] Keeping existing '{cit_text}' (score {existing_score} >= {cit_score})")
            else:
                seen[cit_text] = citation
        
        deduplicated = list(seen.values())
        
        if len(deduplicated) < len(citations):
            logger.info(f"[DEDUP_CLUSTER] Removed {len(citations) - len(deduplicated)} duplicate citations within cluster ({len(citations)} → {len(deduplicated)})")
        
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
        cit_name = getattr(citation, 'extracted_case_name', None)
        cit_year = getattr(citation, 'extracted_date', None)
        
        # Extract year from date if needed
        def extract_year(date_str):
            if not date_str or date_str == 'N/A':
                return None
            year_match = re.search(r'(19|20)\d{2}', str(date_str))
            return int(year_match.group(0)) if year_match else None
        
        cit_year_int = extract_year(cit_year)
        
        # Check against first citation in cluster - USE ONLY EXTRACTED DATA
        first_cit = existing_citations[0]
        first_name = getattr(first_cit, 'extracted_case_name', None)
        first_year = getattr(first_cit, 'extracted_date', None)
        
        first_year_int = extract_year(first_year)
        
        # VALIDATION 1: Year consistency check (EXTRACTED DATA ONLY)
        # If both have years, they must be within 2 years of each other
        if cit_year_int and first_year_int:
            year_diff = abs(cit_year_int - first_year_int)
            if year_diff > 2:
                logger.warning(f"MASTER_CLUSTER: Extracted year mismatch: {cit_year_int} vs {first_year_int} (diff: {year_diff} years)")
                return False
        
        # VALIDATION 2: Case name similarity (EXTRACTED DATA ONLY)
        # If both have case names, they must be similar
        if cit_name and cit_name != 'N/A' and first_name and first_name != 'N/A':
            similarity = self._calculate_name_similarity(cit_name, first_name)
            if similarity < self.case_name_similarity_threshold:
                logger.warning(f"MASTER_CLUSTER: Extracted case name mismatch: '{cit_name}' vs '{first_name}' (similarity: {similarity:.2f})")
                return False
        
        # P5 FIX: VALIDATION 3: Same reporter + different volumes = DIFFERENT CASES
        # This prevents false clustering like "506 U.S." and "546 U.S." being grouped
        # Same case can have DIFFERENT reporters (e.g., "100 F.3d 1" and "100 S.Ct. 1")
        # but CANNOT have same reporter with different volumes
        cit_text = getattr(citation, 'citation', None) or getattr(citation, 'text', '')
        first_text = getattr(first_cit, 'citation', None) or getattr(first_cit, 'text', '')
        
        if cit_text and first_text:
            # Extract reporter and volume from both citations
            cit_parsed = self._parse_citation_components(cit_text)
            first_parsed = self._parse_citation_components(first_text)
            
            if cit_parsed and first_parsed:
                cit_reporter = cit_parsed.get('reporter', '')
                cit_volume = cit_parsed.get('volume', '')
                first_reporter = first_parsed.get('reporter', '')
                first_volume = first_parsed.get('volume', '')
                
                # If both have same reporter but different volumes, they are DIFFERENT cases
                if cit_reporter and first_reporter and cit_reporter == first_reporter:
                    if cit_volume and first_volume and cit_volume != first_volume:
                        logger.warning(f"P5_FIX: Preventing false cluster - same reporter '{cit_reporter}' but different volumes: {cit_volume} vs {first_volume}")
                        return False
        
        # FIX #17: Removed all canonical data validation
        # Clustering should be based ONLY on extracted data (from the document),
        # NOT on canonical data (from the API)
        
        return True
    
    def _apply_verification_to_clusters(self, clusters: List[Dict[str, Any]]) -> None:
        """Apply verification to clusters if enabled - OPTIMIZED WITH BATCH API."""
        logger.error(f"🔥 [VERIFY-DEBUG] _apply_verification_to_clusters called: enable_verification={self.enable_verification}, clusters={len(clusters)}")
        if not self.enable_verification:
            logger.error(f"🔥 [VERIFY-DEBUG] Verification DISABLED - returning early")
            return
        
        logger.error(f"🔥 [VERIFY-DEBUG] Verification ENABLED - proceeding with {len(clusters)} clusters")
        
        try:
            # OPTIMIZATION: Use batch verification instead of one-by-one
            # Collect all unique citations across all clusters
            all_citations = []
            citation_to_cluster_map = {}  # Map citation text -> (cluster_idx, citation_idx)
            
            for cluster_idx, cluster in enumerate(clusters):
                citations = cluster.get('citations', [])
                if not citations:
                    continue
                
                for cit_idx, citation_obj in enumerate(citations):
                    citation_text = getattr(citation_obj, 'citation', str(citation_obj))
                    case_name = getattr(citation_obj, 'extracted_case_name', None)
                    case_date = getattr(citation_obj, 'extracted_date', None)
                    
                    # Skip citations that already have errors
                    if hasattr(citation_obj, 'error') and citation_obj.error:
                        continue
                    
                    all_citations.append({
                        'citation': citation_text,
                        'case_name': case_name,
                        'case_date': case_date,
                        'cluster_idx': cluster_idx,
                        'cit_idx': cit_idx
                    })
                    citation_to_cluster_map[citation_text] = (cluster_idx, cit_idx)
            
            if not all_citations:
                logger.info("No citations to verify")
                return
            
            logger.info(f"🚀 BATCH VERIFICATION: Verifying {len(all_citations)} citations in single batch API call")
            
            # Use batch verification API
            from src.unified_verification_master import get_master_verifier
            verifier = get_master_verifier()
            
            # Prepare batch data
            citation_texts = [c['citation'] for c in all_citations]
            case_names = [c['case_name'] for c in all_citations]
            case_dates = [c['case_date'] for c in all_citations]
            
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
            
            logger.info(f"✅ BATCH VERIFICATION: Received {len(batch_results)} results")
            
            # DEBUG: Log verification success rate
            verified_count = sum(1 for r in batch_results if r.verified)
            logger.error(f"[BATCH-VERIFY-DEBUG] Verified: {verified_count}/{len(batch_results)}")
            for r in batch_results[:5]:
                logger.error(f"  - {r.citation}: verified={r.verified}, source={r.source if r.verified else r.error}")
            
            # Apply results back to citations
            for idx, (cit_info, result) in enumerate(zip(all_citations, batch_results)):
                cluster_idx = cit_info['cluster_idx']
                cit_idx = cit_info['cit_idx']
                cluster = clusters[cluster_idx]
                citations = cluster.get('citations', [])
                citation_obj = citations[cit_idx]
                citation_text = cit_info['citation']
                
                if result.verified:
                    # VERIFIED: Apply canonical data
                    logger.error(f"🔧 [APPLY-VERIFICATION] Citation: {citation_text} - VERIFIED")
                    logger.error(f"   📝 result.canonical_name = {result.canonical_name}")
                    logger.error(f"   📝 result.canonical_date = {result.canonical_date}")
                    
                    if hasattr(citation_obj, '__dict__'):
                        citation_obj.verified = True
                        citation_obj.canonical_name = result.canonical_name
                        citation_obj.canonical_date = result.canonical_date
                        citation_obj.canonical_url = result.canonical_url
                        citation_obj.verification_source = result.source
                        logger.error(f"   ✅ AFTER (object): verified=True, canonical_name = {citation_obj.canonical_name}")
                    elif isinstance(citation_obj, dict):
                        citation_obj['verified'] = True
                        citation_obj['canonical_name'] = result.canonical_name
                        citation_obj['canonical_date'] = result.canonical_date
                        citation_obj['canonical_url'] = result.canonical_url
                        citation_obj['verification_source'] = result.source
                        logger.error(f"   ✅ AFTER (dict): verified=True, canonical_name = {citation_obj['canonical_name']}")
                else:
                    # UNVERIFIED: Mark as unverified, store error
                    logger.error(f"❌ [APPLY-VERIFICATION] Citation: {citation_text} - UNVERIFIED")
                    logger.error(f"   ⚠️ Error: {result.error}")
                    
                    if hasattr(citation_obj, '__dict__'):
                        citation_obj.verified = False
                        citation_obj.verification_error = result.error
                        citation_obj.canonical_name = None
                        citation_obj.canonical_date = None
                        logger.error(f"   ❌ AFTER (object): verified=False, will need true_by_parallel")
                    elif isinstance(citation_obj, dict):
                        citation_obj['verified'] = False
                        citation_obj['verification_error'] = result.error
                        citation_obj['canonical_name'] = None
                        citation_obj['canonical_date'] = None
                        logger.error(f"   ❌ AFTER (dict): verified=False, will need true_by_parallel")
        
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
            citations = cluster.get('citations', [])
            citation_texts = []
            
            for citation in citations:
                citation_text = getattr(citation, 'citation', str(citation))
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
            citations = cluster.get('citations', [])
            
            if len(citations) <= 1:
                # Single citation clusters are always valid
                validated_clusters.append(cluster)
                continue
            
            # CRITICAL FIX: Check proximity FIRST - if citations are close together, TRUST the clustering!
            # Parallel citations are typically within 50-200 characters of each other
            positions = []
            for citation in citations:
                pos = None
                if hasattr(citation, 'start_index'):
                    pos = citation.start_index
                elif isinstance(citation, dict):
                    pos = citation.get('start_index')
                if pos is not None:
                    positions.append(pos)
            
            # If citations are in close proximity (<= 200 chars), they're LIKELY parallel
            # BUT still check canonical names to prevent grouping different cases!
            if len(positions) >= 2:
                sorted_positions = sorted(positions)
                max_distance = sorted_positions[-1] - sorted_positions[0]
                if max_distance <= 200:
                    # Proximity suggests parallel, but verify canonical names match
                    canonical_names = set()
                    for citation in citations:
                        if hasattr(citation, 'canonical_name'):
                            canon = citation.canonical_name
                        elif isinstance(citation, dict):
                            canon = citation.get('canonical_name')
                        else:
                            canon = None
                        
                        if canon and canon != 'N/A':
                            canonical_names.add(canon)
                    
                    # If we have multiple different canonical names, these are DIFFERENT cases!
                    if len(canonical_names) > 1:
                        logger.error(
                            f"🚫 [PROXIMITY-OVERRIDE-FAILED] Citations within {max_distance} chars BUT have different canonical names: {canonical_names}. "
                            f"These are DIFFERENT cases incorrectly grouped by proximity. Applying P5_FIX validation..."
                        )
                        # Continue to P5_FIX validation below
                    else:
                        logger.error(f"✅ [PROXIMITY-OVERRIDE] Cluster with {len(citations)} citations within {max_distance} chars and matching canonical names - definitely parallel")
                        validated_clusters.append(cluster)
                        continue
                else:
                    logger.error(f"⚠️ [PROXIMITY-CHECK] Cluster with {len(citations)} citations spread over {max_distance} chars - APPLYING P5_FIX validation")
            
            # P5 FIX ENHANCED: Comprehensive false clustering detection
            # Only run this for non-proximate citations
            # Collect citation metadata for validation
            citation_metadata = []
            reporter_volumes = {}  # {reporter: set of volumes}
            
            for citation in citations:
                if hasattr(citation, 'citation'):
                    cit_text = citation.citation
                elif isinstance(citation, dict):
                    cit_text = citation.get('citation', '') or citation.get('text', '')
                else:
                    cit_text = str(citation)
                
                parsed = self._parse_citation_components(cit_text)
                
                # Extract year from citation object
                year = None
                if hasattr(citation, 'extracted_date'):
                    year = citation.extracted_date
                elif isinstance(citation, dict):
                    year = citation.get('extracted_date')
                
                if parsed:
                    reporter = parsed.get('reporter')
                    volume = parsed.get('volume')
                    
                    citation_metadata.append({
                        'citation': cit_text,
                        'reporter': reporter,
                        'volume': volume,
                        'year': year
                    })
                    
                    if reporter and volume:
                        if reporter not in reporter_volumes:
                            reporter_volumes[reporter] = set()
                        reporter_volumes[reporter].add(volume)
            
            # P5 VALIDATION 1: Check for incompatible reporter types
            # Federal vs State reporters should NEVER cluster
            # Supreme Court vs Circuit/District should NEVER cluster (different courts)
            supreme_court_reporters = set(['U.S.', 'S.Ct.', 'L.Ed.', 'L.Ed.2d'])
            circuit_reporters = set(['F.2d', 'F.3d', 'F.4th'])
            district_reporters = set(['F.Supp.', 'F.Supp.2d', 'F.Supp.3d'])
            state_reporters = set(['P.2d', 'P.3d', 'A.2d', 'A.3d', 'N.E.2d', 'N.E.3d', 'N.W.2d', 'S.E.2d', 'S.W.2d', 'S.W.3d', 'So.2d', 'So.3d'])
            
            has_supreme = any(meta['reporter'] in supreme_court_reporters for meta in citation_metadata if meta.get('reporter'))
            has_circuit = any(meta['reporter'] in circuit_reporters for meta in citation_metadata if meta.get('reporter'))
            has_district = any(meta['reporter'] in district_reporters for meta in citation_metadata if meta.get('reporter'))
            has_state = any(meta['reporter'] in state_reporters for meta in citation_metadata if meta.get('reporter'))
            
            # Federal vs State = NEVER parallel
            if (has_supreme or has_circuit or has_district) and has_state:
                logger.error(
                    f"🚫 P5_FIX: FALSE CLUSTERING DETECTED in cluster '{cluster.get('case_name', 'N/A')}' - "
                    f"Mixed federal and state reporters (cannot be parallel citations). "
                    f"Splitting cluster..."
                )
                split_clusters = self._split_cluster_by_reporter_volume(cluster, citations)
                validated_clusters.extend(split_clusters)
                continue
            
            # Supreme Court vs Circuit/District = NEVER parallel (different courts)
            if has_supreme and (has_circuit or has_district):
                logger.error(
                    f"🚫 P5_FIX: FALSE CLUSTERING DETECTED in cluster '{cluster.get('case_name', 'N/A')}' - "
                    f"Mixed Supreme Court and Circuit/District reporters (different courts, cannot be parallel). "
                    f"Splitting cluster..."
                )
                split_clusters = self._split_cluster_by_reporter_volume(cluster, citations)
                validated_clusters.extend(split_clusters)
                continue
            
            # P5 VALIDATION 2: Check for large year differences
            # Citations from different years (e.g., 1999 vs 2019) are unlikely to be parallel
            years = [meta['year'] for meta in citation_metadata if meta.get('year')]
            if len(years) >= 2:
                try:
                    year_ints = [int(str(y)[:4]) for y in years if y]  # Extract first 4 digits
                    if year_ints:
                        year_range = max(year_ints) - min(year_ints)
                        if year_range > 2:  # Allow 2 years difference for delayed publication
                            logger.error(
                                f"🚫 P5_FIX: FALSE CLUSTERING DETECTED in cluster '{cluster.get('case_name', 'N/A')}' - "
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
                        f"🚫 P5_FIX: FALSE CLUSTERING DETECTED in cluster '{cluster.get('case_name', 'N/A')}' - "
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
                if hasattr(citation, 'start_index'):
                    pos = citation.start_index
                elif isinstance(citation, dict):
                    pos = citation.get('start_index', 0)
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
                        case_name = getattr(citation, 'extracted_case_name', None)
                        if case_name and case_name not in ('N/A', 'Unknown', None):
                            case_names.append(case_name.lower().strip())
                    
                    # If all citations have the same case name, they're parallel citations - DON'T split
                    unique_case_names = set(case_names) if case_names else set()
                    if len(unique_case_names) == 1 and len(citations) <= 5:  # Parallel citations typically 2-4 cites
                        logger.info(
                            f"✅ CLUSTER_VALIDATION: Keeping parallel citations together despite span={span}. "
                            f"All {len(citations)} citations reference: {list(unique_case_names)[0]}"
                        )
                        validated_clusters.append(cluster)
                        continue
                    
                    # Not parallel citations - proceed with split
                    logger.warning(
                        f"⚠️ CLUSTER_VALIDATION: Suspicious cluster with span={span} chars "
                        f"(threshold={max_allowed_span}). This may indicate incorrect clustering. "
                        f"Cluster has {len(citations)} citations spanning {span} characters."
                    )
                    
                    # Log the citations for debugging
                    for i, citation in enumerate(citations):
                        citation_text = getattr(citation, 'citation', str(citation))[:60]
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
        self, 
        original_cluster: Dict[str, Any], 
        citations: List[Any], 
        positions: List[int]
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
                'cluster_id': f"{original_cluster.get('cluster_id', 'unknown')}_split{group_idx+1}",
                'citations': group_citations,
                'size': len(group_citations),
                'case_name': original_cluster.get('case_name', 'N/A'),
                'case_year': original_cluster.get('case_year', 'N/A'),
                'confidence': original_cluster.get('confidence', 0.0) * 0.8,  # Lower confidence for split clusters
                'verification_status': original_cluster.get('verification_status', 'not_verified'),
                'metadata': {
                    **original_cluster.get('metadata', {}),
                    'split_from': original_cluster.get('cluster_id', 'unknown'),
                    'split_reason': 'proximity_validation'
                }
            }
            
            logger.info(
                f"✂️ CLUSTER_VALIDATION: Split cluster {original_cluster.get('cluster_id')} "
                f"into subcluster {new_cluster['cluster_id']} with {len(group_citations)} citations"
            )
            
            new_clusters.append(new_cluster)
        
        return new_clusters
    
    def _split_cluster_by_reporter_volume(
        self,
        original_cluster: Dict[str, Any],
        citations: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        P5 FIX: Split a cluster that has same reporter + different volumes (false clustering).
        
        Each unique reporter+volume combination becomes its own cluster.
        Example: ["506 U.S. 224", "546 U.S. 345"] would be split into 2 clusters.
        """
        # Group citations by reporter+volume
        groups = {}  # {(reporter, volume): [citations]}
        
        for citation in citations:
            if hasattr(citation, 'citation'):
                cit_text = citation.citation
            elif isinstance(citation, dict):
                cit_text = citation.get('citation', '') or citation.get('text', '')
            else:
                cit_text = str(citation)
            
            parsed = self._parse_citation_components(cit_text)
            if parsed:
                reporter = parsed.get('reporter')
                volume = parsed.get('volume')
                key = (reporter, volume)
            else:
                # Unparseable citation - put in its own group
                key = ('unknown', cit_text)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(citation)
        
        # Create new clusters from groups
        new_clusters = []
        for group_idx, ((reporter, volume), group_citations) in enumerate(groups.items()):
            new_cluster = {
                'cluster_id': f"{original_cluster.get('cluster_id', 'unknown')}_vol{group_idx+1}",
                'citations': group_citations,
                'size': len(group_citations),
                'case_name': original_cluster.get('case_name', 'N/A'),
                'case_year': original_cluster.get('case_year', 'N/A'),
                'confidence': original_cluster.get('confidence', 0.0) * 0.7,  # Lower confidence for split clusters
                'verification_status': original_cluster.get('verification_status', 'not_verified'),
                'metadata': {
                    **original_cluster.get('metadata', {}),
                    'split_from': original_cluster.get('cluster_id', 'unknown'),
                    'split_reason': 'false_clustering_same_reporter_different_volumes',
                    'reporter': reporter,
                    'volume': volume
                }
            }
            
            logger.info(
                f"✂️ P5_FIX: Split false cluster '{original_cluster.get('case_name', 'N/A')}' - "
                f"created subcluster for {reporter} vol.{volume} with {len(group_citations)} citation(s)"
            )
            
            new_clusters.append(new_cluster)
        
        return new_clusters
    
    def _format_clusters_for_output(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format clusters for final output and update citation objects with cluster IDs."""
        formatted_clusters = []
        
        for cluster in clusters:
            cluster_id = cluster.get('cluster_id', 'unknown')
            citations = cluster.get('citations', [])
            
            best_name = cluster.get('case_name', 'N/A')
            if best_name in (None, '', 'N/A', 'Unknown', 'Unknown Case'):
                inferred_name = self._select_best_case_name(citations)
                if inferred_name:
                    best_name = inferred_name
            
            best_year = cluster.get('case_year', 'N/A')
            if best_year in (None, '', 'N/A', 'Unknown'):
                inferred_year = self._select_best_case_year(citations)
                if inferred_year:
                    best_year = inferred_year
            
            # CRITICAL FIX: Propagate canonical data to parallel citations
            # Find the first verified citation with canonical data
            best_verified = None
            for cit in citations:
                is_verified = getattr(cit, 'verified', False)
                has_canonical = getattr(cit, 'canonical_name', None) is not None
                logger.info(f"🔍 CLUSTER_FORMAT: Checking citation {getattr(cit, 'citation', str(cit))[:50]} - verified={is_verified}, has_canonical={has_canonical}")
                if is_verified and has_canonical:
                    best_verified = cit
                    logger.info(f"✅ CLUSTER_FORMAT: Found best_verified citation: {best_verified.citation} with canonical_name={best_verified.canonical_name}")
                    break
            
            # Propagate canonical data to unverified parallel citations
            # IMPORTANT: Keep verified=False, only set true_by_parallel=True
            if best_verified and len(citations) > 1:
                for cit in citations:
                    is_verified = getattr(cit, 'verified', False)
                    if not is_verified:
                        # Mark as true_by_parallel but keep verified=False
                        # Each citation is independently verified
                        if hasattr(cit, '__dict__'):
                            cit.true_by_parallel = True
                            cit.canonical_name = getattr(best_verified, 'canonical_name', None)
                            cit.canonical_date = getattr(best_verified, 'canonical_date', None)
                            cit.canonical_url = getattr(best_verified, 'canonical_url', None)
                            # Don't change verified status - keep it False
                        elif isinstance(cit, dict):
                            cit['true_by_parallel'] = True
                            cit['canonical_name'] = getattr(best_verified, 'canonical_name', None)
                            cit['canonical_date'] = getattr(best_verified, 'canonical_date', None)
                            cit['canonical_url'] = getattr(best_verified, 'canonical_url', None)
                            # Don't change verified status - keep it False
                        logger.info(f"✅ Propagated canonical data (true_by_parallel) to parallel: {getattr(cit, 'citation', str(cit))}")
            
            # CRITICAL FIX: Extract cluster-level canonical data from verified citations
            cluster_canonical_name = None
            cluster_canonical_date = None
            cluster_verification_source = None
            
            # Find first verified citation with canonical data
            if best_verified:
                cluster_canonical_name = getattr(best_verified, 'canonical_name', None)
                cluster_canonical_date = getattr(best_verified, 'canonical_date', None)
                cluster_verification_source = getattr(best_verified, 'verification_source', getattr(best_verified, 'source', None))
                logger.info(f"📋 CLUSTER_FORMAT: Setting cluster canonical data - name={cluster_canonical_name}, date={cluster_canonical_date}, source={cluster_verification_source}")
            else:
                logger.warning(f"⚠️ CLUSTER_FORMAT: No best_verified found for cluster {cluster_id} with {len(citations)} citations")
            
            formatted_cluster = {
                'cluster_id': cluster_id,
                'cluster_case_name': best_name or 'N/A',
                'cluster_year': best_year or 'N/A',
                'cluster_size': cluster.get('size', 0),
                'citations': citations,
                'confidence': cluster.get('confidence', 0.0),
                'verification_status': 'verified' if best_verified else 'not_verified',
                'verification_source': cluster_verification_source,
                'canonical_name': cluster_canonical_name,
                'canonical_date': cluster_canonical_date,
                'metadata': cluster.get('metadata', {}),
                'cluster_members': []
            }
            
            for citation in citations:
                citation_text = getattr(citation, 'citation', str(citation))
                formatted_cluster['cluster_members'].append(citation_text)
                
                if hasattr(citation, 'cluster_id'):
                    citation.cluster_id = cluster_id
                if hasattr(citation, 'is_cluster'):
                    citation.is_cluster = len(citations) > 1
                if hasattr(citation, 'cluster_case_name'):
                    citation.cluster_case_name = best_name or 'N/A'
                if hasattr(citation, 'cluster_year'):
                    citation.cluster_year = best_year or 'N/A'
                
                if isinstance(citation, dict):
                    citation['cluster_case_name'] = best_name or 'N/A'
                    citation['cluster_year'] = best_year or 'N/A'
            
            formatted_clusters.append(formatted_cluster)
        
        return formatted_clusters
    
    def _normalize_case_name(self, case_name: str) -> str:
        """Normalize case name for clustering."""
        if not case_name:
            return 'unknown'
        
        # Convert to lowercase and remove extra whitespace
        normalized = case_name.lower().strip()
        
        # Remove common variations
        normalized = re.sub(r'\s+v\.\s+', ' v ', normalized)
        normalized = re.sub(r'\s+vs\.\s+', ' v ', normalized)
        normalized = re.sub(r'\s+vs\s+', ' v ', normalized)
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
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
            citations = cluster.get('citations', [])
            if len(citations) <= 1:
                # Single citation clusters don't need validation
                validated_clusters.append(cluster)
                continue
            
            # FIX #47: Check if citations are in close proximity (likely parallel)
            positions = []
            for citation in citations:
                pos = None
                if hasattr(citation, 'start_index'):
                    pos = citation.start_index
                elif isinstance(citation, dict):
                    pos = citation.get('start_index')
                if pos is not None:
                    positions.append(pos)
            
            # DIAGNOSTIC: Check if positions were found
            if len(citations) > 1 and len(positions) == 0:
                logger.error(f"🚨 [PROXIMITY-BUG] Cluster has {len(citations)} citations but NO positions found!")
                logger.error(f"   First citation type: {type(citations[0])}")
                if hasattr(citations[0], '__dict__'):
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
                logger.error(f"🔍 [PROXIMITY-CHECK] {len(citations)} citations, distance={max_distance} chars, is_close={is_close_proximity}")
            elif len(citations) > 1:
                logger.error(f"⚠️ [PROXIMITY-CHECK] {len(citations)} citations but only {len(positions)} positions - CANNOT determine proximity!")
            
            # FIX #48: Group citations by EXTRACTED case name + year (from document)
            extracted_groups = {}
            no_extraction_citations = []
            
            for citation in citations:
                # FIX #48: Get EXTRACTED name and date (from document)
                extracted_name = None
                extracted_date = None
                
                if hasattr(citation, 'extracted_case_name'):
                    extracted_name = citation.extracted_case_name
                    extracted_date = getattr(citation, 'extracted_date', None)
                elif isinstance(citation, dict):
                    extracted_name = citation.get('extracted_case_name')
                    extracted_date = citation.get('extracted_date')
                
                # Skip citations without extraction data
                if not extracted_name or extracted_name == 'N/A':
                    no_extraction_citations.append(citation)
                    continue
                
                # Normalize the extracted name
                normalized_name = self._normalize_case_name(extracted_name)
                
                # Extract year from extracted date
                year = None
                if extracted_date:
                    year_match = re.search(r'(19|20)\d{2}', str(extracted_date))
                    if year_match:
                        year = year_match.group(0)
                
                group_key = f"{normalized_name}_{year}" if year else normalized_name
                
                if group_key not in extracted_groups:
                    extracted_groups[group_key] = []
                extracted_groups[group_key].append(citation)
            
            # FIX #48: If all citations have the same extracted data, keep the cluster
            if len(extracted_groups) <= 1:
                logger.debug(f"✅ [FIX #48] Cluster validation: {len(extracted_groups)} extracted group(s) - keeping intact")
                validated_clusters.append(cluster)
                continue
            
            # FIX #49: If citations are in CLOSE proximity, ALWAYS keep them together!
            # Proximity is the PRIMARY signal for parallel citations.
            # Extracted data is SECONDARY (can have extraction errors).
            if is_close_proximity:
                logger.info(f"✅ [FIX #49] PROXIMITY OVERRIDE - Keeping cluster intact despite {len(extracted_groups)} different extracted names")
                logger.info(f"   Reason: Citations within 200 chars are likely parallel (extraction may have failed)")
                logger.info(f"   Extracted groups: {list(extracted_groups.keys())}")
                validated_clusters.append(cluster)
                continue
            
            # FIX #48: Check if we should trust similarity over minor name variations (for non-proximate citations)
            if len(extracted_groups) == 2:
                # Check if the extracted names are similar (slight variations vs completely different)
                group_keys = list(extracted_groups.keys())
                name1 = group_keys[0].split('_')[0] if '_' in group_keys[0] else group_keys[0]
                name2 = group_keys[1].split('_')[0] if '_' in group_keys[1] else group_keys[1]
                
                # Extract first word from each name (usually most important)
                words1 = name1.lower().split()
                words2 = name2.lower().split()
                
                first_word_match = (words1 and words2 and words1[0] == words2[0])
                
                # Check for year mismatch (strong signal they're different cases)
                years = [key.split('_')[-1] for key in group_keys if '_' in key]
                year_mismatch = len(years) == 2 and years[0] != years[1] and abs(int(years[0]) - int(years[1])) > 2
                
                if first_word_match and not year_mismatch:
                    # Likely the same case with slight name variations - DON'T split
                    logger.info(f"✅ [FIX #48] Keeping cluster intact - close proximity + similar EXTRACTED names")
                    logger.info(f"   Extracted groups: {group_keys}")
                    validated_clusters.append(cluster)
                    continue
                elif year_mismatch:
                    logger.warning(f"⚠️  [FIX #48] EXTRACTED year mismatch detected ({years}) - will split despite proximity")
            
            # SPLIT THE CLUSTER - citations have different EXTRACTED data!
            logger.warning(f"🔴 FIX #48: Splitting cluster - {len(extracted_groups)} different EXTRACTED cases detected (proximity={is_close_proximity})")
            
            for group_key, group_citations in extracted_groups.items():
                logger.warning(f"   Sub-cluster (extracted): {group_key} with {len(group_citations)} citations")
                
                # Create a new cluster for this extracted group
                new_cluster = {
                    'cluster_id': f"{cluster['cluster_id']}_split_{len(validated_clusters)}",
                    'cluster_key': cluster.get('cluster_key', ''),
                    'citations': group_citations,
                    'size': len(group_citations),
                    'case_name': cluster.get('case_name'),
                    'case_year': cluster.get('case_year'),
                    'confidence': self._calculate_cluster_confidence(group_citations),
                    'metadata': {
                        **cluster.get('metadata', {}),
                        'split_from': cluster['cluster_id'],
                        'split_reason': 'extracted_data_mismatch',
                        'extracted_group_key': group_key
                    }
                }
                validated_clusters.append(new_cluster)
            
            # Add citations without extraction as their own cluster if any exist
            if no_extraction_citations:
                logger.warning(f"   No-extraction sub-cluster: {len(no_extraction_citations)} citations")
                new_cluster = {
                    'cluster_id': f"{cluster['cluster_id']}_no_extraction",
                    'cluster_key': cluster.get('cluster_key', ''),
                    'citations': no_extraction_citations,
                    'size': len(no_extraction_citations),
                    'case_name': cluster.get('case_name'),
                    'case_year': cluster.get('case_year'),
                    'confidence': self._calculate_cluster_confidence(no_extraction_citations),
                    'metadata': {
                        **cluster.get('metadata', {}),
                        'split_from': cluster['cluster_id'],
                        'split_reason': 'no_extraction_data'
                    }
                }
                validated_clusters.append(new_cluster)
        
        logger.info(f"🔍 FIX #48: EXTRACTED data validation: {len(clusters)} input clusters → {len(validated_clusters)} output clusters")
        return validated_clusters
    
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
        case_number_match = re.search(r'No\.\s+\d{2,4}-\d{3,5}', header, re.IGNORECASE)
        if case_number_match:
            # Look backwards from case number for case name
            before_case_num = header[:case_number_match.start()]
            
            # FIX P4: Look for "Plaintiffs" or "Plaintiff" marker to find all plaintiffs
            # This handles multi-plaintiff cases where multiple parties are listed before "v."
            plaintiffs_marker = re.search(r'Plaintiffs?\s*[-–]\s*Appellants?', before_case_num, re.IGNORECASE)
            if plaintiffs_marker:
                # Extract from start to plaintiffs marker
                plaintiff_section = before_case_num[:plaintiffs_marker.start()].strip()
                # Take last 500 chars to get the plaintiff names (handles long descriptions)
                plaintiff_section = plaintiff_section[-500:]
                
                # Find first complete party name (handles "COMPANY NAME, a corp; PERSON NAME, individual")
                # Look for pattern: ALL CAPS NAME followed by comma or semicolon
                first_party = re.search(r'([A-Z][A-Z\s&\.,\'-]{8,100?})(?:,|\;)', plaintiff_section)
                if first_party:
                    plaintiff_name = first_party.group(1).strip()
                    # Clean up trailing punctuation and descriptions
                    plaintiff_name = re.sub(r',\s*a\s+.*$', '', plaintiff_name)  # Remove ", a Nevada..."
                    plaintiff_name = re.sub(r',\s*an\s+.*$', '', plaintiff_name)  # Remove ", an individual..."
                    plaintiff_name = plaintiff_name.strip().strip(',').strip()
                    
                    # Now find defendant after plaintiffs marker
                    after_plaintiffs = before_case_num[plaintiffs_marker.end():]
                    v_match = re.search(r'v\.\s*([A-Z][A-Za-z\s\.,&\-\']{5,80})', after_plaintiffs, re.IGNORECASE)
                    if v_match:
                        defendant_name = v_match.group(1).strip()
                        # Clean defendant name
                        defendant_name = re.sub(r',\s*(?:an?\s+)?individual.*$', '', defendant_name, flags=re.IGNORECASE)
                        defendant_name = defendant_name.strip().strip(',').strip()
                        
                        case_name = f"{plaintiff_name} v. {defendant_name}"
                        logger.warning(f"[CONTAMINATION-FILTER] Found primary case (Strategy 1 Multi-Plaintiff): '{case_name}'")
                        return case_name
            
            # Original single-plaintiff logic as fallback
            v_pattern = re.search(r'([A-Z][A-Za-z\s\.,&\-\']{5,80})\s+v\.\s+([A-Z][A-Za-z\s\.,&\-\']{5,80})', before_case_num, re.IGNORECASE)
            if v_pattern:
                case_name = f"{v_pattern.group(1).strip()} v. {v_pattern.group(2).strip()}"
                logger.warning(f"[CONTAMINATION-FILTER] Found primary case (Strategy 1): '{case_name}'")
                return case_name
        
        # Strategy 2: Look for case name in first few lines (typical brief format)
        lines = header.split('\n')
        for i, line in enumerate(lines[:15]):  # Check first 15 lines
            line = line.strip()
            if ' v. ' in line and len(line) > 10 and len(line) < 150:
                # Check if it looks like a case name (not a citation)
                # Case names usually don't have numbers before "v."
                if not re.search(r'\d+\s+\w+\.\s*\d*\s+\d+', line):  # Not "123 F.3d 456"
                    # Clean up common prefix/suffix patterns
                    cleaned = re.sub(r'^\s*(?:IN\s+THE\s+)?(?:MATTER\s+OF\s+)?', '', line, flags=re.IGNORECASE)
                    cleaned = re.sub(r'\s*,?\s*(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*$', '', cleaned, flags=re.IGNORECASE)
                    
                    if ' v. ' in cleaned and len(cleaned) > 10:
                        logger.warning(f"[CONTAMINATION-FILTER] Found primary case (Strategy 2): '{cleaned}'")
                        return cleaned
        
        # Strategy 3: Pattern match for common formats
        # "PLAINTIFF, v. DEFENDANT," or "PLAINTIFF v. DEFENDANT No."
        pattern = r'([A-Z][A-Za-z\s\.,&\-\']{8,80})\s+v\.\s+([A-Za-z][A-Za-z\s\.,&\-\']{8,80})(?:\s*,|\s+No\.)'
        match = re.search(pattern, header)
        if match:
            case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
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
            case_name = getattr(citation, 'extracted_case_name', None) or getattr(citation, 'canonical_name', None)
            if case_name and case_name != 'N/A':
                case_names.append(case_name)
        
        if len(case_names) > 1:
            # Check consistency
            base_name = case_names[0]
            consistent_count = sum(1 for name in case_names[1:] if self._calculate_name_similarity(base_name, name) > 0.7)
            if consistent_count > 0:
                confidence += 0.2
        
        # Bonus for verification
        verified_count = sum(1 for citation in citations if getattr(citation, 'verified', False))
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
    config: Optional[Dict[str, Any]] = None
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
    return clusterer.cluster_citations(citations, original_text, enable_verification, request_id)
