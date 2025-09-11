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
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import re
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

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
        """Initialize the unified clusterer with configuration."""
        self.config = config or {}
        self.debug_mode = self.config.get('debug_mode', False)
        
        self.proximity_threshold = self.config.get('proximity_threshold', 200)
        self.min_cluster_size = self.config.get('min_cluster_size', 1)  # Allow single citation clusters
        self.case_name_similarity_threshold = self.config.get('case_name_similarity_threshold', 0.8)
        
        if self.debug_mode:
            logger.info("UnifiedCitationClusterer initialized")
    
    def cluster_citations(self, citations: List[Any], original_text: str = "", enable_verification: bool = False) -> List[Dict[str, Any]]:
        """
        Main clustering method with optimal flow:
        1. FIRST: Detect parallel citations (clustering)
        2. THEN: Extract case names/years from first/last in each cluster  
        3. FINALLY: Propagate extracted data to all cluster members
        4. OPTIONALLY: Verify citations with CourtListener API for canonical data
        
        Args:
            citations: List of citation objects to cluster
            original_text: Original text for context (optional)
            enable_verification: Whether to verify citations with CourtListener API
            
        Returns:
            List of cluster dictionaries with proper metadata
        """
        if not citations:
            return []
        
        logger.info(f"Starting unified clustering for {len(citations)} citations")
        
        logger.info("Step 1: Detecting parallel citations and creating clusters")
        parallel_groups = self._detect_parallel_citation_groups(citations, original_text)
        
        logger.info("Step 2: Extracting case names from first and years from last in each cluster")
        clusters = self._extract_and_propagate_metadata(parallel_groups, original_text)
        
        if enable_verification:
            logger.info("Step 3: Verifying citations with CourtListener API")
            self._verify_clusters_with_api(clusters)
        
        logger.info("Step 4: Merging clusters based on propagated extracted case names and years")
        merged_clusters = self._merge_clusters_by_extracted_metadata(clusters)
        
        logger.info("Step 5: Propagating verification status to parallel citations")
        self._propagate_verification_to_parallels(merged_clusters)
        
        formatted_clusters = self._format_clusters_for_output(merged_clusters)
        
        logger.info(f"Unified clustering completed: {len(formatted_clusters)} clusters created")
        
        return formatted_clusters
    
    def _detect_parallel_citation_groups(self, citations: List[Any], text: str) -> List[List[Any]]:
        """
        STEP 1: Detect parallel citation groups based on patterns and proximity.
        This includes both explicit relationships and proximity-based detection.
        """
        groups = []
        visited = set()
        
        sorted_citations = sorted(citations, key=lambda c: c.start_index if hasattr(c, 'start_index') and c.start_index is not None else 0)
        
        for citation in sorted_citations:
            if citation.citation in visited:
                continue
            
            group = [citation]
            visited.add(citation.citation)
            
            parallel_citations = getattr(citation, 'parallel_citations', [])
            citation_lookup = {c.citation: c for c in citations}
            
            for parallel_cite in parallel_citations:
                if parallel_cite in citation_lookup and parallel_cite not in visited:
                    parallel_citation = citation_lookup[parallel_cite]
                    
                    reverse_parallels = getattr(parallel_citation, 'parallel_citations', [])
                    if citation.citation in reverse_parallels:
                        distance = abs(citation.start_index - parallel_citation.start_index)
                        if distance <= self.proximity_threshold:
                            group.append(parallel_citation)
                            visited.add(parallel_cite)
            
            for other_citation in sorted_citations:
                if other_citation.citation in visited:
                    continue
                
                if self._are_citations_parallel_by_proximity(citation, other_citation, text):
                    group.append(other_citation)
                    visited.add(other_citation.citation)
            
            groups.append(group)
        
        logger.info(f"Detected {len(groups)} parallel citation groups (including proximity-based)")
        return groups
    
    def _extract_and_propagate_metadata(self, groups: List[List[Any]], text: str) -> Dict[str, List[Any]]:
        """
        STEP 2: Extract case names from first and years from last citation in each group.
        STEP 3: Propagate the extracted data to all members of each group.
        """
        clusters = {}
        
        for group in groups:
            if not group:
                continue
            
            sorted_group = sorted(group, key=lambda c: c.start_index if hasattr(c, 'start_index') and c.start_index is not None else 0)
            
            case_name = self._extract_case_name_from_citation(sorted_group[0], text)
            
            year = None
            
            if len(sorted_group) > 1:
                last_citation = sorted_group[-1]
                year = self._extract_year_from_citation(last_citation, text)
                
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
            else:
                year = self._extract_year_from_citation(sorted_group[0], text)
            
            if not case_name or case_name == "N/A":
                for citation in sorted_group:
                    extracted_name = self._extract_case_name_from_citation(citation, text)
                    if extracted_name and extracted_name != "N/A":
                        case_name = extracted_name
                        break
            
            if not year or year == "N/A":
                for citation in reversed(sorted_group):
                    extracted_year = self._extract_year_from_citation(citation, text)
                    if extracted_year and extracted_year != "N/A":
                        year = extracted_year
                        break
            
            if self.debug_mode and len(sorted_group) > 1:
                citation_list = [c.citation for c in sorted_group]
            
            for citation in sorted_group:
                citation.extracted_case_name = case_name or "N/A"
                citation.extracted_date = year or "N/A"
                if True:

                    pass  # Empty block

                
                    pass  # Empty block

                
            if case_name and year and case_name != "N/A" and year != "N/A":
                cluster_key = f"{case_name}_{year}".replace(' ', '_').replace('.', '_').replace('/', '_')
            else:
                cluster_key = f"group_{sorted_group[0].citation}".replace(' ', '_').replace('.', '_').replace('/', '_')
            
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].extend(sorted_group)
        
        return clusters
    
    def _are_citations_parallel_by_proximity(self, citation1: Any, citation2: Any, text: str) -> bool:
        """
        Determine if two citations are parallel based on proximity and patterns.
        
        Args:
            citation1: First citation to compare
            citation2: Second citation to compare
            text: Original text for context
            
        Returns:
            True if citations appear to be parallel (same case, different reporters)
        """
        if not (hasattr(citation1, 'start_index') and hasattr(citation2, 'start_index')):
            return False
        
        if citation1.start_index is None or citation2.start_index is None:
            return False
            
        distance = abs(citation1.start_index - citation2.start_index)
        if distance > self.proximity_threshold:
            return False
        
        reporter1 = self._extract_reporter_type(citation1.citation)
        reporter2 = self._extract_reporter_type(citation2.citation)
        
        if reporter1 == reporter2:
            return False
        
        is_parallel = self._match_parallel_patterns(citation1.citation, citation2.citation)
        
        if not is_parallel:
            is_parallel = self._check_washington_parallel_patterns(citation1.citation, citation2.citation, text)
        
        if True:

        
            pass  # Empty block

        
        
            pass  # Empty block

        
        
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
                reporter = self._extract_reporter_type(citation.citation)
                if reporter:
                    reporter_types.add(reporter)
            
            if len(reporter_types) > 1:
                merged_clusters[cluster_key] = citations
                for citation in citations:
                    cluster_mapping[citation.citation] = cluster_key
            else:
                sample_citation = citations[0]
                extracted_name = getattr(sample_citation, 'extracted_case_name', 'N/A')
                extracted_year = getattr(sample_citation, 'extracted_date', 'N/A')
                
                if extracted_name and extracted_year and extracted_name != 'N/A' and extracted_year != 'N/A':
                    normalized_name = self._normalize_case_name_for_clustering(extracted_name)
                    metadata_cluster_key = f"{normalized_name}_{extracted_year}"
                else:
                    metadata_cluster_key = cluster_key
                
                existing_cluster = None
                for citation in citations:
                    if citation.citation in cluster_mapping:
                        existing_cluster = cluster_mapping[citation.citation]
                        break
                
                if existing_cluster:
                    for citation in citations:
                        if citation not in merged_clusters[existing_cluster]:
                            merged_clusters[existing_cluster].append(citation)
                            cluster_mapping[citation.citation] = existing_cluster
                else:
                    if metadata_cluster_key not in merged_clusters:
                        merged_clusters[metadata_cluster_key] = []
                    merged_clusters[metadata_cluster_key].extend(citations)
                    for citation in citations:
                        cluster_mapping[citation.citation] = metadata_cluster_key
        
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
        """Extract case name for a specific citation from surrounding text."""
        existing_name = getattr(citation, 'extracted_case_name', None)
        if existing_name and existing_name != "N/A":
            return existing_name
        
        extracted_name = self._extract_case_name_for_citation(citation, text)
        
        if extracted_name and extracted_name != "N/A":
            if hasattr(citation, 'start_index') and citation.start_index is not None:
                search_start = max(0, citation.start_index - 200)
                search_end = min(len(text), citation.start_index + 50)
                search_text = text[search_start:search_end]
                
                if extracted_name.lower() not in search_text.lower():
                    proximate_name = self._find_proximate_case_name(citation, text)
                    if proximate_name:
                        return proximate_name
        
        return extracted_name

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
        
        search_start = max(0, citation.start_index - 150)
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
        """Extract year for a specific citation from surrounding text."""
        existing_date = getattr(citation, 'extracted_date', None)
        if existing_date and existing_date != "N/A":
            return existing_date
        
        return self._extract_date_for_citation(citation, text)
    
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
                            
                            validation_passed = True
                            if extracted_name and extracted_name != "N/A":
                                similarity = self._calculate_name_similarity(canonical_name, extracted_name)
                                if similarity < 0.3:  # Very low threshold for obvious mismatches
                                    logger.warning(f"✗ Name mismatch: {citation.citation}")
                                    logger.warning(f"  Canonical: '{canonical_name}'")
                                    logger.warning(f"  Extracted: '{extracted_name}'")
                                    logger.warning(f"  Similarity: {similarity:.2f} - rejecting verification")
                                    validation_passed = False
                            
                            if validation_passed:
                                citation.canonical_name = canonical_name
                                citation.canonical_date = result.get('canonical_date')
                                citation.canonical_url = result.get('canonical_url') or result.get('url')
                                citation.verified = True
                                citation.is_verified = True
                                
                                logger.info(f"✓ Verified: {citation.citation} -> {canonical_name}")
                            else:
                                citation.verified = False
                                citation.is_verified = False
                                logger.info(f"✗ Failed validation: {citation.citation}")
                        else:
                            citation.verified = False
                            citation.is_verified = False
                            error_msg = result.get('error', 'Unknown error')
                            logger.info(f"✗ Unverified: {citation.citation} - {error_msg}")
                        
                        if not hasattr(citation, 'metadata'):
                            citation.metadata = {}
                        citation.metadata.update({
                            'verification_status': 'verified' if getattr(citation, 'is_verified', False) else 'unverified',
                            'verification_source': 'courtlistener_batch_api',
                            'canonical_data_available': bool(getattr(citation, 'is_verified', False)),
                            'verification_error': result.get('error') if not result.get('verified') else None
                        })
                
                else:
                    logger.warning(f"Batch verification failed with status {response.status_code}: {response.text[:200]}")
                    for citation in batch:
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
                    
                    if result and result.get('verified', False):
                        citation.verified = True
                        citation.is_verified = True
                        citation.source = result.get('source', 'enhanced_fallback')  # Use user-friendly source directly
                        citation.url = result.get('url')
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
        if not text or not hasattr(citation, 'start_index') or citation.start_index is None:
            return "N/A"
        
        try:
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            
            citation_text = getattr(citation, 'citation', None)
            start_index = getattr(citation, 'start_index', None)
            end_index = getattr(citation, 'end_index', None)
            
            
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
        
        start_pos = max(0, citation.start_index - 200)
        end_pos = citation.start_index
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
        """Clean extracted case name to remove contamination while preserving legitimate parts."""
        if not case_name:
            return ""
        
        contamination_phrases = [
            r'\b(de\s+novo)\b', r'\b(questions?\s+of\s+law)\b', r'\b(statutory\s+interpretation)\b',
            r'\b(in\s+light\s+of)\b', r'\b(the\s+record\s+certified)\b', r'\b(federal\s+court)\b',
            r'\b(this\s+court\s+reviews?)\b', r'\b(we\s+review)\b', r'\b(certified\s+questions?)\b',
            r'\b(issue\s+of\s+law)\b', r'\b(also\s+an?\s+issue)\b'
        ]
        
        cleaned = case_name
        for phrase_pattern in contamination_phrases:
            cleaned = re.sub(phrase_pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        cleaned = re.sub(r'[,;:]+$', '', cleaned)
        
        if len(cleaned) < 5 or len(cleaned) > 100:
            return ""
        
        if not ((' v. ' in cleaned) or cleaned.startswith(('In re ', 'Ex parte '))):
            return ""
        
        return cleaned
    
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
                    
                    cluster_key = f"{case_name}_{year}".replace(' ', '_').replace('.', '_').replace('/', '_')
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
                    
                    citation_name = getattr(citation, 'extracted_case_name', None)
                    parallel_name = getattr(parallel_citation, 'extracted_case_name', None)
                    
                    if (citation_name and parallel_name and 
                        citation_name != "N/A" and parallel_name != "N/A" and
                        citation_name.strip() != parallel_name.strip()):
                        continue  # Different cases - don't group
                    
                    reverse_parallels = getattr(parallel_citation, 'parallel_citations', [])
                    if citation.citation not in reverse_parallels:
                        continue  # Not bidirectional - suspicious
                    
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
        """Format clusters for output with proper metadata."""
        formatted_clusters = []
        
        for cluster_id, citations in clusters.items():
            if len(citations) < 1:
                continue
            
            case_name = None
            year = None
            
            for citation in citations:
                if not case_name:
                    name = getattr(citation, 'extracted_case_name', None)
                    if name and name != "N/A":
                        case_name = name
                
                if not year:
                    date = getattr(citation, 'extracted_date', None)
                    if date and date != "N/A":
                        year = date
                
                if case_name and year:
                    break
            
            cluster_dict = {
                'cluster_id': cluster_id,
                'case_name': case_name or "Unknown Case",
                'year': year or "Unknown Year",
                'size': len(citations),
                'citations': [c.citation for c in citations],
                'citation_objects': [self._serialize_citation_object(c) for c in citations],
                'cluster_type': 'unified_extracted'
            }
            
            verified_citations = [c for c in citations if getattr(c, 'verified', False)]
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
            
            for citation in citations:
                if not hasattr(citation, 'metadata'):
                    citation.metadata = {}
                citation.metadata.update({
                    'is_in_cluster': True,
                    'cluster_id': cluster_id,
                    'cluster_size': len(citations),
                    'cluster_case_name': case_name,
                    'cluster_year': year
                })
                
                if any_verified and not getattr(citation, 'verified', False) and best_verified_citation:
                    citation.true_by_parallel = True
                    citation.metadata['true_by_parallel'] = True
                    
                    citation.canonical_name = getattr(best_verified_citation, 'canonical_name', None)
                    citation.canonical_date = getattr(best_verified_citation, 'canonical_date', None)
                    citation.canonical_url = getattr(best_verified_citation, 'canonical_url', None)
                    citation.url = getattr(best_verified_citation, 'url', None)
                    citation.source = getattr(best_verified_citation, 'source', None)
                    citation.confidence = getattr(best_verified_citation, 'confidence', None)
                    
                    citation.verified = 'true_by_parallel'
                    
                    if not hasattr(citation, 'source') or not citation.source:
                        citation.source = getattr(best_verified_citation, 'source', 'true_by_parallel')
                    
                    logger.info(f"✓ Propagated verification from {best_verified_citation.citation} to {citation.citation} (true_by_parallel)")
            
            formatted_clusters.append(cluster_dict)
        
        return formatted_clusters
    
    def _propagate_verification_to_parallels(self, clusters: Dict[str, List[Any]]) -> None:
        """
        Propagate verification status from verified citations to unverified citations in the same cluster.
        This ensures that parallel citations inherit verification data.
        """
        logger.info(f"Propagating verification status across {len(clusters)} clusters")
        
        for cluster_id, citations in clusters.items():
            if len(citations) < 2:
                continue  # Single citations don't need propagation
            
            verified_citations = [c for c in citations if getattr(c, 'verified', False)]
            
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
                    citation.verified = 'true_by_parallel'
                    
                    if not hasattr(citation, 'metadata'):
                        citation.metadata = {}
                    citation.metadata['true_by_parallel'] = True
                    
                    citation.canonical_name = getattr(best_verified_citation, 'canonical_name', None)
                    citation.canonical_date = getattr(best_verified_citation, 'canonical_date', None)
                    citation.canonical_url = getattr(best_verified_citation, 'canonical_url', None)
                    citation.url = getattr(best_verified_citation, 'url', None)
                    citation.source = getattr(best_verified_citation, 'source', None)
                    citation.confidence = getattr(best_verified_citation, 'confidence', None)
                    
                    if not hasattr(citation, 'source') or not citation.source:
                        citation.source = getattr(best_verified_citation, 'source', 'true_by_parallel')
                    
                    logger.info(f"✓ Propagated verification from {best_verified_citation.citation} to {citation.citation} (true_by_parallel)")
        
        logger.info("Verification propagation completed")
    
    def _serialize_citation_object(self, citation: Any) -> Dict[str, Any]:
        """Serialize a citation object to a dictionary with all relevant fields."""
        try:
            verified_status = getattr(citation, 'verified', False)
            true_by_parallel = getattr(citation, 'true_by_parallel', False)
            
            if verified_status == 'true_by_parallel':
                true_by_parallel = True
            
            citation_dict = {
                'citation': citation.citation,
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
                'source': getattr(citation, 'source', None),  # Include source field
                'error': getattr(citation, 'error', None)
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




def cluster_citations_unified(citations: List[Any], original_text: str = "", enable_verification: bool = False) -> List[Dict[str, Any]]:
    """
    Convenience function for unified citation clustering with optional verification.
    
    Args:
        citations: List of citation objects to cluster
        original_text: Original text for context (optional)
        enable_verification: Whether to verify citations with CourtListener API
        
    Returns:
        List of cluster dictionaries with proper metadata
    """
    clusterer = UnifiedCitationClusterer()
    return clusterer.cluster_citations(citations, original_text, enable_verification)
