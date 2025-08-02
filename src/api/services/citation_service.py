"""
Extracted citation processing business logic from the main API file.
This separates concerns and makes the code more testable and maintainable.
"""

import os
import logging
import time
import uuid
from typing import Dict, List, Any, Optional
from src.redis_distributed_processor import DockerOptimizedProcessor

logger = logging.getLogger(__name__)


class CitationService:
    """Service for processing citations with Redis-distributed processing."""
    
    def __init__(self):
        self.processor = DockerOptimizedProcessor()
        self.cache_ttl = 3600  # 1 hour cache
    
    def should_process_immediately(self, input_data: Dict) -> bool:
        """Determine if input should be processed immediately vs queued."""
        if input_data.get('type') == 'text':
            text = input_data.get('text', '')
            # Process short texts immediately (< 10KB)
            return len(text) < 10 * 1024
        
        return False
    
    async def process_immediately(self, input_data: Dict) -> Dict[str, Any]:
        """Process input immediately (for short texts)."""
        try:
            if input_data.get('type') == 'text':
                text = input_data.get('text', '')
                return await self.process_citations_from_text(text)
            
            return {'status': 'error', 'message': 'Invalid input type for immediate processing'}
            
        except Exception as e:
            logger.error(f"Immediate processing failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
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
        """Process a file-based citation task."""
        start_time = time.time()
        logger.info(f"[DEBUG] ENTERED _process_file_task for task_id={task_id}, input_data_keys={list(input_data.keys())}")
        file_path = input_data.get('file_path')
        filename = input_data.get('filename', 'unknown')
        logger.info(f"[DEBUG] file_path={file_path}, filename={filename}")
        
        if not file_path or not os.path.exists(file_path):
            logger.error(f"[DEBUG] File not found: {file_path} for task_id={task_id}")
            return {
                'status': 'failed',
                'error': f'File not found: {file_path}',
                'task_id': task_id
            }
        
        try:
            logger.info(f"[DEBUG] Before calling process_document for file_path={file_path}")
            result = await self.processor.process_document(file_path)
            logger.info(f"[DEBUG] After process_document for file_path={file_path}, result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            
            if isinstance(result, dict) and result.get('status') == 'error':
                logger.error(f"[DEBUG] process_document returned error for task_id={task_id}: {result.get('error')}")
                return {
                    'status': 'failed',
                    'error': result.get('error', 'Unknown processing error'),
                    'task_id': task_id
                }
            
            # Add task metadata
            result['task_id'] = task_id
            result['filename'] = filename
            result['processing_time'] = time.time() - start_time
            
            logger.info(f"[DEBUG] Successfully processed file task {task_id}")
            return result
            
        except Exception as e:
            logger.error(f"[DEBUG] Exception in _process_file_task for task_id={task_id}: {e}", exc_info=True)
            return {
                'status': 'failed',
                'error': f'File processing failed: {str(e)}',
                'task_id': task_id,
                'processing_time': time.time() - start_time
            }
    
    async def _process_url_task(self, task_id: str, input_data: Dict) -> Dict[str, Any]:
        """Process URL input task."""
        url = input_data.get('url')
        
        if not url:
            return {
                'status': 'failed',
                'error': 'No URL provided',
                'task_id': task_id
            }
        
        try:
            # Download and process URL
            import tempfile
            import requests
            
            # Download file
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            # Process using distributed processor
            result = await self.processor.process_document(temp_file_path)
            
            # Clean up
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            return {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'statistics': result.get('statistics', {}),
                'metadata': {
                    'url': url,
                    'text_length': result.get('text_length', 0)
                },
                'processing_time': result.get('processing_time', 0)
            }
            
        except Exception as e:
            # Clean up on error
            try:
                os.remove(temp_file_path)
            except:
                pass
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
        Process text to extract and analyze citations.
        
        Args:
            text: The input text to process for citations
            
        Returns:
            Dict containing citation results and metadata
            
        Raises:
            Exception: If any error occurs during processing
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Input validation
            if text is None:
                error_msg = f"[Request {request_id}] Invalid input text. Text is None"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'error': 'Invalid input: text cannot be None',
                    'request_id': request_id
                }
            
            if not isinstance(text, str):
                error_msg = f"[Request {request_id}] Invalid input text. Expected string, got {type(text)}"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'error': 'Invalid input: text must be a string',
                    'request_id': request_id
                }
            
            if not text.strip():
                error_msg = f"[Request {request_id}] Invalid input text. Text is empty or whitespace only"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'error': 'Invalid input: text must not be empty',
                    'request_id': request_id
                }
            
            logger.info(f"[Request {request_id}] Starting citation processing for text (length: {len(text)})")
                
            logger.debug(f"[Request {request_id}] Importing required modules")
            try:
                from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                from src.citation_clustering import group_citations_into_clusters
                logger.debug(f"[Request {request_id}] Successfully imported required modules")
            except ImportError as ie:
                error_msg = f"[Request {request_id}] Failed to import required modules: {str(ie)}"
                logger.error(error_msg, exc_info=True)
                return {
                    'status': 'error',
                    'error': 'Service configuration error',
                    'details': str(ie) if os.getenv('FLASK_ENV') == 'development' else None,
                    'request_id': request_id
                }
            
            # Initialize processor
            try:
                logger.debug(f"[Request {request_id}] Initializing UnifiedCitationProcessorV2")
                processor = UnifiedCitationProcessorV2()
                logger.debug(f"[Request {request_id}] Successfully initialized processor")
            except Exception as e:
                error_msg = f"[Request {request_id}] Failed to initialize citation processor: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return {
                    'status': 'error',
                    'error': 'Failed to initialize citation processor',
                    'details': str(e) if os.getenv('FLASK_ENV') == 'development' else None,
                    'request_id': request_id
                }
            
            # Process text
            try:
                logger.debug(f"[Request {request_id}] Starting text processing")
                # Use the async process_document_citations method which performs real citation extraction
                citation_results = await processor.process_document_citations(text)
                logger.info(f"[Request {request_id}] Processed text, found {len(citation_results.get('citations', []))} citations")
                
                # Ensure we have a valid citations list
                if 'citations' not in citation_results:
                    citation_results['citations'] = []
                    
                # Process clusters
                try:
                    if 'clusters' not in citation_results or not citation_results['clusters']:
                        logger.debug(f"[Request {request_id}] No clusters found, running clustering")
                        citation_results['clusters'] = group_citations_into_clusters(
                            citation_results['citations'], 
                            original_text=text
                        )
                    logger.debug(f"[Request {request_id}] Found {len(citation_results['clusters'])} clusters")
                except Exception as cluster_error:
                    logger.error(
                        f"[Request {request_id}] Error in clustering: {str(cluster_error)}", 
                        exc_info=True
                    )
                    citation_results['clusters'] = []
                
                # Add processing metadata
                citation_results['status'] = 'success'
                citation_results['request_id'] = request_id
                citation_results['processing_time'] = time.time() - start_time
                
                return citation_results
                
            except Exception as process_error:
                error_msg = f"[Request {request_id}] Error processing text: {str(process_error)}"
                logger.error(error_msg, exc_info=True)
                return {
                    'status': 'error',
                    'error': 'Failed to process text',
                    'details': str(process_error) if os.getenv('FLASK_ENV') == 'development' else None,
                    'request_id': request_id
                }
                
        except Exception as unexpected_error:
            error_msg = f"[Request {request_id}] Unexpected error in process_citations_from_text: {str(unexpected_error)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'error': 'Unexpected error during processing',
                'details': str(unexpected_error) if os.getenv('FLASK_ENV') == 'development' else None,
                'request_id': request_id
            } 