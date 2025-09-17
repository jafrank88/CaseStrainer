"""
Extracted citation processing business logic from the main API file.
This separates concerns and makes the code more testable and maintainable.
"""

import asyncio
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

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
            return len(text) < 2 * 1024  # Changed from 10KB to 2KB
        elif input_type == 'file':
            # which can take a long time and should never be done synchronously
            return False
        elif input_type == 'url':
            # URLs should use async processing for large documents
            return False
        
        return False
    
    def process_immediately(self, input_data: Dict) -> Dict[str, Any]:
        """Process input immediately using the enhanced sync processor."""
        try:
            from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
            from src.config import get_citation_config, get_config_value
            
            # Get configuration
            config = get_citation_config()
            
            # Get API key from environment
            courtlistener_api_key = get_config_value('COURTLISTENER_API_KEY')
            if courtlistener_api_key:
                logger.info(f"[CitationService] Using CourtListener API key: {courtlistener_api_key[:8]}...{courtlistener_api_key[-8:]}")
            else:
                logger.warning("[CitationService] CourtListener API key not found in environment")
            
            # Configure processor with defaults from config
            processor_options = ProcessingOptions(
                enable_local_processing=True,
                enable_async_verification=True,  # Re-enabled for proper async processing
                enhanced_sync_threshold=15 * 1024,  # 15KB for enhanced sync
                ultra_fast_threshold=500,
                clustering_threshold=300,
                enable_enhanced_verification=config.get('enable_verification', True),
                enable_cross_validation=True,
                enable_false_positive_prevention=True,
                enable_confidence_scoring=config.get('verification_options', {}).get('enable_confidence_scoring', True),
                min_confidence_threshold=config.get('verification_options', {}).get('min_confidence_threshold', 0.7),
                courtlistener_api_key=courtlistener_api_key
            )
            
            logger.info(f"[CitationService] Processing with verification: {processor_options.enable_enhanced_verification}")
            if processor_options.enable_enhanced_verification:
                logger.info("[CitationService] Citation verification is ENABLED")
            else:
                logger.warning("[CitationService] Citation verification is DISABLED - only basic extraction will be performed")
            
            processor = EnhancedSyncProcessor(processor_options)
            text_content = input_data.get('text', '')
            result = processor.process_any_input_enhanced(text_content, input_data.get('type', 'text'), {})
            
            result['processing_mode'] = 'immediate'
            
            if 'progress_data' not in result:
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
            
            logger.info(f"[CitationService] Immediate processing completed via EnhancedSyncProcessor in {result.get('processing_time', 0):.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"[CitationService] Error in immediate processing: {str(e)}", exc_info=True)
            return self._fallback_immediate_processing(input_data)
    
    def _fallback_immediate_processing(self, input_data: Dict) -> Dict[str, Any]:
        """Fallback processing when UnifiedSyncProcessor fails."""
        start_time = time.time()
        
        try:
            if input_data.get('type') == 'text':
                text = input_data.get('text', '')
                
                from src.citation_extractor import CitationExtractor
                extractor = CitationExtractor()
                citations = extractor.extract_citations(text)
                
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
            import re
            from src.citation_extractor import CitationExtractor
            
            extractor = CitationExtractor()
            citations = extractor.extract_citations(text)  # Use existing method
            
            logger.info(f"[CitationService] Fast extraction found {len(citations)} citations")
            return citations
            
        except Exception as e:
            logger.warning(f"[CitationService] Fast extraction failed, falling back to unified extraction: {e}")
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
            options = input_data.get('options', {})
            
            logger.info(f"[TASK:{task_id}] Starting document processing")
            result = await self.processor.process_document(file_path, options=options)
            
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
            
            result.setdefault('citations', [])
            result.setdefault('clusters', [])
            
            result.update({
                'task_id': task_id,
                'filename': filename,
                'status': 'completed',
                'processing_time': time.time() - start_time
            })
            
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
            self._cleanup_temp_file(file_path, task_id)
    
    def _cleanup_temp_file(self, file_path: str, task_id: str) -> None:
        """Safely remove a temporary file with error handling and logging."""
        if not file_path or not os.path.exists(file_path):
            return
            
        try:
            os.remove(file_path)
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
            from src.unified_input_processor import UnifiedInputProcessor
            processor = UnifiedInputProcessor()
            
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
            
            if not result or not result.get('success'):
                error_msg = result.get('error', 'URL processing failed') if result else 'No result returned from processor'
                logger.error(f"URL processing failed for {url}: {error_msg}")
                return {
                    'status': 'failed',
                    'error': error_msg,
                    'task_id': task_id,
                    'processing_time': time.time() - start_time
                }
            
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
        
        has_progress_tracking = False
        
        try:
            if input_data.get('type') == 'text':
                text = input_data.get('text', '')
                
                cache_key = f"text_{hash(text)}"
                if hasattr(self, '_cache') and cache_key in self._cache:
                    cached_result = self._cache[cache_key]
                    if time.time() - cached_result.get('cache_time', 0) < self.cache_ttl:
                        logger.info(f"[CitationService] Cache hit for text pattern, returning cached result in {time.time() - start_time:.3f}s")
                        return cached_result['result']
                
                logger.info(f"[CitationService] Processing text immediately with EnhancedSyncProcessor: {text[:100]}...")
                
                from src.enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
                courtlistener_api_key = os.getenv('COURTLISTENER_API_KEY')
                processor_options = ProcessingOptions(
                    enable_local_processing=True,
                    enable_async_verification=True,
                    enhanced_sync_threshold=15 * 1024,
                    ultra_fast_threshold=500,
                    clustering_threshold=300,
                    enable_enhanced_verification=True,
                    enable_cross_validation=True,
                    enable_false_positive_prevention=True,
                    enable_confidence_scoring=True,
                    courtlistener_api_key=courtlistener_api_key
                )
                enhanced_processor = EnhancedSyncProcessor(processor_options)
                enhanced_result = enhanced_processor.process_any_input_enhanced(text, 'text', {'wait_for_verification': True})
                
                citations_list = enhanced_result.get('citations', [])
                clusters_list = enhanced_result.get('clusters', [])
                processing_time = enhanced_result.get('processing_time', time.time() - start_time)
                logger.info(f"[CitationService] Enhanced path: {len(citations_list)} citations, {len(clusters_list)} clusters in {processing_time:.3f}s")
                
                result = {
                    'citations': citations_list,
                    'clusters': clusters_list,
                    'status': 'completed',
                    'message': f"Found {len(citations_list)} citations in {len(clusters_list)} clusters",
                    'processing_time': processing_time,
                    'processing_mode': 'immediate',
                    'text_length': len(text)
                }
                
                if not hasattr(self, '_cache'):
                    self._cache = {}
                self._cache[cache_key] = {
                    'result': result,
                    'cache_time': time.time()
                }
                
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
    def _get_verified_status(self, citation) -> bool:
        """Determine the verified status of a citation."""
        verified = getattr(citation, 'verified', False)
        if isinstance(verified, bool):
            return verified
        return verified in ("true_by_parallel", True)
    
    def _get_verification_status(self, citation) -> str:
        """Determine the verification status of a citation."""
        if getattr(citation, 'verified', False):
            return 'verified'
        
        if getattr(citation, 'true_by_parallel', False):
            return 'true_by_parallel'
        
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
            citation_lookup = {getattr(c, 'citation', str(c)): c for c in citations}
            logger.info(f"[VERIFICATION] Created citation lookup with {len(citation_lookup)} citations")
            
            for i, cluster in enumerate(clusters):
                logger.info(f"[VERIFICATION] Processing cluster {i+1}: {cluster}")
                
                if not isinstance(cluster, dict):
                    logger.warning(f"[VERIFICATION] Cluster {i+1} is not a dict: {type(cluster)}")
                    continue
                
                cluster_citations = cluster.get('citations', [])
                citation_objects = cluster.get('citation_objects', [])
                
                if not cluster_citations and not citation_objects:
                    logger.warning(f"[VERIFICATION] Cluster {i+1} has no citations or citation_objects")
                    continue
                
                if citation_objects:
                    logger.info(f"[VERIFICATION] Cluster {i+1} using citation_objects: {len(citation_objects)} objects")
                    
                    any_verified = False
                    verified_citation = None
                    
                    for citation_obj in citation_objects:
                        if getattr(citation_obj, 'verified', False):
                            any_verified = True
                            verified_citation = citation_obj
                            logger.info(f"[VERIFICATION] Found verified citation in cluster {i+1}: {getattr(citation_obj, 'citation', 'unknown')}")
                            break
                    
                    if any_verified and verified_citation:
                        for citation_obj in citation_objects:
                            if not getattr(citation_obj, 'verified', False):
                                citation_obj.true_by_parallel = True
                                
                                if not hasattr(citation_obj, 'metadata'):
                                    citation_obj.metadata = {}
                                citation_obj.metadata['true_by_parallel'] = True
                                
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
                    logger.info(f"[VERIFICATION] Cluster {i+1} using citations list: {cluster_citations}")
                    
                    if len(cluster_citations) < 2:
                        continue
                    
                    any_verified = False
                    verified_citation = None
                    
                    for citation_text in cluster_citations:
                        citation_obj = citation_lookup.get(citation_text)
                        if citation_obj and getattr(citation_obj, 'verified', False):
                            any_verified = True
                            verified_citation = citation_obj
                            break
                    
                    if any_verified and verified_citation:
                        for citation_text in cluster_citations:
                            citation_obj = citation_lookup.get(citation_text)
                            if citation_obj and not getattr(citation_obj, 'verified', False):
                                citation_obj.true_by_parallel = True
                                
                                if not hasattr(citation_obj, 'metadata'):
                                    citation_obj.metadata = {}
                                citation_obj.metadata['true_by_parallel'] = True
                                
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
            input_data = {'url': url}
            task_id = str(uuid.uuid4())
            
            result = await self._process_url_task(task_id, input_data)
            
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