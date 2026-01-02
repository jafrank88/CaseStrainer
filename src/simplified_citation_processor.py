"""
Simplified Citation Processor - A unified approach to citation processing.

This module consolidates all citation processing logic into a single, 
configuration-driven processor to eliminate code duplication and complexity.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List
import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Processing mode enumeration."""
    SYNCHRONOUS = "sync"
    ASYNCHRONOUS = "async"


@dataclass
class ProcessingConfig:
    """Configuration for citation processing."""
    enable_verification: bool = True
    enable_clustering: bool = True
    max_citations: int = 1000
    timeout_seconds: int = 300
    cache_results: bool = True
    async_threshold_kb: int = 5
    progress_callback: Optional[Callable] = None
    external_apis: List[str] = field(default_factory=lambda: [
        'justia', 'openjurist', 'cornell_lii', 'google_scholar'
    ])


@dataclass
class ProcessingResult:
    """Standardized result format."""
    citations: List[Dict[str, Any]] = field(default_factory=list)
    clusters: List[Dict[str, Any]] = field(default_factory=list)
    verification_results: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0
    mode: ProcessingMode = ProcessingMode.SYNCHRONOUS
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimplifiedCitationProcessor:
    """
    Single processor for all citation processing needs.
    
    This class consolidates the functionality from:
    - UnifiedInputProcessor
    - CitationProcessor
    - ChunkedCitationProcessor
    - RQ worker logic
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self._cache = {} if self.config.cache_results else None
        
    def process(self, input_data: Dict, request_id: str) -> ProcessingResult:
        """
        Unified entry point for all citation processing.
        
        Args:
            input_data: Dictionary containing text, file, or URL
            request_id: Unique request identifier
            
        Returns:
            ProcessingResult with standardized format
        """
        start_time = time.time()
        
        # Determine processing mode
        mode = self._determine_processing_mode(input_data)
        
        # Extract text from input
        text = self._extract_text(input_data)
        
        # Process citations
        if mode == ProcessingMode.SYNCHRONOUS:
            result = self._process_sync(text, request_id)
        else:
            result = self._process_async(text, request_id)
            
        # Add metadata
        result.processing_time = time.time() - start_time
        result.mode = mode
        result.metadata.update({
            'input_type': input_data.get('type', 'unknown'),
            'text_length': len(text),
            'config': {
                'verification': self.config.enable_verification,
                'clustering': self.config.enable_clustering,
                'max_citations': self.config.max_citations
            }
        })
        
        return result
    
    def _determine_processing_mode(self, input_data: Dict) -> ProcessingMode:
        """Determine if processing should be sync or async."""
        text = input_data.get('text', '')
        
        # Check if text is provided and exceeds threshold
        if text and len(text.encode('utf-8')) / 1024 >= self.config.async_threshold_kb:
            return ProcessingMode.ASYNCHRONOUS
            
        # For files and URLs, always use async
        if input_data.get('type') in ['file', 'url']:
            return ProcessingMode.ASYNCHRONOUS
            
        return ProcessingMode.SYNCHRONOUS
    
    def _extract_text(self, input_data: Dict) -> str:
        """Extract text from various input types."""
        input_type = input_data.get('type', 'text')
        
        if input_type == 'text':
            return input_data.get('text', '')
        elif input_type == 'file':
            return self._extract_text_from_file(input_data.get('file_path', ''))
        elif input_type == 'url':
            return self._extract_text_from_url(input_data.get('url', ''))
        else:
            raise ValueError(f"Unsupported input type: {input_type}")
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from file."""
        # Implementation would use UnifiedTextExtractor
        # For now, return placeholder
        logger.info(f"Extracting text from file: {file_path}")
        return ""
    
    def _extract_text_from_url(self, url: str) -> str:
        """Extract text from URL."""
        # Implementation would use web scraping
        # For now, return placeholder
        logger.info(f"Extracting text from URL: {url}")
        return ""
    
    def _process_sync(self, text: str, request_id: str) -> ProcessingResult:
        """Process text synchronously."""
        logger.info(f"[{request_id}] Processing synchronously")
        
        # Check cache first
        cache_key = hash(text) if self._cache else None
        if cache_key and cache_key in self._cache:
            logger.info(f"[{request_id}] Using cached result")
            return self._cache[cache_key]
        
        # Extract citations
        citations = self._extract_citations(text, request_id)
        
        # Apply limits
        if len(citations) > self.config.max_citations:
            citations = citations[:self.config.max_citations]
            logger.warning(f"[{request_id}] Limited citations to {self.config.max_citations}")
        
        # Verify if enabled
        verification_results = None
        if self.config.enable_verification:
            verification_results = self._verify_citations(citations, request_id)
        
        # Cluster if enabled
        clusters = []
        if self.config.enable_clustering:
            clusters = self._cluster_citations(citations, request_id)
        
        result = ProcessingResult(
            citations=citations,
            clusters=clusters,
            verification_results=verification_results,
            metadata={'request_id': request_id}
        )
        
        # Cache result
        if cache_key:
            self._cache[cache_key] = result
        
        return result
    
    def _process_async(self, text: str, request_id: str) -> ProcessingResult:
        """Process text asynchronously by enqueuing job."""
        logger.info(f"[{request_id}] Processing asynchronously - enqueuing job")
        
        # Import here to avoid circular imports
        from src.redis_helper import get_rq_queue
        
        queue = get_rq_queue()
        job = queue.enqueue(
            _process_async_task,
            text=text,
            config=self.config,
            request_id=request_id,
            timeout=self.config.timeout_seconds
        )
        
        return ProcessingResult(
            task_id=job.id,
            mode=ProcessingMode.ASYNCHRONOUS,
            metadata={
                'request_id': request_id,
                'status': 'queued',
                'job_id': job.id
            }
        )
    
    def _extract_citations(self, text: str, request_id: str) -> List[Dict[str, Any]]:
        """Extract citations from text."""
        # Import the actual extraction function
        from src.citation_extraction_endpoint import extract_citations_with_clustering
        
        logger.info(f"[{request_id}] Extracting citations from {len(text)} characters")
        
        # Update progress if callback provided
        if self.config.progress_callback:
            self.config.progress_callback(20, "Extracting citations...")
        
        # Use existing extraction logic
        result = extract_citations_with_clustering(
            text,
            enable_verification=self.config.enable_verification,  # Use config setting instead of hardcoded False
            progress_callback=self.config.progress_callback
        )
        
        citations = result.get('citations', [])
        logger.info(f"[{request_id}] Extracted {len(citations)} citations")
        
        return citations
    
    def _verify_citations(self, citations: List[Dict[str, Any]], request_id: str) -> Dict[str, Any]:
        """Verify citations against external sources using optimized parallel verification."""
        if not citations:
            return {}
        
        logger.info(f"[{request_id}] Verifying {len(citations)} citations with OPTIMIZED engine")
        
        # Import optimized verification logic
        from src.optimized_verification_master import get_optimized_verifier
        
        verifier = get_optimized_verifier()
        
        # Update progress
        if self.config.progress_callback:
            self.config.progress_callback(50, "Verifying citations...")
        
        # Extract citation data for verification
        citation_texts = [c.get('citation', '') for c in citations]
        case_names = [c.get('extracted_case_name') for c in citations]
        case_dates = [c.get('extracted_date') for c in citations]
        
        # Use optimized batch verification with parallel processing
        import asyncio
        
        def run_optimized_batch_verification():
            """Run optimized batch verification in a new event loop"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    verifier.verify_citations_batch_optimized(
                        citation_texts, 
                        case_names, 
                        case_dates,
                        batch_size=50,  # Use CourtListener's optimal batch size
                        timeout_per_citation=10.0,  # Standard timeout
                        progress_callback=self.config.progress_callback,
                        enable_parallel=True  # Enable parallel fallback verification
                    )
                )
            finally:
                loop.close()
        
        # Handle async context properly
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Use thread pool for running event loop
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=1) as executor:
                    results = executor.submit(run_optimized_batch_verification).result(timeout=self.config.timeout_seconds + 30)
            else:
                results = loop.run_until_complete(
                    verifier.verify_citations_batch_optimized(
                        citation_texts, 
                        case_names, 
                        case_dates,
                        batch_size=50,  # Use CourtListener's optimal batch size
                        timeout_per_citation=10.0,  # Standard timeout
                        progress_callback=self.config.progress_callback,
                        enable_parallel=True
                    )
                )
        except RuntimeError:
            # Create new event loop if needed
            results = run_optimized_batch_verification()
        
        # Apply results to citations (same format as current system)
        verified_count = 0
        possible_matches = 0
        sources_used = set()
        
        for i, result in enumerate(results or []):
            if i >= len(citations):
                break
                
            citation = citations[i]
            
            # Track sources used
            if hasattr(result, 'source') and result.source:
                sources_used.add(result.source)
            
            # Apply verification data (same as current system)
            if hasattr(result, 'verified') and result.verified:
                citation['verified'] = True
                citation['possible_match'] = False
                citation['canonical_name'] = getattr(result, 'canonical_name', None)
                citation['canonical_date'] = getattr(result, 'canonical_date', None)
                citation['canonical_url'] = getattr(result, 'canonical_url', None)
                citation['verification_source'] = getattr(result, 'source', None)
                citation['verification_error'] = None
                citation['verification_method'] = 'optimized_parallel'
                verified_count += 1
            elif hasattr(result, 'possible_match') and result.possible_match:
                citation['verified'] = False
                citation['possible_match'] = True
                citation['canonical_name'] = getattr(result, 'canonical_name', None)
                citation['canonical_date'] = getattr(result, 'canonical_date', None)
                citation['canonical_url'] = getattr(result, 'canonical_url', None)
                citation['verification_source'] = getattr(result, 'source', None)
                citation['verification_error'] = getattr(result, 'error', None)
                citation['verification_method'] = 'optimized_parallel'
                possible_matches += 1
            else:
                citation['verified'] = False
                citation['possible_match'] = False
                citation['verification_error'] = getattr(result, 'error', 'Not found')
                citation['verification_method'] = 'optimized_parallel'
        
        # Get cache stats for monitoring
        cache_stats = verifier.get_cache_stats()
        
        logger.info(f"[{request_id}] Optimized verification complete: {verified_count} verified, {possible_matches} possible matches")
        logger.info(f"[{request_id}] Sources used: {list(sources_used)}, Cache size: {cache_stats['cache_size']}")
        
        # Return verification summary with optimization metrics
        return {
            'verified_count': verified_count,
            'possible_matches': possible_matches,
            'total_citations': len(citations),
            'verification_rate': (verified_count + possible_matches) / len(citations) if citations else 0,
            'sources_used': list(sources_used),
            'verified': [bool(c.get('verified', False)) for c in citations],
            'data': {cit.get('citation', ''): cit for cit in citations},
            'optimization_metrics': {
                'method': 'optimized_parallel',
                'cache_hits': cache_stats['cache_size'],
                'parallel_sources': self.config.external_apis,
                'batch_size': 20,
                'enable_parallel': True
            }
        }
    
    def _cluster_citations(self, citations: List[Dict[str, Any]], request_id: str) -> List[Dict[str, Any]]:
        """Cluster similar citations."""
        if not citations:
            return []
        
        logger.info(f"[{request_id}] Clustering {len(citations)} citations")
        
        # Import clustering logic
        from src.unified_citation_clustering import cluster_citations_unified
        
        # Update progress
        if self.config.progress_callback:
            self.config.progress_callback(80, "Clustering citations...")
        
        # Cluster citations
        clusters = cluster_citations_unified(citations)
        
        logger.info(f"[{request_id}] Created {len(clusters)} clusters")
        return clusters


def _process_async_task(text: str, config: ProcessingConfig, request_id: str) -> Dict[str, Any]:
    """
    Task function for async processing.
    
    This function runs in the RQ worker process.
    """
    processor = SimplifiedCitationProcessor(config)
    result = processor._process_sync(text, request_id)
    
    # Convert to dict for Redis storage
    return {
        'citations': result.citations,
        'clusters': result.clusters,
        'verification_results': result.verification_results,
        'processing_time': result.processing_time,
        'metadata': result.metadata
    }


# Factory function for easy instantiation
def create_processor(**kwargs) -> SimplifiedCitationProcessor:
    """Create a SimplifiedCitationProcessor with the given configuration."""
    config = ProcessingConfig(**kwargs)
    return SimplifiedCitationProcessor(config)
