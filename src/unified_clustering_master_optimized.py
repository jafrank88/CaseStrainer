"""
Optimized Clustering Master - Fast version without excessive logging
"""

import re
import logging
import time
from typing import Dict, Any, Optional, List, Union, Set, Tuple
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

class OptimizedClusteringMaster:
    """
    Optimized clustering with O(n log n) complexity instead of O(n²)
    """
    
    def __init__(self, enable_verification: bool = False, proximity_threshold: int = 100):
        self.enable_verification = enable_verification
        self.proximity_threshold = proximity_threshold
        self.document_primary_case_name = None
        
        # Pre-compiled regex patterns for performance
        self.reporter_patterns = {
            'federal': re.compile(r'\d+\s+(?:U\.S\.|F\.(\d+)\.|S\. Ct\.|L\. Ed\.|Fed\. Appx\.)', re.IGNORECASE),
            'regional': re.compile(r'\d+\s+(?:[A-Z]\.(\d+)\.|[A-Z]+\.?\s+App\.)', re.IGNORECASE),
            'state': re.compile(r'\d+\s+(?:[A-Za-z]+\.\s*\d+|[A-Za-z]+\s+App\.\s*\d+)', re.IGNORECASE)
        }
        
        # Parallel citation patterns
        self.parallel_patterns = [
            re.compile(r'(\d+\s+F\.\d+)', re.IGNORECASE),
            re.compile(r'(\d+\s+U\.S\.\s+\d+)', re.IGNORECASE),
            re.compile(r'(\d+\s+S\. Ct\.\s+\d+)', re.IGNORECASE),
            re.compile(r'(\d+\s+L\. Ed\.\s+\d+)', re.IGNORECASE),
        ]
    
    def cluster_citations(
        self,
        citations: List[Any],
        original_text: str = "",
        enable_verification: bool = None,
        request_id: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Fast clustering implementation
        """
        start_time = time.time()
        
        if not citations:
            return []
        
        # Use instance setting if not explicitly overridden
        if enable_verification is None:
            enable_verification = self.enable_verification
        
        logger.info(f"[OPTIMIZED-CLUSTER] Processing {len(citations)} citations")
        
        try:
            # Step 1: Extract citation data for fast comparison
            citation_data = self._extract_citation_data(citations)
            
            # Step 2: Group by potential parallel citations using hash-based approach
            parallel_groups = self._detect_parallel_citations_fast(citations, citation_data)
            
            # Step 3: Create cluster objects
            clusters = []
            for i, group in enumerate(parallel_groups):
                cluster = self._create_cluster_from_group(group, i)
                if cluster:
                    clusters.append(cluster)
            
            elapsed = time.time() - start_time
            logger.info(f"[OPTIMIZED-CLUSTER] Created {len(clusters)} clusters in {elapsed:.2f}s")
            
            return clusters
            
        except Exception as e:
            logger.error(f"[OPTIMIZED-CLUSTER] Clustering failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_citation_data(self, citations: List[Any]) -> List[Dict[str, Any]]:
        """Extract key data from citations for fast comparison"""
        data_list = []
        
        for citation in citations:
            data = {
                'citation_text': '',
                'case_name': None,
                'year': None,
                'start_index': 0,
                'end_index': 0,
                'canonical_name': None,
                'canonical_date': None,
                'reporter_type': None,
                'citation_hash': None
            }
            
            # Extract data from dict or object
            if isinstance(citation, dict):
                data['citation_text'] = citation.get('citation', '')
                data['case_name'] = citation.get('case_name') or citation.get('extracted_case_name')
                data['year'] = citation.get('extracted_date') or citation.get('date')
                data['start_index'] = citation.get('start_index', 0)
                data['end_index'] = citation.get('end_index', 0)
                data['canonical_name'] = citation.get('canonical_name')
                data['canonical_date'] = citation.get('canonical_date')
            elif hasattr(citation, '__dict__'):
                data['citation_text'] = getattr(citation, 'citation', '')
                data['case_name'] = getattr(citation, 'case_name', None) or getattr(citation, 'extracted_case_name', None)
                data['year'] = getattr(citation, 'extracted_date', None) or getattr(citation, 'date', None)
                data['start_index'] = getattr(citation, 'start_index', 0)
                data['end_index'] = getattr(citation, 'end_index', 0)
                data['canonical_name'] = getattr(citation, 'canonical_name', None)
                data['canonical_date'] = getattr(citation, 'canonical_date', None)
            
            # Determine reporter type
            data['reporter_type'] = self._get_reporter_type(data['citation_text'])
            
            # Create hash for fast comparison
            data['citation_hash'] = self._create_citation_hash(data)
            
            data_list.append(data)
        
        return data_list
    
    def _get_reporter_type(self, citation_text: str) -> str:
        """Quickly determine reporter type"""
        if not citation_text:
            return 'unknown'
        
        citation_upper = citation_text.upper()
        
        if 'U.S.' in citation_upper or 'F.' in citation_upper or 'S. CT.' in citation_upper:
            return 'federal'
        elif any(state in citation_upper for state in ['CAL.', 'N.Y.', 'ILL.', 'PA.', 'TEX.']):
            return 'regional'
        elif any(pattern in citation_upper for pattern in ['WN.', 'WASH.', 'P.3D', 'P.2D']):
            return 'state'
        
        return 'unknown'
    
    def _create_citation_hash(self, data: Dict[str, Any]) -> str:
        """Create hash for citation grouping"""
        # Use canonical data if available, otherwise extracted
        if data['canonical_name'] and data['canonical_date']:
            return f"{data['canonical_name']}_{data['canonical_date']}"
        elif data['case_name'] and data['year']:
            return f"{data['case_name']}_{data['year']}"
        else:
            # Fallback to citation text
            return re.sub(r'[^\w]', '_', data['citation_text'][:50])
    
    def _detect_parallel_citations_fast(self, citations: List[Any], citation_data: List[Dict[str, Any]]) -> List[List[Any]]:
        """
        Fast parallel citation detection using hash-based grouping
        O(n) complexity instead of O(n²)
        """
        # Group citations by hash
        hash_groups = defaultdict(list)
        for i, data in enumerate(citation_data):
            hash_groups[data['citation_hash']].append(i)
        
        parallel_groups = []
        processed_indices = set()
        
        # Process hash groups
        for hash_key, indices in hash_groups.items():
            if len(indices) > 1:
                # Multiple citations with same hash - likely parallels
                group = [citations[i] for i in indices]
                parallel_groups.append(group)
                processed_indices.update(indices)
        
        # Add remaining citations as single groups
        for i, citation in enumerate(citations):
            if i not in processed_indices:
                parallel_groups.append([citation])
        
        return parallel_groups
    
    def _create_cluster_from_group(self, citation_group: List[Any], cluster_index: int) -> Optional[Dict[str, Any]]:
        """Create cluster object from citation group"""
        if not citation_group:
            return None
        
        # USER FIX: Find best data from ANY citation in the group, preferring verified ones
        best_canonical_name = None
        best_canonical_date = None
        best_extracted_name = None
        best_case_name = None
        best_year = None
        is_verified = False
        
        for cit in citation_group:
            cit_data = self._extract_single_citation_data(cit)
            cit_verified = cit.get('verified', False) if isinstance(cit, dict) else getattr(cit, 'verified', False)
            
            # Track if any citation is verified
            if cit_verified:
                is_verified = True
            
            # Get canonical data from verified citations
            if cit_verified and cit_data.get('canonical_name') and not best_canonical_name:
                best_canonical_name = cit_data.get('canonical_name')
                best_canonical_date = cit_data.get('canonical_date')
            
            # Get best extracted name (prefer longer, more complete names)
            ext_name = cit_data.get('case_name')
            if ext_name and (not best_extracted_name or len(ext_name) > len(best_extracted_name)):
                best_extracted_name = ext_name
            
            # Fallback case name and year
            if not best_case_name and cit_data.get('case_name'):
                best_case_name = cit_data.get('case_name')
            if not best_year and cit_data.get('year'):
                best_year = cit_data.get('year')
        
        # Determine cluster type
        cluster_type = ClusterType.PARALLEL if len(citation_group) > 1 else ClusterType.EXTRACTED
        
        # Create cluster with best available data
        cluster = {
            'cluster_id': f'cluster_{cluster_index + 1}',
            'cluster_type': cluster_type.value,
            'case_name': best_canonical_name or best_case_name,
            'cluster_year': best_canonical_date or best_year,
            'citations': citation_group,
            'cluster_size': len(citation_group),
            'confidence': 0.8 if len(citation_group) > 1 else 0.5,
            'metadata': {
                'created_by': 'optimized_clustering',
                'processing_time': time.time()
            },
            'verification_status': 'verified' if is_verified else 'not_verified',
            'verified': is_verified,
            'canonical_name': best_canonical_name,
            'canonical_date': best_canonical_date,
            'extracted_case_name': best_extracted_name,
            'verifying_display_name': best_canonical_name or best_case_name,
            'submitted_display_name': best_extracted_name,
            'cluster_members': [self._extract_single_citation_data(c).get('citation_text', '') for c in citation_group]
        }
        
        return cluster
    
    def _extract_single_citation_data(self, citation: Any) -> Dict[str, Any]:
        """Extract data from a single citation"""
        data = {}
        
        if isinstance(citation, dict):
            data['citation_text'] = citation.get('citation', '')
            data['case_name'] = citation.get('case_name') or citation.get('extracted_case_name')
            data['year'] = citation.get('extracted_date') or citation.get('date')
            data['canonical_name'] = citation.get('canonical_name')
            data['canonical_date'] = citation.get('canonical_date')
        elif hasattr(citation, '__dict__'):
            data['citation_text'] = getattr(citation, 'citation', '')
            data['case_name'] = getattr(citation, 'case_name', None) or getattr(citation, 'extracted_case_name', None)
            data['year'] = getattr(citation, 'extracted_date', None) or getattr(citation, 'date', None)
            data['canonical_name'] = getattr(citation, 'canonical_name', None)
            data['canonical_date'] = getattr(citation, 'canonical_date', None)
        
        return data

# Convenience function for backward compatibility
def cluster_citations_optimized(
    citations: List[Any],
    original_text: str = "",
    enable_verification: bool = False,
    request_id: str = ""
) -> List[Dict[str, Any]]:
    """
    Optimized clustering function for fast processing
    """
    clusterer = OptimizedClusteringMaster(enable_verification=enable_verification)
    return clusterer.cluster_citations(citations, original_text, enable_verification, request_id)
