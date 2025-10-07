"""
Enhanced Citation Clustering System

This module consolidates all the best clustering features from across the codebase:
- Proximity-based parallel detection
- Metadata propagation (case name from first, year from last)
- Pattern caching and optimization
- Similarity-based clustering
- Verification status propagation
- Memory caching for performance
"""

import logging
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import re
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClusteringConfig:
    """Configuration for enhanced clustering."""
    proximity_threshold: int = 100  # Reduced from 200 to 100 for better case separation
    min_cluster_size: int = 1
    case_name_similarity_threshold: float = 0.7
    date_similarity_threshold: int = 2  # Years within this range are similar
    enable_caching: bool = True
    cache_ttl: int = 1800  # 30 minutes
    debug_mode: bool = False

class EnhancedCitationClusterer:
    """
    Enhanced citation clustering system that integrates the best features from:
    - UnifiedCitationClusterer
    - Performance optimizations
    - Citation processor similarity logic
    - Enhanced sync processor data propagation
    """
    
    def __init__(self, config: Optional[ClusteringConfig] = None):
        """Initialize the enhanced clusterer."""
        self.config = config or ClusteringConfig()
        
        self._parallel_patterns = self._compile_parallel_patterns()
        
        self._cache = {}
        self._cache_timestamps = {}
        
        if self.config.debug_mode:
            logger.info("EnhancedCitationClusterer initialized")
    
    def _compile_parallel_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for parallel citation detection."""
        return {
            'parallel_indicators': re.compile(r'\b(?:see\s+also|also|accord|cf\.?|compare|citing|quoting)\b', re.IGNORECASE),
            'separator_patterns': re.compile(r'[;,]\s*(?:see\s+)?(?:also\s+)?'),
            'washington_parallel': re.compile(r'(\d+)\s+(?:Wn\.|Wash\.)\d*d\s+\d+.*?(\d+)\s+(?:P\.|A\.)\d*d\s+\d+'),
            'federal_parallel': re.compile(r'(\d+)\s+F\.\d*d\s+\d+.*?(\d+)\s+U\.S\.\s+\d+'),
            'supreme_parallel': re.compile(r'(\d+)\s+S\.\s*Ct\.\s+\d+.*?(\d+)\s+L\.\s*Ed\.\d*d\s+\d+')
        }
    
    def cluster_citations(self, citations: List[Any], text: str = "", request_id: str = "", enable_verification: bool = False) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Use cluster_citations_unified_master() instead.
        
        This function now delegates to the new unified master implementation
        that consolidates all 45+ duplicate clustering functions.
        
        MIGRATION: Replace calls with:
        from src.unified_clustering_master import cluster_citations_unified_master
        """
        import warnings
        warnings.warn(
            "EnhancedClusterer.cluster_citations() is deprecated. Use cluster_citations_unified_master() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Delegate to the new master implementation
        from src.unified_clustering_master import cluster_citations_unified_master
        return cluster_citations_unified_master(
            citations=citations,
            original_text=text,
            enable_verification=enable_verification,
            request_id=request_id
        )
    
    def _detect_parallel_citations_enhanced(self, citations: List[Any], text: str) -> List[List[Any]]:
        """
        Enhanced parallel detection using proximity, patterns, and indicators.
        """
        if len(citations) <= 1:
            return []
        
        cache_key = self._get_cache_key(citations, text)
        if self.config.enable_caching and cache_key in self._cache:
            if self.config.debug_mode:
                return self._cache[cache_key]
        
        case_year_groups = self._group_by_case_name_and_year(citations)
        if case_year_groups and len(case_year_groups) > 1:
            if self.config.debug_mode:
                return case_year_groups
        
        case_name_groups = self._group_by_case_name_only(citations)
        if case_name_groups and len(case_name_groups) > 1:
            if self.config.debug_mode:
                return case_name_groups
        
        if True:

        
            pass  # Empty block

        
        
            pass  # Empty block

        
        
        citation_positions = []
        for citation in citations:
            citation_text = self._get_citation_text(citation)
            pos = text.find(citation_text) if citation_text else -1
            if pos != -1:
                citation_positions.append((citation, pos, pos + len(citation_text)))
        
        citation_positions.sort(key=lambda x: x[1])
        
        groups = self._group_by_proximity_enhanced(citation_positions)
        
        parallel_groups = self._detect_parallel_indicators(groups, text)
        
        if self.config.enable_caching:
            self._cache[cache_key] = parallel_groups
            self._cache_timestamps[cache_key] = time.time()
        
        return parallel_groups
    
    def _group_by_case_name_and_year(self, citations: List[Any]) -> List[List[Any]]:
        """Group citations by case name and year using original extracted data."""
        if not citations:
            return []
        
        groups = defaultdict(list)
        
        for citation in citations:
            # Prefer original extracted data for clustering
            if isinstance(citation, dict):
                case_name = citation.get('original_case_name', citation.get('extracted_case_name'))
                year = citation.get('original_date', citation.get('extracted_date'))
            else:
                case_name = getattr(citation, 'original_case_name', 
                                  getattr(citation, 'extracted_case_name', None))
                year = getattr(citation, 'original_date', 
                             getattr(citation, 'extracted_date', None))
            
            if case_name and year and case_name != 'N/A' and year != 'N/A':
                cleaned_case_name = self._clean_case_name_for_clustering(case_name)
                normalized_year = self._normalize_year_for_clustering(year)
                if cleaned_case_name and normalized_year:
                    key = (cleaned_case_name, normalized_year)
                    groups[key].append(citation)
        
        result = [group for group in groups.values() if len(group) > 1]
        
        if self.config.debug_mode and result:
            for i, group in enumerate(result):
                first_cite = group[0]
                case_name = getattr(first_cite, 'original_case_name', 
                                  getattr(first_cite, 'extracted_case_name', 'Unknown'))
                year = getattr(first_cite, 'original_date', 
                             getattr(first_cite, 'extracted_date', 'Unknown'))
                logger.debug(f"Case name/year group {i+1}: {case_name} ({year}) - {len(group)} citations")
        
        return result
    
    def _group_by_case_name_only(self, citations: List[Any]) -> List[List[Any]]:
        """Group citations by case name only, using original extracted data."""
        if not citations:
            return []
        
        groups = defaultdict(list)
        
        for citation in citations:
            # Prefer original extracted data for clustering
            if isinstance(citation, dict):
                case_name = citation.get('original_case_name', citation.get('extracted_case_name'))
            else:
                case_name = getattr(citation, 'original_case_name', 
                                  getattr(citation, 'extracted_case_name', None))
            
            if case_name and case_name != 'N/A':
                cleaned_case_name = self._clean_case_name_for_clustering(case_name)
                if cleaned_case_name:
                    groups[cleaned_case_name].append(citation)
        
        result = [group for group in groups.values() if len(group) > 1]
        
        if self.config.debug_mode and result:
            for i, group in enumerate(result):
                first_cite = group[0]
                case_name = getattr(first_cite, 'original_case_name', 
                                  getattr(first_cite, 'extracted_case_name', 'Unknown'))
                logger.debug(f"Case name group {i+1}: {case_name} - {len(group)} citations")
        
        return result
    
    def _group_by_proximity_enhanced(self, citation_positions: List[Tuple[Any, int, int]]) -> List[List[Any]]:
        """Enhanced proximity grouping with better boundary detection."""
        if not citation_positions:
            return []
        
        groups = []
        current_group = [citation_positions[0]]
        
        for i in range(1, len(citation_positions)):
            current_citation, current_start, current_end = citation_positions[i]
            last_citation, last_start, last_end = current_group[-1]
            
            distance = current_start - last_end
            
            if distance <= self.config.proximity_threshold:
                current_group.append(citation_positions[i])
            else:
                if len(current_group) > 1:
                    groups.append([c[0] for c in current_group])
                current_group = [citation_positions[i]]
        
        if len(current_group) > 1:
            groups.append([c[0] for c in current_group])
        
        return groups
    
    def _detect_parallel_indicators(self, groups: List[List[Any]], text: str) -> List[List[Any]]:
        """Detect parallel citations using linguistic indicators."""
        parallel_groups = []
        
        for group in groups:
            citations_in_group = [self._get_citation_text(c) for c in group]
            
            has_parallel_indicators = self._check_parallel_indicators(text, citations_in_group)
            
            if has_parallel_indicators or len(group) >= 2:
                parallel_groups.append(group)
        
        return parallel_groups
    
    def _check_parallel_indicators(self, text: str, citations: List[str]) -> bool:
        """Check for parallel citation indicators in text."""
        for pattern_name, pattern in self._parallel_patterns.items():
            if pattern.search(text):
                return True
        
        for i, citation1 in enumerate(citations):
            for j, citation2 in enumerate(citations[i+1:], i+1):
                if self._are_citations_likely_parallel(citation1, citation2):
                    return True
        
        return False
    
    def _are_citations_likely_parallel(self, citation1: str, citation2: str) -> bool:
        """Check if two citations are likely parallel based on patterns."""
        if self._check_washington_parallel_patterns(citation1, citation2):
            return True
        
        if self._check_federal_parallel_patterns(citation1, citation2):
            return True
        
        return False
    
    def _check_washington_parallel_patterns(self, citation1: str, citation2: str) -> bool:
        """Check Washington State parallel patterns."""
        wash_patterns = [r'\b\d+\s+(?:Wn\.|Wash\.)\d*d\s+\d+', r'\b\d+\s+(?:P\.|A\.)\d*d\s+\d+']
        
        has_wash = any(re.search(pattern, citation1) for pattern in wash_patterns)
        has_pacific = any(re.search(pattern, citation2) for pattern in wash_patterns)
        
        return has_wash and has_pacific
    
    def _check_federal_parallel_patterns(self, citation1: str, citation2: str) -> bool:
        """Check federal parallel patterns."""
        fed_patterns = [r'\b\d+\s+F\.\d*d\s+\d+', r'\b\d+\s+U\.S\.\s+\d+', r'\b\d+\s+S\.\s*Ct\.\s+\d+']
        
        has_fed = any(re.search(pattern, citation1) for pattern in fed_patterns)
        has_supreme = any(re.search(pattern, citation2) for pattern in fed_patterns)
        
        return has_fed and has_supreme
    
    def _extract_and_propagate_metadata_enhanced(self, citations: List[Any], groups: List[List[Any]], text: str) -> List[Dict[str, Any]]:
        """
        Enhanced metadata extraction and propagation.
        Uses original extracted data for clustering while preserving verified data separately.
        """
        enhanced_citations = []
        
        for group in groups:
            if len(group) < 2:
                continue
            
            # Get the first and last citations in the group
            first_citation = group[0]
            last_citation = group[-1]
            
            # Get the best case name from the first citation
            if isinstance(first_citation, dict):
                first_case_name = first_citation.get('original_case_name', 
                                                  first_citation.get('extracted_case_name'))
            else:
                first_case_name = getattr(first_citation, 'original_case_name', 
                                       getattr(first_citation, 'extracted_case_name', None))
            
            # If we still don't have a case name, try to extract it
            if not first_case_name or first_case_name == 'N/A':
                first_case_name = self._extract_case_name(first_citation, text)
            
            # Clean the case name for clustering
            if first_case_name and first_case_name != 'N/A':
                first_case_name = self._clean_case_name_for_clustering(first_case_name)
            
            # Get the best year from the last citation
            if isinstance(last_citation, dict):
                last_year = last_citation.get('original_date', 
                                           last_citation.get('extracted_date'))
            else:
                last_year = getattr(last_citation, 'original_date',
                                 getattr(last_citation, 'extracted_date', None))
            
            # If we still don't have a year, try to extract it
            if not last_year or last_year == 'N/A':
                last_year = self._extract_year(last_citation, text)
            
            # Normalize the year for clustering
            if last_year and last_year != 'N/A':
                last_year = self._normalize_year_for_clustering(last_year)
            
            # Process each citation in the group
            for citation in group:
                # Get the original extracted data
                if isinstance(citation, dict):
                    original_case_name = citation.get('original_case_name', 
                                                   citation.get('extracted_case_name'))
                    original_date = citation.get('original_date',
                                              citation.get('extracted_date'))
                    is_verified = citation.get('verified', False)
                    verification_status = citation.get('verification_status', 'not_verified')
                    verification_source = citation.get('verification_source')
                else:
                    original_case_name = getattr(citation, 'original_case_name',
                                              getattr(citation, 'extracted_case_name', None))
                    original_date = getattr(citation, 'original_date',
                                         getattr(citation, 'extracted_date', None))
                    is_verified = getattr(citation, 'verified', False)
                    verification_status = getattr(citation, 'verification_status', 'not_verified')
                    verification_source = getattr(citation, 'verification_source', None)
                
                # Create enhanced citation with all metadata
                enhanced_citation = {
                    'citation': self._get_citation_text(citation),
                    'original_case_name': original_case_name,
                    'original_date': original_date,
                    'cluster_case_name': first_case_name,
                    'cluster_date': last_year,
                    'is_parallel': len(group) > 1,
                    'verified': is_verified,
                    'verification_status': verification_status,
                    'verification_source': verification_source,
                    'metadata': {}
                }
                
                # Add verified data if available
                if is_verified and verification_status == 'verified':
                    if isinstance(citation, dict):
                        enhanced_citation.update({
                            'verified_case_name': citation.get('verified_case_name'),
                            'verified_date': citation.get('verified_date'),
                            'canonical_url': citation.get('canonical_url')
                        })
                    else:
                        enhanced_citation.update({
                            'verified_case_name': getattr(citation, 'verified_case_name', None),
                            'verified_date': getattr(citation, 'verified_date', None),
                            'canonical_url': getattr(citation, 'canonical_url', None)
                        })
                
                # Add any additional metadata
                if isinstance(citation, dict):
                    enhanced_citation['metadata'].update({
                        k: v for k, v in citation.items()
                        if k not in enhanced_citation and not k.startswith('_')
                    })
                else:
                    enhanced_citation['metadata'].update({
                        k: getattr(citation, k) 
                        for k in dir(citation) 
                        if not k.startswith('_') and not callable(getattr(citation, k))
                    })
                
                enhanced_citations.append(enhanced_citation)
        
        # Add any ungrouped citations
        grouped_citations = {c for group in groups for c in group}
        for citation in citations:
            if citation not in grouped_citations:
                # Similar processing for ungrouped citations
                if isinstance(citation, dict):
                    original_case_name = citation.get('original_case_name', 
                                                   citation.get('extracted_case_name'))
                    original_date = citation.get('original_date',
                                              citation.get('extracted_date'))
                    is_verified = citation.get('verified', False)
                    verification_status = citation.get('verification_status', 'not_verified')
                    verification_source = citation.get('verification_source')
                else:
                    original_case_name = getattr(citation, 'original_case_name',
                                              getattr(citation, 'extracted_case_name', None))
                    original_date = getattr(citation, 'original_date',
                                         getattr(citation, 'extracted_date', None))
                    is_verified = getattr(citation, 'verified', False)
                    verification_status = getattr(citation, 'verification_status', 'not_verified')
                    verification_source = getattr(citation, 'verification_source', None)
                
                enhanced_citation = {
                    'citation': self._get_citation_text(citation),
                    'original_case_name': original_case_name,
                    'original_date': original_date,
                    'cluster_case_name': original_case_name,
                    'cluster_date': original_date,
                    'is_parallel': False,
                    'verified': is_verified,
                    'verification_status': verification_status,
                    'verification_source': verification_source,
                    'metadata': {}
                }
                
                # Add verified data if available
                if is_verified and verification_status == 'verified':
                    if isinstance(citation, dict):
                        enhanced_citation.update({
                            'verified_case_name': citation.get('verified_case_name'),
                            'verified_date': citation.get('verified_date'),
                            'canonical_url': citation.get('canonical_url')
                        })
                    else:
                        enhanced_citation.update({
                            'verified_case_name': getattr(citation, 'verified_case_name', None),
                            'verified_date': getattr(citation, 'verified_date', None),
                            'canonical_url': getattr(citation, 'canonical_url', None)
                        })
                
                enhanced_citations.append(enhanced_citation)
        
        return enhanced_citations
    
    def _extract_case_name(self, citation: Any, text: str) -> Optional[str]:
        """Extract case name from citation using UnifiedCaseNameExtractorV2."""
        try:
            from src.unified_case_name_extractor_v2 import get_unified_extractor
            extractor = get_unified_extractor()
            citation_text = self._get_citation_text(citation)
            result = extractor.extract_case_name_and_date(text, citation_text, debug=self.config.debug_mode)
            return result.case_name
        except Exception as e:
            if self.config.debug_mode:
                return None
    
    def _extract_year(self, citation: Any, text: str) -> Optional[str]:
        """Extract year from citation using UnifiedCaseNameExtractorV2."""
        try:
            from src.unified_case_name_extractor_v2 import get_unified_extractor
            extractor = get_unified_extractor()
            citation_text = self._get_citation_text(citation)
            result = extractor.extract_case_name_and_date(text, citation_text, debug=self.config.debug_mode)
            return result.year
        except Exception as e:
            if self.config.debug_mode:
                return None
    
    def _create_final_clusters_enhanced(self, enhanced_citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create final clusters using propagated metadata with improved naming."""
        clusters = defaultdict(list)
        
        # First pass: group by extracted case name and year
        for citation in enhanced_citations:
            # Prefer verified data if available, otherwise use extracted
            case_name = citation.get('verified_case_name') or citation.get('extracted_case_name')
            year = citation.get('verified_date') or citation.get('extracted_date')
            
            if case_name and year:
                # Normalize year to handle date ranges
                normalized_year = str(year).split('-')[0] if year and '-' in str(year) else str(year)
                key = (case_name.strip(), normalized_year)
                clusters[key].append(citation)
        
        final_clusters = []
        for (case_name, year), citations in clusters.items():
            if not case_name or case_name == 'N/A':
                # Try to find a better name in the cluster
                for citation in citations:
                    alt_name = (citation.get('verified_case_name') or 
                              citation.get('extracted_case_name'))
                    if alt_name and alt_name != 'N/A':
                        case_name = alt_name
                        break
                
                # If still no good name, skip this cluster
                if not case_name or case_name == 'N/A':
                    continue
            
            # Track verification status
            verified_citations = sum(1 for c in citations if c.get('verified', False))
            cluster_has_verified = verified_citations > 0
            
            # Ensure all citations in the cluster have consistent metadata
            for citation in citations:
                citation['cluster_case_name'] = case_name
                citation['cluster_year'] = year
                citation['is_in_cluster'] = True
                
                # Set true_by_parallel for unverified citations in verified clusters
                if cluster_has_verified and not citation.get('verified', False):
                    citation['true_by_parallel'] = True
            
            # Create the cluster object
            cluster = {
                'cluster_id': f"{case_name.replace(' ', '_')}_{year}",
                'case_name': case_name,
                'year': year,
                'size': len(citations),
                'citations': [c['citation'] for c in citations],
                'citation_objects': citations,
                'cluster_type': 'enhanced_proximity_propagation',
                'confidence_score': sum(c.get('confidence_score', 0.5) for c in citations) / len(citations),
                'cluster_has_verified': cluster_has_verified,
                'verified': cluster_has_verified,
                'verified_citations': verified_citations,
                'total_citations': len(citations)
            }
            final_clusters.append(cluster)
        
        return final_clusters
    
    def _apply_similarity_refinement(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply similarity-based refinement to clusters."""
        refined_clusters = []
        
        for cluster in clusters:
            citations = cluster['citation_objects']
            
            if self._validate_cluster_similarity(citations):
                refined_clusters.append(cluster)
            else:
                sub_clusters = self._split_cluster_by_similarity(citations)
                refined_clusters.extend(sub_clusters)
        
        return refined_clusters
    
    def _validate_cluster_similarity(self, citations: List[Any]) -> bool:
        """Validate that citations in a cluster are similar enough."""
        if len(citations) <= 1:
            return True
        
        case_names = []
        for citation in citations:
            case_name = getattr(citation, 'extracted_case_name', None)
            if case_name:
                case_names.append(case_name)
        
        if len(case_names) >= 2:
            similarities = []
            for i, name1 in enumerate(case_names):
                for j, name2 in enumerate(case_names[i+1:], i+1):
                    similarity = self._calculate_name_similarity(name1, name2)
                    similarities.append(similarity)
            
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                return avg_similarity >= self.config.case_name_similarity_threshold
        
        return True
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        if not name1 or not name2:
            return 0.0
        
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _split_cluster_by_similarity(self, citations: List[Any]) -> List[Dict[str, Any]]:
        """Split a cluster into sub-clusters based on similarity."""
        sub_clusters = []
        
        for citation in citations:
            case_name = getattr(citation, 'extracted_case_name', 'Unknown')
            year = getattr(citation, 'extracted_date', 'Unknown')
            
            sub_cluster = {
                'cluster_id': f"{case_name.replace(' ', '_')}_{year}_split",
                'case_name': case_name,
                'year': year,
                'size': 1,
                'citations': [self._get_citation_text(citation)],
                'citation_objects': [citation],
                'cluster_type': 'similarity_split',
                'confidence_score': 0.5
            }
            sub_clusters.append(sub_cluster)
        
        return sub_clusters
    
    def _get_citation_text(self, citation: Any) -> str:
        """Extract citation text from various citation object types."""
        if isinstance(citation, dict):
            return citation.get('citation', str(citation))
        elif hasattr(citation, 'citation'):
            return getattr(citation, 'citation', str(citation))
        else:
            return str(citation)
    
    def _get_cache_key(self, citations: List[Any], text: str) -> str:
        """Generate cache key for citations and text."""
        citation_texts = [self._get_citation_text(c) for c in citations]
        return f"{hash(tuple(citation_texts))}_{hash(text[:1000])}"
    
    def clear_cache(self):
        """Clear the clustering cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._cache_timestamps.items()
            if current_time - timestamp > self.config.cache_ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
            del self._cache_timestamps[key]
    
    def _clean_case_name_for_clustering(self, case_name: str) -> Optional[str]:
        """Clean case name for clustering by removing extra context and normalizing."""
        if not case_name:
            return None
        
        
        if re.match(r'^[A-Z][A-Za-z\s,\.\'-]*\s+v\.\s+[A-Z][&A-Za-z\s,\.\'-]*$', case_name):
            return case_name.strip()
        if re.match(r'^In\s+re\s+[A-Za-z\s,\.\'-]+$', case_name):
            return case_name.strip()
        if re.match(r'^State\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+$', case_name):
            return case_name.strip()
        
        context_phrases = [
            r'^We review statutory interpretation de novo\.\s*',
            r'^The goal of statutory interpretation is to give effect to the legislature\'s intentions\.\s*',
            r'^In determining the plain meaning of a statute, we look to the text of the statute, as well as its\s*',
            r'^Only if the plain text is susceptible to more than one interpretation do we turn to\s*',
            r'^are\s+questions\s+of\s+law\s+that\s+this\s+court\s+reviews\s+de\s+novo\s+and\s+in\s+light\s+of\s+the\s+record\s+certified\s+by\s+the\s+federal\s+court\.?\s*',
            r'^[^A-Z]*?(?=[A-Z][a-zA-Z\s]*\s+v\.\s+[A-Z])',
        ]
        
        cleaned = case_name
        for pattern in context_phrases:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        case_patterns = [
            r'([A-Z][a-zA-Z\',\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+|\s+\d+\s+Wn\.|\s+\d+\s+P\.|$)',  # Enhanced v. pattern - handles legal entities
            r'(In\s+re\s+[A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+|\s+\d+\s+Wn\.|\s+\d+\s+P\.|$)',  # Enhanced In re pattern
            r'(State\s+v\.\s+[A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+|\s+\d+\s+Wn\.|\s+\d+\s+P\.|$)',  # Enhanced State v. pattern
        ]
        
        for idx, pattern in enumerate(case_patterns):
            match = re.search(pattern, cleaned)
            if match:
                if len(match.groups()) >= 2 and idx == 0:  # Two-party case
                    return f"{match.group(1).strip()} v. {match.group(2).strip()}"
                else:  # Single-party case
                    return match.group(1).strip()
        
        cleaned = cleaned.strip()
        if len(cleaned) > 100:  # Limit length to avoid very long case names
            return None
        
        return cleaned if cleaned else None
    
    def _normalize_year_for_clustering(self, date_str: str) -> Optional[str]:
        """Normalize date to year for clustering purposes."""
        if not date_str or date_str == 'N/A':
            return None
        
        # Extract year from various date formats
        import re
        
        # Try to extract 4-digit year
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            return year_match.group(0)
        
        # If it's already just a year
        if re.match(r'^\d{4}$', date_str.strip()):
            return date_str.strip()
        
        return None
