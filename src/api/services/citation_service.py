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
        """Process input immediately using the unified sync processor."""
        try:
            # Use the new UnifiedSyncProcessor for all immediate processing
            from src.unified_sync_processor import UnifiedSyncProcessor
            
            processor = UnifiedSyncProcessor()
            result = processor.process_text_unified(input_data.get('text', ''), {})
            
            # Update processing mode to maintain backward compatibility
            result['processing_mode'] = 'immediate'
            
            # Ensure progress_data is included in the result
            if 'progress_data' not in result:
                # Add default progress data if not present
                result['progress_data'] = {
                    'current_step': 100,
                    'total_steps': 5,
                    'current_message': 'Processing completed successfully',
                    'start_time': time.time(),
                    'steps': [
                        {'name': 'Initializing...', 'progress': 100, 'status': 'completed', 'message': 'Started immediate processing'},
                        {'name': 'Extract', 'progress': 100, 'status': 'completed', 'message': 'Citations extracted successfully'},
                        {'name': 'Analyze', 'progress': 100, 'status': 'completed', 'message': 'Citations analyzed and normalized'},
                        {'name': 'Extract Names', 'progress': 100, 'status': 'completed', 'message': 'Case names and years extracted'},
                        {'name': 'Cluster', 'progress': 100, 'status': 'completed', 'message': 'Citations clustered successfully'},
                        {'name': 'Verify', 'progress': 100, 'status': 'completed', 'message': 'Verification completed'}
                    ]
                }
            
            logger.info(f"[CitationService] Immediate processing completed via UnifiedSyncProcessor in {result.get('processing_time', 0):.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"[CitationService] Error in immediate processing: {str(e)}", exc_info=True)
            # Fall back to basic processing if UnifiedSyncProcessor fails
            return self._fallback_immediate_processing(input_data)
    
    def _fallback_immediate_processing(self, input_data: Dict) -> Dict[str, Any]:
        """Fallback processing when UnifiedSyncProcessor fails."""
        start_time = time.time()
        
        try:
            if input_data.get('type') == 'text':
                text = input_data.get('text', '')
                
                # Basic citation extraction as fallback
                from src.citation_extractor import CitationExtractor
                extractor = CitationExtractor()
                citations = extractor.extract_citations(text)
                
                # Convert to basic format
                citations_list = []
                for citation in citations:
                    citation_dict = {
                        'citation': str(citation),
                        'extracted_case_name': None,
                        'extracted_date': None,
                        'verified': False,
                        'method': 'fallback'
                    }
                    citations_list.append(citation_dict)
                
                processing_time = time.time() - start_time
                logger.warning(f"[CitationService] Fallback processing completed in {processing_time:.3f}s")
                
                return {
                    'citations': citations_list,
                    'clusters': [],
                    'status': 'completed',
                    'message': f"Fallback processing found {len(citations_list)} citations",
                    'processing_time': processing_time,
                    'processing_mode': 'immediate_fallback',
                    'text_length': len(text)
                }
            
            return {'status': 'error', 'message': 'Invalid input type for immediate processing'}
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error in fallback processing: {str(e)}"
            logger.error(f"[CitationService] {error_msg}", exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'processing_time': processing_time,
                'processing_mode': 'immediate_fallback_error'
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
            logger.warning(f"[CitationService] Fast extraction failed, falling back to unified extraction: {e}")
            # Fall back to unified extraction (non-deprecated)
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            processor = UnifiedCitationProcessorV2()
            return processor._extract_citations_unified(text)
    
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
            result = await self.process_citations_from_text(input_data)
            
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
    
    async def process_citations_from_text(self, input_data):
        """
        Process citations from text input with progress tracking.
        
        Args:
            input_data (dict): Input data containing text and type
            
        Returns:
            dict: Processing results with citations and clusters
        """
        start_time = time.time()
        logger.info(f"[CitationService] Starting citation processing for text input")
        
        # Initialize progress tracking
        try:
            from src.vue_api_endpoints import update_sync_progress, complete_sync_progress
            has_progress_tracking = True
        except ImportError:
            has_progress_tracking = False
            logger.warning("[CitationService] Progress tracking not available")
        
        if has_progress_tracking:
            update_sync_progress('extracting_citations', 10, 'Extracting citations from text...')
        
        try:
            if input_data.get('type') == 'text':
                text = input_data.get('text', '')
                
                # PERFORMANCE OPTIMIZATION: Check cache first for repeated text patterns
                cache_key = f"text_{hash(text)}"
                if hasattr(self, '_cache') and cache_key in self._cache:
                    cached_result = self._cache[cache_key]
                    if time.time() - cached_result.get('cache_time', 0) < self.cache_ttl:
                        logger.info(f"[CitationService] Cache hit for text pattern, returning cached result in {time.time() - start_time:.3f}s")
                        if has_progress_tracking:
                            complete_sync_progress()
                        return cached_result['result']
                
                logger.info(f"[CitationService] Processing text immediately: {text[:100]}...")
                
                if has_progress_tracking:
                    update_sync_progress('extracting_citations', 25, f'Processing {len(text)} characters...')
                
                # PERFORMANCE OPTIMIZATION: Use faster processing for short text
                if len(text) < 500:  # Very short text - use ultra-fast path
                    logger.info(f"[CitationService] Using ultra-fast path for {len(text)} characters")
                    citations = self._extract_citations_fast(text)
                else:
                    # Standard processing for medium text
                    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                    processor = UnifiedCitationProcessorV2()
                    citations = processor._extract_citations_unified(text)
                
                # Citations are already CitationResult objects from extract_with_regex
                citation_results = citations
                
                if has_progress_tracking:
                    update_sync_progress('verifying_citations', 50, f'Found {len(citations)} citations, starting verification...')
                
                # PERFORMANCE OPTIMIZATION: Skip clustering for very short text with few citations
                # BUT always cluster Washington citations for proper parallel detection
                clusters = []  # Initialize clusters
                has_washington_citations = any('Wn.' in str(c) for c in citation_results)
                
                if len(text) < 300 and len(citations) <= 3 and not has_washington_citations:
                    logger.info(f"[CitationService] Skipping clustering for short text with few citations (no Washington citations)")
                    # clusters already initialized to empty list
                else:
                    # Apply clustering with verification
                    from src.unified_citation_clustering import cluster_citations_unified
                    
                    # PERFORMANCE OPTIMIZATION: Smart verification strategy
                    # For Washington citations, ALWAYS enable verification regardless of text length
                    enable_verification = len(text) > 500  # Default threshold
                    
                    # ENHANCED: Special handling for Washington citations to ensure proper clustering
                    if any('Wn.' in str(c) for c in citation_results):
                        logger.info(f"[CitationService] Washington citations detected - ALWAYS enabling verification and clustering")
                        # Force verification and clustering for Washington citations regardless of text length
                        enable_verification = True
                        logger.info(f"[CitationService] Washington citations: verification={enable_verification}, clustering=enabled")
                    
                                    # Only do clustering if we haven't already set clusters
                if not clusters:
                    clustering_result = cluster_citations_unified(
                        citation_results, 
                        text, 
                        enable_verification=enable_verification
                    )
                    
                    # Handle clustering result (can be list or dict)
                    if isinstance(clustering_result, dict):
                        clusters = clustering_result.get('clusters', [])
                    else:
                        # clustering_result is a list of clusters
                        clusters = clustering_result if isinstance(clustering_result, list) else []
                
                # POST-CLUSTERING: Propagate verification status to parallel citations
                if clusters and citation_results:
                    logger.info(f"[CitationService] Propagating verification to {len(clusters)} clusters with {len(citation_results)} citations")
                    self._propagate_verification_to_parallels(citation_results, clusters)
                    logger.info(f"[CitationService] Verification propagation completed")
                
                if has_progress_tracking:
                    update_sync_progress('finalizing_results', 90, 'Finalizing results...')
                
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
                            'verification_status': self._get_verification_status(citation),
                            'true_by_parallel': getattr(citation, 'true_by_parallel', False),
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
                
                if has_progress_tracking:
                    complete_sync_progress()
                
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
                    'verification_status': self._get_verification_status(citation),
                    'true_by_parallel': getattr(citation, 'true_by_parallel', False),
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
    
    def _get_verification_status(self, citation) -> str:
        """Determine the verification status of a citation."""
        # Check if verified is true (direct verification)
        if getattr(citation, 'verified', False):
            return 'verified'
        
        # Check if true_by_parallel is true
        if getattr(citation, 'true_by_parallel', False):
            return 'true_by_parallel'
        
        # Check if metadata contains true_by_parallel flag
        if hasattr(citation, 'metadata') and citation.metadata:
            if citation.metadata.get('true_by_parallel', False):
                return 'true_by_parallel'
        
        return 'unverified'
    
    def _propagate_verification_to_parallels(self, citations: List[Any], clusters: List[Dict[str, Any]]) -> None:
        """
        Post-clustering step: Propagate verification status to parallel citations.
        This ensures that unverified citations in verified clusters are marked as true_by_parallel.
        """
        try:
            # Create a lookup for citations by citation text
            citation_lookup = {getattr(c, 'citation', str(c)): c for c in citations}
            logger.info(f"[VERIFICATION] Created citation lookup with {len(citation_lookup)} citations")
            
            # Process each cluster
            for i, cluster in enumerate(clusters):
                logger.info(f"[VERIFICATION] Processing cluster {i+1}: {cluster}")
                
                if not isinstance(cluster, dict):
                    logger.warning(f"[VERIFICATION] Cluster {i+1} is not a dict: {type(cluster)}")
                    continue
                
                # Handle both cluster formats: 'citations' list or 'citation_objects' list
                cluster_citations = cluster.get('citations', [])
                citation_objects = cluster.get('citation_objects', [])
                
                if not cluster_citations and not citation_objects:
                    logger.warning(f"[VERIFICATION] Cluster {i+1} has no citations or citation_objects")
                    continue
                
                # Use citation_objects if available, otherwise fall back to citations list
                if citation_objects:
                    # Direct access to citation objects
                    logger.info(f"[VERIFICATION] Cluster {i+1} using citation_objects: {len(citation_objects)} objects")
                    
                    # Check if any citation in the cluster is verified
                    any_verified = False
                    verified_citation = None
                    
                    for citation_obj in citation_objects:
                        if getattr(citation_obj, 'verified', False):
                            any_verified = True
                            verified_citation = citation_obj
                            logger.info(f"[VERIFICATION] Found verified citation in cluster {i+1}: {getattr(citation_obj, 'citation', 'unknown')}")
                            break
                    
                    # If cluster has verified citations, propagate to unverified ones
                    if any_verified and verified_citation:
                        for citation_obj in citation_objects:
                            if not getattr(citation_obj, 'verified', False):
                                # Mark as true_by_parallel
                                citation_obj.true_by_parallel = True
                                
                                # Ensure metadata exists
                                if not hasattr(citation_obj, 'metadata'):
                                    citation_obj.metadata = {}
                                citation_obj.metadata['true_by_parallel'] = True
                                
                                # Propagate canonical information from verified citation
                                if hasattr(verified_citation, 'canonical_name') and verified_citation.canonical_name:
                                    citation_obj.canonical_name = verified_citation.canonical_name
                                if hasattr(verified_citation, 'canonical_date') and verified_citation.canonical_date:
                                    citation_obj.canonical_date = verified_citation.canonical_date
                                if hasattr(verified_citation, 'canonical_url') and verified_citation.canonical_url:
                                    citation_obj.canonical_url = verified_citation.canonical_url
                                elif hasattr(verified_citation, 'url') and verified_citation.url:
                                    citation_obj.url = verified_citation.url
                                if hasattr(verified_citation, 'source') and verified_citation.source:
                                    citation_obj.source = verified_citation.source
                                
                                logger.info(f"[VERIFICATION] Marked citation as true_by_parallel: {getattr(citation_obj, 'citation', 'unknown')}")
                else:
                    # Fallback: use citations list and lookup
                    logger.info(f"[VERIFICATION] Cluster {i+1} using citations list: {cluster_citations}")
                    
                    if len(cluster_citations) < 2:
                        continue
                    
                    # Check if any citation in the cluster is verified
                    any_verified = False
                    verified_citation = None
                    
                    for citation_text in cluster_citations:
                        citation_obj = citation_lookup.get(citation_text)
                        if citation_obj and getattr(citation_obj, 'verified', False):
                            any_verified = True
                            verified_citation = citation_obj
                            break
                    
                    # If cluster has verified citations, propagate to unverified ones
                    if any_verified and verified_citation:
                        for citation_text in cluster_citations:
                            citation_obj = citation_lookup.get(citation_text)
                            if citation_obj and not getattr(citation_obj, 'verified', False):
                                # Mark as true_by_parallel
                                citation_obj.true_by_parallel = True
                                
                                # Ensure metadata exists
                                if not hasattr(citation_obj, 'metadata'):
                                    citation_obj.metadata = {}
                                citation_obj.metadata['true_by_parallel'] = True
                                
                                # Propagate canonical information from verified citation
                                if hasattr(verified_citation, 'canonical_name') and verified_citation.canonical_name:
                                    citation_obj.canonical_name = verified_citation.canonical_name
                                if hasattr(verified_citation, 'canonical_date') and verified_citation.canonical_date:
                                    citation_obj.canonical_date = verified_citation.canonical_date
                                if hasattr(verified_citation, 'canonical_url') and verified_citation.canonical_url:
                                    citation_obj.canonical_url = verified_citation.canonical_url
                                elif hasattr(verified_citation, 'url') and verified_citation.url:
                                    citation_obj.url = verified_citation.url
                                if hasattr(verified_citation, 'source') and verified_citation.source:
                                    citation_obj.source = verified_citation.source
                                
                                logger.info(f"[VERIFICATION] Marked citation as true_by_parallel: {citation_text}")
            
            logger.info(f"[VERIFICATION] Completed verification propagation for {len(clusters)} clusters")
            
        except Exception as e:
            logger.error(f"[VERIFICATION] Error in verification propagation: {e}", exc_info=True)

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