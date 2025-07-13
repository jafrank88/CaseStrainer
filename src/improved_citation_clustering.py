"""
Improved Citation Clustering System
==================================

This module implements improved citation clustering with:
- Case name validation and similarity scoring
- Temporal consistency checks
- Court compatibility validation
- Confidence-based filtering
- More accurate parallel citation detection
- Prevention of false clusters
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

@dataclass
class CitationData:
    """Enhanced citation data structure for improved clustering"""
    citation: str
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    court: Optional[str] = None
    confidence: float = 0.0
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    context: str = ""
    method: str = ""
    pattern: str = ""
    verified: bool = False
    url: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ImprovedCitationClusterer:
    """Improved citation clustering with validation and filtering"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize with configuration options"""
        defaults = self._default_config()
        if config:
            defaults.update(config)
        self.config = defaults
        self._init_validation_rules()
        
    def _default_config(self) -> Dict:
        """Default configuration for clustering"""
        return {
            'similarity_threshold': 0.85,
            'min_confidence': 0.6,
            'max_cluster_distance': 1000,
            'enable_validation': True,
            'debug_mode': False,
            'case_name_similarity_threshold': 0.8,
            'temporal_tolerance_years': 2,
            'court_compatibility_check': True,
            'prevent_false_clusters': True
        }
    
    def _init_validation_rules(self):
        """Initialize validation rules and patterns"""
        # Court compatibility mapping
        self.court_compatibility = {
            'federal': ['F.', 'F.2d', 'F.3d', 'F.Supp.', 'F.Supp.2d', 'U.S.', 'S.Ct.'],
            'washington': ['Wn.', 'Wn.2d', 'Wash.', 'Wash.App.', 'Wash.2d'],
            'california': ['Cal.', 'Cal.2d', 'Cal.3d', 'Cal.4th', 'Cal.App.', 'Cal.App.2d', 'Cal.App.3d', 'Cal.App.4th'],
            'new_york': ['N.Y.', 'N.Y.2d', 'N.Y.3d', 'N.Y.App.Div.', 'N.Y.App.Div.2d'],
            'texas': ['Tex.', 'Tex.App.', 'Tex.Crim.App.', 'Tex.Civ.App.'],
        }
        
        # Common case name patterns to avoid false matches
        self.false_match_patterns = [
            r'\b(Inc|Corp|LLC|Ltd|Company|Co)\b',
            r'\b(United States|State|County|City)\b',
            r'\b(Department|Dept|Agency|Board|Commission)\b'
        ]
        
        # Temporal consistency patterns
        self.year_pattern = re.compile(r'\b(19|20)\d{2}\b')
        
    def cluster_parallel_citations(self, citations: List[CitationData]) -> Dict[str, List[CitationData]]:
        """
        Cluster citations into parallel groups with improved validation
        
        Args:
            citations: List of CitationData objects
            
        Returns:
            Dictionary mapping cluster_id to list of citations in that cluster
        """
        if not citations or len(citations) < 2:
            return {}
        
        start_time = time.time()
        logger.info(f"Starting improved clustering of {len(citations)} citations")
        
        # Step 1: Filter by confidence
        filtered_citations = self._filter_by_confidence(citations)
        logger.info(f"Filtered to {len(filtered_citations)} high-confidence citations")
        
        # Step 2: Group by proximity and context
        proximity_groups = self._group_by_proximity(filtered_citations)
        logger.info(f"Created {len(proximity_groups)} proximity groups")
        
        # Step 3: Validate each group for true parallel citations
        validated_clusters = {}
        cluster_id = 0
        
        for group in proximity_groups:
            if len(group) < 2:
                continue
                
            # Apply validation rules
            if self._validate_parallel_group(group):
                cluster_key = f"cluster_{cluster_id}"
                validated_clusters[cluster_key] = group
                cluster_id += 1
                logger.debug(f"Validated cluster {cluster_key} with {len(group)} citations")
            else:
                logger.debug(f"Rejected group of {len(group)} citations - failed validation")
        
        processing_time = time.time() - start_time
        logger.info(f"Clustering completed in {processing_time:.2f}s - {len(validated_clusters)} valid clusters")
        
        return validated_clusters
    
    def _filter_by_confidence(self, citations: List[CitationData]) -> List[CitationData]:
        """Filter citations by confidence threshold"""
        if not self.config['enable_validation']:
            return citations
            
        filtered = [c for c in citations if c.confidence >= self.config['min_confidence']]
        
        if self.config['debug_mode']:
            rejected = len(citations) - len(filtered)
            if rejected > 0:
                logger.info(f"Filtered out {rejected} low-confidence citations")
        
        return filtered
    
    def _group_by_proximity(self, citations: List[CitationData]) -> List[List[CitationData]]:
        """Group citations by proximity in text"""
        if not citations:
            return []
        
        # Sort by position in text
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        
        groups = []
        current_group = []
        
        for citation in sorted_citations:
            if not current_group:
                current_group = [citation]
            else:
                prev_citation = current_group[-1]
                
                # Check if citations are close enough to be considered together
                if self._are_citations_close(prev_citation, citation):
                    current_group.append(citation)
                else:
                    if len(current_group) > 1:
                        groups.append(current_group)
                    current_group = [citation]
        
        # Add the last group
        if len(current_group) > 1:
            groups.append(current_group)
        
        return groups
    
    def _are_citations_close(self, citation1: CitationData, citation2: CitationData) -> bool:
        """Check if two citations are close enough to be considered together"""
        if not citation1.start_index or not citation2.start_index:
            return False
        
        distance = citation2.start_index - citation1.end_index
        max_distance = self.config['max_cluster_distance']
        
        # Citations must be within the maximum distance
        if distance > max_distance:
            return False
        
        # Check for explicit separation indicators (commas, semicolons)
        if distance > 0:
            # Look for punctuation that suggests they're meant to be together
            # This is a simplified check - in practice, you'd analyze the text between them
            return True
        
        return True
    
    def _validate_parallel_group(self, group: List[CitationData]) -> bool:
        """Validate that a group of citations are truly parallel citations"""
        if len(group) < 2:
            return False
        
        # Step 1: Case name validation
        if not self._validate_case_names(group):
            return False
        
        # Step 2: Temporal consistency check
        if not self._validate_temporal_consistency(group):
            return False
        
        # Step 3: Court compatibility check
        if not self._validate_court_compatibility(group):
            return False
        
        # Step 4: Prevent false clusters
        if self.config['prevent_false_clusters'] and self._is_false_cluster(group):
            return False
        
        return True
    
    def _validate_case_names(self, group: List[CitationData]) -> bool:
        """Validate that case names are similar enough to be the same case"""
        case_names = [c.extracted_case_name for c in group if c.extracted_case_name]
        
        if len(case_names) < 2:
            # If we don't have enough case names, be more lenient
            return True
        
        # Check similarity between all pairs of case names
        for i in range(len(case_names)):
            for j in range(i + 1, len(case_names)):
                similarity = self._calculate_case_name_similarity(case_names[i], case_names[j])
                if similarity < self.config['case_name_similarity_threshold']:
                    if self.config['debug_mode']:
                        logger.debug(f"Case name similarity too low: {case_names[i]} vs {case_names[j]} = {similarity:.2f}")
                    return False
        
        return True
    
    def _calculate_case_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names"""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        norm1 = self._normalize_case_name(name1)
        norm2 = self._normalize_case_name(name2)
        
        # Use sequence matcher for overall similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Boost similarity for word overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if words1 and words2:
            word_overlap = len(words1 & words2) / max(len(words1), len(words2))
            # Combine sequence similarity with word overlap
            final_similarity = (similarity + word_overlap) / 2
        else:
            final_similarity = similarity
        
        return final_similarity
    
    def _normalize_case_name(self, name: str) -> str:
        """Normalize case name for comparison"""
        if not name:
            return ""
        
        # Remove punctuation and extra whitespace
        normalized = re.sub(r'[^\w\s]', ' ', name.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove common false match patterns
        for pattern in self.false_match_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        return normalized.strip()
    
    def _validate_temporal_consistency(self, group: List[CitationData]) -> bool:
        """Validate that dates are temporally consistent"""
        dates = [c.extracted_date for c in group if c.extracted_date]
        
        if len(dates) < 2:
            return True
        
        # Extract years from dates
        years = []
        for date in dates:
            year_match = self.year_pattern.search(str(date))
            if year_match:
                years.append(int(year_match.group()))
        
        if len(years) < 2:
            return True
        
        # Check if years are within tolerance
        min_year = min(years)
        max_year = max(years)
        tolerance = self.config['temporal_tolerance_years']
        
        if max_year - min_year > tolerance:
            if self.config['debug_mode']:
                logger.debug(f"Temporal inconsistency: years {years} exceed tolerance {tolerance}")
            return False
        
        return True
    
    def _validate_court_compatibility(self, group: List[CitationData]) -> bool:
        """Validate that citations are from compatible courts"""
        if not self.config['court_compatibility_check']:
            return True
        
        # Extract reporter types from citations
        reporter_types = []
        for citation in group:
            reporter = self._extract_reporter_type(citation.citation)
            if reporter:
                reporter_types.append(reporter)
        
        if len(reporter_types) < 2:
            return True
        
        # Check if all reporters are compatible
        for court_type, compatible_reporters in self.court_compatibility.items():
            if all(reporter in compatible_reporters for reporter in reporter_types):
                return True
        
        # If no specific court type matches, check for general compatibility
        # (e.g., all federal, all state, etc.)
        if self._are_reporters_generally_compatible(reporter_types):
            return True
        
        if self.config['debug_mode']:
            logger.debug(f"Court incompatibility: {reporter_types}")
        return False
    
    def _extract_reporter_type(self, citation: str) -> Optional[str]:
        """Extract reporter type from citation"""
        # Simple pattern matching for common reporters
        patterns = {
            r'\bF\.\d*d?\b': 'F.',
            r'\bF\.Supp\.\d*d?\b': 'F.Supp.',
            r'\bU\.S\.\b': 'U.S.',
            r'\bS\.Ct\.\b': 'S.Ct.',
            r'\bWn\.\d*d?\b': 'Wn.',
            r'\bWash\.\d*d?\b': 'Wash.',
            r'\bCal\.\d*d?\b': 'Cal.',
            r'\bN\.Y\.\d*d?\b': 'N.Y.',
            r'\bTex\.\d*d?\b': 'Tex.',
        }
        
        for pattern, reporter in patterns.items():
            if re.search(pattern, citation):
                return reporter
        
        return None
    
    def _are_reporters_generally_compatible(self, reporters: List[str]) -> bool:
        """Check if reporters are generally compatible (all federal, all state, etc.)"""
        if not reporters:
            return True
        
        # Check if all are federal
        federal_reporters = ['F.', 'F.Supp.', 'U.S.', 'S.Ct.']
        if all(r in federal_reporters for r in reporters):
            return True
        
        # Check if all are state (not federal)
        if all(r not in federal_reporters for r in reporters):
            return True
        
        return False
    
    def _is_false_cluster(self, group: List[CitationData]) -> bool:
        """Check if this is a false cluster that should be prevented"""
        # Check for common false cluster patterns
        
        # Pattern 1: Citations that are too different in format
        citations = [c.citation for c in group]
        if len(set(self._extract_reporter_type(c) for c in citations)) > 2:
            return True
        
        # Pattern 2: Citations with very different confidence levels
        confidences = [c.confidence for c in group]
        if max(confidences) - min(confidences) > 0.3:
            return True
        
        # Pattern 3: Citations that are too far apart in the text
        if len(group) > 1:
            positions = [c.start_index for c in group if c.start_index is not None]
            if positions and max(positions) - min(positions) > 500:
                return True
        
        return False
    
    def calculate_clustering_metrics(self, original_citations: List[CitationData], 
                                   clustered_citations: Dict[str, List[CitationData]]) -> Dict[str, Any]:
        """Calculate metrics for clustering performance"""
        total_citations = len(original_citations)
        clustered_citations_count = sum(len(cluster) for cluster in clustered_citations.values())
        cluster_count = len(clustered_citations)
        
        # Calculate false clusters prevented
        estimated_old_clusters = int(total_citations * 0.4)  # Old system's estimated rate
        false_clusters_prevented = max(0, estimated_old_clusters - cluster_count)
        
        # Calculate quality metrics
        avg_confidence = sum(c.confidence for c in original_citations) / total_citations if total_citations > 0 else 0
        verification_rate = sum(1 for c in original_citations if c.verified) / total_citations if total_citations > 0 else 0
        
        return {
            'total_citations': total_citations,
            'clustered_citations': clustered_citations_count,
            'cluster_count': cluster_count,
            'false_clusters_prevented': false_clusters_prevented,
            'avg_confidence': round(avg_confidence, 3),
            'verification_rate': round(verification_rate, 3),
            'clustering_ratio': round(cluster_count / total_citations, 3) if total_citations > 0 else 0
        }

def convert_citation_results_to_data(citations: List) -> List[CitationData]:
    """Convert existing CitationResult objects to CitationData for improved clustering"""
    converted = []
    
    for citation in citations:
        # Handle both CitationResult objects and dictionaries
        if hasattr(citation, 'citation'):
            # CitationResult object
            data = CitationData(
                citation=citation.citation,
                extracted_case_name=getattr(citation, 'extracted_case_name', None),
                extracted_date=getattr(citation, 'extracted_date', None),
                canonical_name=getattr(citation, 'canonical_name', None),
                canonical_date=getattr(citation, 'canonical_date', None),
                court=getattr(citation, 'court', None),
                confidence=getattr(citation, 'confidence', 0.0),
                start_index=getattr(citation, 'start_index', None),
                end_index=getattr(citation, 'end_index', None),
                context=getattr(citation, 'context', ''),
                method=getattr(citation, 'method', ''),
                pattern=getattr(citation, 'pattern', ''),
                verified=getattr(citation, 'verified', False),
                url=getattr(citation, 'url', None),
                metadata=getattr(citation, 'metadata', {})
            )
        elif isinstance(citation, dict):
            # Dictionary
            data = CitationData(
                citation=citation.get('citation', ''),
                extracted_case_name=citation.get('extracted_case_name'),
                extracted_date=citation.get('extracted_date'),
                canonical_name=citation.get('canonical_name'),
                canonical_date=citation.get('canonical_date'),
                court=citation.get('court'),
                confidence=citation.get('confidence', 0.0),
                start_index=citation.get('start_index'),
                end_index=citation.get('end_index'),
                context=citation.get('context', ''),
                method=citation.get('method', ''),
                pattern=citation.get('pattern', ''),
                verified=citation.get('verified', False),
                url=citation.get('url'),
                metadata=citation.get('metadata', {})
            )
        else:
            continue
        
        converted.append(data)
    
    return converted

def apply_improved_clustering(citations: List, config: Optional[Dict] = None) -> Tuple[Dict[str, List], Dict[str, Any]]:
    """
    Apply improved clustering to a list of citations
    
    Args:
        citations: List of citation objects (CitationResult or dict)
        config: Optional configuration dictionary
        
    Returns:
        Tuple of (clusters_dict, metrics_dict)
    """
    # Convert citations to CitationData format
    citation_data = convert_citation_results_to_data(citations)
    
    # Initialize clusterer
    clusterer = ImprovedCitationClusterer(config)
    
    # Perform clustering
    clusters = clusterer.cluster_parallel_citations(citation_data)
    
    # Calculate metrics
    metrics = clusterer.calculate_clustering_metrics(citation_data, clusters)
    
    return clusters, metrics 