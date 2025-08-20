"""
Extracted citation processing business logic from the main API file.
This separates concerns and makes the code more testable and maintainable.
"""

import asyncio
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from src.redis_distributed_processor import DockerOptimizedProcessor

logger = logging.getLogger(__name__)


class CitationService:
    """Service for processing citations with Redis-distributed processing."""
    
    def __init__(self):
        self.processor = DockerOptimizedProcessor()
        self.cache_ttl = 3600  # 1 hour cache
        self._cache = {}  # Initialize cache
        self._last_cache_cleanup = time.time()
        self._cache_cleanup_interval = 300  # Clean cache every 5 minutes
    
    def should_process_immediately(self, input_data: Dict) -> bool:
        """Determine if input should be processed immediately vs queued."""
        input_type = input_data.get('type')
        
        if input_type == 'text':
            text = input_data.get('text', '')
            # Process short texts immediately (< 2KB) for better performance
            # Most legal text snippets are under 1KB and should be instant
            return len(text) < 2 * 1024  # Changed from 10KB to 2KB
        elif input_type == 'file':
            # Always queue file uploads for async processing
            # File processing involves PDF parsing, text extraction, and citation analysis
            # which can take a long time and should never be done synchronously
            return False
        elif input_type == 'url':
            # Always queue URL processing for better performance and resource management
            return False
        
        return False
    
    def process_immediately(self, input_data: Dict) -> Dict[str, Any]:
        """Process input immediately using direct citation processing (no circular dependency)."""
        start_time = time.time()
        
        try:
            if input_data.get('type') == 'text':
                text = input_data.get('text', '')
                
                # PERFORMANCE OPTIMIZATION: Check cache first for repeated text patterns
                cache_key = f"text_{hash(text)}"
                if hasattr(self, '_cache') and cache_key in self._cache:
                    cached_result = self._cache[cache_key]
                    if time.time() - cached_result.get('cache_time', 0) < self.cache_ttl:
                        logger.info(f"[CitationService] Cache hit for text pattern, returning cached result in {time.time() - start_time:.3f}s")
                        return cached_result['result']
                
                logger.info(f"[CitationService] Processing text immediately: {text[:100]}...")
                
                # PERFORMANCE OPTIMIZATION: Use faster processing for short text
                if len(text) < 500:  # Very short text - use ultra-fast path
                    logger.info(f"[CitationService] Using ultra-fast path for {len(text)} characters")
                    citations = self._extract_citations_fast(text)
                else:
                    # Standard processing for medium text
                    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                    processor = UnifiedCitationProcessorV2()
                    citations = processor._extract_with_regex(text)
                
                # Citations are already CitationResult objects from extract_with_regex
                citation_results = citations
                
                # PERFORMANCE OPTIMIZATION: Skip clustering for very short text with few citations
                if len(text) < 300 and len(citations) <= 3:
                    logger.info(f"[CitationService] Skipping clustering for short text with few citations")
                    clusters = []
                else:
                    # Apply clustering with verification
                    from src.unified_citation_clustering import cluster_citations_unified
                    
                    # PERFORMANCE OPTIMIZATION: Skip verification for immediate processing of short text
                    # This reduces processing time from 79+ seconds to under 1 second
                    enable_verification = len(text) > 500  # Lowered from 1000 to 500 for better coverage
                    
                    # ENHANCED: Special handling for Washington citations to ensure proper clustering
                    if any('Wn.' in str(c) for c in citation_results):
                        logger.info(f"[CitationService] Washington citations detected - ensuring proper parallel detection")
                        # Force clustering even for short text to get proper parallel citation grouping
                        # BUT allow verification to get canonical data (names, years, URLs)
                        enable_verification = True  # Changed from False to True
                        logger.info(f"[CitationService] Enabling verification for Washington citations to get canonical data")
                    
                    clustering_result = cluster_citations_unified(citation_results, text, enable_verification=enable_verification)
                    
                    # Handle clustering result (can be list or dict)
                    if isinstance(clustering_result, dict):
                        clusters = clustering_result.get('clusters', [])
                    else:
                        # clustering_result is a list of clusters
                        clusters = clustering_result if isinstance(clustering_result, list) else []
                
                # Convert citation objects to dictionaries for API response
                citations_list = []
                if citation_results:
                    for citation in citation_results:
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
                            'method': getattr(citation, 'method', 'direct'),
                            'context': getattr(citation, 'context', ''),
                            'is_parallel': getattr(citation, 'is_parallel', False)
                        }
                        citations_list.append(citation_dict)
                
                # Convert clusters to dictionaries
                clusters_list = []
                if clusters:
                    for cluster in clusters:
                        if isinstance(cluster, dict):
                            clusters_list.append(cluster)
                        else:
                            # Convert cluster object to dict if needed
                            cluster_dict = {
                                'case_name': getattr(cluster, 'case_name', None),
                                'year': getattr(cluster, 'year', None),
                                'citations': getattr(cluster, 'citations', [])
                            }
                            clusters_list.append(cluster_dict)
                
                processing_time = time.time() - start_time
                logger.info(f"[CitationService] Found {len(citations_list)} citations, {len(clusters_list)} clusters in {processing_time:.3f}s")
                
                result = {
                    'citations': citations_list,
                    'clusters': clusters_list,
                    'status': 'completed',
                    'message': f"Found {len(citations_list)} citations in {len(clusters_list)} clusters",
                    'processing_time': processing_time,
                    'processing_mode': 'immediate',
                    'text_length': len(text)
                }
                
                # PERFORMANCE OPTIMIZATION: Cache the result for future use
                if not hasattr(self, '_cache'):
                    self._cache = {}
                self._cache[cache_key] = {
                    'result': result,
                    'cache_time': time.time()
                }
                
                # PERFORMANCE OPTIMIZATION: Periodic cache cleanup
                current_time = time.time()
                if current_time - self._last_cache_cleanup > self._cache_cleanup_interval:
                    self._clear_old_cache()
                    self._last_cache_cleanup = current_time
                
                return result
            
            return {'status': 'error', 'message': 'Invalid input type for immediate processing'}
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error in immediate processing: {str(e)}"
            logger.error(f"[CitationService] {error_msg}", exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'processing_time': processing_time,
                'processing_mode': 'immediate'
            }
    
    def _extract_citations_fast(self, text: str) -> List:
        """Ultra-fast citation extraction for very short text using optimized regex patterns."""
        try:
            # Import only what we need for fast processing
            import re
            from src.citation_extractor import CitationExtractor
            
            # Use the existing citation extractor with fast processing
            extractor = CitationExtractor()
            citations = extractor.extract_citations(text)  # Use existing method
            
            logger.info(f"[CitationService] Fast extraction found {len(citations)} citations")
            return citations
            
        except Exception as e:
            logger.warning(f"[CitationService] Fast extraction failed, falling back to standard: {e}")
            # Fall back to standard extraction
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            processor = UnifiedCitationProcessorV2()
            return processor._extract_with_regex(text)
    
    def _clear_old_cache(self):
        """Clear old cache entries to prevent memory bloat."""
        if hasattr(self, '_cache'):
            current_time = time.time()
            old_keys = [
                key for key, value in self._cache.items()
                if current_time - value.get('cache_time', 0) > self.cache_ttl
            ]
            for key in old_keys:
                del self._cache[key]
            
            if old_keys:
                logger.info(f"[CitationService] Cleared {len(old_keys)} old cache entries")
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        if not hasattr(self, '_cache'):
            return {'cache_size': 0, 'cache_hits': 0, 'cache_misses': 0}
        
        current_time = time.time()
        active_entries = sum(
            1 for value in self._cache.values()
            if current_time - value.get('cache_time', 0) <= self.cache_ttl
        )
        
        return {
            'cache_size': len(self._cache),
            'active_entries': active_entries,
            'cache_ttl': self.cache_ttl
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        cache_stats = self._get_cache_stats()
        
        return {
            'cache': cache_stats,
            'immediate_processing_threshold': 2 * 1024,  # 2KB
            'ultra_fast_threshold': 500,  # 500 characters
            'clustering_skip_threshold': 300,  # 300 characters
            'max_citations_for_skip_clustering': 3
        }
    
    async def process_citation_task(self, task_id: str, input_type: str, input_data: Dict) -> Dict[str, Any]:
        """Process a citation task with the given input type and data."""
        logger.info(f"[DEBUG] ENTERED process_citation_task for task_id={task_id}, input_type={input_type}, input_data_keys={list(input_data.keys())}")
        start_time = time.time()
        logger.info(f"Processing citation task {task_id} of type {input_type}")
        
        try:
            if input_type == 'file':
                logger.info(f"[DEBUG] Calling _process_file_task for task_id={task_id}")
                result = await self._process_file_task(task_id, input_data)
                logger.info(f"[DEBUG] Returned from _process_file_task for task_id={task_id}, result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                return result
            elif input_type == 'url':
                logger.info(f"[DEBUG] Calling _process_url_task for task_id={task_id}")
                return await self._process_url_task(task_id, input_data)
            elif input_type == 'text':
                logger.info(f"[DEBUG] Calling _process_text_task for task_id={task_id}")
                return await self._process_text_task(task_id, input_data)
            else:
                logger.info(f"[DEBUG] Unknown input type: {input_type} for task_id={task_id}")
                return {
                    'status': 'failed',
                    'error': f'Unknown input type: {input_type}',
                    'task_id': task_id
                }
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e),
                'task_id': task_id,
                'processing_time': time.time() - start_time
            }
    
    async def _process_file_task(self, task_id: str, input_data: Dict) -> Dict[str, Any]:
        """
        Process a file-based citation task with enhanced error handling and logging.
        
        Args:
            task_id: Unique identifier for the processing task
            input_data: Dictionary containing file processing parameters
                - file_path: Path to the file to process
                - filename: Original filename (for reference)
                - options: Additional processing options
                
        Returns:
            Dict containing processing results with the following keys:
                - status: 'completed', 'failed', or 'error'
                - task_id: The task ID
                - filename: Original filename
                - citations: List of extracted citations
                - clusters: List of citation clusters
                - error: Error message if processing failed
                - processing_time: Total processing time in seconds
        """
        start_time = time.time()
        file_path = input_data.get('file_path')
        filename = input_data.get('filename', 'unknown')
        
        logger.info(f"[TASK:{task_id}] Starting file processing for {filename} (path: {file_path})")
        logger.debug(f"[TASK:{task_id}] Input data keys: {list(input_data.keys())}")
        
        # Validate input
        if not file_path:
            error_msg = "No file path provided in input data"
            logger.error(f"[TASK:{task_id}] {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'task_id': task_id,
                'processing_time': time.time() - start_time
            }
            
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(f"[TASK:{task_id}] {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'task_id': task_id,
                'processing_time': time.time() - start_time
            }
        
        try:
            # Prepare processing options
            options = input_data.get('options', {})
            logger.debug(f"[TASK:{task_id}] Processing options: {options}")
            
            # Process the document
            logger.info(f"[TASK:{task_id}] Starting document processing")
            result = await self.processor.process_document(file_path, options=options)
            
            # Validate processing result
            if not isinstance(result, dict):
                error_msg = f"Unexpected result type from processor: {type(result).__name__}"
                logger.error(f"[TASK:{task_id}] {error_msg}")
                raise ValueError(error_msg)
                
            if result.get('status') == 'error':
                error_msg = result.get('error', 'Unknown processing error')
                logger.error(f"[TASK:{task_id}] Processing error: {error_msg}")
                return {
                    'status': 'failed',
                    'error': error_msg,
                    'task_id': task_id,
                    'processing_time': time.time() - start_time
                }
            
            # Ensure required fields are present
            result.setdefault('citations', [])
            result.setdefault('clusters', [])
            
            # Add metadata
            result.update({
                'task_id': task_id,
                'filename': filename,
                'status': 'completed',
                'processing_time': time.time() - start_time
            })
            
            # Log success
            logger.info(
                f"[TASK:{task_id}] Successfully processed file: "
                f"{len(result['citations'])} citations, {len(result['clusters'])} clusters "
                f"in {result['processing_time']:.2f}s"
            )
            
            return result
            
        except asyncio.CancelledError:
            logger.warning(f"[TASK:{task_id}] Processing was cancelled")
            raise
            
        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            logger.error(f"[TASK:{task_id}] {error_msg}", exc_info=True)
            return {
                'status': 'error',
                'error': error_msg,
                'task_id': task_id,
                'processing_time': time.time() - start_time
            }
            
        finally:
            # Always clean up the temporary file
            self._cleanup_temp_file(file_path, task_id)
    
    def _cleanup_temp_file(self, file_path: str, task_id: str) -> None:
        """Safely remove a temporary file with error handling and logging."""
        if not file_path or not os.path.exists(file_path):
            return
            
        try:
            os.remove(file_path)
            logger.debug(f"[TASK:{task_id}] Removed temporary file: {file_path}")
        except PermissionError as e:
            logger.warning(f"[TASK:{task_id}] Permission denied when removing {file_path}: {e}")
        except OSError as e:
            logger.warning(f"[TASK:{task_id}] Error removing {file_path}: {e}")
    
    async def _process_url_task(self, task_id: str, input_data: Dict) -> Dict[str, Any]:
        """Process URL input task with timeout protection."""
        url = input_data.get('url')
        start_time = time.time()
        
        if not url:
            return {
                'status': 'failed',
                'error': 'No URL provided',
                'task_id': task_id
            }
        
        try:
            # Use UnifiedInputProcessor for URL processing with timeout protection
            from src.unified_input_processor import UnifiedInputProcessor
            processor = UnifiedInputProcessor()
            
            # Process URL with timeout protection
            import asyncio
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: processor.process_any_input(
                        input_data=input_data,  # Fixed: pass full input_data, not just url
                        input_type='url',
                        request_id=task_id,
                        source_name='url_task'
                    )
                ),
                timeout=300  # 5 minute timeout
            )
            
            # Convert to expected format
            if not result or not result.get('success'):
                error_msg = result.get('error', 'URL processing failed') if result else 'No result returned from processor'
                logger.error(f"URL processing failed for {url}: {error_msg}")
                return {
                    'status': 'failed',
                    'error': error_msg,
                    'task_id': task_id,
                    'processing_time': time.time() - start_time
                }
            
            # Successful processing
            return {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'clusters': result.get('clusters', []),
                'statistics': result.get('statistics', {}),
                'metadata': {
                    'url': url,
                    'text_length': result.get('text_length', 0),
                    **result.get('metadata', {})
                },
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            # Log error and re-raise
            logger.error(f"Error in _process_url_task: {str(e)}", exc_info=True)
            raise
    
    async def _process_text_task(self, task_id: str, input_data: Dict) -> Dict[str, Any]:
        """Process text input task."""
        text = input_data.get('text', '')
        source_name = input_data.get('source_name', 'pasted_text')
        
        if not text:
            return {
                'status': 'failed',
                'error': 'No text provided',
                'task_id': task_id
            }

        try:
            # Process citations from text using async/await
            logger.info(f"[TEXT_PROCESSING] Starting text processing for task {task_id}")
            result = await self.process_citations_from_text(text)
            
            if not result or 'citations' not in result:
                logger.error(f"[TEXT_PROCESSING] No citations found in result for task {task_id}")
                raise ValueError("No citations found in processing result")
                
            logger.info(f"[TEXT_PROCESSING] Processed {len(result.get('citations', []))} citations for task {task_id}")

            return {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'clusters': result.get('clusters', []),
                'statistics': result.get('statistics', {}),
                'metadata': {
                    'source_name': source_name,
                    'text_length': len(text)
                },
                'processing_time': time.time() - time.time()  # Will be set by caller
            }

        except Exception as e:
            logger.error(f"[TEXT_PROCESSING] Error processing text for task {task_id}: {str(e)}", exc_info=True)
            raise
    
    async def process_citations_from_text(self, text: str) -> Dict[str, Any]:
        """
        Process text to extract and analyze citations with optimized performance.
        
        Args:
            text: The input text to process for citations
            
        Returns:
            Dict containing:
                - citations: List of extracted and processed citations
                - clusters: List of citation clusters
                - processing_time: Total processing time in seconds
                - status: Processing status ('completed' or 'error')
                - error: Error message if processing failed
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        def log(level: str, message: str) -> None:
            """Helper function for consistent logging with request ID."""
            getattr(logger, level)(f"[REQ:{request_id}] {message}")
        
        log('info', f"Starting citation processing for text (length: {len(text)})")
        
        # Initialize result dict with default values
        result = {
            'citations': [],
            'clusters': [],
            'status': 'completed',
            'processing_time': 0.0
        }
        
        try:
            # Import required modules
            log('debug', 'Importing required modules')
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            from src.services.citation_clusterer import CitationClusterer
            
            # Initialize processor with optimized settings
            log('debug', 'Initializing processor')
            processor = UnifiedCitationProcessorV2()
            
            # Process text with timeout protection
            log('debug', 'Starting text processing')
            process_start = time.time()
            process_result = await processor.process_text(text)
            process_time = time.time() - process_start
            
            # Validate and normalize result
            if not isinstance(process_result, dict):
                raise ValueError(f"Expected dict from process_text, got {type(process_result).__name__}")
                
            # Get citations and ensure it's a list
            citations = process_result.get('citations', [])
            if not isinstance(citations, list):
                raise ValueError(f"Expected citations to be a list, got {type(citations).__name__}")
                
            log('info', f"Extracted {len(citations)} citations in {process_time:.2f}s")
            
            # Run clustering if needed
            clusters = process_result.get('clusters', [])
            if not clusters and citations:
                log('debug', 'No clusters found, running clustering')
                cluster_start = time.time()
                clusterer = CitationClusterer()
                clusters = clusterer.cluster_citations(citations)
                log('debug', f"Clustered {len(citations)} citations into {len(clusters)} clusters in {time.time() - cluster_start:.2f}s")
            
            # Convert citations to serializable format
            converted_citations = self._convert_citations_to_dicts(citations, request_id)
            
            # Prepare final result
            result.update({
                'citations': converted_citations,
                'clusters': clusters,
                'processing_time': time.time() - start_time,
                'metadata': {
                    'request_id': request_id,
                    'text_length': len(text),
                    'citation_count': len(converted_citations),
                    'cluster_count': len(clusters)
                }
            })
            
            log('info', 
                f"Processed text: {len(converted_citations)} citations, "
                f"{len(clusters)} clusters in {result['processing_time']:.2f}s"
            )
            
            return result
            
        except asyncio.CancelledError:
            log('warning', 'Processing was cancelled')
            raise
            
        except Exception as e:
            error_msg = f"Error processing citations: {str(e)}"
            log('error', error_msg)
            
            result.update({
                'status': 'error',
                'error': error_msg,
                'processing_time': time.time() - start_time
            })
            return result
    
    def _convert_citations_to_dicts(self, citations: List[Any], request_id: str) -> List[Dict[str, Any]]:
        """Convert CitationResult objects to serializable dictionaries."""
        if not citations:
            return []
            
        converted = []
        
        for citation in citations:
            try:
                if not hasattr(citation, 'citation'):
                    converted.append(citation)  # Already a dict
                    continue
                    
                # Create base citation dict
                citation_dict = {
                    'citation': citation.citation,
                    'case_name': citation.extracted_case_name or citation.case_name,
                    'extracted_case_name': citation.extracted_case_name,
                    'canonical_name': citation.canonical_name,
                    'extracted_date': citation.extracted_date,
                    'canonical_date': citation.canonical_date,
                    'verified': self._get_verified_status(citation),
                    'court': citation.court,
                    'confidence': citation.confidence,
                    'method': citation.method,
                    'pattern': getattr(citation, 'pattern', None),
                    'context': getattr(citation, 'context', ''),
                    'start_index': getattr(citation, 'start_index', 0),
                    'end_index': getattr(citation, 'end_index', 0),
                    'is_parallel': getattr(citation, 'is_parallel', False),
                    'is_cluster': getattr(citation, 'is_cluster', False),
                    'parallel_citations': getattr(citation, 'parallel_citations', []),
                    'pinpoint_pages': getattr(citation, 'pinpoint_pages', []),
                    'docket_numbers': getattr(citation, 'docket_numbers', []),
                    'case_history': getattr(citation, 'case_history', []),
                    'publication_status': getattr(citation, 'publication_status', None),
                    'url': getattr(citation, 'url', None),
                    'source': getattr(citation, 'source', None),
                    'error': getattr(citation, 'error', None),
                    'metadata': {},
                    'extraction_method': getattr(citation, 'extraction_method', None)
                }
                
                # Add metadata if available
                if hasattr(citation, 'metadata') and citation.metadata:
                    citation_dict['metadata'].update({
                        'cluster_extracted_case_name': citation.metadata.get('cluster_extracted_case_name'),
                        'cluster_extracted_date': citation.metadata.get('cluster_extracted_date'),
                        'cluster_canonical_name': citation.metadata.get('cluster_canonical_name'),
                        'cluster_canonical_date': citation.metadata.get('cluster_canonical_date'),
                        'cluster_url': citation.metadata.get('cluster_url'),
                        'is_in_cluster': citation.metadata.get('is_in_cluster', False),
                        'cluster_id': citation.metadata.get('cluster_id'),
                        'cluster_size': citation.metadata.get('cluster_size', 0),
                        'cluster_members': citation.metadata.get('cluster_members', [])
                    })
                    
                    # Copy any additional metadata
                    for key, value in citation.metadata.items():
                        if key not in citation_dict['metadata']:
                            citation_dict['metadata'][key] = value
                
                converted.append(citation_dict)
                
            except Exception as e:
                logger.error(
                    f"[REQ:{request_id}] Error converting citation to dict: {str(e)}",
                    exc_info=True
                )
                # Include as much info as possible even if conversion failed
                converted.append({
                    'citation': str(citation),
                    'error': f'Error converting citation: {str(e)}',
                    'raw': str(vars(citation) if hasattr(citation, '__dict__') else citation)
                })
        
        return converted
    
    def _get_verified_status(self, citation) -> bool:
        """Determine the verified status of a citation."""
        verified = getattr(citation, 'verified', False)
        if isinstance(verified, bool):
            return verified
        return verified in ("true_by_parallel", True)
            
            # This block intentionally left blank - duplicate code removed

    async def process_citations_from_url(self, url: str) -> Dict[str, Any]:
        """
        Process URL to extract and analyze citations.
        
        Args:
            url: The URL to process for citations
            
        Returns:
            Dict containing citations, clusters, and processing metadata
        """
        start_time = time.time()
        logger.info(f"[Request {uuid.uuid4()}] Starting URL processing: {url}")
        
        try:
            # Create a task-like input data structure
            input_data = {'url': url}
            task_id = str(uuid.uuid4())
            
            # Use the existing URL processing logic
            result = await self._process_url_task(task_id, input_data)
            
            # Add processing time
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            return result
            
        except Exception as e:
            logger.error(f"[Request {uuid.uuid4()}] Error processing URL: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'citations': [],
                'clusters': [],
                'processing_time': time.time() - start_time
            } 