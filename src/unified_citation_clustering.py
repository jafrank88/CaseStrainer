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
        
        # Configuration parameters
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
        
        # Step 1: FIRST - Detect parallel citations and create clusters
        # This is based on citation patterns, proximity, and explicit relationships
        logger.info("Step 1: Detecting parallel citations and creating clusters")
        parallel_groups = self._detect_parallel_citation_groups(citations, original_text)
        
        # Step 2: THEN - Extract case names and years from first/last in each cluster
        logger.info("Step 2: Extracting case names from first and years from last in each cluster")
        clusters = self._extract_and_propagate_metadata(parallel_groups, original_text)
        
        # Step 3: OPTIONALLY - Verify citations with CourtListener API
        if enable_verification:
            logger.info("Step 3: Verifying citations with CourtListener API")
            self._verify_clusters_with_api(clusters)
        
        # Step 4: Merge clusters based on propagated extracted metadata
        logger.info("Step 4: Merging clusters based on propagated extracted case names and years")
        merged_clusters = self._merge_clusters_by_extracted_metadata(clusters)
        
        # Step 5: Format clusters for output
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
        
        # Sort citations by position for proximity analysis
        sorted_citations = sorted(citations, key=lambda c: c.start_index if hasattr(c, 'start_index') and c.start_index is not None else 0)
        
        for citation in sorted_citations:
            if citation.citation in visited:
                continue
            
            group = [citation]
            visited.add(citation.citation)
            
            # Method 1: Check for explicit parallel relationships
            parallel_citations = getattr(citation, 'parallel_citations', [])
            citation_lookup = {c.citation: c for c in citations}
            
            for parallel_cite in parallel_citations:
                if parallel_cite in citation_lookup and parallel_cite not in visited:
                    parallel_citation = citation_lookup[parallel_cite]
                    
                    # Verify bidirectional relationship
                    reverse_parallels = getattr(parallel_citation, 'parallel_citations', [])
                    if citation.citation in reverse_parallels:
                        # Verify proximity (must be reasonably close)
                        distance = abs(citation.start_index - parallel_citation.start_index)
                        if distance <= self.proximity_threshold:
                            group.append(parallel_citation)
                            visited.add(parallel_cite)
            
            # Method 2: Check for proximity-based parallel citations
            for other_citation in sorted_citations:
                if other_citation.citation in visited:
                    continue
                
                # Check if citations are close enough to be parallel
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
            
            # Sort by position in text
            sorted_group = sorted(group, key=lambda c: c.start_index if hasattr(c, 'start_index') and c.start_index is not None else 0)
            
            # Extract case name from FIRST citation in group
            case_name = self._extract_case_name_from_citation(sorted_group[0], text)
            
            # For parallel citations, try to find the most reliable year
            # Look for years that appear after all the citations in the group
            year = None
            
            # First, try to extract year considering the entire group's text span
            if len(sorted_group) > 1:
                # For parallel citations, look for year after the last citation
                last_citation = sorted_group[-1]
                year = self._extract_year_from_citation(last_citation, text)
                
                # If that fails, try each citation and pick the most reliable one
                if not year or year == "N/A":
                    candidate_years = []
                    for citation in sorted_group:
                        extracted_year = self._extract_year_from_citation(citation, text)
                        if extracted_year and extracted_year != "N/A" and extracted_year.isdigit():
                            candidate_years.append(extracted_year)
                    
                    # Use the most common year, or the most recent if all different
                    if candidate_years:
                        from collections import Counter
                        year_counts = Counter(candidate_years)
                        year = year_counts.most_common(1)[0][0]
            else:
                # Single citation - extract normally
                year = self._extract_year_from_citation(sorted_group[0], text)
            
            # If we couldn't extract case name from first, try other citations in the group
            if not case_name or case_name == "N/A":
                for citation in sorted_group:
                    extracted_name = self._extract_case_name_from_citation(citation, text)
                    if extracted_name and extracted_name != "N/A":
                        case_name = extracted_name
                        break
            
            # Final fallback for year extraction
            if not year or year == "N/A":
                for citation in reversed(sorted_group):
                    extracted_year = self._extract_year_from_citation(citation, text)
                    if extracted_year and extracted_year != "N/A":
                        year = extracted_year
                        break
            
            # Debug logging for year extraction
            if self.debug_mode and len(sorted_group) > 1:
                citation_list = [c.citation for c in sorted_group]
                logger.debug(f"Parallel group: {citation_list} -> case_name: '{case_name}', year: '{year}'")
            
            # Propagate extracted case name and year to ALL citations in this group
            for citation in sorted_group:
                citation.extracted_case_name = case_name or "N/A"
                citation.extracted_date = year or "N/A"
                if self.debug_mode:
                    logger.debug(f"Propagated to {citation.citation}: case_name='{citation.extracted_case_name}', date='{citation.extracted_date}'")
            
            # Create cluster
            if case_name and year and case_name != "N/A" and year != "N/A":
                cluster_key = f"{case_name}_{year}".replace(' ', '_').replace('.', '_').replace('/', '_')
            else:
                # Fallback cluster for citations without proper metadata
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
        # Check proximity first - must be within reasonable distance
        if not (hasattr(citation1, 'start_index') and hasattr(citation2, 'start_index')):
            return False
        
        # Check if start_index values are not None
        if citation1.start_index is None or citation2.start_index is None:
            return False
            
        distance = abs(citation1.start_index - citation2.start_index)
        if distance > self.proximity_threshold:
            return False
        
        # Check if they're different reporter types (likely parallel)
        reporter1 = self._extract_reporter_type(citation1.citation)
        reporter2 = self._extract_reporter_type(citation2.citation)
        
        # If same reporter type, probably not parallel
        if reporter1 == reporter2:
            return False
        
        # Check for common parallel patterns
        is_parallel = self._match_parallel_patterns(citation1.citation, citation2.citation)
        
        if self.debug_mode and is_parallel:
            logger.debug(f"Detected parallel citations by proximity: {citation1.citation} & {citation2.citation}")
        
        return is_parallel
    
    def _extract_reporter_type(self, citation: str) -> str:
        """
        Extract the reporter type from a citation.
        
        Args:
            citation: Citation string to analyze
            
        Returns:
            Reporter type (e.g., 'wash2d', 'p3d', 'p2d')
        """
        citation_lower = citation.lower().replace(' ', '').replace('.', '')
        
        # Common reporter patterns
        if 'wash2d' in citation_lower or 'wn2d' in citation_lower:
            return 'wash2d'
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
        # Common parallel combinations
        parallel_combinations = [
            ('wash2d', 'p3d'),  # Washington 2d and Pacific 3d
            ('wash2d', 'p2d'),  # Washington 2d and Pacific 2d
            ('us', 'sct'),      # U.S. and Supreme Court Reporter
            ('fed', 'f3d'),     # Federal and F.3d
            ('fed', 'f2d'),     # Federal and F.2d
        ]
        
        reporter1 = self._extract_reporter_type(citation1)
        reporter2 = self._extract_reporter_type(citation2)
        
        # Check if the combination is a known parallel pattern
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
            
            # Check if this cluster contains parallel citations (multiple different reporter types)
            reporter_types = set()
            for citation in citations:
                reporter = self._extract_reporter_type(citation.citation)
                if reporter:
                    reporter_types.add(reporter)
            
            # If this cluster has parallel citations (multiple reporters), keep it together
            if len(reporter_types) > 1:
                logger.debug(f"Preserving parallel cluster '{cluster_key}' with reporters: {reporter_types}")
                # Keep the original cluster key to preserve parallel relationship
                merged_clusters[cluster_key] = citations
                for citation in citations:
                    cluster_mapping[citation.citation] = cluster_key
            else:
                # Single reporter type - safe to merge by extracted metadata
                sample_citation = citations[0]
                extracted_name = getattr(sample_citation, 'extracted_case_name', 'N/A')
                extracted_year = getattr(sample_citation, 'extracted_date', 'N/A')
                
                # Create a new cluster key based on extracted metadata
                if extracted_name and extracted_year and extracted_name != 'N/A' and extracted_year != 'N/A':
                    # Normalize the case name for clustering
                    normalized_name = self._normalize_case_name_for_clustering(extracted_name)
                    metadata_cluster_key = f"{normalized_name}_{extracted_year}"
                else:
                    # Fallback to original cluster key if metadata is incomplete
                    metadata_cluster_key = cluster_key
                
                # Check if any citation in this group is already assigned to a different cluster
                existing_cluster = None
                for citation in citations:
                    if citation.citation in cluster_mapping:
                        existing_cluster = cluster_mapping[citation.citation]
                        break
                
                if existing_cluster:
                    # Merge into existing cluster
                    for citation in citations:
                        if citation not in merged_clusters[existing_cluster]:
                            merged_clusters[existing_cluster].append(citation)
                            cluster_mapping[citation.citation] = existing_cluster
                else:
                    # Create new cluster or merge into existing metadata cluster
                    if metadata_cluster_key not in merged_clusters:
                        merged_clusters[metadata_cluster_key] = []
                    merged_clusters[metadata_cluster_key].extend(citations)
                    for citation in citations:
                        cluster_mapping[citation.citation] = metadata_cluster_key
        
        logger.info(f"Merged {len(clusters)} initial clusters into {len(merged_clusters)} final clusters (preserving parallel relationships)")
        
        # Log the merging details in debug mode
        if self.debug_mode:
            for cluster_key, citations in merged_clusters.items():
                citation_strs = [c.citation for c in citations]
                reporter_types = [self._extract_reporter_type(c.citation) for c in citations]
                logger.debug(f"Final cluster '{cluster_key}': {citation_strs} (reporters: {reporter_types})")
        
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
        
        # Convert to lowercase and replace problematic characters
        normalized = case_name.lower().strip()
        
        # Standardize common variations
        normalized = normalized.replace('in re the marriage of', 'in re marriage of')
        normalized = normalized.replace('in the matter of', 'in re')
        normalized = normalized.replace('matter of', 'in re')
        
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)
        
        return normalized
    
    def _extract_case_name_from_citation(self, citation: Any, text: str) -> str:
        """Extract case name for a specific citation from surrounding text."""
        # First check if citation already has extracted case name
        existing_name = getattr(citation, 'extracted_case_name', None)
        if existing_name and existing_name != "N/A":
            return existing_name
        
        # Otherwise extract from text context
        return self._extract_case_name_for_citation(citation, text)
    
    def _extract_year_from_citation(self, citation: Any, text: str) -> str:
        """Extract year for a specific citation from surrounding text."""
        # First check if citation already has extracted date
        existing_date = getattr(citation, 'extracted_date', None)
        if existing_date and existing_date != "N/A":
            return existing_date
        
        # Otherwise extract from text context
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
        
        # Get API key from environment
        api_key = os.getenv('COURTLISTENER_API_KEY')
        if not api_key:
            logger.warning("COURTLISTENER_API_KEY not found in environment - skipping verification")
            return
        
        # Collect all citations for batch processing
        all_citations = []
        for citations_list in clusters.values():
            all_citations.extend(citations_list)
        
        if not all_citations:
            return
        
        logger.info(f"Batch verifying {len(all_citations)} citations with CourtListener API")
        
        # Process in batches to respect rate limits (180/minute = 3 per second)
        batch_size = 50  # Conservative batch size
        batches = [all_citations[i:i + batch_size] for i in range(0, len(all_citations), batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} citations)")
            
            try:
                # Prepare batch request
                citations_text = ' '.join([citation.citation for citation in batch])
                
                url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
                headers = {
                    'Authorization': f'Token {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {'text': citations_text}
                
                # Make API request
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Create mapping from citation text to verification results
                    verification_results = {}
                    for result in response_data:
                        citation_text = result.get('citation', '')
                        if citation_text and result.get('clusters'):
                            # Use the first cluster (most relevant)
                            cluster = result['clusters'][0]
                            
                            # Extract canonical data from API response
                            case_name = cluster.get('case_name', '')
                            date_filed = cluster.get('date_filed', '')
                            absolute_url = cluster.get('absolute_url', '')
                            
                            # Validate essential data (best practice from enhanced verifier)
                            if (case_name and case_name.strip() and 
                                absolute_url and absolute_url.strip() and
                                len(case_name.strip()) >= 5):
                                
                                # Extract year from date_filed
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
                                # Failed validation - missing essential data
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
                    
                    # Apply results to citations with validation
                    for citation in batch:
                        result = verification_results.get(citation.citation, {'verified': False})
                        
                        if result.get('verified', False):
                            # Additional validation against extracted data (best practice)
                            canonical_name = result.get('canonical_name')
                            extracted_name = getattr(citation, 'extracted_case_name', None)
                            
                            # Validate name similarity if we have extracted name
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
                                # Populate canonical data from API
                                citation.canonical_name = canonical_name
                                citation.canonical_date = result.get('canonical_date')
                                citation.canonical_url = result.get('canonical_url') or result.get('url')
                                citation.verified = True
                                citation.is_verified = True
                                
                                logger.info(f"✓ Verified: {citation.citation} -> {canonical_name}")
                            else:
                                # Failed validation - mark as unverified
                                citation.verified = False
                                citation.is_verified = False
                                logger.info(f"✗ Failed validation: {citation.citation}")
                        else:
                            # Mark as unverified but keep extracted data
                            citation.verified = False
                            citation.is_verified = False
                            error_msg = result.get('error', 'Unknown error')
                            logger.info(f"✗ Unverified: {citation.citation} - {error_msg}")
                        
                        # Update metadata
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
                    # Mark all citations in this batch as verification failed
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
                # Mark all citations in this batch as verification failed
                for citation in batch:
                    citation.is_verified = False
                    if not hasattr(citation, 'metadata'):
                        citation.metadata = {}
                    citation.metadata.update({
                        'verification_status': 'error',
                        'verification_error': str(e),
                        'canonical_data_available': False
                    })
            
            # Rate limiting: 180/minute = 3 per second = 0.33 seconds between requests
            if batch_idx < len(batches) - 1:  # Don't wait after the last batch
                time.sleep(0.4)  # Conservative rate limiting
        
        # Step 4: Apply comprehensive legal web search verification for unverified citations
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
        
        # Normalize names for comparison
        def normalize_name(name):
            return name.lower().replace('.', '').replace(',', '').replace('v.', 'v').strip()
        
        norm1 = normalize_name(name1)
        norm2 = normalize_name(name2)
        
        # Simple token-based similarity
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
        
        Uses the comprehensive verification system that includes:
        - vLex
        - CaseMine
        - Justia
        - Cornell Law
        - Google Scholar
        - And many other legal databases
        """
        try:
            from src.citation_verification import verify_citations_with_legal_websearch
        except ImportError:
            logger.warning("Comprehensive verification module not available - skipping fallback")
            return
        
        # Use comprehensive legal web search verification
        try:
            logger.info(f"Applying comprehensive verification to {len(citations)} unverified citations")
            
            # Convert citations to the format expected by verify_citations_with_legal_websearch
            citation_list = []
            for citation in citations:
                citation_list.append(citation)
            
            # Call the comprehensive verification system
            # Note: This is an async function, so we need to handle it properly
            import asyncio
            
            try:
                # Try to get the event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an event loop, create a task
                    task = asyncio.create_task(verify_citations_with_legal_websearch(citation_list))
                    # For now, we'll wait for it to complete
                    # In a real async environment, this would be handled differently
                    loop.run_until_complete(task)
                    verified_results = task.result()
                else:
                    # Run in the event loop
                    verified_results = loop.run_until_complete(verify_citations_with_legal_websearch(citation_list))
            except RuntimeError:
                # No event loop, create one
                verified_results = asyncio.run(verify_citations_with_legal_websearch(citation_list))
            
            # Update citations with verification results
            for citation in citations:
                # Find matching verified result
                for verified_citation in verified_results:
                    if verified_citation.citation == citation.citation and verified_citation.verified:
                        # Update citation with verification data
                        citation.verified = True
                        citation.is_verified = True
                        citation.source = verified_citation.source
                        citation.url = verified_citation.url
                        
                        # Update canonical data if available
                        if hasattr(verified_citation, 'canonical_name') and verified_citation.canonical_name:
                            citation.canonical_name = verified_citation.canonical_name
                        if hasattr(verified_citation, 'canonical_date') and verified_citation.canonical_date:
                            citation.canonical_date = verified_citation.canonical_date
                        if hasattr(verified_citation, 'canonical_url') and verified_citation.canonical_url:
                            citation.canonical_url = verified_citation.canonical_url
                        
                        # Update metadata
                        if not hasattr(citation, 'metadata'):
                            citation.metadata = {}
                        citation.metadata.update({
                            'verification_status': 'verified_comprehensive',
                            'verification_source': f"comprehensive_{verified_citation.source}",
                            'canonical_data_available': True
                        })
                        
                        logger.info(f"✓ Comprehensive verification: {citation.citation} -> {citation.canonical_name} via {verified_citation.source}")
                        break
                        
        except Exception as e:
            logger.warning(f"Comprehensive verification error: {e}")
            # If comprehensive verification fails, just log the error
            # Don't fall back to the old system
    
    def _extract_case_names_and_dates(self, citations: List[Any], text: str):
        """
        Extract case names and dates for all citations.
        This ensures we have the data needed for clustering.
        """
        for citation in citations:
            # Ensure we have extracted_case_name and extracted_date
            if not hasattr(citation, 'extracted_case_name') or not citation.extracted_case_name:
                citation.extracted_case_name = self._extract_case_name_for_citation(citation, text)
            
            if not hasattr(citation, 'extracted_date') or not citation.extracted_date:
                citation.extracted_date = self._extract_date_for_citation(citation, text)
    
    def _extract_case_name_for_citation(self, citation: Any, text: str) -> str:
        """Extract case name for a single citation from the surrounding text."""
        if not text or not hasattr(citation, 'start_index') or citation.start_index is None:
            return "N/A"
        
        # Look for case name patterns before the citation
        start_pos = max(0, citation.start_index - 200)
        end_pos = citation.start_index
        context = text[start_pos:end_pos]
        
        # Common case name patterns
        case_patterns = [
            r'([A-Z][a-zA-Z\s&.]+\s+v\.?\s+[A-Z][a-zA-Z\s&.]+)',  # Standard "X v. Y" pattern
            r'([A-Z][a-zA-Z\s&.]+\s+vs\.?\s+[A-Z][a-zA-Z\s&.]+)',  # "X vs. Y" pattern
            r'(In re [A-Z][a-zA-Z\s&.]+)',  # "In re X" pattern
            r'(Ex parte [A-Z][a-zA-Z\s&.]+)',  # "Ex parte X" pattern
        ]
        
        # Debug logging
        if self.debug_mode:
            logger.debug(f"Case extraction context for {citation.citation}: '{context}'")
            logger.debug(f"Citation start_index: {citation.start_index}")
        
        for pattern in case_patterns:
            matches = re.findall(pattern, context)
            if matches:
                # Return the last (closest) match
                case_name = matches[-1].strip()
                if len(case_name) > 5 and case_name != "N/A":
                    if self.debug_mode:
                        logger.debug(f"Found case name '{case_name}' with pattern '{pattern}'")
                    return case_name
        
        if self.debug_mode:
            logger.debug(f"No case name found for {citation.citation}")
        
        return "N/A"
    
    def _extract_date_for_citation(self, citation: Any, text: str) -> str:
        """Extract date/year for a single citation from the surrounding text."""
        if not text or not hasattr(citation, 'start_index') or citation.start_index is None:
            return "N/A"
        
        # For parallel citations, look for the CLOSEST year after the citation
        citation_end = getattr(citation, 'end_index', citation.start_index + len(citation.citation))
        
        # Look for year patterns, prioritizing those closest to this citation
        start_pos = max(0, citation.start_index - 50)
        end_pos = min(len(text), citation_end + 100)  # Reduced window to avoid distant years
        context = text[start_pos:end_pos]
        
        # Year patterns with position tracking
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
                    # Calculate distance from citation end
                    year_pos_in_text = start_pos + match.start()
                    distance = abs(year_pos_in_text - citation_end)
                    
                    # Prefer years in parentheses and closer to the citation
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
        # Sort citations by position in text
        positioned_citations = [c for c in citations if hasattr(c, 'start_index') and c.start_index is not None]
        positioned_citations.sort(key=lambda c: c.start_index)
        
        # Group citations that are close together
        citation_groups = []
        current_group = []
        
        for citation in positioned_citations:
            if not current_group:
                current_group = [citation]
            else:
                # Check if this citation is close to the last one in the group
                last_citation = current_group[-1]
                distance = citation.start_index - (last_citation.start_index + len(last_citation.citation))
                
                if distance <= self.proximity_threshold:
                    current_group.append(citation)
                else:
                    # Start a new group
                    if len(current_group) >= 2:
                        citation_groups.append(current_group)
                    current_group = [citation]
        
        # Don't forget the last group
        if len(current_group) >= 2:
            citation_groups.append(current_group)
        
        # Mark parallel citations within each group
        for group in citation_groups:
            # Check if citations in this group are likely parallel
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
        
        # Extract reporter information
        reporters = set()
        years = set()
        
        for citation in citations:
            # Extract reporter from citation string
            reporter_match = re.search(r'\b([A-Z][a-zA-Z.]*\.?)\s+\d+', citation.citation)
            if reporter_match:
                reporters.add(reporter_match.group(1))
            
            # Extract year
            year_match = re.search(r'\b(\d{4})\b', citation.citation)
            if year_match:
                years.add(year_match.group(1))
        
        # Parallel citations typically have:
        # 1. Different reporters (F.3d vs. S. Ct. vs. L. Ed.)
        # 2. Same or similar years
        # 3. Close proximity in text
        
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
        
        # First, group citations by parallel relationships
        parallel_groups = self._group_by_parallel_relationships(citations)
        
        # For each parallel group, apply the first/last logic ONLY within that group
        for group in parallel_groups:
            if len(group) < 2:
                # Single citations - don't propagate, just cluster individually
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
            
            # Sort by position in text
            sorted_group = sorted(group, key=lambda c: c.start_index if hasattr(c, 'start_index') and c.start_index is not None else 0)
            
            # Extract case name from FIRST citation in this specific group
            first_citation = sorted_group[0]
            case_name = getattr(first_citation, 'extracted_case_name', None)
            if not case_name or case_name == "N/A":
                # Try to find a valid case name from any citation in this group only
                for citation in sorted_group:
                    name = getattr(citation, 'extracted_case_name', None)
                    if name and name != "N/A" and len(name) > 5:
                        case_name = name
                        break
            
            # Extract year from LAST citation in this specific group
            last_citation = sorted_group[-1]
            year = getattr(last_citation, 'extracted_date', None)
            if not year or year == "N/A":
                # Try to find a valid year from any citation in this group only
                for citation in reversed(sorted_group):
                    date = getattr(citation, 'extracted_date', None)
                    if date and date != "N/A":
                        year = date
                        break
            
            # Skip if we don't have both case name and year
            if not case_name or not year or case_name == "N/A" or year == "N/A":
                continue
            
            # Propagate case name and year ONLY within this specific parallel group
            for citation in sorted_group:
                citation.extracted_case_name = case_name
                citation.extracted_date = year
            
            # Create cluster key and add to clusters
            cluster_key = f"{case_name}_{year}".replace(' ', '_').replace('.', '_').replace('/', '_')
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].extend(sorted_group)
        
        # The parallel groups processing above should have handled ALL citations
        # No additional processing needed - this was causing the contamination bug!
        
        # Return all clusters (including single citations for frontend compatibility)
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
            
            # Start with just this citation
            group = [citation]
            group_citations = {citation.citation}
            visited.add(citation.citation)
            
            # Only add citations that are explicitly listed as parallel to this one
            parallel_citations = getattr(citation, 'parallel_citations', [])
            
            for parallel_cite in parallel_citations:
                if parallel_cite in citation_lookup and parallel_cite not in visited:
                    parallel_citation = citation_lookup[parallel_cite]
                    
                    # CRITICAL SAFETY CHECK: Verify they're actually the same case
                    citation_name = getattr(citation, 'extracted_case_name', None)
                    parallel_name = getattr(parallel_citation, 'extracted_case_name', None)
                    
                    # If both have case names, they MUST match exactly
                    if (citation_name and parallel_name and 
                        citation_name != "N/A" and parallel_name != "N/A" and
                        citation_name.strip() != parallel_name.strip()):
                        print(f"DEBUG: Skipping parallel grouping - different cases: '{citation_name}' vs '{parallel_name}'")
                        continue  # Different cases - don't group
                    
                    # ADDITIONAL SAFETY: Check if the parallel citation claims to be parallel back
                    reverse_parallels = getattr(parallel_citation, 'parallel_citations', [])
                    if citation.citation not in reverse_parallels:
                        print(f"DEBUG: Skipping - not bidirectional parallel: {citation.citation} -> {parallel_cite}")
                        continue  # Not bidirectional - suspicious
                    
                    # If only one has a case name, verify proximity (must be very close)
                    if ((not citation_name or citation_name == "N/A") or 
                        (not parallel_name or parallel_name == "N/A")):
                        distance = abs(citation.start_index - parallel_citation.start_index)
                        if distance > 50:  # Very conservative - must be very close
                            print(f"DEBUG: Skipping - too far apart: {distance} chars")
                            continue
                    
                    # Safe to add to group
                    group.append(parallel_citation)
                    group_citations.add(parallel_cite)
                    visited.add(parallel_cite)
            
            # Always add the group (even single citations)
            groups.append(group)
        
        return groups
    
    def _merge_overlapping_clusters(self, clusters: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
        """Merge clusters that have overlapping citations."""
        merged_clusters = {}
        cluster_mapping = {}  # Maps citation to cluster_id
        
        for cluster_id, citations in clusters.items():
            # Check if any citation is already in another cluster
            existing_cluster_id = None
            for citation in citations:
                citation_key = citation.citation
                if citation_key in cluster_mapping:
                    existing_cluster_id = cluster_mapping[citation_key]
                    break
            
            if existing_cluster_id:
                # Merge with existing cluster
                target_cluster_id = existing_cluster_id
                if target_cluster_id not in merged_clusters:
                    merged_clusters[target_cluster_id] = []
                
                for citation in citations:
                    if citation not in merged_clusters[target_cluster_id]:
                        merged_clusters[target_cluster_id].append(citation)
                        cluster_mapping[citation.citation] = target_cluster_id
            else:
                # Create new cluster
                merged_clusters[cluster_id] = citations
                for citation in citations:
                    cluster_mapping[citation.citation] = cluster_id
        
        return merged_clusters
    
    def _format_clusters_for_output(self, clusters: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Format clusters for output with proper metadata."""
        formatted_clusters = []
        
        for cluster_id, citations in clusters.items():
            # Include all clusters (single citations and multi-citation clusters)
            if len(citations) < 1:
                continue
            
            # Get representative case name and year
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
            
            # Create cluster dictionary
            cluster_dict = {
                'cluster_id': cluster_id,
                'case_name': case_name or "Unknown Case",
                'year': year or "Unknown Year",
                'size': len(citations),
                'citations': [c.citation for c in citations],
                'citation_objects': citations,
                'cluster_type': 'unified_extracted'
            }
            
            # Check if any citation in the cluster is verified
            any_verified = any(getattr(c, 'verified', False) for c in citations)
            
            # Add cluster metadata to each citation and set true_by_parallel status
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
                
                # Set true_by_parallel for unverified citations in clusters with verified citations
                if any_verified and not getattr(citation, 'verified', False):
                    # This citation is not verified, but another in the cluster is
                    citation.true_by_parallel = True
                    if not hasattr(citation, 'metadata'):
                        citation.metadata = {}
                    citation.metadata['true_by_parallel'] = True
            
            formatted_clusters.append(cluster_dict)
        
        return formatted_clusters


# Deprecated function wrappers for backward compatibility
def group_citations_into_clusters(citations: list, original_text: Optional[str] = None) -> list:
    """
    DEPRECATED: Use UnifiedCitationClusterer instead.
    
    This function is kept for backward compatibility but delegates to the new
    unified clustering system.
    """
    logger.warning("group_citations_into_clusters is deprecated. Use UnifiedCitationClusterer instead.")
    
    clusterer = UnifiedCitationClusterer()
    clusters = clusterer.cluster_citations(citations, original_text or "")
    
    # Convert to old format for compatibility
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


def _are_likely_parallel_citations(citation1, citation2) -> bool:
    """
    DEPRECATED: Use UnifiedCitationClusterer instead.
    
    This function is kept for backward compatibility.
    """
    logger.warning("_are_likely_parallel_citations is deprecated. Use UnifiedCitationClusterer instead.")
    
    clusterer = UnifiedCitationClusterer()
    return clusterer._are_citations_parallel([citation1, citation2])


# Main function for easy access
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
