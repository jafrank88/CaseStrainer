"""
Unified Sync Processor
Combines the best features of all three sync paths:
- CitationService's ultra-fast processing
- UnifiedInputProcessor's smart routing  
- Enhanced Validator's frontend optimization

This eliminates redundancy and provides a single, optimized sync processing path.
"""

import os
import sys
import time
import logging
import hashlib
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProcessingOptions:
    """Configuration options for text processing."""
    enable_verification: bool = True
    enable_clustering: bool = True
    enable_caching: bool = True
    force_ultra_fast: bool = False
    skip_clustering_threshold: int = 300
    ultra_fast_threshold: int = 500
    sync_threshold: int = 2 * 1024  # 2KB
    max_citations_for_skip_clustering: int = 3

class UnifiedSyncProcessor:
    """
    Unified processor that consolidates all sync processing logic into a single,
    optimized code path while maintaining the performance characteristics of each
    individual path.
    """
    
    def __init__(self, options: Optional[ProcessingOptions] = None):
        self.options = options or ProcessingOptions()
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        self._cache_cleanup_interval = 300  # Clean cache every 5 minutes
        self._last_cache_cleanup = time.time()
        
        # Performance thresholds
        self.immediate_processing_threshold = self.options.sync_threshold
        self.ultra_fast_threshold = self.options.ultra_fast_threshold
        self.clustering_skip_threshold = self.options.skip_clustering_threshold
        self.max_citations_for_skip_clustering = self.options.max_citations_for_skip_clustering
        
        logger.info(f"[UnifiedSyncProcessor] Initialized with thresholds: "
                   f"sync={self.immediate_processing_threshold}, "
                   f"ultra_fast={self.ultra_fast_threshold}, "
                   f"clustering_skip={self.clustering_skip_threshold}")
    
    def process_text_unified(self, text: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Single entry point that automatically chooses the best processing strategy.
        
        Args:
            text: Text to process for citations
            options: Optional processing options to override defaults
            
        Returns:
            Dictionary with citation processing results
        """
        start_time = time.time()
        request_id = f"sync_{int(start_time * 1000)}"
        
        try:
            logger.info(f"[UnifiedSyncProcessor {request_id}] Processing text: {len(text)} characters")
            
            # 1. Smart routing - determine if this should be processed synchronously
            if not self._should_process_sync(text):
                logger.info(f"[UnifiedSyncProcessor {request_id}] Text too long for sync processing, redirecting to async")
                return self._redirect_to_async(text, request_id)
            
            # 2. Check cache for repeated text patterns
            if self.options.enable_caching:
                cached_result = self._check_cache(text)
                if cached_result:
                    logger.info(f"[UnifiedSyncProcessor {request_id}] Cache hit, returning cached result in {time.time() - start_time:.3f}s")
                    return cached_result
            
            # 3. Choose processing strategy based on text characteristics
            if self._should_use_ultra_fast(text) or self.options.force_ultra_fast:
                logger.info(f"[UnifiedSyncProcessor {request_id}] Using ultra-fast path")
                result = self._process_ultra_fast(text, request_id)
            elif self._should_skip_clustering(text):
                logger.info(f"[UnifiedSyncProcessor {request_id}] Using fast path without clustering")
                result = self._process_without_clustering(text, request_id)
            else:
                logger.info(f"[UnifiedSyncProcessor {request_id}] Using full processing with verification")
                result = self._process_with_verification(text, request_id, options)
            
            # 4. Cache the result if caching is enabled
            if self.options.enable_caching:
                self._cache_result(text, result)
            
            # 5. Add metadata and return
            result.update({
                'processing_mode': 'unified_sync',
                'processing_time': time.time() - start_time,
                'request_id': request_id,
                'text_length': len(text),
                'processing_strategy': self._get_processing_strategy(text)
            })
            
            logger.info(f"[UnifiedSyncProcessor {request_id}] Processing completed in {result['processing_time']:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"[UnifiedSyncProcessor {request_id}] Error in unified processing: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Unified processing failed: {str(e)}',
                'citations': [],
                'clusters': [],
                'processing_mode': 'unified_sync_error',
                'processing_time': time.time() - start_time,
                'request_id': request_id,
                'text_length': len(text)
            }
        finally:
            # Clean up old cache entries periodically
            self._cleanup_cache()
    
    def _should_process_sync(self, text: str) -> bool:
        """Smart routing logic - determine if text should be processed synchronously."""
        return len(text) < self.immediate_processing_threshold
    
    def _should_use_ultra_fast(self, text: str) -> bool:
        """Ultra-fast path logic - determine if text qualifies for fastest processing."""
        return len(text) < self.ultra_fast_threshold
    
    def _should_skip_clustering(self, text: str) -> bool:
        """Clustering skip logic - determine if clustering can be skipped for speed."""
        # This will be evaluated after citation extraction
        return False  # Will be set dynamically
    
    def _redirect_to_async(self, text: str, request_id: str) -> Dict[str, Any]:
        """Fallback to async processing when text is too long for sync."""
        return {
            'success': True,
            'status': 'redirected_to_async',
            'message': f'Text too long ({len(text)} chars) for sync processing. Redirecting to async.',
            'task_id': request_id,
            'processing_mode': 'async_redirect',
            'text_length': len(text),
            'request_id': request_id
        }
    
    def _check_cache(self, text: str) -> Optional[Dict[str, Any]]:
        """Check cache for repeated text patterns."""
        cache_key = f"text_{hashlib.md5(text.encode()).hexdigest()}"
        
        if cache_key in self.cache:
            cached_entry = self.cache[cache_key]
            if time.time() - cached_entry.get('cache_time', 0) < self.cache_ttl:
                logger.info(f"[UnifiedSyncProcessor] Cache hit for text pattern")
                return cached_entry['result']
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        
        return None
    
    def _cache_result(self, text: str, result: Dict[str, Any]):
        """Cache the processing result for future use."""
        cache_key = f"text_{hashlib.md5(text.encode()).hexdigest()}"
        self.cache[cache_key] = {
            'result': result,
            'cache_time': time.time()
        }
        logger.info(f"[UnifiedSyncProcessor] Cached result for text pattern")
    
    def _cleanup_cache(self):
        """Clean up old cache entries to prevent memory bloat."""
        current_time = time.time()
        if current_time - self._last_cache_cleanup > self._cache_cleanup_interval:
            old_keys = [
                key for key, value in self.cache.items()
                if current_time - value.get('cache_time', 0) > self.cache_ttl
            ]
            for key in old_keys:
                del self.cache[key]
            
            if old_keys:
                logger.info(f"[UnifiedSyncProcessor] Cleared {len(old_keys)} old cache entries")
            
            self._last_cache_cleanup = current_time
    
    def _process_ultra_fast(self, text: str, request_id: str) -> Dict[str, Any]:
        """Ultra-fast processing path for very short text."""
        try:
            logger.info(f"[UnifiedSyncProcessor {request_id}] Ultra-fast extraction for {len(text)} characters")
            
            # Use the fastest citation extraction method
            citations = self._extract_citations_fast(text)
            
            # Convert to standard format
            citations_list = self._convert_citations_to_dicts(citations)
            
            return {
                'success': True,
                'citations': citations_list,
                'clusters': [],  # No clustering for ultra-fast path
                'processing_strategy': 'ultra_fast',
                'extraction_method': 'fast_regex'
            }
            
        except Exception as e:
            logger.warning(f"[UnifiedSyncProcessor {request_id}] Ultra-fast processing failed: {e}")
            # Fall back to standard processing
            return self._process_without_clustering(text, request_id)
    
    def _process_without_clustering(self, text: str, request_id: str) -> Dict[str, Any]:
        """Fast processing without clustering for short text with few citations."""
        try:
            logger.info(f"[UnifiedSyncProcessor {request_id}] Fast processing without clustering")
            
            # Extract citations using standard method
            citations = self._extract_citations_standard(text)
            
            # Convert to standard format
            citations_list = self._convert_citations_to_dicts(citations)
            
            return {
                'success': True,
                'citations': citations_list,
                'clusters': [],  # No clustering
                'processing_strategy': 'fast_no_clustering',
                'extraction_method': 'standard_regex'
            }
            
        except Exception as e:
            logger.warning(f"[UnifiedSyncProcessor {request_id}] Fast processing failed: {e}")
            # Fall back to full processing
            return self._process_with_verification(text, request_id, {})
    
    def _process_with_verification(self, text: str, request_id: str, options: Optional[Dict]) -> Dict[str, Any]:
        """Full processing with clustering and verification."""
        try:
            logger.info(f"[UnifiedSyncProcessor {request_id}] Full processing with verification")
            
            # Extract citations
            citations = self._extract_citations_standard(text)
            citation_results = citations
            
            # Determine if clustering should be skipped based on actual citation count
            if len(text) < self.clustering_skip_threshold and len(citations) <= self.max_citations_for_skip_clustering:
                logger.info(f"[UnifiedSyncProcessor {request_id}] Skipping clustering for short text with few citations")
                clusters = []
            else:
                # Apply clustering with verification
                clusters = self._apply_clustering_with_verification(citation_results, text, request_id, options)
            
            # Convert to standard format
            citations_list = self._convert_citations_to_dicts(citation_results)
            clusters_list = self._convert_clusters_to_dicts(clusters)
            
            return {
                'success': True,
                'citations': citations_list,
                'clusters': clusters_list,
                'processing_strategy': 'full_with_verification',
                'extraction_method': 'standard_regex',
                'clustering_applied': len(clusters) > 0,
                'verification_applied': self._has_verification(citations)
            }
            
        except Exception as e:
            logger.error(f"[UnifiedSyncProcessor {request_id}] Full processing failed: {e}")
            # Fall back to basic extraction
            return self._extract_citations_fallback(text, request_id)
    
    def _extract_citations_fast(self, text: str) -> List:
        """Ultra-fast citation extraction for very short text."""
        try:
            # Import only what we need for fast processing
            from src.citation_extractor import CitationExtractor
            
            # Use the existing citation extractor with fast processing
            extractor = CitationExtractor()
            citations = extractor.extract_citations(text)
            
            logger.info(f"[UnifiedSyncProcessor] Fast extraction found {len(citations)} citations")
            return citations
            
        except Exception as e:
            logger.warning(f"[UnifiedSyncProcessor] Fast extraction failed, falling back to standard: {e}")
            # Fall back to standard extraction
            return self._extract_citations_standard(text)
    
    def _extract_citations_standard(self, text: str) -> List:
        """Standard citation extraction for medium-length text."""
        try:
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            processor = UnifiedCitationProcessorV2()
            citations = processor._extract_with_regex(text)
            
            logger.info(f"[UnifiedSyncProcessor] Standard extraction found {len(citations)} citations")
            return citations
            
        except Exception as e:
            logger.error(f"[UnifiedSyncProcessor] Standard extraction failed: {e}")
            return []
    
    def _extract_citations_fallback(self, text: str, request_id: str) -> Dict[str, Any]:
        """Fallback extraction when all other methods fail."""
        logger.warning(f"[UnifiedSyncProcessor {request_id}] Using fallback extraction")
        
        # Try basic regex extraction as last resort
        import re
        basic_citations = re.findall(r'\b\d+\s+Wn\.\d+\s+\d+', text)
        
        return {
            'success': True,
            'citations': [{'citation': c, 'extracted_case_name': None, 'extracted_date': None} for c in basic_citations],
            'clusters': [],
            'processing_strategy': 'fallback',
            'extraction_method': 'basic_regex',
            'warning': 'Used fallback extraction due to processing errors'
        }
    
    def _apply_clustering_with_verification(self, citations: List, text: str, request_id: str, options: Optional[Dict]) -> List:
        """Apply clustering with verification for citations."""
        try:
            from src.unified_citation_clustering import cluster_citations_unified
            
            # Smart verification strategy
            enable_verification = len(text) > 500  # Lowered from 1000 to 500 for better coverage
            
            # Special handling for Washington citations
            if any('Wn.' in str(c) for c in citations) and len(text) >= 300:
                logger.info(f"[UnifiedSyncProcessor {request_id}] Washington citations detected - ensuring proper parallel detection")
                enable_verification = True
            elif any('Wn.' in str(c) for c in citations) and len(text) < 300:
                logger.info(f"[UnifiedSyncProcessor {request_id}] Washington citations detected but text too short - using fast path")
                enable_verification = False
            
            # Apply clustering
            clustering_result = cluster_citations_unified(
                citations, 
                text, 
                enable_verification=enable_verification
            )
            
            # Handle clustering result (can be list or dict)
            if isinstance(clustering_result, dict):
                clusters = clustering_result.get('clusters', [])
            else:
                clusters = clustering_result if isinstance(clustering_result, list) else []
            
            logger.info(f"[UnifiedSyncProcessor {request_id}] Clustering completed with {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.warning(f"[UnifiedSyncProcessor {request_id}] Clustering failed: {e}")
            return []
    
    def _convert_citations_to_dicts(self, citations: List) -> List[Dict[str, Any]]:
        """Convert citation objects to dictionaries for API response."""
        citations_list = []
        if citations:
            for citation in citations:
                citation_dict = {
                    'citation': getattr(citation, 'citation', str(citation)),
                    'case_name': getattr(citation, 'extracted_case_name', None) or getattr(citation, 'case_name', None),
                    'extracted_case_name': getattr(citation, 'extracted_case_name', None),
                    'canonical_name': getattr(citation, 'canonical_name', None),
                    'extracted_date': getattr(citation, 'extracted_date', None),
                    'canonical_date': getattr(citation, 'canonical_date', None),
                    'canonical_url': getattr(citation, 'canonical_url', None) or getattr(citation, 'url', None),
                    'year': getattr(citation, 'year', None),
                    'verified': getattr(citation, 'verified', False) or getattr(citation, 'is_verified', False),
                    'court': getattr(citation, 'court', None),
                    'confidence': getattr(citation, 'confidence', 0.0),
                    'method': getattr(citation, 'method', 'unified_sync'),
                    'context': getattr(citation, 'context', ''),
                    'is_parallel': getattr(citation, 'is_parallel', False)
                }
                citations_list.append(citation_dict)
        
        return citations_list
    
    def _convert_clusters_to_dicts(self, clusters: List) -> List[Dict[str, Any]]:
        """Convert cluster objects to dictionaries for API response."""
        clusters_list = []
        if clusters:
            for cluster in clusters:
                cluster_dict = {
                    'cluster_id': getattr(cluster, 'cluster_id', None),
                    'citations': [str(c) for c in getattr(cluster, 'citations', [])],
                    'canonical_name': getattr(cluster, 'canonical_name', None),
                    'canonical_date': getattr(cluster, 'canonical_date', None),
                    'canonical_url': getattr(cluster, 'canonical_url', None),
                    'verification_status': getattr(cluster, 'verification_status', 'unverified'),
                    'confidence': getattr(cluster, 'confidence', 0.0)
                }
                clusters_list.append(cluster_dict)
        
        return clusters_list
    
    def _has_verification(self, citations: List) -> bool:
        """Check if any citations have verification data."""
        return any(
            getattr(c, 'verified', False) or getattr(c, 'is_verified', False) or 
            getattr(c, 'canonical_name', None) or getattr(c, 'canonical_url', None)
            for c in citations
        )
    
    def _get_processing_strategy(self, text: str) -> str:
        """Determine which processing strategy was used."""
        if len(text) < self.ultra_fast_threshold:
            return 'ultra_fast'
        elif len(text) < self.clustering_skip_threshold:
            return 'fast_no_clustering'
        else:
            return 'full_with_verification'
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        cache_stats = self._get_cache_stats()
        
        return {
            'cache': cache_stats,
            'thresholds': {
                'immediate_processing_threshold': self.immediate_processing_threshold,
                'ultra_fast_threshold': self.ultra_fast_threshold,
                'clustering_skip_threshold': self.clustering_skip_threshold,
                'max_citations_for_skip_clustering': self.max_citations_for_skip_clustering
            },
            'processing_modes': ['ultra_fast', 'fast_no_clustering', 'full_with_verification'],
            'cache_ttl': self.cache_ttl
        }
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {'cache_size': 0, 'active_entries': 0}
        
        current_time = time.time()
        active_entries = sum(
            1 for value in self.cache.values()
            if current_time - value.get('cache_time', 0) <= self.cache_ttl
        )
        
        return {
            'cache_size': len(self.cache),
            'active_entries': active_entries
        }
