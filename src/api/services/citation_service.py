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
        input_type = input_data.get('type')
        
        if input_type == 'text':
            text = input_data.get('text', '')
            # Process short texts immediately (< 10KB)
            return len(text) < 10 * 1024
        elif input_type == 'file':
            # Check file size - queue large files for async processing
            file_size = input_data.get('file_size', 0)
            # Queue files larger than 5MB for async processing
            return file_size < 5 * 1024 * 1024  # 5MB threshold
        elif input_type == 'url':
            # Always queue URL processing for better performance and resource management
            return False
        
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
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"[DEBUG] Cleaned up temporary file: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"[DEBUG] Failed to clean up file {file_path}: {cleanup_error}")
    
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
            Dict containing citations, clusters, and processing metadata
        """
        start_time = time.time()
        logger.info(f"[Request {uuid.uuid4()}] Starting citation processing for text (length: {len(text)})")
        
        try:
            # Import required modules
            logger.debug(f"[Request {uuid.uuid4()}] Importing required modules")
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            from src.services.citation_clusterer import CitationClusterer
            logger.debug(f"[Request {uuid.uuid4()}] Successfully imported required modules")
            
            # Initialize processor
            logger.debug(f"[Request {uuid.uuid4()}] Initializing UnifiedCitationProcessorV2")
            processor = UnifiedCitationProcessorV2()
            logger.debug(f"[Request {uuid.uuid4()}] Successfully initialized processor")
            
            # Process text
            logger.debug(f"[Request {uuid.uuid4()}] Starting text processing")
            result = await processor.process_text(text)
            logger.info(f"[Request {uuid.uuid4()}] Processed text, found {len(result.get('citations', []))} citations")
            
            # Run clustering if no clusters found
            if not result.get('clusters'):
                logger.debug(f"[Request {uuid.uuid4()}] No clusters found, running clustering")
                clusterer = CitationClusterer()
                clusters = clusterer.cluster_citations(result.get('citations', []))
                result['clusters'] = clusters
                logger.debug(f"[Request {uuid.uuid4()}] Found {len(clusters)} clusters")
            
            # Convert CitationResult objects in citations array to dictionaries for JSON serialization
            if result.get('citations'):
                logger.debug(f"[Request {uuid.uuid4()}] Converting CitationResult objects in citations array to dictionaries")
                converted_citations = []
                for citation in result['citations']:
                    if hasattr(citation, 'citation'):  # CitationResult object
                        citation_dict = {
                            'citation': citation.citation,
                            'case_name': citation.extracted_case_name or citation.case_name,
                            'extracted_case_name': citation.extracted_case_name,
                            'canonical_name': citation.canonical_name,
                            'extracted_date': citation.extracted_date,
                            'canonical_date': citation.canonical_date,
                            'verified': citation.verified if isinstance(citation.verified, bool) else (citation.verified == "true_by_parallel" or citation.verified == True),
                            'court': citation.court,
                            'confidence': citation.confidence,
                            'method': citation.method,
                            'pattern': citation.pattern,
                            'context': citation.context,
                            'start_index': citation.start_index,
                            'end_index': citation.end_index,
                            'is_parallel': citation.is_parallel,
                            'is_cluster': citation.is_cluster,
                            'parallel_citations': citation.parallel_citations,
                            'cluster_members': citation.metadata.get('cluster_members', []) if citation.metadata else [],
                            'pinpoint_pages': citation.pinpoint_pages,
                            'docket_numbers': citation.docket_numbers,
                            'case_history': citation.case_history,
                            'publication_status': citation.publication_status,
                            'url': citation.url,
                            'source': citation.source,
                            'error': citation.error,
                            'metadata': citation.metadata or {},
                            'extraction_method': getattr(citation, 'extraction_method', None),
                        }
                        # Ensure cluster metadata is properly included
                        if citation.metadata:
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
                        converted_citations.append(citation_dict)
                    else:
                        converted_citations.append(citation)  # Already a dict
                result['citations'] = converted_citations
                logger.debug(f"[Request {uuid.uuid4()}] Converted {len(converted_citations)} citations")
            
            # Convert CitationResult objects in clusters to dictionaries for JSON serialization
            if result.get('clusters'):
                logger.debug(f"[Request {uuid.uuid4()}] Converting CitationResult objects in clusters to dictionaries")
                converted_clusters = []
                for cluster in result['clusters']:
                    if isinstance(cluster, dict):
                        # Convert CitationResult objects in cluster['citations'] to dictionaries
                        if 'citations' in cluster and isinstance(cluster['citations'], list):
                            converted_citations_in_cluster = []
                            for citation in cluster['citations']:
                                if hasattr(citation, 'citation'):  # CitationResult object
                                    citation_dict = {
                                        'citation': citation.citation,
                                        'case_name': citation.extracted_case_name or citation.case_name,
                                        'extracted_case_name': citation.extracted_case_name,
                                        'canonical_name': citation.canonical_name,
                                        'extracted_date': citation.extracted_date,
                                        'canonical_date': citation.canonical_date,
                                        'verified': citation.verified if isinstance(citation.verified, bool) else (citation.verified == "true_by_parallel" or citation.verified == True),
                                        'court': citation.court,
                                        'confidence': citation.confidence,
                                        'method': citation.method,
                                        'pattern': citation.pattern,
                                        'context': citation.context,
                                        'start_index': citation.start_index,
                                        'end_index': citation.end_index,
                                        'is_parallel': citation.is_parallel,
                                        'is_cluster': citation.is_cluster,
                                        'parallel_citations': citation.parallel_citations,
                                        'cluster_members': citation.metadata.get('cluster_members', []) if citation.metadata else [],
                                        'pinpoint_pages': citation.pinpoint_pages,
                                        'docket_numbers': citation.docket_numbers,
                                        'case_history': citation.case_history,
                                        'publication_status': citation.publication_status,
                                        'url': citation.url,
                                        'source': citation.source,
                                        'error': citation.error,
                                        'metadata': citation.metadata or {},
                                        'extraction_method': getattr(citation, 'extraction_method', None),
                                    }
                                    # Ensure cluster metadata is properly included
                                    if citation.metadata:
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
                                    converted_citations_in_cluster.append(citation_dict)
                                else:
                                    converted_citations_in_cluster.append(citation)  # Already a dict
                            cluster['citations'] = converted_citations_in_cluster
                        converted_clusters.append(cluster)
                    else:
                        converted_clusters.append(cluster)
                result['clusters'] = converted_clusters
                logger.debug(f"[Request {uuid.uuid4()}] Converted {len(converted_clusters)} clusters")
            
            # Add processing time
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            return result
            
        except Exception as e:
            logger.error(f"[Request {uuid.uuid4()}] Error processing text: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'citations': [],
                'clusters': [],
                'processing_time': time.time() - start_time
            }

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