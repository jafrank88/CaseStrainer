"""
Improved Citation Clustering Algorithm

This module provides an enhanced clustering algorithm that addresses the issues
found in the current clustering implementation:
1. Single-citation clusters (should group related citations)
2. Missing parallel citation detection
3. Poor semantic grouping of nearby citations
"""

import re
from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CitationCluster:
    """Represents a cluster of related citations."""
    cluster_id: str
    citations: tuple
    case_name: str = None
    year: str = None
    canonical_name: str = None
    canonical_date: str = None
    url: str = None
    confidence: float = 0.0
    cluster_type: str = "semantic"
    # Exclude metadata from hash/eq by using field(compare=False, hash=False, default_factory=dict)
    metadata: Any = field(default_factory=dict, compare=False, hash=False)

    def __init__(self, cluster_id, citations, case_name=None, year=None, canonical_name=None, canonical_date=None, url=None, confidence=0.0, cluster_type="semantic", metadata=None):
        object.__setattr__(self, 'cluster_id', cluster_id)
        object.__setattr__(self, 'citations', tuple(citations))
        object.__setattr__(self, 'case_name', case_name)
        object.__setattr__(self, 'year', year)
        object.__setattr__(self, 'canonical_name', canonical_name)
        object.__setattr__(self, 'canonical_date', canonical_date)
        object.__setattr__(self, 'url', url)
        object.__setattr__(self, 'confidence', confidence)
        object.__setattr__(self, 'cluster_type', cluster_type)
        object.__setattr__(self, 'metadata', metadata or {})

class ImprovedClusteringAlgorithm:
    """
    Enhanced clustering algorithm that groups citations based on multiple criteria:
    1. Proximity in text
    2. Parallel citation relationships
    3. Semantic similarity (same case, same year)
    4. Contextual clues
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_proximity_distance = self.config.get('max_proximity_distance', 200)
        self.min_cluster_size = self.config.get('min_cluster_size', 2)
        self.case_name_similarity_threshold = self.config.get('case_name_similarity_threshold', 0.7)
        self.year_tolerance = self.config.get('year_tolerance', 1)
        
    def cluster_citations(self, citations: List[Dict[str, Any]], text: str) -> List[CitationCluster]:
        """
        Main clustering method that applies multiple clustering strategies.
        
        Args:
            citations: List of citation dictionaries with metadata
            text: Original text for context analysis
            
        Returns:
            List of CitationCluster objects
        """
        if not citations or len(citations) < 2:
            return []
        
        logger.info(f"Starting improved clustering for {len(citations)} citations")
        
        # Step 1: Proximity-based clustering
        proximity_clusters = self._cluster_by_proximity(citations, text)
        logger.info(f"Created {len(proximity_clusters)} proximity clusters")
        
        # Step 2: Parallel citation detection
        parallel_clusters = self._detect_parallel_citations(citations, text)
        logger.info(f"Detected {len(parallel_clusters)} parallel citation groups")
        
        # Step 3: Semantic clustering (same case, same year)
        semantic_clusters = self._cluster_by_semantic_similarity(citations)
        logger.info(f"Created {len(semantic_clusters)} semantic clusters")
        
        # Step 4: Merge overlapping clusters
        merged_clusters = self._merge_overlapping_clusters(
            proximity_clusters + parallel_clusters + semantic_clusters
        )
        logger.info(f"Merged into {len(merged_clusters)} final clusters")
        
        # Step 5: Filter and validate clusters
        final_clusters = self._filter_valid_clusters(merged_clusters)
        logger.info(f"Final result: {len(final_clusters)} valid clusters")
        
        return final_clusters
    
    def _cluster_by_proximity(self, citations: List[Dict[str, Any]], text: str) -> List[CitationCluster]:
        """Group citations that appear close together in the text."""
        if not citations:
            return []
        
        # Sort citations by position in text
        sorted_citations = sorted(citations, key=lambda x: x.get('start_index', 0))
        
        clusters = []
        current_cluster = []
        
        for i, citation in enumerate(sorted_citations):
            if not current_cluster:
                current_cluster = [citation]
            else:
                prev_citation = current_cluster[-1]
                
                # Check if citations are close enough
                if self._are_citations_close(prev_citation, citation, text):
                    current_cluster.append(citation)
                else:
                    # Finalize current cluster if it has multiple citations
                    if len(current_cluster) >= self.min_cluster_size:
                        cluster = self._create_cluster_from_citations(current_cluster, "proximity")
                        clusters.append(cluster)
                    current_cluster = [citation]
        
        # Handle the last cluster
        if len(current_cluster) >= self.min_cluster_size:
            cluster = self._create_cluster_from_citations(current_cluster, "proximity")
            clusters.append(cluster)
        
        return clusters
    
    def _are_citations_close(self, citation1: Dict[str, Any], citation2: Dict[str, Any], text: str) -> bool:
        """Check if two citations are close enough to be clustered together."""
        start1 = citation1.get('start_index', 0)
        end1 = citation1.get('end_index', start1)
        start2 = citation2.get('start_index', 0)
        
        # Check distance
        distance = start2 - end1
        if distance > self.max_proximity_distance:
            return False
        
        # Check for contextual clues that suggest they should be together
        if distance > 0:
            text_between = text[end1:start2]
            
            # Look for punctuation that suggests they're meant to be together
            if ',' in text_between and len(text_between.strip()) < 50:
                return True
            
            # Look for connecting words
            connecting_words = ['and', 'or', 'also', 'further', 'additionally']
            text_lower = text_between.lower()
            if any(word in text_lower for word in connecting_words):
                return True
        
        return True
    
    def _detect_parallel_citations(self, citations: List[Dict[str, Any]], text: str) -> List[CitationCluster]:
        """Detect citations that are parallel citations to the same case."""
        if not citations:
            return []
        
        # Group by case name similarity
        case_groups = defaultdict(list)
        
        for citation in citations:
            case_name = citation.get('extracted_case_name') or citation.get('canonical_name')
            if case_name:
                # Normalize case name for grouping
                normalized_name = self._normalize_case_name(case_name)
                case_groups[normalized_name].append(citation)
        
        clusters = []
        for case_name, group_citations in case_groups.items():
            if len(group_citations) >= self.min_cluster_size:
                # Check if they have similar years
                year_groups = self._group_by_year(group_citations)
                for year, year_citations in year_groups.items():
                    if len(year_citations) >= self.min_cluster_size:
                        cluster = self._create_cluster_from_citations(year_citations, "parallel")
                        clusters.append(cluster)
        
        return clusters
    
    def _cluster_by_semantic_similarity(self, citations: List[Dict[str, Any]]) -> List[CitationCluster]:
        """Cluster citations based on semantic similarity (same case, same year)."""
        if not citations:
            return []
        
        # Create similarity matrix
        similarity_groups = []
        processed = set()
        
        for i, citation1 in enumerate(citations):
            if i in processed:
                continue
            
            similar_group = [citation1]
            processed.add(i)
            
            for j, citation2 in enumerate(citations[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_semantically_similar(citation1, citation2):
                    similar_group.append(citation2)
                    processed.add(j)
            
            if len(similar_group) >= self.min_cluster_size:
                cluster = self._create_cluster_from_citations(similar_group, "semantic")
                similarity_groups.append(cluster)
        
        return similarity_groups
    
    def _are_semantically_similar(self, citation1: Dict[str, Any], citation2: Dict[str, Any]) -> bool:
        """Check if two citations are semantically similar."""
        # Check case name similarity
        case1 = citation1.get('extracted_case_name') or citation1.get('canonical_name')
        case2 = citation2.get('extracted_case_name') or citation2.get('canonical_name')
        
        if case1 and case2:
            similarity = self._calculate_case_name_similarity(case1, case2)
            if similarity >= self.case_name_similarity_threshold:
                # Check year similarity
                year1 = citation1.get('extracted_date') or citation1.get('canonical_date')
                year2 = citation2.get('extracted_date') or citation2.get('canonical_date')
                
                if self._are_years_similar(year1, year2):
                    return True
        
        return False
    
    def _calculate_case_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        norm1 = self._normalize_case_name(name1)
        norm2 = self._normalize_case_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        # Simple word overlap similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _normalize_case_name(self, case_name: str) -> str:
        """Normalize case name for comparison."""
        if not case_name:
            return ""
        
        # Remove common prefixes and suffixes
        normalized = case_name.lower()
        normalized = re.sub(r'\b(inc|llc|ltd|corp|corporation|company)\b', '', normalized)
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _are_years_similar(self, year1: str, year2: str) -> bool:
        """Check if two years are similar within tolerance."""
        if not year1 or not year2:
            return False
        
        try:
            # Extract year from various formats
            y1 = self._extract_year(year1)
            y2 = self._extract_year(year2)
            
            if y1 and y2:
                return abs(y1 - y2) <= self.year_tolerance
        except (ValueError, TypeError):
            pass
        
        return False
    
    def _extract_year(self, date_str: str) -> int:
        """Extract year from date string."""
        if not date_str:
            return None
        
        # Try to extract 4-digit year
        year_match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
        if year_match:
            return int(year_match.group())
        
        return None
    
    def _group_by_year(self, citations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group citations by year."""
        year_groups = defaultdict(list)
        
        for citation in citations:
            year = citation.get('extracted_date') or citation.get('canonical_date')
            if year:
                year_key = str(self._extract_year(year) or year)
                year_groups[year_key].append(citation)
        
        return year_groups
    
    def _create_cluster_from_citations(self, citations: List[Dict[str, Any]], cluster_type: str) -> CitationCluster:
        """Create a CitationCluster from a list of citations."""
        if not citations:
            return None
        
        # Extract cluster metadata from the best citation
        best_citation = self._select_best_citation(citations)
        
        cluster = CitationCluster(
            cluster_id=f"cluster_{cluster_type}_{len(citations)}",
            citations=[c.get('citation', '') for c in citations],
            case_name=best_citation.get('extracted_case_name'),
            year=best_citation.get('extracted_date'),
            canonical_name=best_citation.get('canonical_name'),
            canonical_date=best_citation.get('canonical_date'),
            url=best_citation.get('url'),
            confidence=sum(c.get('confidence', 0) for c in citations) / len(citations),
            cluster_type=cluster_type,
            metadata={
                'size': len(citations),
                'citation_objects': citations
            }
        )
        
        return cluster
    
    def _select_best_citation(self, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best citation from a group for metadata."""
        # Prefer verified citations
        verified = [c for c in citations if c.get('verified', False)]
        if verified:
            return verified[0]
        
        # Prefer citations with canonical names
        with_canonical = [c for c in citations if c.get('canonical_name')]
        if with_canonical:
            return with_canonical[0]
        
        # Prefer citations with extracted case names
        with_case_name = [c for c in citations if c.get('extracted_case_name')]
        if with_case_name:
            return with_case_name[0]
        
        # Return the first citation as fallback
        return citations[0]
    
    def _merge_overlapping_clusters(self, clusters: List[CitationCluster]) -> List[CitationCluster]:
        """Merge clusters that have overlapping citations."""
        if not clusters:
            return []
        
        # Build citation to cluster mapping
        citation_to_clusters = defaultdict(list)
        for cluster in clusters:
            for citation in cluster.citations:
                citation_to_clusters[citation].append(cluster)
        
        # Find connected components
        merged_clusters = []
        processed_clusters = set()
        
        for cluster in clusters:
            if cluster in processed_clusters:
                continue
            
            # Find all connected clusters
            connected = self._find_connected_clusters(cluster, citation_to_clusters)
            
            # Merge connected clusters
            if len(connected) > 1:
                merged = self._merge_cluster_group(connected)
                merged_clusters.append(merged)
            else:
                merged_clusters.append(cluster)
            
            processed_clusters.update(connected)
        
        return merged_clusters
    
    def _find_connected_clusters(self, start_cluster: CitationCluster, 
                                citation_to_clusters: Dict[str, List[CitationCluster]]) -> Set[CitationCluster]:
        """Find all clusters connected to the start cluster."""
        connected = {start_cluster}
        to_process = [start_cluster]
        
        while to_process:
            current = to_process.pop()
            
            for citation in current.citations:
                for neighbor in citation_to_clusters[citation]:
                    if neighbor not in connected:
                        connected.add(neighbor)
                        to_process.append(neighbor)
        
        return connected
    
    def _merge_cluster_group(self, clusters: Set[CitationCluster]) -> CitationCluster:
        """Merge a group of clusters into a single cluster."""
        if not clusters:
            return None
        
        # Combine all citations
        all_citations = []
        for cluster in clusters:
            all_citations.extend(cluster.citations)
        
        # Remove duplicates while preserving order
        unique_citations = []
        seen = set()
        for citation in all_citations:
            if citation not in seen:
                unique_citations.append(citation)
                seen.add(citation)
        
        # Select best metadata
        best_cluster = max(clusters, key=lambda c: c.confidence)
        
        merged = CitationCluster(
            cluster_id=f"merged_{len(unique_citations)}",
            citations=tuple(unique_citations),
            case_name=best_cluster.case_name,
            year=best_cluster.year,
            canonical_name=best_cluster.canonical_name,
            canonical_date=best_cluster.canonical_date,
            url=best_cluster.url,
            confidence=sum(c.confidence for c in clusters) / len(clusters),
            cluster_type="merged",
            metadata={
                'size': len(unique_citations),
                'merged_from': [c.cluster_id for c in clusters]
            }
        )
        
        return merged
    
    def _filter_valid_clusters(self, clusters: List[CitationCluster]) -> List[CitationCluster]:
        """Filter clusters to only include valid ones."""
        valid_clusters = []
        
        for cluster in clusters:
            # Must have minimum size
            if len(cluster.citations) < self.min_cluster_size:
                continue
            
            # Must have at least one unique citation
            if len(set(cluster.citations)) < self.min_cluster_size:
                continue
            
            # Must have some metadata
            if not cluster.case_name and not cluster.canonical_name:
                continue
            
            valid_clusters.append(cluster)
        
        return valid_clusters

def apply_improved_clustering(citations: List[Dict[str, Any]], text: str, 
                            config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Apply the improved clustering algorithm to citations.
    
    Args:
        citations: List of citation dictionaries
        text: Original text for context
        config: Optional configuration
        
    Returns:
        List of cluster dictionaries in the expected format
    """
    algorithm = ImprovedClusteringAlgorithm(config)
    clusters = algorithm.cluster_citations(citations, text)
    
    # Convert to expected format
    result = []
    for cluster in clusters:
        cluster_dict = {
            'cluster_id': cluster.cluster_id,
            'canonical_name': cluster.canonical_name or cluster.case_name,
            'canonical_date': cluster.canonical_date or cluster.year,
            'extracted_case_name': cluster.case_name,
            'extracted_date': cluster.year,
            'url': cluster.url,
            'source': 'improved_clustering',
            'citations': cluster.citations,
            'has_parallel_citations': len(cluster.citations) > 1,
            'size': len(cluster.citations),
            'confidence': cluster.confidence,
            'cluster_type': cluster.cluster_type
        }
        result.append(cluster_dict)
    
    return result 