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
        self.case_name_similarity_threshold = self.config.get('case_name_similarity_threshold', 0.6)
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
                cleaned = name.strip()
                if cleaned and cleaned not in ('N/A', 'Unknown', 'Unknown Case'):
                    candidates.append((self._score_case_name(cleaned), cleaned))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

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
        
        logger.info(f"🎯 MASTER_CLUSTER: Starting clustering for {len(citations)} citations (verification: {enable_verification})")
        
        if not citations:
            logger.warning("MASTER_CLUSTER: No citations provided")
            return []
        
        try:
            # Step 1: Detect parallel citations and create initial groups
            logger.info("MASTER_CLUSTER: Step 1 - Detecting parallel citations")
            parallel_groups = self._detect_parallel_citations(citations, original_text)
            logger.info(f"MASTER_CLUSTER: Created {len(parallel_groups)} parallel groups")
            
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
                self._apply_verification_to_clusters(final_clusters)
            
            # Step 5: Merge and deduplicate clusters
            logger.info("MASTER_CLUSTER: Step 5 - Merging and deduplicating")
            merged_clusters = self._merge_and_deduplicate_clusters(final_clusters)
            logger.info(f"MASTER_CLUSTER: Final result: {len(merged_clusters)} clusters")
            
            # Step 6: Format clusters for output
            formatted_clusters = self._format_clusters_for_output(merged_clusters)
            
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
                    similarity = self._calculate_name_similarity(case_names[i], case_names[j])
                    if similarity >= self.case_name_similarity_threshold:
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
        
        # Check if either citation is in the other's parallel citations
        if citation1_text in parallel2 or citation2_text in parallel1:
            if self.debug_mode:
                logger.debug("PARALLEL_CHECK matched via parallel_citations metadata")
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

        # If same reporter, they can't be parallel (must be different reporters)
        if reporter1 == reporter2:
            if self.debug_mode:
                logger.debug(
                    "PARALLEL_CHECK rejected: same reporter type | reporter=%s",
                    reporter1,
                )
            return False

        # If either reporter is unknown, we can't reliably determine if they're parallel
        if 'unknown' in (reporter1, reporter2):
            if self.debug_mode:
                logger.debug("PARALLEL_CHECK rejected: unknown reporter type")
            return False

        # Check known parallel patterns
        if not self._match_parallel_patterns(citation1_text, citation2_text):
            if self.debug_mode:
                logger.debug("PARALLEL_CHECK reporter pair not recognized as parallel")
            
            # If patterns don't match, try case name similarity as a fallback
            case_name1 = self._get_case_name(citation1)
            case_name2 = self._get_case_name(citation2)
            
            if case_name1 and case_name2 and case_name1 != 'N/A' and case_name2 != 'N/A':
                similarity = self._calculate_name_similarity(case_name1, case_name2)
                if similarity >= 0.8:  # High threshold for case name similarity
                    if self.debug_mode:
                        logger.debug(
                            "PARALLEL_CHECK matched via case name similarity (%.2f): %s ↔ %s",
                            similarity,
                            case_name1,
                            case_name2
                        )
                    return True
            
            return False

        # Washington-specific handling
        if 'wash' in reporter1 or 'wash' in reporter2:
            if not self._check_washington_parallel_patterns(citation1_text, citation2_text):
                if self.debug_mode:
                    logger.debug("PARALLEL_CHECK Washington reporter validation failed")
                return False

        # Check proximity in text
        def get_start_index(cit: Any) -> int:
            if isinstance(cit, dict):
                return cit.get('start_index', cit.get('start', 0))
            return getattr(cit, 'start_index', getattr(cit, 'start', 0))

        start1 = get_start_index(citation1)
        start2 = get_start_index(citation2)
        distance = abs(start1 - start2)
        
        # Adjust proximity threshold based on citation types
        proximity_threshold = self.proximity_threshold
        if 'U.S.' in citation1_text or 'U.S.' in citation2_text:
            # Be more lenient with US Supreme Court citations
            proximity_threshold = max(proximity_threshold, 500)
            
        if distance > proximity_threshold:
            if self.debug_mode:
                logger.debug(
                    "PARALLEL_CHECK rejected by proximity | distance=%s threshold=%s",
                    distance,
                    proximity_threshold,
                )
            return False

        # If we get here, the citations are likely parallel
        if self.debug_mode:
            logger.debug(
                "PARALLEL_CHECK ACCEPTED | %s ↔ %s | distance=%s",
                citation1_text,
                citation2_text,
                distance
            )
            
        return True
        
    def _get_case_name(self, citation: Any) -> Optional[str]:
        """Helper to extract case name from a citation object."""
        if isinstance(citation, dict):
            return (
                citation.get('canonical_name')
                or citation.get('cluster_case_name')
                or citation.get('extracted_case_name')
                or citation.get('case_name')
            )
        return (
            getattr(citation, 'canonical_name', None)
            or getattr(citation, 'cluster_case_name', None)
            or getattr(citation, 'extracted_case_name', None)
            or getattr(citation, 'case_name', None)
        )

        name1 = get_case_name(citation1)
        name2 = get_case_name(citation2)
        if name1 and name2 and name1 != 'N/A' and name2 != 'N/A':
            similarity = self._calculate_name_similarity(name1, name2)
            if similarity < self.case_name_similarity_threshold:
                if self.debug_mode:
                    logger.debug(
                        "PARALLEL_CHECK rejected by case-name similarity | score=%.3f threshold=%.3f",
                        similarity,
                        self.case_name_similarity_threshold,
                    )
                return False

        def get_year(cit: Any) -> Optional[str]:
            if isinstance(cit, dict):
                return cit.get('canonical_date') or cit.get('cluster_year') or cit.get('extracted_date')
            return (
                getattr(cit, 'canonical_date', None)
                or getattr(cit, 'cluster_year', None)
                or getattr(cit, 'extracted_date', None)
            )

        year1 = get_year(citation1)
        year2 = get_year(citation2)
        if year1 and year2 and year1 != 'N/A' and year2 != 'N/A' and year1 != year2:
            if self.debug_mode:
                logger.debug(
                    "PARALLEL_CHECK rejected by year mismatch | %s vs %s",
                    year1,
                    year2,
                )
            return False

        if self.debug_mode:
            logger.debug("PARALLEL_CHECK success")
        return True

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

            if not case_name:
                for citation in group:
                    extracted_name = getattr(citation, 'extracted_case_name', None)
                    fallback_name = getattr(citation, 'canonical_name', None)
                    if extracted_name and extracted_name != 'N/A':
                        case_name = extracted_name
                        break
                    if fallback_name and fallback_name != 'N/A':
                        case_name = fallback_name
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

            current_name = getattr(enhanced, 'extracted_case_name', None)
            if case_name and case_name != 'N/A' and self._should_replace_case_name(current_name, case_name):
                enhanced.extracted_case_name = case_name
                current_name = case_name
            if verified_flag and canonical_name and canonical_name != 'N/A' and self._should_replace_case_name(current_name, canonical_name):
                enhanced.extracted_case_name = canonical_name

            current_year = getattr(enhanced, 'extracted_date', None)
            if case_year and case_year != 'N/A' and (not current_year or current_year in ('', 'N/A', 'Unknown')):
                enhanced.extracted_date = case_year
                current_year = case_year
            if verified_flag and canonical_date and canonical_date != 'N/A':
                canonical_year = self._extract_year_value(canonical_date) or canonical_date
                if not current_year or current_year in ('', 'N/A', 'Unknown'):
                    enhanced.extracted_date = canonical_year

            enhanced.is_parallel = parallel
            enhanced.parallel_citations = [member for member in members if member != original_citation_text]
        elif isinstance(enhanced, dict):
            enhanced['cluster_case_name'] = case_name
            enhanced['cluster_year'] = case_year
            enhanced['cluster_size'] = len(group)
            enhanced['is_in_cluster'] = parallel
            enhanced['cluster_members'] = members

            current_name = enhanced.get('extracted_case_name')
            if case_name and case_name != 'N/A' and self._should_replace_case_name(current_name, case_name):
                enhanced['extracted_case_name'] = case_name
                current_name = case_name
            if verified_flag and canonical_name and canonical_name != 'N/A' and self._should_replace_case_name(current_name, canonical_name):
                enhanced['extracted_case_name'] = canonical_name

            current_year = enhanced.get('extracted_date')
            if case_year and case_year != 'N/A' and (not current_year or current_year in ('', 'N/A', 'Unknown')):
                enhanced['extracted_date'] = case_year
                current_year = case_year
            if verified_flag and canonical_date and canonical_date != 'N/A':
                canonical_year = self._extract_year_value(canonical_date) or canonical_date
                if not current_year or current_year in ('', 'N/A', 'Unknown'):
                    enhanced['extracted_date'] = canonical_year

            enhanced['is_parallel'] = parallel
            enhanced['parallel_citations'] = [member for member in members if member != original_citation_text]

        return enhanced

    def _create_final_clusters(self, enhanced_citations: List[Any]) -> List[Dict[str, Any]]:
        """Create final clusters based on metadata similarity with validation."""
        clusters = defaultdict(list)
        
        for citation in enhanced_citations:
            # Create cluster key based on case name and year
            case_name = getattr(citation, 'cluster_case_name', None) or getattr(citation, 'extracted_case_name', None)
            case_year = getattr(citation, 'cluster_year', None) or getattr(citation, 'extracted_date', None)
            
            # Normalize for clustering
            if case_name and case_name != 'N/A':
                normalized_name = self._normalize_case_name(case_name)
            else:
                normalized_name = 'unknown'
            
            if case_year and case_year != 'N/A':
                # Extract just the year (handle dates like "2016-03-24")
                year_match = re.search(r'(19|20)\d{2}', str(case_year))
                normalized_year = year_match.group(0) if year_match else str(case_year)[:4]
            else:
                normalized_year = 'unknown'
            
            cluster_key = f"{normalized_name}_{normalized_year}"
            
            # VALIDATION: Check if this citation should be added to this cluster
            if cluster_key in clusters and not self._should_add_to_cluster(citation, clusters[cluster_key]):
                # Create a new unique cluster key for this citation
                cluster_key = f"{normalized_name}_{normalized_year}_{len(clusters)}"
                logger.warning(f"MASTER_CLUSTER: Citation {getattr(citation, 'citation', 'unknown')} failed validation, creating separate cluster")
            
            clusters[cluster_key].append(citation)
        
        # Convert to list of cluster dictionaries
        final_clusters = []
        for i, (cluster_key, citations) in enumerate(clusters.items()):
            cluster = {
                'cluster_id': f"cluster_{i+1}",
                'cluster_key': cluster_key,
                'citations': citations,
                'size': len(citations),
                'case_name': citations[0].get('cluster_case_name') if hasattr(citations[0], 'get') else getattr(citations[0], 'cluster_case_name', None),
                'case_year': citations[0].get('cluster_year') if hasattr(citations[0], 'get') else getattr(citations[0], 'cluster_year', None),
                'confidence': self._calculate_cluster_confidence(citations),
                'metadata': {
                    'cluster_type': 'metadata_based',
                    'created_by': 'unified_master',
                    'cluster_key': cluster_key
                }
            }
            final_clusters.append(cluster)
        
        return final_clusters
    
    def _should_add_to_cluster(self, citation: Any, existing_citations: List[Any]) -> bool:
        """Validate if a citation should be added to an existing cluster."""
        if not existing_citations:
            return True
        
        # Get citation metadata - PREFER CANONICAL DATA OVER EXTRACTED
        cit_name = getattr(citation, 'canonical_name', None) or getattr(citation, 'cluster_case_name', None) or getattr(citation, 'extracted_case_name', None)
        # CRITICAL: Use canonical_date first (verified), fallback to extracted
        cit_year = getattr(citation, 'canonical_date', None) or getattr(citation, 'cluster_year', None) or getattr(citation, 'extracted_date', None)
        cit_canonical_name = getattr(citation, 'canonical_name', None)
        cit_canonical_date = getattr(citation, 'canonical_date', None)
        
        # Extract year from date if needed
        def extract_year(date_str):
            if not date_str or date_str == 'N/A':
                return None
            year_match = re.search(r'(19|20)\d{2}', str(date_str))
            return int(year_match.group(0)) if year_match else None
        
        cit_year_int = extract_year(cit_year)
        cit_canonical_year = extract_year(cit_canonical_date)
        
        # Check against first citation in cluster - PREFER CANONICAL DATA
        first_cit = existing_citations[0]
        first_name = getattr(first_cit, 'canonical_name', None) or getattr(first_cit, 'cluster_case_name', None) or getattr(first_cit, 'extracted_case_name', None)
        # CRITICAL: Use canonical_date first (verified), fallback to extracted
        first_year = getattr(first_cit, 'canonical_date', None) or getattr(first_cit, 'cluster_year', None) or getattr(first_cit, 'extracted_date', None)
        first_canonical_name = getattr(first_cit, 'canonical_name', None)
        first_canonical_date = getattr(first_cit, 'canonical_date', None)
        
        first_year_int = extract_year(first_year)
        first_canonical_year = extract_year(first_canonical_date)
        
        # VALIDATION 1: Year consistency check
        # If both have years, they must be within 2 years of each other
        if cit_year_int and first_year_int:
            year_diff = abs(cit_year_int - first_year_int)
            if year_diff > 2:
                logger.warning(f"MASTER_CLUSTER: Year mismatch: {cit_year_int} vs {first_year_int} (diff: {year_diff} years)")
                return False
        
        # VALIDATION 2: Canonical data consistency
        # If both have canonical dates, check consistency
        if cit_canonical_year and first_canonical_year:
            canonical_diff = abs(cit_canonical_year - first_canonical_year)
            if canonical_diff > 2:
                logger.warning(f"MASTER_CLUSTER: Canonical year mismatch: {cit_canonical_year} vs {first_canonical_year}")
                return False
        
        # VALIDATION 3: Case name similarity
        # If both have case names, they must be similar
        if cit_name and cit_name != 'N/A' and first_name and first_name != 'N/A':
            similarity = self._calculate_name_similarity(cit_name, first_name)
            if similarity < self.case_name_similarity_threshold:
                logger.warning(f"MASTER_CLUSTER: Case name mismatch: '{cit_name}' vs '{first_name}' (similarity: {similarity:.2f})")
                return False
        
        # VALIDATION 4: Canonical name consistency
        if cit_canonical_name and cit_canonical_name != 'N/A' and first_canonical_name and first_canonical_name != 'N/A':
            canonical_similarity = self._calculate_name_similarity(cit_canonical_name, first_canonical_name)
            if canonical_similarity < self.case_name_similarity_threshold:
                logger.warning(f"MASTER_CLUSTER: Canonical name mismatch: '{cit_canonical_name}' vs '{first_canonical_name}'")
                return False
        
        return True
    
    def _apply_verification_to_clusters(self, clusters: List[Dict[str, Any]]) -> None:
        """Apply verification to clusters if enabled."""
        if not self.enable_verification:
            return
        
        try:
            # Import verification master
            from src.unified_verification_master import verify_citation_unified_master_sync
            
            for cluster in clusters:
                citations = cluster.get('citations', [])
                if not citations:
                    continue
                
                # Verify the first citation in each cluster
                first_citation = citations[0]
                citation_text = getattr(first_citation, 'citation', str(first_citation))
                case_name = getattr(first_citation, 'extracted_case_name', None)
                case_date = getattr(first_citation, 'extracted_date', None)
                
                try:
                    verification_result = verify_citation_unified_master_sync(
                        citation=citation_text,
                        extracted_case_name=case_name,
                        extracted_date=case_date,
                        timeout=5.0
                    )
                    
                    if verification_result.get('verified', False):
                        # Propagate verification to all citations in cluster
                        for i, citation in enumerate(citations):
                            if hasattr(citation, '__dict__'):
                                citation.verified = True
                                citation.canonical_name = verification_result.get('canonical_name')
                                citation.canonical_date = verification_result.get('canonical_date')
                                citation.canonical_url = verification_result.get('canonical_url')
                                citation.verification_source = verification_result.get('source')
                                # Set true_by_parallel for all citations except the first one
                                if i > 0:
                                    citation.true_by_parallel = True
                            elif isinstance(citation, dict):
                                citation['verified'] = True
                                citation['canonical_name'] = verification_result.get('canonical_name')
                                citation['canonical_date'] = verification_result.get('canonical_date')
                                citation['canonical_url'] = verification_result.get('canonical_url')
                                citation['verification_source'] = verification_result.get('source')
                                # Set true_by_parallel for all citations except the first one
                                if i > 0:
                                    citation['true_by_parallel'] = True
                        
                        cluster['verification_status'] = 'verified'
                        cluster['verification_source'] = verification_result.get('source')
                        
                except Exception as e:
                    logger.warning(f"MASTER_CLUSTER: Verification failed for cluster {cluster.get('cluster_id')}: {e}")
                    cluster['verification_status'] = 'failed'
        
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
            
            formatted_cluster = {
                'cluster_id': cluster_id,
                'cluster_case_name': best_name or 'N/A',
                'cluster_year': best_year or 'N/A',
                'cluster_size': cluster.get('size', 0),
                'citations': citations,
                'confidence': cluster.get('confidence', 0.0),
                'verification_status': cluster.get('verification_status', 'not_verified'),
                'verification_source': cluster.get('verification_source', None),
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
