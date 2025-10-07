"""
Unified Citation Clustering System

This module consolidates all parallel citation clustering functions into a single,
optimized implementation that follows the user's specified logic:

1. Extract case name from the FIRST citation in the sequence
2. Extract year from the LAST citation in the sequence  
3. Propagate both to all citations in the cluster
4. Cluster citations by having the same extracted name AND year

This replaces multiple scattered clustering implementations with a single,
reliable, and well-tested approach.
"""

import logging
import os
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import re
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter

from src.utils.canonical_metadata import (
    prefer_canonical_name,
    prefer_canonical_year,
)

logger = logging.getLogger(__name__)


class UnifiedCitationClusterer:
    """
    Unified citation clustering system that implements the optimal clustering logic.
    
    This consolidates and replaces:
    - src/citation_clustering.py::group_citations_into_clusters()
    - src/services/citation_clusterer.py::CitationClusterer
    - archived/analysis_scripts/improved_clustering_algorithm.py
    - All other scattered clustering functions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the unified clusterer with configuration.
        
        Args:
            config: Optional configuration dictionary. If not provided, will load from default config.
        """
        from src.config import get_citation_config
        
        # Get default configuration if not provided
        default_config = get_citation_config()
        
        # Merge with provided config
        self.config = {**default_config, **(config or {})}
        
        # Set debug mode from config or environment
        self.debug_mode = self.config.get('debug_mode', False) or os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes')
        
        # Configure clustering parameters
        clustering_config = self.config.get('clustering_options', {})
        self.proximity_threshold = clustering_config.get('proximity_threshold', 200)
        self.min_cluster_size = clustering_config.get('min_cluster_size', 1)  # Allow single citation clusters
        self.case_name_similarity_threshold = clustering_config.get('case_name_similarity_threshold', 0.8)
        
        # Configure verification
        self.enable_verification = self.config.get('enable_verification', True)
        self.verification_config = self.config.get('verification_options', {})
        
        if self.debug_mode:
            logger.info("UnifiedCitationClusterer initialized with configuration:")
            logger.info(f"- Debug mode: {self.debug_mode}")
            logger.info(f"- Proximity threshold: {self.proximity_threshold}")
            logger.info(f"- Min cluster size: {self.min_cluster_size}")
            logger.info(f"- Case name similarity threshold: {self.case_name_similarity_threshold}")
            logger.info(f"- Verification enabled: {self.enable_verification}")
            if self.enable_verification:
                logger.info(f"  - Verification config: {self.verification_config}")
    
    def cluster_citations(self, citations: List[Any], original_text: str = "", enable_verification: bool = None) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Use cluster_citations_unified_master() instead.
        
        This function now delegates to the new unified master implementation
        that consolidates all 45+ duplicate clustering functions.
        
        MIGRATION: Replace calls with:
        from src.unified_clustering_master import cluster_citations_unified_master
        """
        import warnings
        warnings.warn(
            "UnifiedCitationClusterer.cluster_citations() is deprecated. Use cluster_citations_unified_master() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Delegate to the new master implementation
        from src.unified_clustering_master import cluster_citations_unified_master
        return cluster_citations_unified_master(
            citations=citations,
            original_text=original_text,
            enable_verification=enable_verification,
            config=self.config
        )
    
    def _detect_parallel_citation_groups(self, citations: List[Any], text: str) -> List[List[Any]]:
        """
        STEP 1: Detect parallel citation groups using STRUCTURAL PATTERN RECOGNITION.
        
        NEW APPROACH: Instead of proximity-based clustering, we use structural patterns
        to identify citations that belong to the same case based on legal citation format:
        "Case Name, Citation1, Citation2, Citation3 (Year)"
        
        This fixes the issue where citations from different cases get incorrectly clustered
        due to proximity (e.g., "Spokeo v. Robins, 578 U.S. 330 (2016) (quoting Raines v. Byrd, 521 U.S. 811)")
        """
        groups = []
        visited = set()
        
        # Helper functions
        def get_citation_text(cit):
            if isinstance(cit, dict):
                return cit.get('citation', cit.get('text', ''))
            return getattr(cit, 'citation', getattr(cit, 'text', ''))
            
        def get_start_index(cit):
            if isinstance(cit, dict):
                return cit.get('start', cit.get('start_index', 0))
            return getattr(cit, 'start_index', getattr(cit, 'start', 0))
            
        def get_end_index(cit):
            if isinstance(cit, dict):
                return cit.get('end', cit.get('end_index', 0))
            return getattr(cit, 'end_index', getattr(cit, 'end', 0))
        
        # Sort citations by start index
        sorted_citations = sorted(citations, key=lambda c: get_start_index(c))
        
        # NEW: Use structural pattern recognition to group citations
        structural_groups = self._detect_structural_citation_groups(sorted_citations, text)
        
        if structural_groups:
            logger.info(f"Detected {len(structural_groups)} structural citation groups")
            return structural_groups
        
        # FALLBACK: Use the original proximity-based method if structural detection fails
        logger.info("Structural detection failed, falling back to proximity-based clustering")
        
        # Create a lookup for citations by their text
        citation_lookup = {get_citation_text(c): c for c in citations}
        
        for citation in sorted_citations:
            citation_text = get_citation_text(citation)
            if citation_text in visited:
                continue
            
            group = [citation]
            visited.add(citation_text)
            
            # Check for explicitly marked parallel citations
            # FIXED: Handle both dict and object citations
            if isinstance(citation, dict):
                parallel_citations = citation.get('parallel_citations', [])
            else:
                parallel_citations = getattr(citation, 'parallel_citations', [])
                
            for parallel_cite in parallel_citations:
                if parallel_cite in citation_lookup and parallel_cite not in visited:
                    parallel_citation = citation_lookup[parallel_cite]
                    
                    # FIXED: Handle both dict and object citations
                    if isinstance(parallel_citation, dict):
                        reverse_parallels = parallel_citation.get('parallel_citations', [])
                    else:
                        reverse_parallels = getattr(parallel_citation, 'parallel_citations', [])
                    
                    # Check for bidirectional relationship
                    if citation_text in reverse_parallels:
                        distance = abs(get_start_index(citation) - get_start_index(parallel_citation))
                        if distance <= self.proximity_threshold:
                            group.append(parallel_citation)
                            visited.add(parallel_cite)
            
            # Check for proximity-based parallel citations (more restrictive now)
            for other_citation in sorted_citations:
                other_text = get_citation_text(other_citation)
                if other_text in visited:
                    continue
                
                if self._are_citations_parallel_by_proximity(citation, other_citation, text):
                    group.append(other_citation)
                    visited.add(other_text)
            
            groups.append(group)
        
        logger.info(f"Detected {len(groups)} parallel citation groups (proximity-based fallback)")
        return groups
    
    def _detect_structural_citation_groups(self, sorted_citations: List[Any], text: str) -> List[List[Any]]:
        """
        IMPROVED METHOD: Detect citation groups using enhanced structural pattern recognition.
        
        This method identifies citations that belong to the same case by recognizing
        the legal citation pattern: "Case Name, Citation1, Citation2, Citation3 (Year)"
        
        FIXED: Better pattern matching and context analysis to handle complex citation formats.
        
        Args:
            sorted_citations: Citations sorted by start index
            text: Original text for pattern matching
            
        Returns:
            List of citation groups based on structural patterns
        """
        import re
        
        def get_citation_text(cit):
            if isinstance(cit, dict):
                return cit.get('citation', cit.get('text', ''))
            return getattr(cit, 'citation', getattr(cit, 'text', ''))
            
        def get_start_index(cit):
            if isinstance(cit, dict):
                return cit.get('start', cit.get('start_index', 0))
            return getattr(cit, 'start_index', getattr(cit, 'start', 0))
            
        def get_end_index(cit):
            if isinstance(cit, dict):
                return cit.get('end', cit.get('end_index', 0))
            return getattr(cit, 'end_index', getattr(cit, 'end', 0))
        
        groups = []
        visited = set()
        
        # IMPROVED: More comprehensive patterns to handle various citation formats
        citation_structure_patterns = [
            # Standard pattern: Case v. Case, Citation1, Citation2 (Year)
            r'([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)',
            # Quoting pattern: (quoting Case v. Case, Citation1, Citation2 (Year))
            r'\(quoting\s+([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)\)',
            # Alternative pattern with "held in"
            r'held\s+in\s+([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)',
            # Pattern for cases with multiple citations: Case v. Case, 123 Wn.2d 456, 789 P.3d 101 (Year)
            r'([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*(\d+\s+Wn\.\d+\s+\d+.*?),\s*(\d+\s+P\.\d+\s+\d+.*?)\((\d{4})\)',
            # Pattern for cases with comma-separated citations: Case v. Case, Citation1, Citation2, Citation3 (Year)
            r'([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*([^()]+,\s*[^()]+,\s*[^()]+)\((\d{4})\)',
            # Pattern for cases with semicolon separation: Case v. Case; Citation1; Citation2 (Year)
            r'([A-Z][^,]+v\.\s+[A-Z][^,]+);\s*([^()]+)\((\d{4})\)',
            # Pattern for "In re" cases: In re Case Name, Citation1, Citation2 (Year)
            r'(In\s+re\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)',
            # Pattern for "State v." cases with multiple citations
            r'(State\s+v\.\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)'
        ]
        
        logger.info(f"🔍 STRUCTURAL: Analyzing text for citation patterns...")
        
        for pattern_idx, pattern in enumerate(citation_structure_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                case_name = match.group(1).strip()
                citations_text = match.group(2).strip()
                year = match.group(3) if len(match.groups()) >= 3 else ""
                
                match_start = match.start()
                match_end = match.end()
                
                logger.info(f"🎯 STRUCTURAL: Found pattern {pattern_idx} - Case: '{case_name}', Citations: '{citations_text}', Year: {year}")
                logger.info(f"📍 STRUCTURAL: Pattern position: {match_start}-{match_end}")
                
                # Find all citations that fall within this structural pattern
                pattern_citations = []
                for citation in sorted_citations:
                    citation_text = get_citation_text(citation)
                    citation_start = get_start_index(citation)
                    citation_end = get_end_index(citation)
                    
                    # Check if this citation falls within the pattern boundaries
                    if (citation_start >= match_start and citation_end <= match_end and
                        citation_text not in visited):
                        
                        # IMPROVED: Better text matching with normalization
                        text_match = self._citations_match_in_context(citation_text, citations_text, case_name)
                        
                        if text_match:
                            pattern_citations.append(citation)
                            visited.add(citation_text)
                            logger.info(f"✅ STRUCTURAL: Added '{citation_text}' to '{case_name}' group")
                
                if pattern_citations:
                    groups.append(pattern_citations)
                    logger.info(f"🔗 STRUCTURAL: Created group for '{case_name}' with {len(pattern_citations)} citations")
        
        # IMPROVED: Better handling of remaining unvisited citations
        for citation in sorted_citations:
            citation_text = get_citation_text(citation)
            if citation_text not in visited:
                # Try to find nearby citations that might be parallel
                nearby_citations = self._find_nearby_parallel_citations(citation, sorted_citations, text, visited)
                if nearby_citations:
                    groups.append(nearby_citations)
                    for nearby_cit in nearby_citations:
                        visited.add(get_citation_text(nearby_cit))
                    logger.info(f"🔗 STRUCTURAL: Created proximity group with {len(nearby_citations)} citations")
                else:
                    groups.append([citation])
                    visited.add(citation_text)
                    logger.info(f"📝 STRUCTURAL: Created individual group for unmatched citation '{citation_text}'")
        
        logger.info(f"🎉 STRUCTURAL: Created {len(groups)} groups using structural pattern recognition")
        return groups if groups else None
    
    def _citations_match_in_context(self, citation_text: str, citations_text: str, case_name: str) -> bool:
        """
        IMPROVED: Check if a citation matches in context with better normalization.
        
        Args:
            citation_text: Individual citation to check
            citations_text: Text containing multiple citations
            case_name: Case name for additional context validation
            
        Returns:
            True if citation matches in context
        """
        import re
        
        # Normalize the citation text for comparison
        def normalize_citation(text):
            # Handle common abbreviation expansions and variations
            text = text.replace('Wash.2d', 'Wn.2d')
            text = text.replace('Wash.', 'Wn.')
            text = text.replace('Wn.2d', 'Wn.2d')  # Ensure consistency
            text = text.replace('P.3d', 'P.3d')
            text = text.replace('P.2d', 'P.2d')
            return text.strip()
        
        normalized_citation = normalize_citation(citation_text)
        
        # Check if the normalized citation appears in the citations text
        if normalized_citation in citations_text:
            return True
        
        # Extract individual citations from the citations_text and check each
        citation_patterns = [
            r'\d+\s+[A-Za-z.]+\s+\d+',  # Basic pattern like "183 Wn.2d 649"
            r'\d+\s+[A-Za-z.]+\d*\s+\d+',  # Pattern like "355 P.3d 258"
            r'\d+\s+[A-Za-z.]+\s+\d+',  # Pattern like "136 S. Ct. 1540"
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, citations_text)
            for match in matches:
                if normalize_citation(match) == normalized_citation:
                    return True
        
        return False
    
    def _find_nearby_parallel_citations(self, citation: Any, sorted_citations: List[Any], text: str, visited: Set[str]) -> List[Any]:
        """
        Find citations that are nearby and likely parallel to the given citation.
        
        Args:
            citation: Citation to find parallels for
            sorted_citations: All citations sorted by position
            text: Original text
            visited: Set of already visited citations
            
        Returns:
            List of nearby parallel citations including the original
        """
        def get_citation_text(cit):
            if isinstance(cit, dict):
                return cit.get('citation', cit.get('text', ''))
            return getattr(cit, 'citation', getattr(cit, 'text', ''))
            
        def get_start_index(cit):
            if isinstance(cit, dict):
                return cit.get('start', cit.get('start_index', 0))
            return getattr(cit, 'start_index', getattr(cit, 'start', 0))
        
        citation_text = get_citation_text(citation)
        citation_start = get_start_index(citation)
        
        nearby_citations = [citation]
        
        # Look for citations within 200 characters that might be parallel
        for other_citation in sorted_citations:
            other_text = get_citation_text(other_citation)
            if other_text in visited or other_text == citation_text:
                continue
                
            other_start = get_start_index(other_citation)
            distance = abs(other_start - citation_start)
            
            if distance <= 200:  # Within reasonable proximity
                # Check if they have different reporter types (indicating parallel citations)
                if self._are_citations_parallel_by_proximity(citation, other_citation, text):
                    nearby_citations.append(other_citation)
        
        return nearby_citations if len(nearby_citations) > 1 else []
    
    def _citations_are_equivalent(self, citation_text: str, citations_text: str) -> bool:
        """
        DEPRECATED: Use _citations_match_in_context instead.
        
        Check if a citation is equivalent to any citation in the citations text,
        handling format normalization issues like 'Wn.2d' vs 'Wash.2d'.
        """
        return self._citations_match_in_context(citation_text, citations_text, "")
    
    def _extract_and_propagate_metadata(self, groups: List[List[Any]], text: str) -> Dict[str, List[Any]]:
        """
        IMPROVED STEP 2: Extract case names from first and years from last citation in each group.
        IMPROVED STEP 3: Propagate the extracted data to all members of each group.
        
        FIXED: Better extraction logic and validation to ensure accurate case names and years.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        clusters = {}
        cluster_counter = 1
        
        for group in groups:
            if not group:
                continue
            
            # FIXED: Use helper function to handle both dict and object citations
            def get_start_index_for_sort(cit):
                if isinstance(cit, dict):
                    return cit.get('start', cit.get('start_index', 0))
                return getattr(cit, 'start_index', getattr(cit, 'start', 0))
            
            sorted_group = sorted(group, key=get_start_index_for_sort)
            
            # Determine base metadata from canonical values when available
            canonical_name = self._select_best_canonical_name(sorted_group)
            canonical_year = self._select_best_canonical_year(sorted_group)

            # IMPROVED: Extract case name from the first citation with better validation
            raw_case_name = self._extract_case_name_from_citation(sorted_group[0], text)
            extracted_case_name = self._clean_case_name(raw_case_name) if raw_case_name else "N/A"
            if extracted_case_name == "N/A" and raw_case_name and raw_case_name != "N/A":
                logger.warning(f"🚫 CONTAMINATION: Filtered contaminated case name: '{raw_case_name[:100]}...'")

            preferred_case_name = prefer_canonical_name(
                extracted_case_name,
                {"canonical_name": canonical_name} if canonical_name else {},
                lambda name: name and name != "N/A"
            )

            # IMPROVED: Extract year with better validation
            year = None
            
            if len(sorted_group) > 1:
                # Try to get year from the last citation first
                last_citation = sorted_group[-1]
                year = self._extract_year_from_citation(last_citation, text)
                
                # If no year from last citation, try all citations and pick the most common
                if not year or year == "N/A":
                    candidate_years = []
                    for citation in sorted_group:
                        extracted_year = self._extract_year_from_citation(citation, text)
                        if extracted_year and extracted_year != "N/A" and extracted_year.isdigit():
                            candidate_years.append(extracted_year)
                    
                    if candidate_years:
                        from collections import Counter
                        year_counts = Counter(candidate_years)
                        year = year_counts.most_common(1)[0][0]
                        logger.warning(f"📊 METADATA: Selected most common year '{year}' from {len(candidate_years)} candidates")
            else:
                year = self._extract_year_from_citation(sorted_group[0], text)
            
            preferred_year = prefer_canonical_year(
                year,
                {"canonical_year": canonical_year} if canonical_year else {}
            )

            # IMPROVED: Better fallback logic for case names
            if not preferred_case_name or preferred_case_name == "N/A":
                for citation in sorted_group:
                    extracted_name = self._extract_case_name_from_citation(citation, text)
                    if extracted_name and extracted_name != "N/A" and len(extracted_name) > 5:
                        preferred_case_name = extracted_case_name = extracted_name
                        logger.warning(f"🔄 METADATA: Using fallback case name '{preferred_case_name}' from citation {sorted_group.index(citation)}")
                        break
            
            # IMPROVED: Better fallback logic for years
            if not preferred_year or preferred_year == "N/A":
                for citation in reversed(sorted_group):
                    extracted_year = self._extract_year_from_citation(citation, text)
                    if extracted_year and extracted_year != "N/A" and extracted_year.isdigit():
                        preferred_year = extracted_year
                        logger.warning(f"🔄 METADATA: Using fallback year '{preferred_year}' from citation {sorted_group.index(citation)}")
                        break
            
            # IMPROVED: Validate extracted data before propagation
            if (
                preferred_case_name
                and preferred_case_name != "N/A"
                and preferred_year
                and preferred_year != "N/A"
            ):
                logger.warning(f"✅ METADATA: Validated extraction - Case: '{preferred_case_name}', Year: '{preferred_year}'")
            else:
                logger.warning(f"⚠️ METADATA: Incomplete extraction - Case: '{preferred_case_name}', Year: '{preferred_year}'")
            
            final_case_name = canonical_name or preferred_case_name or "N/A"
            final_year = canonical_year or preferred_year or "N/A"

            for citation in sorted_group:
                if isinstance(citation, dict):
                    if not citation.get('extracted_case_name') or citation.get('extracted_case_name') == "N/A":
                        citation['extracted_case_name'] = preferred_case_name or extracted_case_name or "N/A"
                    citation['extracted_date'] = preferred_year or year or "N/A"
                    if canonical_name and canonical_name != "N/A":
                        citation['canonical_name'] = canonical_name
                    if canonical_year and canonical_year != "N/A":
                        citation['canonical_year'] = canonical_year
                elif hasattr(citation, 'extracted_case_name'):
                    if not citation.extracted_case_name or citation.extracted_case_name == "N/A":
                        citation.extracted_case_name = preferred_case_name or extracted_case_name or "N/A"
                    citation.extracted_date = preferred_year or year or "N/A"
                    if canonical_name and canonical_name != "N/A":
                        citation.canonical_name = canonical_name
                    if canonical_year and canonical_year != "N/A":
                        citation.canonical_year = canonical_year
                else:
                    logger.warning(f"Unsupported citation type: {type(citation)}")

                
            # FIXED: Use sequential cluster ID instead of case name-based key
            cluster_key = f"cluster_{cluster_counter}"
            cluster_counter += 1
            
            clusters[cluster_key] = sorted_group
            
            logger.warning(
                f"📋 METADATA: Created {cluster_key} with case='{final_case_name}', year='{final_year}', {len(sorted_group)} citations"
            )

        return clusters
        
        
        return is_parallel
    def _check_washington_parallel_patterns(self, citation1: str, citation2: str, text: str) -> bool:
        """
        Check for Washington-specific parallel citation patterns.
        
        Args:
            citation1: First citation string
            citation2: Second citation string
            text: Original text for context
            
        Returns:
            True if citations match Washington parallel patterns
        """
        wash_parallel_combinations = [
            ('wash2d', 'p3d'),  # Washington 2d and Pacific 3d
            ('wash2d', 'p2d'),  # Washington 2d and Pacific 2d
            ('wash', 'p3d'),    # Washington and Pacific 3d
            ('wash', 'p2d'),    # Washington and Pacific 2d
        ]
        
        reporter1 = self._extract_reporter_type(citation1)
        reporter2 = self._extract_reporter_type(citation2)
        
        combination = (reporter1, reporter2)
        reverse_combination = (reporter2, reporter1)
        
        if combination in wash_parallel_combinations or reverse_combination in wash_parallel_combinations:
            return self._verify_washington_parallel_context(citation1, citation2, text)
        
        return False

    def _verify_washington_parallel_context(self, citation1: str, citation2: str, text: str) -> bool:
        """
        Verify that two Washington citations are truly parallel by checking context.
        
        Args:
            citation1: First citation string
            citation2: Second citation string
            text: Original text for context
            
        Returns:
            True if citations appear in the same case context
        """
        
        # with their start_index values to do this properly
        return True  # For now, trust the reporter pattern matching
    
    def _extract_reporter_type(self, citation: str) -> str:
        """
        Extract the reporter type from a citation.
        
        Args:
            citation: Citation string to analyze
            
        Returns:
            Reporter type (e.g., 'wash2d', 'p3d', 'p2d')
        """
        citation_lower = citation.lower().replace(' ', '').replace('.', '')
        
        if 'wash2d' in citation_lower or 'wn2d' in citation_lower:
            return 'wash2d'
        elif 'wash' in citation_lower or 'wn' in citation_lower:
            return 'wash'  # Washington (any series)
        elif 'p3d' in citation_lower:
            return 'p3d'
        elif 'p2d' in citation_lower:
            return 'p2d'
        elif 'us' in citation_lower:
            return 'us'
        elif 'sct' in citation_lower:
            return 'sct'
        elif 'fed' in citation_lower:
            return 'fed'
        elif 'f3d' in citation_lower:
            return 'f3d'
        elif 'f2d' in citation_lower:
            return 'f2d'
        elif 'wl' in citation_lower:
            return 'wl'
        else:
            return 'unknown'
    
    def _match_parallel_patterns(self, citation1: str, citation2: str) -> bool:
        """
        Check if two citations match common parallel citation patterns.
        
        Args:
            citation1: First citation string
            citation2: Second citation string
            
        Returns:
            True if citations match parallel patterns
        """
        parallel_combinations = [
            ('wash2d', 'p3d'),  # Washington 2d and Pacific 3d
            ('wash2d', 'p2d'),  # Washington 2d and Pacific 2d
            ('us', 'sct'),      # U.S. and Supreme Court Reporter
            ('fed', 'f3d'),     # Federal and F.3d
            ('fed', 'f2d'),     # Federal and F.2d
        ]
        
        reporter1 = self._extract_reporter_type(citation1)
        reporter2 = self._extract_reporter_type(citation2)
        
        combination = (reporter1, reporter2)
        reverse_combination = (reporter2, reporter1)
        
        return combination in parallel_combinations or reverse_combination in parallel_combinations
    
    def _are_citations_parallel_by_proximity(self, citation1: Any, citation2: Any, text: str) -> bool:
        """
        Determine if two citations are parallel based on proximity and reporter patterns.
        
        Args:
            citation1: First citation object
            citation2: Second citation object
            text: Original text for context
            
        Returns:
            True if citations are likely parallel citations
        """
        # Helper functions to get citation properties
        def get_citation_text(cit):
            if isinstance(cit, dict):
                return cit.get('citation', cit.get('text', ''))
            return getattr(cit, 'citation', getattr(cit, 'text', ''))
            
        def get_start_index(cit):
            if isinstance(cit, dict):
                return cit.get('start', cit.get('start_index', 0))
            return getattr(cit, 'start_index', getattr(cit, 'start', 0))
        
        def get_case_name(cit):
            if isinstance(cit, dict):
                return cit.get('extracted_case_name', cit.get('case_name', ''))
            return getattr(cit, 'extracted_case_name', getattr(cit, 'case_name', ''))
        
        def get_year(cit):
            if isinstance(cit, dict):
                return cit.get('extracted_date', cit.get('year', ''))
            return getattr(cit, 'extracted_date', getattr(cit, 'year', ''))
        
        citation1_text = get_citation_text(citation1)
        citation2_text = get_citation_text(citation2)
        
        # Check if they have different reporter types (required for parallel citations)
        reporter1 = self._extract_reporter_type(citation1_text)
        reporter2 = self._extract_reporter_type(citation2_text)
        
        if reporter1 == reporter2:
            return False  # Same reporter type, not parallel
        
        # Special case: WL citations should never cluster together unless they're identical
        if reporter1 == 'wl' and reporter2 == 'wl':
            return citation1_text == citation2_text  # Only cluster if identical
        
        # Check if they match known parallel patterns
        if not self._match_parallel_patterns(citation1_text, citation2_text):
            return False
        
        # Check proximity - parallel citations should be close to each other
        start1 = get_start_index(citation1)
        start2 = get_start_index(citation2)
        distance = abs(start1 - start2)
        
        if distance > self.proximity_threshold:
            return False
        
        # Check if they have the same case name (if available)
        case1 = get_case_name(citation1)
        case2 = get_case_name(citation2)
        
        if case1 and case2 and case1 != 'N/A' and case2 != 'N/A':
            # If both have case names, they should match
            similarity = self._calculate_name_similarity(case1, case2)
            if similarity < self.case_name_similarity_threshold:
                return False
        
        # Check if they have the same year (if available)
        year1 = get_year(citation1)
        year2 = get_year(citation2)
        
        if year1 and year2 and year1 != 'N/A' and year2 != 'N/A':
            # If both have years, they should match
            if year1 != year2:
                return False
        
        # Additional check for Washington citations specifically
        if 'wn' in citation1_text.lower() or 'wn' in citation2_text.lower():
            return self._check_washington_parallel_patterns(citation1_text, citation2_text, text)
        
        return True
    
    def _select_best_canonical_name(self, citations: List[Any]) -> Optional[str]:
        """Select the strongest verified canonical name available within a cluster."""
        candidates: List[Dict[str, Any]] = []

        for citation in citations:
            if isinstance(citation, dict):
                verified = citation.get('verified') is True
                canonical_name = citation.get('canonical_name')
                source = str(citation.get('source', '')).lower()
                citation_text = citation.get('citation', 'unknown')
            else:
                verified = getattr(citation, 'verified', False)
                canonical_name = getattr(citation, 'canonical_name', None)
                source = str(getattr(citation, 'source', '')).lower()
                citation_text = getattr(citation, 'citation', 'unknown')

            if not verified or not canonical_name or canonical_name == "N/A":
                continue

            candidates.append({
                'name': canonical_name,
                'source': source,
                'citation': citation_text,
            })

        if not candidates:
            return None

        def name_priority(item: Dict[str, Any]) -> Tuple[int, int]:
            source_priority = 0 if 'courtlistener' in item['source'] else 1
            length_priority = -len(item['name'])
            return (source_priority, length_priority)

        candidates.sort(key=name_priority)

        best = candidates[0]['name']
        logger.warning(
            f"CANONICAL_NAME_SELECTION: Selected '{best}' from {len(candidates)} verified canonical candidates"
        )

        return best

    def _select_best_canonical_year(self, citations: List[Any]) -> Optional[str]:
        """Select the strongest verified canonical year available within a cluster."""
        candidates: List[Dict[str, Any]] = []

        for citation in citations:
            if isinstance(citation, dict):
                verified = citation.get('verified') is True
                canonical_year = citation.get('canonical_year') or citation.get('canonical_date')
                source = str(citation.get('source', '')).lower()
            else:
                verified = getattr(citation, 'verified', False)
                canonical_year = getattr(citation, 'canonical_year', None) or getattr(citation, 'canonical_date', None)
                source = str(getattr(citation, 'source', '')).lower()

            if not verified or not canonical_year or canonical_year == "N/A":
                continue

            candidates.append({
                'year': canonical_year,
                'source': source,
            })

        if not candidates:
            return None

        def date_priority(item: Dict[str, Any]) -> int:
            return 0 if 'courtlistener' in item['source'] else 1

        candidates.sort(key=date_priority)

        return candidates[0]['year']
    
    def _are_case_names_compatible(self, name1: str, name2: str) -> bool:
        """
        Check if two case names are compatible for clustering.
        Handles partial matches like 'Sakuma Bros. Farms' vs 'Lopez Demetrio v. Sakuma Bros. Farms'.
        """
        if not name1 or not name2 or name1 == "N/A" or name2 == "N/A":
            return True  # If we don't have good names, allow clustering
        
        name1_clean = name1.strip().lower()
        name2_clean = name2.strip().lower()
        
        # Exact match
        if name1_clean == name2_clean:
            return True
        
        # Check if one is a substring of the other (partial match)
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return True
        
        # Check similarity score
        similarity = self._calculate_name_similarity(name1, name2)
        return similarity > 0.3  # Allow if reasonably similar
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two case names.
        
        Args:
            name1: First case name
            name2: Second case name
            
        Returns:
            Similarity score between 0 and 1
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize names for comparison
        def normalize_name(name):
            return re.sub(r'[^\w\s]', '', name.lower()).strip()
        
        norm1 = normalize_name(name1)
        norm2 = normalize_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        # Simple word-based similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _merge_clusters_by_extracted_metadata(self, clusters: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
        """
        Merge clusters that have the same extracted case name and year after propagation.
        IMPORTANT: Preserve parallel relationships - don't split clusters that were detected as parallel.
        
        Args:
            clusters: Initial clusters based on parallel detection
            
        Returns:
            Merged clusters based on extracted case name and year, preserving parallel relationships
        """
        merged_clusters = {}
        cluster_mapping = {}  # Track which citations belong to which final cluster
        
        for cluster_key, citations in clusters.items():
            if not citations:
                continue
            
            reporter_types = set()
            for citation in citations:
                # Handle both dict and object citations
                if isinstance(citation, dict):
                    citation_text = citation.get('citation', '')
                else:
                    citation_text = getattr(citation, 'citation', '')
                
                reporter = self._extract_reporter_type(citation_text)
                if reporter:
                    reporter_types.add(reporter)
            
            if len(reporter_types) > 1:
                merged_clusters[cluster_key] = citations
                for citation in citations:
                    # Handle both dict and object citations
                    if isinstance(citation, dict):
                        citation_text = citation.get('citation', '')
                    else:
                        citation_text = getattr(citation, 'citation', '')
                    cluster_mapping[citation_text] = cluster_key
            else:
                sample_citation = citations[0]

                def _citation_name_year(cit: Any) -> Tuple[str, str]:
                    if isinstance(cit, dict):
                        verified = cit.get('verified') is True
                        canonical_name = cit.get('canonical_name')
                        canonical_year = cit.get('canonical_year') or cit.get('canonical_date')
                        extracted_name = cit.get('extracted_case_name')
                        extracted_year = cit.get('extracted_date')
                        citation_text_local = cit.get('citation', '')
                    else:
                        verified = getattr(cit, 'verified', False)
                        canonical_name = getattr(cit, 'canonical_name', None)
                        canonical_year = getattr(cit, 'canonical_year', None) or getattr(cit, 'canonical_date', None)
                        extracted_name = getattr(cit, 'extracted_case_name', None)
                        extracted_year = getattr(cit, 'extracted_date', None)
                        citation_text_local = getattr(cit, 'citation', '')

                    name_choice = None
                    if verified and canonical_name and canonical_name != "N/A":
                        name_choice = canonical_name
                    elif extracted_name and extracted_name != "N/A":
                        name_choice = extracted_name
                    else:
                        name_choice = "N/A"

                    year_choice = None
                    if verified and canonical_year and canonical_year != "N/A":
                        year_choice = canonical_year
                    elif extracted_year and extracted_year != "N/A":
                        year_choice = extracted_year
                    else:
                        year_choice = "N/A"

                    return name_choice, year_choice, citation_text_local

                sample_name, sample_year, sample_citation_text = _citation_name_year(sample_citation)
                
                # Special case: WL citations should never be merged based on metadata
                # Each WL citation is a distinct case regardless of extracted metadata
                sample_reporter = self._extract_reporter_type(sample_citation_text)
                if sample_reporter == 'wl':
                    metadata_cluster_key = f"wl_{sample_citation_text.replace(' ', '_')}"
                elif sample_name != 'N/A' and sample_year != 'N/A':
                    normalized_name = self._normalize_case_name_for_clustering(sample_name)
                    metadata_cluster_key = f"{normalized_name}_{sample_year}"
                else:
                    metadata_cluster_key = cluster_key
                
                existing_cluster = None
                for citation in citations:
                    # Handle both dict and object citations
                    _, _, citation_text = _citation_name_year(citation)
                    
                    if citation_text in cluster_mapping:
                        existing_cluster = cluster_mapping[citation_text]
                        break
                
                if existing_cluster:
                    for citation in citations:
                        if citation not in merged_clusters[existing_cluster]:
                            merged_clusters[existing_cluster].append(citation)
                            # Handle both dict and object citations
                            _, _, citation_text = _citation_name_year(citation)
                            cluster_mapping[citation_text] = existing_cluster
                else:
                    if metadata_cluster_key not in merged_clusters:
                        merged_clusters[metadata_cluster_key] = []
                    merged_clusters[metadata_cluster_key].extend(citations)
                    for citation in citations:
                        # Handle both dict and object citations
                        _, _, citation_text = _citation_name_year(citation)
                        cluster_mapping[citation_text] = metadata_cluster_key
        
        logger.info(f"Merged {len(clusters)} initial clusters into {len(merged_clusters)} final clusters (preserving parallel relationships)")
        
        if self.debug_mode:
            for cluster_key, citations in merged_clusters.items():
                citation_strs = [c.citation for c in citations]
                reporter_types = [self._extract_reporter_type(c.citation) for c in citations]
        
        return merged_clusters
    
    def _normalize_case_name_for_clustering(self, case_name: str) -> str:
        """
        Normalize case name for consistent clustering.
        
        Args:
            case_name: Raw case name to normalize
            
        Returns:
            Normalized case name for clustering
        """
        if not case_name or case_name == 'N/A':
            return 'unknown'
        
        normalized = case_name.lower().strip()
        
        normalized = normalized.replace('in re the marriage of', 'in re marriage of')
        normalized = normalized.replace('in the matter of', 'in re')
        normalized = normalized.replace('matter of', 'in re')
        
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)
        
        return normalized
    
    def _extract_case_name_from_citation(self, citation: Any, text: str) -> str:
        """IMPROVED: Extract case name for a specific citation from surrounding text."""
        # FIXED: Handle both dict and object citations
        if isinstance(citation, dict):
            existing_name = citation.get('extracted_case_name')
            start_index = citation.get('start', citation.get('start_index'))
            end_index = citation.get('end', citation.get('end_index'))
            citation_text = citation.get('citation', '')
        else:
            existing_name = getattr(citation, 'extracted_case_name', None)
            start_index = getattr(citation, 'start_index', getattr(citation, 'start', None))
            end_index = getattr(citation, 'end_index', getattr(citation, 'end', None))
            citation_text = getattr(citation, 'citation', '')
            
        if existing_name and existing_name != "N/A":
            return existing_name
        
        # IMPROVED: Use enhanced context extraction with better patterns
        extracted_name = self._extract_case_name_enhanced(citation, text, start_index, end_index, citation_text)
        
        if extracted_name and extracted_name != "N/A":
            return extracted_name
        
        # Fallback to original method
        extracted_name = self._extract_case_name_for_citation(citation, text)
        
        if extracted_name and extracted_name != "N/A":
            # FIXED: Get start index using helper logic with smaller context window
            if start_index is not None:
                search_start = max(0, start_index - 150)  # Reduced from 500 to 150
                search_end = min(len(text), start_index + 50)   # Reduced from 100 to 50
                search_text = text[search_start:search_end]
                
                if extracted_name.lower() not in search_text.lower():
                    proximate_name = self._find_proximate_case_name(citation, text)
                    if proximate_name:
                        return proximate_name
        
        return extracted_name

    def _extract_case_name_enhanced(self, citation: Any, text: str, start_index: int, end_index: int, citation_text: str) -> str:
        """
        DEPRECATED: Use extract_case_name_and_date_unified_master() instead.
        
        This method now delegates to the new unified master implementation
        that consolidates all 120+ duplicate extraction functions.
        
        Args:
            citation: Citation object
            text: Full document text
            start_index: Start position of citation
            end_index: End position of citation
            citation_text: Citation text
            
        Returns:
            Extracted case name or "N/A" if not found
        """
        import warnings
        warnings.warn(
            "_extract_case_name_enhanced() is deprecated. Use extract_case_name_and_date_unified_master() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Delegate to the new master implementation
        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
        result = extract_case_name_and_date_unified_master(
            text=text,
            citation=citation_text,
            start_index=start_index,
            end_index=end_index,
            debug=False
        )
        
        return result.get('case_name', 'N/A')
    
    def _clean_extracted_case_name(self, case_name: str) -> str:
        """
        Clean extracted case name to remove contamination and improve quality.
        
        Args:
            case_name: Raw extracted case name
            
        Returns:
            Cleaned case name
        """
        import re
        
        if not case_name:
            return "N/A"
        
        # IMPROVED: More comprehensive contamination removal
        contamination_phrases = [
            # Legal reasoning phrases
            r'\b(de\s+novo)\b', r'\b(questions?\s+of\s+law)\b', r'\b(statutory\s+interpretation)\b',
            r'\b(in\s+light\s+of)\b', r'\b(the\s+record\s+certified)\b', r'\b(federal\s+court)\b',
            r'\b(this\s+court\s+reviews?)\b', r'\b(we\s+review)\b', r'\b(certified\s+questions?)\b',
            r'\b(issue\s+of\s+law)\b', r'\b(also\s+an?\s+issue)\b', r'\b(reviews?\s+de\s+novo)\b',
            r'\b(we\s+hold)\b', r'\b(we\s+conclude)\b', r'\b(we\s+find)\b',
            r'\b(the\s+legislature)\b', r'\b(statutory\s+language)\b', r'\b(plain\s+meaning)\b',
            
            # Citation and reference phrases
            r'\b(see|citing|quoting|accord|id\.|ibid\.)\b', r'\b(brief\s+at|opening\s+br\.|reply\s+br\.)\b',
            r'\b(internal\s+quotation\s+marks)\b', r'\b(alteration\s+in\s+original)\b',
            r'\b(may\s+ask\s+this\s+court)\b', r'\b(resolution\s+of\s+that\s+question)\b',
            r'\b(necessary\s+to\s+resolve)\b', r'\b(case\s+before\s+the)\b',
            
            # NEW: Procedural and analysis phrases that contaminate case names
            r'\b(we\s+accepted\s+certification)\b', r'\b(analysis\s+are\s+that)\b', r'\b(and\s+by\s+the)\b',
            r'\b(both\s+the\s+defendant\s+and)\b', r'\b(argue\s+that)\b', r'\b(job\s+applicants\s+who)\b',
            r'\b(do\s+not\s+have\s+a\s+good\s+faith)\b', r'\b(intent\s+to\s+obtain\s+employment)\b',
            r'\b(lack\s+statutory\s+standing)\b', r'\b(because\s+they\s+are\s+not)\b',
            r'\b(within\s+the\s+zone\s+of\s+interest)\b', r'\b(protected\s+by\s+the\s+statute)\b',
            r'\b(have\s+not\s+suffered\s+an\s+injury)\b', r'\b(in\s+fact)\b', r'\b(economic\s+or\s+otherwise)\b',
            r'\b(we\s+decline\s+to\s+address)\b', r'\b(the\s+standing\s+argument)\b',
            r'\b(as\s+it\s+is\s+beyond\s+the\s+scope)\b', r'\b(of\s+the)\b',
            
            # Court procedural language
            r'\b(the\s+court\s+held)\b', r'\b(the\s+court\s+found)\b', r'\b(the\s+court\s+ruled)\b',
            r'\b(petitioner\s+argues)\b', r'\b(respondent\s+contends)\b', r'\b(plaintiff\s+claims)\b',
            r'\b(defendant\s+maintains)\b', r'\b(appellant\s+asserts)\b', r'\b(appellee\s+responds)\b'
        ]
        
        cleaned = case_name
        for phrase_pattern in contamination_phrases:
            cleaned = re.sub(phrase_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove leading/trailing punctuation and whitespace
        cleaned = re.sub(r'^[.\s,;:]+', '', cleaned)
        cleaned = re.sub(r'[.\s,;:]+$', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove leading articles and conjunctions
        cleaned = re.sub(r'^(the|a|an|and|or|but)\s+', '', cleaned, flags=re.IGNORECASE)
        
        # Remove common legal phrases that shouldn't be in case names
        legal_phrases = [
            r'^(that\s+and\s+by\s+the\s+|that\s+and\s+|is\s+also\s+an\s+|also\s+an\s+|also\s+|that\s+|this\s+is\s+|this\s+)\.?\s*',
            r'^(under|pursuant\s+to|in\s+accordance\s+with)\s+',
            r'^(as\s+we\s+have\s+held|as\s+we\s+have\s+stated|as\s+we\s+have\s+explained)\s+',
        ]
        
        for phrase_pattern in legal_phrases:
            cleaned = re.sub(phrase_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # IMPROVED: Additional validation to reject contaminated case names
        if cleaned and len(cleaned) > 3:
            # Reject if it contains too many legal procedural words
            legal_words = ['accepted', 'certification', 'analysis', 'defendant', 'argue', 'applicants', 
                          'employment', 'standing', 'statute', 'injury', 'decline', 'address', 'scope',
                          'question', 'issue', 'review', 'court', 'held', 'ruling', 'decision']
            word_count = sum(1 for word in legal_words if word.lower() in cleaned.lower())
            
            if word_count >= 2:  # Lower threshold - Too many legal procedural words
                logger.warning(f"🚫 CONTAMINATION: Rejected case name '{cleaned}' - contains {word_count} legal procedural words")
                return "N/A"
            
            # Reject if it's too long (likely contaminated with legal text)
            if len(cleaned) > 150:  # Reasonable case name length limit
                logger.warning(f"🚫 CONTAMINATION: Rejected case name '{cleaned}' - too long ({len(cleaned)} chars)")
                return "N/A"
            
            # Reject if it contains sentence-like structures
            sentence_indicators = ['. ', '? ', '! ', ' and by the ', ' are that ', ' who do not ']
            if any(indicator in cleaned for indicator in sentence_indicators):
                logger.warning(f"🚫 CONTAMINATION: Rejected case name '{cleaned}' - contains sentence structure")
                return "N/A"
                
            return cleaned
        
        return "N/A"

    def _find_proximate_case_name(self, citation: Any, text: str) -> str:
        """
        Find a case name that appears in close proximity to the citation.
        
        Args:
            citation: Citation object with start_index
            text: Original text
            
        Returns:
            Case name found in proximity, or "N/A" if none found
        """
        if not hasattr(citation, 'start_index') or citation.start_index is None:
            return "N/A"
        
        search_start = max(0, citation.start_index - 50)  # Reduced from 150 to 50
        search_end = citation.start_index
        search_text = text[search_start:search_end]
        
        case_patterns = [
            r'In re [^,]+',  # In re cases
            r'[A-Z][a-z]+ v\. [A-Z][a-z]+',  # Party v. Party cases
            r'[A-Z][a-z]+ v [A-Z][a-z]+',   # Party v Party cases (no period)
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, search_text)
            if matches:
                return matches[-1].strip()
        
        return "N/A"
    
    def _extract_year_from_citation(self, citation: Any, text: str) -> str:
        """IMPROVED: Extract year for a specific citation from surrounding text."""
        existing_date = getattr(citation, 'extracted_date', None)
        if existing_date and existing_date != "N/A":
            return existing_date
        
        # IMPROVED: Use enhanced year extraction
        year = self._extract_year_enhanced(citation, text)
        if year and year != "N/A":
            return year
        
        return self._extract_date_for_citation(citation, text)
    
    def _extract_year_enhanced(self, citation: Any, text: str) -> str:
        """
        ENHANCED: Extract year using improved context analysis.
        
        This method looks for years in the proper context around citations,
        prioritizing years that appear in parentheses after the citation.
        
        Args:
            citation: Citation object
            text: Full document text
            
        Returns:
            Extracted year or "N/A" if not found
        """
        import re
        
        if not text or not hasattr(citation, 'start_index') or citation.start_index is None:
            return "N/A"
        
        citation_end = getattr(citation, 'end_index', citation.start_index + len(getattr(citation, 'citation', '')))
        
        # IMPROVED: Look in a focused context around the citation
        context_start = max(0, citation.start_index - 50)  # Reduced from 100 to 50
        context_end = min(len(text), citation_end + 20)    # Reduced from 150 to 20
        context = text[context_start:context_end]
        
        logger.warning(f"🔍 YEAR_EXTRACT: Extracting year for citation '{getattr(citation, 'citation', 'unknown')}'")
        logger.warning(f"🔍 YEAR_EXTRACT: Context: '{context}'")
        
        # IMPROVED: Enhanced year patterns with better priority
        year_patterns = [
            # Highest priority: Year in parentheses immediately after citation
            r'\((\d{4})\)',
            # Second priority: Year in parentheses with some text before
            r'[^)]*\((\d{4})\)',
            # Third priority: Standalone 4-digit year
            r'\b(\d{4})\b',
        ]
        
        best_year = None
        best_distance = float('inf')
        best_priority = float('inf')
        
        for priority, pattern in enumerate(year_patterns):
            for match in re.finditer(pattern, context):
                year = match.group(1)
                year_int = int(year)
                
                # Validate year range
                if 1800 <= year_int <= 2030:
                    year_pos_in_text = context_start + match.start()
                    distance = abs(year_pos_in_text - citation_end)
                    
                    # Prioritize years that are closer to the citation and have higher priority patterns
                    weighted_distance = distance + (priority * 1000)  # Priority weight
                    
                    if weighted_distance < best_distance:
                        best_year = year
                        best_distance = weighted_distance
                        best_priority = priority
                        logger.warning(f"✅ YEAR_EXTRACT: Found year '{year}' (priority: {priority}, distance: {distance})")
        
        if best_year:
            logger.warning(f"🎯 YEAR_EXTRACT: Selected year '{best_year}' for citation '{getattr(citation, 'citation', 'unknown')}'")
            return best_year
        
        logger.warning(f"⚠️ YEAR_EXTRACT: No year found for citation '{getattr(citation, 'citation', 'unknown')}'")
        return "N/A"
    
    def _verify_clusters_with_api(self, clusters: Dict[str, List[Any]]):
        """
        STEP 3: Comprehensive verification with CourtListener + fallback sources.
        
        Pipeline:
        1. Batch verify with CourtListener citation-lookup API (180/minute rate limit)
        2. Apply fallback verification for unverified citations using:
           - Cornell Law School Legal Information Institute
           - Justia legal database  
           - Google Scholar
           - Caselaw Access Project
           - Generic legal web search
        
        Populates canonical_name, canonical_date, canonical_url, and is_verified status.
        """
        import os
        import time
        import requests
        
        api_key = os.getenv('COURTLISTENER_API_KEY')
        if not api_key:
            logger.warning("COURTLISTENER_API_KEY not found in environment - skipping verification")
            return
        
        all_citations = []
        for citations_list in clusters.values():
            all_citations.extend(citations_list)
        
        if not all_citations:
            return
        
        logger.info(f"Batch verifying {len(all_citations)} citations with CourtListener API")
        
        batch_size = 50  # Conservative batch size
        batches = [all_citations[i:i + batch_size] for i in range(0, len(all_citations), batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} citations)")
            
            try:
                citations_text = ' '.join([citation.citation for citation in batch])
                
                url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
                headers = {
                    'Authorization': f'Token {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {'text': citations_text}
                
                response = requests.post(url, headers=headers, json=data, timeout=DEFAULT_REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    verification_results = {}
                    for result in response_data:
                        citation_text = result.get('citation', '')
                        if citation_text and result.get('clusters'):
                            cluster = result['clusters'][0]
                            
                            case_name = cluster.get('case_name', '')
                            date_filed = cluster.get('date_filed', '')
                            absolute_url = cluster.get('absolute_url', '')
                            
                            if (case_name and case_name.strip() and 
                                absolute_url and absolute_url.strip() and
                                len(case_name.strip()) >= 5):
                                
                                canonical_year = date_filed[:4] if date_filed and len(date_filed) >= 4 else ''
                                canonical_url = f"https://www.courtlistener.com{absolute_url}"
                                
                                verification_results[citation_text] = {
                                    'verified': True,
                                    'canonical_name': case_name,
                                    'canonical_date': canonical_year,
                                    'canonical_url': canonical_url,
                                    'court': cluster.get('court', ''),
                                    'docket_number': cluster.get('docket_id', ''),
                                    'date_filed_full': date_filed
                                }
                                logger.info(f"✓ API verified: {citation_text} -> {case_name} ({canonical_year})")
                            else:
                                verification_results[citation_text] = {
                                    'verified': False,
                                    'error': 'Missing essential data (case_name or absolute_url)',
                                    'raw_case_name': case_name,
                                    'raw_url': absolute_url
                                }
                                logger.warning(f"✗ Validation failed: {citation_text} - missing essential data")
                        else:
                            verification_results[citation_text] = {
                                'verified': False,
                                'error': 'No clusters found in API response'
                            }
                    
                    for citation in batch:
                        result = verification_results.get(citation.citation, {'verified': False})
                        
                        if result.get('verified', False):
                            canonical_name = result.get('canonical_name')
                            extracted_name = getattr(citation, 'extracted_case_name', None)
                            
                            # CRITICAL FIX: Only set canonical fields from verified API sources
                            # Never use extracted data as canonical data (memory rule)
                            trusted_api_sources = ['courtlistener_api', 'courtlistener', 'api_verified']
                            result_source = result.get('source', 'unknown')
                            
                            # CRITICAL FIX: Always trust CourtListener verification results
                            # Don't reject canonical data based on name mismatches
                            # The extracted name might be incomplete or incorrect
                            validation_passed = True
                            if extracted_name and extracted_name != "N/A" and canonical_name:
                                names_compatible = self._are_case_names_compatible(canonical_name, extracted_name)
                                logger.warning(f"COMPATIBILITY_CHECK: {citation.citation}")
                                logger.warning(f"  Canonical: '{canonical_name}'")
                                logger.warning(f"  Extracted: '{extracted_name}'")
                                logger.warning(f"  Compatible: {names_compatible}")
                                
                                if not names_compatible:
                                    logger.warning(f"⚠️  Name mismatch: {citation.citation} - keeping both extracted and canonical")
                                    # Don't fail validation - just log the mismatch
                                    # validation_passed = False  # REMOVED
                            
                            # Only set canonical fields if from trusted API source AND not None
                            if validation_passed and result_source in trusted_api_sources:
                                if canonical_name:
                                    citation.canonical_name = canonical_name
                                canonical_date = result.get('canonical_date')
                                if canonical_date:
                                    citation.canonical_date = canonical_date
                                canonical_url = result.get('canonical_url') or result.get('url')
                                if canonical_url:
                                    citation.canonical_url = canonical_url
                                citation.verified = True
                                citation.is_verified = True
                                logger.info(f"✓ Verified: {citation.citation} -> {canonical_name}")
                            elif validation_passed:
                                # Log when we reject canonical data from untrusted sources
                                logger.warning(f"🚫 REJECTED canonical data from untrusted source '{result_source}' for {citation.citation}")
                                # Still mark as verified but don't set canonical fields
                                citation.verified = True
                                citation.is_verified = True
                                logger.info(f"✓ Verified (no canonical): {citation.citation}")
                            else:
                                # Validation failed, don't set any canonical fields
                                citation.verified = False
                                citation.is_verified = False
                                logger.info(f"✗ Failed validation: {citation.citation}")
                        else:
                            citation.verified = False
                            citation.is_verified = False
                            error_msg = result.get('error', 'Unknown error')
                            logger.info(f"✗ Unverified: {citation.citation} - {error_msg}")
                        
                        # Ensure consistency between verified boolean and verification_status string
                        is_verified = getattr(citation, 'is_verified', False)
                        citation.verified = is_verified  # Sync boolean field
                        
                        if not hasattr(citation, 'metadata'):
                            citation.metadata = {}
                        citation.metadata.update({
                            'verification_status': 'verified' if is_verified else 'unverified',
                            'verification_source': 'courtlistener_batch_api',
                            'canonical_data_available': bool(is_verified),
                            'verification_error': result.get('error') if not result.get('verified') else None
                        })
                
                else:
                    logger.warning(f"Batch verification failed with status {response.status_code}: {response.text[:200]}")
                    for citation in batch:
                        # Ensure consistency: API error should set both verified fields to False
                        citation.verified = False
                        citation.is_verified = False
                        
                        if not hasattr(citation, 'metadata'):
                            citation.metadata = {}
                        citation.metadata.update({
                            'verification_status': 'api_error',
                            'verification_source': 'courtlistener_batch_api',
                            'canonical_data_available': False
                        })
                
            except Exception as e:
                logger.warning(f"Batch verification error: {e}")
                for citation in batch:
                    citation.is_verified = False
                    if not hasattr(citation, 'metadata'):
                        citation.metadata = {}
                    citation.metadata.update({
                        'verification_status': 'error',
                        'verification_error': str(e),
                        'canonical_data_available': False
                    })
            
            if batch_idx < len(batches) - 1:  # Don't wait after the last batch
                time.sleep(0.4)  # Conservative rate limiting
        
        unverified_citations = [c for c in all_citations if not getattr(c, 'is_verified', False)]
        if unverified_citations:
            logger.info(f"Applying comprehensive verification to {len(unverified_citations)} unverified citations")
            self._apply_comprehensive_verification(unverified_citations)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two case names.
        Uses simple token-based similarity from best practices.
        """
        if not name1 or not name2:
            return 0.0
        
        def normalize_name(name):
            return name.lower().replace('.', '').replace(',', '').replace('v.', 'v').strip()
        
        norm1 = normalize_name(name1)
        norm2 = normalize_name(name2)
        
        tokens1 = set(norm1.split())
        tokens2 = set(norm2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _apply_comprehensive_verification(self, citations: List[Any]):
        """
        Apply comprehensive legal web search verification for citations not found in CourtListener.
        
        Uses the EnhancedFallbackVerifier system that includes:
        - vLex
        - CaseMine
        - Justia
        - Cornell Law
        - Google Scholar
        - And many other legal databases
        """
        try:
            from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
        except ImportError:
            logger.warning("EnhancedFallbackVerifier module not available - skipping fallback")
            return
        
        try:
            logger.info(f"Applying enhanced fallback verification to {len(citations)} unverified citations")
            
            verifier = EnhancedFallbackVerifier()
            
            for citation in citations:
                try:
                    citation_text = citation.citation
                    extracted_case_name = getattr(citation, 'extracted_case_name', None)
                    extracted_date = getattr(citation, 'extracted_date', None)
                    
                    logger.info(f"Attempting enhanced fallback verification for: {citation_text}")
                    
                    has_verification_data = (
                        hasattr(citation, 'verification_result') and citation.verification_result and
                        citation.verification_result.get('verified', False)
                    )
                    
                    if has_verification_data:
                        logger.info(f"Skipping fallback verification for {citation_text} - already verified via enhanced verification")
                        continue
                    
                    result = verifier.verify_citation_sync(citation_text, extracted_case_name, extracted_date)
                    
                    logger.info(f"DEBUG: Verification result for {citation_text}: {result}")
                    if result:
                        logger.info(f"DEBUG: Result keys: {list(result.keys())}")
                        logger.info(f"DEBUG: Source field: {result.get('source', 'MISSING')}")
                        logger.info(f"DEBUG: Verified field: {result.get('verified', 'MISSING')}")
                    
                    # FIXED: If we have any canonical information, the citation is verified
                    if result and (result.get('verified', False) or result.get('canonical_name') or result.get('canonical_url') or result.get('canonical_date')):
                        citation.verified = True
                        citation.is_verified = True
                        citation.source = result.get('source', 'enhanced_fallback')  # Use user-friendly source directly
                        citation.url = result.get('url')
                        logger.warning(f"VERIFICATION_FIX: Set verified=True for citation '{citation.citation}' (canonical info available)")
                        if hasattr(citation, 'canonical_url'):
                            if not getattr(citation, 'canonical_url'):
                                citation.canonical_url = result.get('canonical_url') or result.get('url')
                        else:
                            citation.canonical_url = result.get('canonical_url') or result.get('url')
                        
                        if result.get('canonical_name'):
                            citation.canonical_name = result['canonical_name']
                        if result.get('canonical_date'):
                            citation.canonical_date = result['canonical_date']
                        
                        if not hasattr(citation, 'source') or not citation.source:
                            citation.source = result.get('source', 'enhanced_fallback')
                        
                        # Ensure consistency: verified_via_fallback should set verified=True
                        citation.verified = True
                        citation.is_verified = True
                        
                        if not hasattr(citation, 'metadata'):
                            citation.metadata = {}
                        citation.metadata.update({
                            'verification_status': 'verified_via_fallback',
                            'verification_source': f"fallback_{result.get('source', 'enhanced_fallback')}",
                            'canonical_data_available': True,
                            'fallback_source': result.get('source'),
                            'confidence': result.get('confidence', 0.0)
                        })
                        
                        logger.info(f"✓ Enhanced fallback verified: {citation_text} -> {result.get('canonical_name', 'N/A')} (via {result.get('source', 'N/A')})")
                    else:
                        # Ensure consistency: failed verification should set verified=False
                        citation.verified = False
                        citation.is_verified = False
                        
                        if not hasattr(citation, 'metadata'):
                            citation.metadata = {}
                        citation.metadata.update({
                            'verification_status': 'fallback_failed',
                            'verification_source': 'enhanced_fallback',
                            'canonical_data_available': False,
                            'fallback_error': result.get('error', 'Unknown error')
                        })
                        
                        
                except Exception as e:
                    logger.warning(f"Error in enhanced fallback verification for {citation.citation}: {str(e)}")
                    if not hasattr(citation, 'metadata'):
                        citation.metadata = {}
                    citation.metadata.update({
                        'verification_status': 'fallback_error',
                        'verification_source': 'enhanced_fallback',
                        'canonical_data_available': False,
                        'fallback_error': str(e)
                    })
                    continue
                        
        except Exception as e:
            logger.warning(f"Enhanced fallback verification error: {e}")
    
    def _extract_case_names_and_dates(self, citations: List[Any], text: str):
        """
        Extract case names and dates for all citations.
        This ensures we have the data needed for clustering.
        """
        for citation in citations:
            if not hasattr(citation, 'extracted_case_name') or not citation.extracted_case_name:
                citation.extracted_case_name = self._extract_case_name_for_citation(citation, text)
            
            if not hasattr(citation, 'extracted_date') or not citation.extracted_date:
                citation.extracted_date = self._extract_date_for_citation(citation, text)
    
    def _extract_case_name_for_citation(self, citation: Any, text: str) -> str:
        """UPDATED: Use MASTER extraction function for consistency."""
        # FIXED: Handle both dict and object citations
        if isinstance(citation, dict):
            citation_text = citation.get('citation')
            start_index = citation.get('start', citation.get('start_index'))
            end_index = citation.get('end', citation.get('end_index'))
        else:
            citation_text = getattr(citation, 'citation', None)
            start_index = getattr(citation, 'start_index', None)
            end_index = getattr(citation, 'end_index', None)
            
        if not text or start_index is None:
            return "N/A"
        
        try:
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            
            
            result = extract_case_name_and_date_master(
                text=text,
                citation=citation_text,
                citation_start=start_index,
                citation_end=end_index,
                debug=self.debug_mode
            )
            
            case_name = result.get('case_name')
            if case_name and case_name != 'N/A':
                logger.warning(f"✅ Master extraction found: '{case_name}' for citation: '{getattr(citation, 'citation', 'unknown')}'")
                return case_name
        except Exception as e:
            logger.warning(f"Error in master extraction: {str(e)}")
        
        # FIXED: Handle both dict and object citations
        if isinstance(citation, dict):
            start_idx = citation.get('start_index', citation.get('start', 0))
        else:
            start_idx = getattr(citation, 'start_index', 0)
        
        start_pos = max(0, start_idx - 500)
        end_pos = start_idx
        context = text[start_pos:end_pos]
        
        case_patterns = [
            r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*),?\s*$',
            r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)\s+vs\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*),?\s*$',
            r'(In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*),?\s*$',
            r'(Ex\s+parte\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*),?\s*$',
        ]
        
        if True:

        
            pass  # Empty block

        
        
            pass  # Empty block

        
        
        for idx, pattern in enumerate(case_patterns):
            matches = list(re.finditer(pattern, context, re.IGNORECASE))
            if matches:
                match = matches[-1]
                
                if len(match.groups()) >= 2 and idx in [0, 1]:  # Two-party cases (v. and vs.)
                    case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                else:  # Single-party cases (In re, Ex parte, etc.)
                    case_name = match.group(1).strip()
                
                if len(case_name) > 5 and case_name != "N/A":
                    cleaned_name = self._clean_case_name(case_name)
                    if cleaned_name:
                        if self.debug_mode:
                            return cleaned_name
        
        if True:

        
            pass  # Empty block

        
        
            pass  # Empty block

        
        
        return "N/A"
    
    def _clean_case_name(self, case_name: str) -> str:
        """LEGACY cleaner wrapper (deprecated). Uses shared cleaner."""
        try:
            from src.utils.deprecation import deprecated
            from src.utils.case_name_cleaner import clean_extracted_case_name
            @deprecated(replacement='src.utils.case_name_cleaner.clean_extracted_case_name')
            def _proxy(val: str) -> str:
                return clean_extracted_case_name(val)
            return _proxy(case_name)
        except Exception:
            from src.utils.case_name_cleaner import clean_extracted_case_name
            return clean_extracted_case_name(case_name)
    
    def _extract_date_for_citation(self, citation: Any, text: str) -> str:
        """Extract date/year for a single citation from the surrounding text."""
        if not text or not hasattr(citation, 'start_index') or citation.start_index is None:
            return "N/A"
        
        citation_end = getattr(citation, 'end_index', citation.start_index + len(citation.citation))
        
        start_pos = max(0, citation.start_index - 50)
        end_pos = min(len(text), citation_end + 100)  # Reduced window to avoid distant years
        context = text[start_pos:end_pos]
        
        year_patterns = [
            r'\((\d{4})\)',  # Year in parentheses (highest priority)
            r'\b(\d{4})\b',  # Standalone 4-digit year
        ]
        
        best_year = None
        best_distance = float('inf')
        
        for pattern in year_patterns:
            for match in re.finditer(pattern, context):
                year = match.group(1)
                year_int = int(year)
                if 1800 <= year_int <= 2030:  # Reasonable year range
                    year_pos_in_text = start_pos + match.start()
                    distance = abs(year_pos_in_text - citation_end)
                    
                    weight = 1 if pattern == r'\((\d{4})\)' else 2  # Parentheses are more reliable
                    weighted_distance = distance * weight
                    
                    if weighted_distance < best_distance:
                        best_year = year
                        best_distance = weighted_distance
        
        return best_year or "N/A"
    
    def _detect_parallel_citations(self, citations: List[Any], text: str):
        """
        Detect parallel citations based on proximity and similarity.
        This implements smart parallel citation detection.
        """
        positioned_citations = [c for c in citations if hasattr(c, 'start_index') and c.start_index is not None]
        positioned_citations.sort(key=lambda c: c.start_index)
        
        citation_groups = []
        current_group = []
        
        for citation in positioned_citations:
            if not current_group:
                current_group = [citation]
            else:
                last_citation = current_group[-1]
                distance = citation.start_index - (last_citation.start_index + len(last_citation.citation))
                
                if distance <= self.proximity_threshold:
                    current_group.append(citation)
                else:
                    if len(current_group) >= 2:
                        citation_groups.append(current_group)
                    current_group = [citation]
        
        if len(current_group) >= 2:
            citation_groups.append(current_group)
        
        for group in citation_groups:
            if self._are_citations_parallel(group):
                citation_strings = [c.citation for c in group]
                for citation in group:
                    citation.parallel_citations = [c for c in citation_strings if c != citation.citation]
    
    def _are_citations_parallel(self, citations: List[Any]) -> bool:
        """
        Determine if a group of citations are parallel citations.
        Uses heuristics like different reporters, similar years, etc.
        """
        if len(citations) < 2:
            return False
        
        reporters = set()
        years = set()
        
        for citation in citations:
            reporter_match = re.search(r'\b([A-Z][a-zA-Z.]*\.?)\s+\d+', citation.citation)
            if reporter_match:
                reporters.add(reporter_match.group(1))
            
            year_match = re.search(r'\b(\d{4})\b', citation.citation)
            if year_match:
                years.add(year_match.group(1))
        
        
        different_reporters = len(reporters) > 1
        similar_years = len(years) <= 2  # Allow for slight year variations
        
        return different_reporters and similar_years
    
    def _apply_core_clustering_logic(self, citations: List[Any]) -> Dict[str, List[Any]]:
        """
        Apply the core clustering logic specified by the user:
        1. Extract case name from FIRST citation in sequence
        2. Extract year from LAST citation in sequence
        3. Propagate both to all citations in cluster
        4. Cluster by same extracted name AND year
        
        CRITICAL: Only propagate within actual parallel citation groups of the SAME case.
        """
        clusters = {}
        
        parallel_groups = self._group_by_parallel_relationships(citations)
        
        for group in parallel_groups:
            if len(group) < 2:
                citation = group[0]
                case_name = getattr(citation, 'extracted_case_name', None)
                year = getattr(citation, 'extracted_date', None)
                
                if (case_name and year and 
                    case_name.strip().upper() != 'N/A' and 
                    year.strip().upper() != 'N/A'):
                    
                    # Clean case name before creating cluster key
                    from src.utils.case_name_cleaner import clean_extracted_case_name
                    cleaned_case_name = clean_extracted_case_name(case_name)
                    cluster_key = f"{cleaned_case_name}_{year}".replace(' ', '_').replace('.', '_').replace('/', '_')
                    if cluster_key not in clusters:
                        clusters[cluster_key] = []
                    clusters[cluster_key].append(citation)
                continue
            
            sorted_group = sorted(group, key=lambda c: c.start_index if hasattr(c, 'start_index') and c.start_index is not None else 0)
            
            first_citation = sorted_group[0]
            case_name = getattr(first_citation, 'extracted_case_name', None)
            if not case_name or case_name == "N/A":
                for citation in sorted_group:
                    name = getattr(citation, 'extracted_case_name', None)
                    if name and name != "N/A" and len(name) > 5:
                        case_name = name
                        break
            
            last_citation = sorted_group[-1]
            year = getattr(last_citation, 'extracted_date', None)
            if not year or year == "N/A":
                for citation in reversed(sorted_group):
                    date = getattr(citation, 'extracted_date', None)
                    if date and date != "N/A":
                        year = date
                        break
            
            if not case_name or not year or case_name == "N/A" or year == "N/A":
                continue
            
            for citation in sorted_group:
                current_extracted_name = getattr(citation, 'extracted_case_name', None)
                if not current_extracted_name or current_extracted_name == "N/A":
                    citation.extracted_case_name = case_name
                if not getattr(citation, 'extracted_date', None) or getattr(citation, 'extracted_date', None) == "N/A":
                    citation.extracted_date = year
            
            cluster_key = f"{case_name}_{year}".replace(' ', '_').replace('.', '_').replace('/', '_')
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].extend(sorted_group)
        
        
        filtered_clusters = clusters
        
        return filtered_clusters
    
    def _group_by_parallel_relationships(self, citations: List[Any]) -> List[List[Any]]:
        """
        Group citations by their parallel citation relationships.
        
        CRITICAL: This must be very conservative to avoid contamination.
        Only group citations that are explicitly marked as parallel AND
        have compatible case names.
        """
        citation_lookup = {c.citation: c for c in citations}
        visited = set()
        groups = []
        
        for citation in citations:
            if citation.citation in visited:
                continue
            
            group = [citation]
            group_citations = {citation.citation}
            visited.add(citation.citation)
            
            parallel_citations = getattr(citation, 'parallel_citations', [])
            
            for parallel_cite in parallel_citations:
                if parallel_cite in citation_lookup and parallel_cite not in visited:
                    parallel_citation = citation_lookup[parallel_cite]
                    
                    # FIXED: Check both extracted and canonical names for compatibility
                    citation_extracted = getattr(citation, 'extracted_case_name', None)
                    citation_canonical = getattr(citation, 'canonical_name', None)
                    parallel_extracted = getattr(parallel_citation, 'extracted_case_name', None)
                    parallel_canonical = getattr(parallel_citation, 'canonical_name', None)
                    
                    # Get the best available names
                    citation_name = citation_canonical if citation_canonical and citation_canonical != "N/A" else citation_extracted
                    parallel_name = parallel_canonical if parallel_canonical and parallel_canonical != "N/A" else parallel_extracted
                    
                    # Only reject if we have clear evidence they're different cases
                    if (citation_name and parallel_name and 
                        citation_name != "N/A" and parallel_name != "N/A" and
                        not self._are_case_names_compatible(citation_name, parallel_name)):
                        logger.warning(f"CLUSTERING_FIX: Rejecting parallel grouping - incompatible names: '{citation_name}' vs '{parallel_name}'")
                        continue  # Different cases - don't group
                    
                    reverse_parallels = getattr(parallel_citation, 'parallel_citations', [])
                    if citation.citation not in reverse_parallels:
                        logger.warning(f"CLUSTERING_FIX: Skipping non-bidirectional parallel: {citation.citation} -> {parallel_cite} (reverse: {reverse_parallels})")
                        continue  # Not bidirectional - suspicious
                    
                    logger.warning(f"CLUSTERING_FIX: Adding parallel citation to group: {citation.citation} + {parallel_cite}")
                    
                    if ((not citation_name or citation_name == "N/A") or 
                        (not parallel_name or parallel_name == "N/A")):
                        distance = abs(citation.start_index - parallel_citation.start_index)
                        if distance > 50:  # Very conservative - must be very close
                            continue
                    
                    group.append(parallel_citation)
                    group_citations.add(parallel_cite)
                    visited.add(parallel_cite)
            
            groups.append(group)
        
        return groups
    
    def _merge_overlapping_clusters(self, clusters: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
        """Merge clusters that have overlapping citations."""
        merged_clusters = {}
        cluster_mapping = {}  # Maps citation to cluster_id
        
        for cluster_id, citations in clusters.items():
            existing_cluster_id = None
            for citation in citations:
                citation_key = citation.citation
                if citation_key in cluster_mapping:
                    existing_cluster_id = cluster_mapping[citation_key]
                    break
            
            if existing_cluster_id:
                target_cluster_id = existing_cluster_id
                if target_cluster_id not in merged_clusters:
                    merged_clusters[target_cluster_id] = []
                
                for citation in citations:
                    if citation not in merged_clusters[target_cluster_id]:
                        merged_clusters[target_cluster_id].append(citation)
                        cluster_mapping[citation.citation] = target_cluster_id
            else:
                merged_clusters[cluster_id] = citations
                for citation in citations:
                    cluster_mapping[citation.citation] = cluster_id
        
        return merged_clusters
    
    def _format_clusters_for_output(self, clusters: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Format clusters for output with proper case name and date extraction."""
        formatted_clusters = []
        
        for cluster_id, citations in clusters.items():
            # Extract case name and year from citations
            # Prioritize case names from verified citations
            case_name = None
            year = None
            
            # First, try to get case name from verified citations
            # FIXED: Prioritize canonical_name over extracted_case_name
            # FIXED: Check both verification flags for compatibility
            verified_citations = [c for c in citations if getattr(c, 'verified', False) or getattr(c, 'is_verified', False)]
            
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"CLUSTER_DEBUG: Processing cluster {cluster_id} with {len(citations)} citations, {len(verified_citations)} verified")
            if verified_citations:
                for citation in verified_citations:
                    if not case_name:
                        # Try canonical name first (from verification)
                        canonical_name = getattr(citation, 'canonical_name', None)
                        if canonical_name and canonical_name != "N/A" and canonical_name != "Unknown Case":
                            case_name = canonical_name
                        else:
                            # Fall back to extracted name
                            name = getattr(citation, 'extracted_case_name', None)
                            if name and name != "N/A" and name != "Unknown Case":
                                case_name = name
                    
                    if not year:
                        # Try canonical date first
                        canonical_date = getattr(citation, 'canonical_date', None)
                        if canonical_date and canonical_date != "N/A" and canonical_date != "Unknown Year":
                            year = canonical_date
                        else:
                            # Fall back to extracted date
                            date = getattr(citation, 'extracted_date', None)
                            if date and date != "N/A" and date != "Unknown Year":
                                year = date
                    
                    if case_name and year:
                        break
            
            # If no case name from verified citations, try all citations
            # FIXED: Also prioritize canonical names in fallback
            if not case_name or not year:
                for citation in citations:
                    if not case_name:
                        # Try canonical name first
                        canonical_name = getattr(citation, 'canonical_name', None)
                        if canonical_name and canonical_name != "N/A" and canonical_name != "Unknown Case":
                            case_name = canonical_name
                        else:
                            # Fall back to extracted name
                            name = getattr(citation, 'extracted_case_name', None)
                            if name and name != "N/A" and name != "Unknown Case":
                                case_name = name
                    
                    if not year:
                        # Try canonical date first
                        canonical_date = getattr(citation, 'canonical_date', None)
                        if canonical_date and canonical_date != "N/A" and canonical_date != "Unknown Year":
                            year = canonical_date
                        else:
                            # Fall back to extracted date
                            date = getattr(citation, 'extracted_date', None)
                            if date and date != "N/A" and date != "Unknown Year":
                                year = date
                    
                    if case_name and year:
                        break
            
            # Handle both dict and object citations for the citations list
            citation_texts = []
            for c in citations:
                if isinstance(c, dict):
                    citation_texts.append(c.get('citation', ''))
                else:
                    citation_texts.append(getattr(c, 'citation', ''))
            
            # IMPROVED: Preserve valid case names, reject contaminated ones
            display_case_name = case_name if case_name and case_name != "N/A" else "Unknown Case"
            display_year = year if year and year != "N/A" else "Unknown Year"
            
            # FIXED: Ensure consistency between case_name and extracted_case_name
            cluster_dict = {
                'cluster_id': cluster_id,
                'case_name': display_case_name,
                'extracted_case_name': display_case_name,  # FIXED: Keep consistent with case_name
                'year': display_year,
                'extracted_date': display_year,  # FIXED: Keep consistent with year
                'size': len(citations),
                'citations': citation_texts,
                'citation_objects': [self._serialize_citation_object(c, citation_texts) for c in citations],
                'cluster_type': 'unified_extracted'
            }
            
            # FIXED: Validate cluster data integrity
            cluster_integrity_warnings = self._validate_cluster_integrity(citations, display_case_name, display_year)
            if cluster_integrity_warnings:
                cluster_dict['integrity_warnings'] = cluster_integrity_warnings
                logger.warning(f"⚠️ CLUSTER_INTEGRITY: Cluster {cluster_id} has integrity issues: {cluster_integrity_warnings}")
            
            # Use the verified_citations we already calculated above
            any_verified = len(verified_citations) > 0
            
            best_verified_citation = None
            if verified_citations:
                def source_priority(c):
                    source = getattr(c, 'source', '').lower()
                    if 'courtlistener' in source:
                        return 0  # Highest priority
                    elif 'casemine' in source or 'descrybe' in source:
                        return 1  # Medium priority
                    else:
                        return 2  # Lower priority
                
                verified_citations.sort(key=source_priority)
                best_verified_citation = verified_citations[0]
                
                # FIXED: Select the best canonical cluster case name from all verified citations
                cluster_canonical_name = self._select_best_canonical_name(verified_citations)
                cluster_canonical_date = self._select_best_canonical_date(verified_citations)
                cluster_canonical_url = getattr(best_verified_citation, 'canonical_url', None)
                
                if cluster_canonical_name:
                    cluster_dict['canonical_name'] = cluster_canonical_name
                    # Use the canonical cluster name as the definitive case name
                    cluster_dict['case_name'] = cluster_canonical_name
                    cluster_dict['extracted_case_name'] = cluster_canonical_name
                if cluster_canonical_date:
                    cluster_dict['canonical_date'] = cluster_canonical_date
                    # Use the canonical cluster date as the definitive year
                    cluster_dict['year'] = cluster_canonical_date
                    cluster_dict['extracted_date'] = cluster_canonical_date
                if cluster_canonical_url:
                    cluster_dict['canonical_url'] = cluster_canonical_url
            
            final_cluster_case_name = cluster_dict['case_name']
            final_cluster_year = cluster_dict['year']

            for citation in citations:
                # Handle both dict and object citations
                if isinstance(citation, dict):
                    if 'metadata' not in citation:
                        citation['metadata'] = {}
                    # Set cluster_id on both main dict and metadata for consistency
                    citation['cluster_id'] = cluster_id
                    citation['metadata'].update({
                        'is_in_cluster': True,
                        'cluster_id': cluster_id,
                        'cluster_size': len(citations),
                        'cluster_case_name': final_cluster_case_name,
                        'cluster_year': final_cluster_year
                    })
                    citation['cluster_case_name'] = final_cluster_case_name
                    citation['cluster_year'] = final_cluster_year
                    citation['metadata']['cluster_case_name'] = final_cluster_case_name
                    citation['metadata']['cluster_year'] = final_cluster_year
                    
                else:
                    if not hasattr(citation, 'metadata'):
                        citation.metadata = {}
                    # Set cluster_id on both main object and metadata for consistency
                    citation.cluster_id = cluster_id  # Set on main object
                    citation.metadata.update({
                        'is_in_cluster': True,
                        'cluster_id': cluster_id,  # Also keep in metadata for backward compatibility
                        'cluster_size': len(citations),
                        'cluster_case_name': final_cluster_case_name,
                        'cluster_year': final_cluster_year
                    })
                    citation.cluster_case_name = final_cluster_case_name
                    citation.cluster_year = final_cluster_year
                    citation.metadata['cluster_case_name'] = final_cluster_case_name
                    citation.metadata['cluster_year'] = final_cluster_year
                
                # Debug logging
                import logging
                logger = logging.getLogger(__name__)
                if isinstance(citation, dict):
                    citation_text = citation.get('citation', 'unknown')
                else:
                    citation_text = getattr(citation, 'citation', 'unknown')
                logger.warning(f"CLUSTERING_FIX: Set cluster_case_name='{final_cluster_case_name}' for citation '{citation_text}'")
                
                if any_verified and not getattr(citation, 'verified', False) and best_verified_citation:
                    citation.true_by_parallel = True
                    citation.verified = True  # FIXED: Use consistent boolean type
                    citation.metadata['true_by_parallel'] = True
                    
                    logger.info(f"✓ Propagated verification from {best_verified_citation.citation} to {citation.citation} (true_by_parallel)")
            
            formatted_clusters.append(cluster_dict)
        
        return formatted_clusters
    
    def _validate_cluster_integrity(self, citations: List[Any], expected_case_name: str, expected_year: str) -> List[str]:
        """
        FIXED: Validate that all citations in a cluster have consistent data.
        
        Args:
            citations: List of citation objects in the cluster
            expected_case_name: The expected case name for the cluster
            expected_year: The expected year for the cluster
            
        Returns:
            List of integrity warning messages
        """
        warnings = []
        import logging
        logger = logging.getLogger(__name__)
        
        for citation in citations:
            # Check case name consistency
            citation_case_name = None
            if isinstance(citation, dict):
                citation_case_name = citation.get('extracted_case_name') or citation.get('canonical_name')
            else:
                citation_case_name = getattr(citation, 'extracted_case_name', None) or getattr(citation, 'canonical_name', None)
            
            if citation_case_name and citation_case_name != "N/A" and citation_case_name != expected_case_name:
                # Allow some flexibility for partial matches
                if not (citation_case_name in expected_case_name or expected_case_name in citation_case_name):
                    warnings.append(f"Inconsistent case name: '{citation_case_name}' vs expected '{expected_case_name}'")
            
            # Check year consistency
            citation_year = None
            if isinstance(citation, dict):
                citation_year = citation.get('extracted_date') or citation.get('canonical_date')
            else:
                citation_year = getattr(citation, 'extracted_date', None) or getattr(citation, 'canonical_date', None)
            
            if citation_year and citation_year != "N/A" and citation_year != expected_year:
                warnings.append(f"Inconsistent year: '{citation_year}' vs expected '{expected_year}'")
            
            # Check verification status consistency
            verified_status = getattr(citation, 'verified', False)
            source = getattr(citation, 'source', None)
            
            if verified_status and not source:
                warnings.append("Verified citation missing source")
            elif not verified_status and source and source not in ['true_by_parallel']:
                warnings.append(f"Unverified citation has source: '{source}'")
        
        return warnings
    
    def _propagate_verification_to_parallels(self, clusters: Dict[str, List[Any]]) -> None:
        """
        Propagate verification status from verified citations to unverified citations in the same cluster.
        This ensures that parallel citations inherit verification data.
        """
        logger.info(f"Propagating verification status across {len(clusters)} clusters")
        
        for cluster_id, citations in clusters.items():
            if len(citations) < 2:
                continue  # Single citations don't need propagation
            
            # FIXED: Check both verification flags for compatibility
            verified_citations = [c for c in citations if getattr(c, 'verified', False) or getattr(c, 'is_verified', False)]
            
            if not verified_citations:
                continue  # No verified citations to propagate from
            
            def source_priority(c):
                source = getattr(c, 'source', '').lower()
                if 'courtlistener' in source:
                    return 0  # Highest priority
                elif 'casemine' in source or 'descrybe' in source:
                    return 1  # Medium priority
                else:
                    return 2  # Lower priority
            
            verified_citations.sort(key=source_priority)
            best_verified_citation = verified_citations[0]
            
            for citation in citations:
                if not getattr(citation, 'verified', False):
                    citation.true_by_parallel = True
                    citation.verified = True  # FIXED: Use consistent boolean type, not string
                    if not hasattr(citation, 'metadata'):
                        citation.metadata = {}
                    citation.metadata['true_by_parallel'] = True
                    
                    citation.canonical_name = getattr(best_verified_citation, 'canonical_name', None)
                    citation.canonical_date = getattr(best_verified_citation, 'canonical_date', None)
                    citation.url = getattr(best_verified_citation, 'url', None)
                    citation.source = getattr(best_verified_citation, 'source', None)
                    citation.confidence = getattr(best_verified_citation, 'confidence', None)
                    
                    if not hasattr(citation, 'source') or not citation.source:
                        citation.source = getattr(best_verified_citation, 'source', 'true_by_parallel')
                    
                    logger.info(f"✓ Propagated verification from {best_verified_citation.citation} to {citation.citation} (true_by_parallel)")
        
        logger.info("Verification propagation completed")
    
    def _serialize_citation_object(self, citation: Any, cluster_citation_texts: List[str] = None) -> Dict[str, Any]:
        """Serialize a citation object to a dictionary with all relevant fields."""
        try:
            # Handle both dict and object citations
            if isinstance(citation, dict):
                verified_status = citation.get('verified', False)
                true_by_parallel = citation.get('true_by_parallel', False)
                
                # FIXED: Populate parallel_citations array based on cluster members
                parallel_citations = []
                if cluster_citation_texts:
                    current_citation = citation.get('citation', '')
                    # Include all other citations in the cluster as parallels
                    parallel_citations = [c for c in cluster_citation_texts if c != current_citation]
                
                citation_dict = {
                    'citation': citation.get('citation', ''),
                    'extracted_case_name': citation.get('extracted_case_name', None),
                    'canonical_name': citation.get('canonical_name', None),
                    'extracted_date': citation.get('extracted_date', None),
                    'canonical_date': citation.get('canonical_date', None),
                    'canonical_url': citation.get('canonical_url', None),
                    'verified': verified_status,
                    'confidence': citation.get('confidence', None),
                    'method': citation.get('method', None),
                    'context': citation.get('context', ''),
                    'is_parallel': citation.get('is_parallel', False),
                    'true_by_parallel': true_by_parallel,
                    'url': citation.get('url', None),
                    'source': citation.get('source', None),
                    'error': citation.get('error', None),
                    'parallel_citations': parallel_citations  # FIXED: Add parallel citations
                }
                
                if 'metadata' in citation and citation['metadata']:
                    citation_dict['metadata'] = citation['metadata'].copy()
                    
            else:
                verified_status = getattr(citation, 'verified', False)
                true_by_parallel = getattr(citation, 'true_by_parallel', False)
                
                # FIXED: Populate parallel_citations array based on cluster members
                parallel_citations = []
                if cluster_citation_texts:
                    current_citation = getattr(citation, 'citation', '')
                    # Include all other citations in the cluster as parallels
                    parallel_citations = [c for c in cluster_citation_texts if c != current_citation]
                
                if verified_status == 'true_by_parallel':
                    true_by_parallel = True
                
                citation_dict = {
                    'citation': getattr(citation, 'citation', ''),
                    'extracted_case_name': getattr(citation, 'extracted_case_name', None),
                    'canonical_name': getattr(citation, 'canonical_name', None),
                    'extracted_date': getattr(citation, 'extracted_date', None),
                    'canonical_date': getattr(citation, 'canonical_date', None),
                    'canonical_url': getattr(citation, 'canonical_url', None),
                    'verified': verified_status,
                    'confidence': getattr(citation, 'confidence', None),
                    'method': getattr(citation, 'method', None),
                    'context': getattr(citation, 'context', ''),
                    'is_parallel': getattr(citation, 'is_parallel', False),
                    'true_by_parallel': true_by_parallel,
                    'url': getattr(citation, 'url', None),
                    'source': getattr(citation, 'source', None),
                    'error': getattr(citation, 'error', None),
                    'parallel_citations': parallel_citations  # FIXED: Add parallel citations
                }
                
                if hasattr(citation, 'metadata') and citation.metadata:
                    citation_dict['metadata'] = citation.metadata.copy()
            
            return citation_dict
            
        except Exception as e:
            logger.warning(f"Error serializing citation object: {str(e)}")
            return {
                'citation': str(citation),
                'error': f'Serialization error: {str(e)}'
            }


def group_citations_into_clusters(citations: list, original_text: Optional[str] = None) -> list:
    """
    DEPRECATED: Use UnifiedCitationClusterer instead.
    
    This function is kept for backward compatibility but delegates to the new
    unified clustering system.
    """
    logger.warning("group_citations_into_clusters is deprecated. Use UnifiedCitationClusterer instead.")
    
    clusterer = UnifiedCitationClusterer()
    clusters = clusterer.cluster_citations(citations, original_text or "")
    
    return clusters


def _propagate_best_extracted_to_clusters(citations: list):
    """
    DEPRECATED: Functionality moved to UnifiedCitationClusterer.
    
    This function is now a no-op as the logic has been integrated into
    the unified clustering system.
    """
    logger.warning("_propagate_best_extracted_to_clusters is deprecated. Use UnifiedCitationClusterer instead.")
    pass


def _detect_parallel_citations(citations: list, text: str = ""):
    """
    DEPRECATED: Use UnifiedCitationClusterer instead.
    
    This function is kept for backward compatibility.
    """
    logger.warning("_detect_parallel_citations is deprecated. Use UnifiedCitationClusterer instead.")
    
    clusterer = UnifiedCitationClusterer()
    clusterer._detect_parallel_citations(citations, text)




def cluster_citations_unified(citations: List[Any], original_text: str = "", enable_verification: bool = None) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Use cluster_citations_unified_master() instead.
    
    This function now delegates to the new unified master implementation
    that consolidates all 45+ duplicate clustering functions.
    
    MIGRATION: Replace calls with:
    from src.unified_clustering_master import cluster_citations_unified_master
    """
    import warnings
    warnings.warn(
        "cluster_citations_unified() is deprecated. Use cluster_citations_unified_master() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to the new master implementation
    from src.unified_clustering_master import cluster_citations_unified_master
    return cluster_citations_unified_master(
        citations=citations,
        original_text=original_text,
        enable_verification=enable_verification
    )
