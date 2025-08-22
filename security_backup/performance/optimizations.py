"""
Optimized versions of citation processing services with performance improvements.

This module provides enhanced versions of the citation services with caching,
async improvements, and algorithmic optimizations.
"""

import asyncio
import re
import time
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from ..services.interfaces import ICitationExtractor, ICitationVerifier, ICitationClusterer
from ..services.citation_extractor import CitationExtractor
from ..services.citation_verifier import CitationVerifier
from ..services.citation_clusterer import CitationClusterer
from ..models import CitationResult, ProcessingConfig
from .cache import cache_manager, cached, MemoryCache
from .profiler import profiler

logger = logging.getLogger(__name__)


class OptimizedCitationExtractor(ICitationExtractor):
    """
    Optimized citation extractor with caching and performance improvements.
    """
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        # Convert ProcessingConfig to dict for base extractor
        config_dict = config.__dict__ if hasattr(config, '__dict__') else {}
        self.base_extractor = CitationExtractor(config_dict)
        
        # Performance optimizations
        self._compiled_patterns = {}
        self._compile_patterns()
        
        # Caching
        self.cache = MemoryCache(max_size=500, default_ttl=1800)  # 30 minutes
        cache_manager.register_cache('extractor', self.cache)
        
        # Thread pool for parallel processing
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        
        if config.debug_mode:
            logger.info("OptimizedCitationExtractor initialized with caching and parallel processing")
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance."""
        # Common citation patterns - compiled once for reuse
        self._compiled_patterns = {
            'us_supreme_court': re.compile(
                r'\b(\d+)\s+U\.S\.\s+(\d+)\s*\((\d{4})\)',
                re.IGNORECASE
            ),
            'federal_reporter': re.compile(
                r'\b(\d+)\s+F\.\s*(?:2d|3d)?\s+(\d+)\s*\([^)]*(\d{4})[^)]*\)',
                re.IGNORECASE
            ),
            'supreme_court_reporter': re.compile(
                r'\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\s*\((\d{4})\)',
                re.IGNORECASE
            ),
            'lawyers_edition': re.compile(
                r'\b(\d+)\s+L\.\s*Ed\.\s*(?:2d)?\s+(\d+)\s*\((\d{4})\)',
                re.IGNORECASE
            ),
            'case_name': re.compile(
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                re.IGNORECASE
            )
        }
    
    @profiler.profile_sync("extract_citations_optimized")
    def extract_citations(self, text: str) -> List[CitationResult]:
        """Extract citations with performance optimizations."""
        # Check cache first
        cache_key = self.cache.generate_key("extract", text[:1000])  # Use first 1000 chars for key
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            if self.config.debug_mode:
                logger.debug("Cache hit for citation extraction")
            return cached_result
        
        # Split large texts for parallel processing
        if len(text) > 10000:  # 10KB threshold
            result = self._extract_parallel(text)
        else:
            result = self._extract_single(text)
        
        # Cache the result
        self.cache.set(cache_key, result)
        
        return result
    
    def _extract_single(self, text: str) -> List[CitationResult]:
        """Extract citations from a single text block."""
        citations = []
        
        # Use compiled patterns for faster matching
        for pattern_name, pattern in self._compiled_patterns.items():
            if pattern_name == 'case_name':
                continue  # Handle case names separately
            
            for match in pattern.finditer(text):
                citation_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                # Extract metadata using compiled patterns
                metadata = self._extract_metadata_fast(citation_text, text, start_pos)
                
                citation = CitationResult(
                    citation=citation_text,
                    start_index=start_pos,
                    end_index=end_pos,
                    method="optimized_regex",
                    pattern=pattern_name,
                    confidence=0.8,
                    context=text[max(0, start_pos-50):end_pos+50],
                    **metadata
                )
                citations.append(citation)
        
        # Deduplicate and sort
        citations = self._deduplicate_fast(citations)
        return sorted(citations, key=lambda x: x.start_index or 0)
    
    def _extract_parallel(self, text: str) -> List[CitationResult]:
        """Extract citations using parallel processing for large texts."""
        # Split text into chunks
        chunk_size = 5000  # 5KB chunks with overlap
        overlap = 500      # 500 char overlap to catch citations spanning chunks
        
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            chunks.append((chunk, i))
        
        # Process chunks in parallel
        all_citations = []
        futures = []
        
        for chunk, offset in chunks:
            future = self._thread_pool.submit(self._extract_chunk, chunk, offset)
            futures.append(future)
        
        # Collect results
        for future in as_completed(futures):
            try:
                chunk_citations = future.result()
                all_citations.extend(chunk_citations)
            except Exception as e:
                logger.error(f"Error processing chunk: {e}")
        
        # Deduplicate across chunks
        all_citations = self._deduplicate_fast(all_citations)
        return sorted(all_citations, key=lambda x: x.start_index or 0)
    
    def _extract_chunk(self, chunk: str, offset: int) -> List[CitationResult]:
        """Extract citations from a text chunk."""
        citations = self._extract_single(chunk)
        
        # Adjust positions for offset
        for citation in citations:
            if citation.start_index is not None:
                citation.start_index += offset
            if citation.end_index is not None:
                citation.end_index += offset
        
        return citations
    
    def _extract_metadata_fast(self, citation_text: str, full_text: str, start_pos: int) -> Dict[str, Any]:
        """Fast metadata extraction using compiled patterns."""
        metadata = {}
        
        # Look for case name near the citation
        context_start = max(0, start_pos - 200)
        context_end = min(len(full_text), start_pos + len(citation_text) + 200)
        context = full_text[context_start:context_end]
        
        case_match = self._compiled_patterns['case_name'].search(context)
        if case_match:
            metadata['extracted_case_name'] = case_match.group(0)
        
        # Extract year from citation
        year_match = re.search(r'\((\d{4})\)', citation_text)
        if year_match:
            metadata['extracted_date'] = year_match.group(1)
        
        return metadata
    
    def _deduplicate_fast(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Fast deduplication using set operations."""
        seen = set()
        unique_citations = []
        
        for citation in citations:
            # Create a simple key for deduplication
            key = (citation.citation.strip().lower(), citation.start_index)
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)
        
        return unique_citations
    
    def extract_metadata(self, citation: CitationResult, text: str) -> CitationResult:
        """Extract metadata for a citation using optimized methods."""
        # Use the fast metadata extraction method
        start_pos = citation.start_index or 0
        metadata = self._extract_metadata_fast(citation.citation, text, start_pos)
        
        # Update citation with metadata
        if 'extracted_case_name' in metadata:
            citation.extracted_case_name = metadata['extracted_case_name']
        if 'extracted_date' in metadata:
            citation.extracted_date = metadata['extracted_date']
        
        return citation


class OptimizedCitationVerifier(ICitationVerifier):
    """
    Optimized citation verifier with intelligent caching and batch processing.
    """
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.base_verifier = CitationVerifier(config)
        
        # Multi-level caching
        self.verification_cache = MemoryCache(max_size=1000, default_ttl=3600)  # 1 hour
        self.landmark_cache = MemoryCache(max_size=200, default_ttl=86400)     # 24 hours
        
        cache_manager.register_cache('verifier', self.verification_cache)
        cache_manager.register_cache('landmark', self.landmark_cache)
        
        # Rate limiting
        self._last_api_call = 0
        self._min_api_interval = 0.1  # 100ms between API calls
        self._api_lock = threading.Lock()
        
        if config.debug_mode:
            logger.info("OptimizedCitationVerifier initialized with multi-level caching")
    
    @profiler.profile_async("verify_citations_optimized")
    async def verify_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Verify citations with optimizations."""
        if not citations:
            return citations
        
        # Separate cached and uncached citations
        cached_citations = []
        uncached_citations = []
        
        for citation in citations:
            cache_key = self._get_verification_cache_key(citation)
            cached_result = self.verification_cache.get(cache_key)
            
            if cached_result is not None:
                # Apply cached verification data
                citation.verified = cached_result.get('verified', False)
                citation.canonical_name = cached_result.get('canonical_name')
                citation.canonical_date = cached_result.get('canonical_date')
                citation.url = cached_result.get('url')
                citation.court = cached_result.get('court')
                citation.docket_number = cached_result.get('docket_number')
                cached_citations.append(citation)
                
                if self.config.debug_mode:
                    logger.debug(f"Cache hit for verification: {citation.citation}")
            else:
                uncached_citations.append(citation)
        
        # Verify uncached citations in batches
        if uncached_citations:
            verified_citations = await self._verify_batch(uncached_citations)
            
            # Cache the results
            for citation in verified_citations:
                cache_key = self._get_verification_cache_key(citation)
                cache_data = {
                    'verified': citation.verified,
                    'canonical_name': citation.canonical_name,
                    'canonical_date': citation.canonical_date,
                    'url': citation.url,
                    'court': citation.court,
                    'docket_number': citation.docket_number
                }
                self.verification_cache.set(cache_key, cache_data)
            
            cached_citations.extend(verified_citations)
        
        return cached_citations
    
    async def _verify_batch(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Verify citations in optimized batches."""
        # Check landmark cases first (fast)
        landmark_verified = []
        api_needed = []
        
        for citation in citations:
            landmark_key = self._get_landmark_cache_key(citation)
            landmark_result = self.landmark_cache.get(landmark_key)
            
            if landmark_result is not None:
                citation.verified = True
                citation.canonical_name = landmark_result.get('canonical_name')
                citation.canonical_date = landmark_result.get('canonical_date')
                citation.method = 'landmark_cache'
                landmark_verified.append(citation)
            else:
                api_needed.append(citation)
        
        # Process API verifications with rate limiting
        if api_needed:
            api_verified = await self._verify_with_rate_limiting(api_needed)
            landmark_verified.extend(api_verified)
        
        return landmark_verified
    
    async def _verify_with_rate_limiting(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Verify citations with intelligent rate limiting."""
        verified = []
        
        for citation in citations:
            # Rate limiting
            with self._api_lock:
                now = time.time()
                time_since_last = now - self._last_api_call
                if time_since_last < self._min_api_interval:
                    await asyncio.sleep(self._min_api_interval - time_since_last)
                self._last_api_call = time.time()
            
            # Use base verifier for actual API call
            try:
                verified_citation = await self.base_verifier.verify_single_citation(citation)
                verified.append(verified_citation)
                
                # Cache landmark cases for future use
                if verified_citation.verified:
                    landmark_key = self._get_landmark_cache_key(verified_citation)
                    landmark_data = {
                        'canonical_name': verified_citation.canonical_name,
                        'canonical_date': verified_citation.canonical_date
                    }
                    self.landmark_cache.set(landmark_key, landmark_data)
                
            except Exception as e:
                logger.error(f"Error verifying citation {citation.citation}: {e}")
                verified.append(citation)  # Return unverified
        
        return verified
    
    def _get_verification_cache_key(self, citation: CitationResult) -> str:
        """Generate cache key for verification."""
        return self.verification_cache.generate_key("verify", citation.citation.strip().lower())
    
    def _get_landmark_cache_key(self, citation: CitationResult) -> str:
        """Generate cache key for landmark cases."""
        # Use case name if available, otherwise citation text
        key_text = citation.extracted_case_name or citation.citation
        return self.landmark_cache.generate_key("landmark", key_text.strip().lower())


class OptimizedCitationClusterer(ICitationClusterer):
    """
    Optimized citation clusterer with improved algorithms and caching.
    """
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.base_clusterer = CitationClusterer(config)
        
        # Caching for parallel citation detection
        self.parallel_cache = MemoryCache(max_size=300, default_ttl=1800)  # 30 minutes
        cache_manager.register_cache('clusterer', self.parallel_cache)
        
        # Pre-compiled patterns for parallel detection
        self._parallel_patterns = self._compile_parallel_patterns()
        
        if config.debug_mode:
            logger.info("OptimizedCitationClusterer initialized with pattern caching")
    
    def _compile_parallel_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for parallel citation detection."""
        return {
            'us_reports': re.compile(r'(\d+)\s+U\.S\.\s+(\d+)', re.IGNORECASE),
            'supreme_court': re.compile(r'(\d+)\s+S\.\s*Ct\.\s+(\d+)', re.IGNORECASE),
            'lawyers_ed': re.compile(r'(\d+)\s+L\.\s*Ed\.\s*(?:2d)?\s+(\d+)', re.IGNORECASE),
            'federal': re.compile(r'(\d+)\s+F\.\s*(?:2d|3d)?\s+(\d+)', re.IGNORECASE)
        }
    
    @profiler.profile_sync("detect_parallel_citations_optimized")
    def detect_parallel_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """Detect parallel citations with optimizations."""
        if len(citations) <= 1:
            return citations
        
        # Check cache for parallel detection results
        cache_key = self._get_parallel_cache_key(citations)
        cached_result = self.parallel_cache.get(cache_key)
        if cached_result is not None:
            if self.config.debug_mode:
                logger.debug("Cache hit for parallel detection")
            return cached_result
        
        # Use optimized parallel detection
        result = self._detect_parallel_optimized(citations, text)
        
        # Cache the result
        self.parallel_cache.set(cache_key, result)
        
        return result
    
    def _detect_parallel_optimized(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """Optimized parallel citation detection."""
        # Sort citations by position
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        
        # Group by proximity
        groups = self._group_by_proximity(sorted_citations, max_distance=100)
        
        # Detect parallels in each group
        for group in groups:
            self._detect_parallels_in_group(group, text)
        
        return sorted_citations
    
    def _group_by_proximity(self, citations: List[CitationResult], max_distance: int) -> List[List[CitationResult]]:
        """Group citations by proximity in text."""
        if not citations:
            return []
        
        # Sort by position
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        
        groups = []
        current_group = [sorted_citations[0]]
        
        for i in range(1, len(sorted_citations)):
            current_citation = sorted_citations[i]
            last_citation = current_group[-1]
            
            # Check if citations are within proximity
            current_start = current_citation.start_index or 0
            last_end = last_citation.end_index or 0
            distance = current_start - last_end
            
            if distance <= max_distance:
                current_group.append(current_citation)
            else:
                groups.append(current_group)
                current_group = [current_citation]
        
        groups.append(current_group)
        return groups
    
    def _detect_parallels_in_group(self, group: List[CitationResult], text: str) -> None:
        """Detect parallel citations within a proximity group."""
        # Get text range for this group
        start_positions = [c.start_index for c in group if c.start_index is not None]
        end_positions = [c.end_index for c in group if c.end_index is not None]
        
        if not start_positions or not end_positions:
            return
            
        start_pos = min(start_positions) - 50
        end_pos = max(end_positions) + 50
        group_text = text[max(0, start_pos):min(len(text), end_pos)]
        
        # Look for patterns indicating parallel citations
        parallel_indicators = [
            r'\b(?:see\s+also|also|accord|cf\.?|compare)\b',
            r'\b(?:citing|quoting|overruled\s+by|reversed\s+by)\b',
            r'[;,]\s*(?:see\s+)?(?:also\s+)?'
        ]
        
        has_parallel_indicators = any(
            re.search(pattern, group_text, re.IGNORECASE) 
            for pattern in parallel_indicators
        )
        
        if has_parallel_indicators or len(group) >= 3:
            # Mark citations as parallel to each other
            for i, citation1 in enumerate(group):
                parallels = []
                for j, citation2 in enumerate(group):
                    if i != j and self._are_likely_parallel(citation1, citation2):
                        parallels.append(citation2.citation)
                
                if parallels:
                    citation1.parallel_citations = parallels
    
    def _are_likely_parallel(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """Check if two citations are likely parallel citations."""
        # Same case name
        if (citation1.extracted_case_name and citation2.extracted_case_name and
            citation1.extracted_case_name.lower() == citation2.extracted_case_name.lower()):
            return True
        
        # Same year
        if (citation1.extracted_date and citation2.extracted_date and
            citation1.extracted_date == citation2.extracted_date):
            return True
        
        # Different reporter types (strong indicator)
        patterns1 = set()
        patterns2 = set()
        
        for pattern_name, pattern in self._parallel_patterns.items():
            if pattern.search(citation1.citation):
                patterns1.add(pattern_name)
            if pattern.search(citation2.citation):
                patterns2.add(pattern_name)
        
        # Different patterns but both valid = likely parallel
        return len(patterns1) > 0 and len(patterns2) > 0 and patterns1 != patterns2
    
    @profiler.profile_sync("cluster_citations_optimized")
    def cluster_citations(self, citations: List[CitationResult]) -> List[Dict[str, Any]]:
        """Cluster citations with optimizations."""
        if not citations:
            return []
        
        # Use base clusterer but with optimized pre-processing
        return self.base_clusterer.cluster_citations(citations)
    
    def _get_parallel_cache_key(self, citations: List[CitationResult]) -> str:
        """Generate cache key for parallel detection."""
        # Use citation positions and text as key
        key_data = [(c.citation, c.start_index, c.end_index) for c in citations[:10]]  # Limit for performance
        return self.parallel_cache.generate_key("parallel", str(key_data))


# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor performance of optimized services."""
    
    def __init__(self):
        self.metrics = {}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        return cache_manager.get_all_stats()
    
    def get_profiler_summary(self) -> Dict[str, Any]:
        """Get profiler summary."""
        return profiler.get_summary()
    
    def print_performance_report(self):
        """Print a comprehensive performance report."""
        print("\n" + "="*60)
        print("PERFORMANCE OPTIMIZATION REPORT")
        print("="*60)
        
        # Cache statistics
        print("\nCACHE STATISTICS:")
        print("-"*30)
        cache_stats = self.get_cache_stats()
        for cache_name, stats in cache_stats.items():
            print(f"{cache_name.upper()} Cache:")
            print(f"  Hit Rate: {stats.get('hit_rate', 0):.1%}")
            print(f"  Size: {stats.get('size', 0)}")
            print(f"  Hits: {stats.get('hits', 0)}")
            print(f"  Misses: {stats.get('misses', 0)}")
            print()
        
        # Profiler statistics
        print("EXECUTION STATISTICS:")
        print("-"*30)
        profiler_stats = self.get_profiler_summary()
        for operation, stats in profiler_stats.items():
            print(f"{operation}:")
            print(f"  Average Time: {stats.get('avg_time', 0):.3f}s")
            print(f"  Total Calls: {stats.get('count', 0)}")
            print(f"  Total Time: {stats.get('total_time', 0):.3f}s")
            print()
        
        print("="*60)


# Global performance monitor
performance_monitor = PerformanceMonitor()
