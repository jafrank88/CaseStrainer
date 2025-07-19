"""
Extracted citation processing business logic from the main API file.
This separates concerns and makes the code more testable and maintainable.
"""

import os
import logging
import time
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
    
    def process_immediately(self, input_data: Dict) -> Dict[str, Any]:
        """Process input immediately (for short texts)."""
        try:
            if input_data.get('type') == 'text':
                text = input_data.get('text', '')
                return self.process_citations_from_text(text)
            
            return {'status': 'error', 'message': 'Invalid input type for immediate processing'}
            
        except Exception as e:
            logger.error(f"Immediate processing failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def process_citation_task(self, task_id: str, input_type: str, input_data: Dict) -> Dict[str, Any]:
        """
        Process citation task asynchronously using Redis-distributed processing.
        This is the main function called by RQ workers.
        """
        start_time = time.time()
        logger.info(f"Processing citation task {task_id} of type {input_type}")
        
        try:
            if input_type == 'file':
                return await self._process_file_task(task_id, input_data)
            elif input_type == 'url':
                return await self._process_url_task(task_id, input_data)
            elif input_type == 'text':
                return await self._process_text_task(task_id, input_data)
            else:
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
        """Process file upload task."""
        file_path = input_data.get('file_path')
        filename = input_data.get('filename', 'unknown')
        
        if not file_path or not os.path.exists(file_path):
            return {
                'status': 'failed',
                'error': f'File not found: {file_path}',
                'task_id': task_id
            }
        
        try:
            # Use distributed processor for text extraction
            result = await self.processor.process_document(file_path)
            
            # Clean up temporary file
            try:
                os.remove(file_path)
            except:
                pass
            
            return {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'statistics': result.get('statistics', {}),
                'metadata': {
                    'filename': filename,
                    'text_length': result.get('text_length', 0)
                },
                'processing_time': result.get('processing_time', 0)
            }
            
        except Exception as e:
            # Clean up on error
            try:
                os.remove(file_path)
            except:
                pass
            raise
    
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
            response = requests.get(url, timeout=60, timeout=30)
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
            # Process citations from text
            result = self.process_citations_from_text(text)
            
            return {
                'status': 'completed',
                'task_id': task_id,
                'citations': result.get('citations', []),
                'statistics': result.get('statistics', {}),
                'metadata': {
                    'source_name': source_name,
                    'text_length': len(text)
                },
                'processing_time': time.time() - time.time()  # Will be set by caller
            }
            
        except Exception as e:
            raise
    
    def process_citations_from_text(self, text: str) -> Dict[str, Any]:
        """Process citations from extracted text using existing citation processor."""
        try:
            # Use existing citation processor
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            
            processor = UnifiedCitationProcessorV2()
            citation_results = processor.process_text(text)
            
            # Convert CitationResult objects to dictionaries
            processed_citations = []
            for citation in citation_results:
                citation_dict = {
                    'citation': citation.citation,
                    'case_name': citation.extracted_case_name or citation.case_name,
                    'extracted_case_name': citation.extracted_case_name,
                    'canonical_name': citation.canonical_name,
                    'extracted_date': citation.extracted_date,
                    'canonical_date': citation.canonical_date,
                    'verified': citation.verified,
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
                    'cluster_members': citation.cluster_members,
                    'pinpoint_pages': citation.pinpoint_pages,
                    'docket_numbers': citation.docket_numbers,
                    'case_history': citation.case_history,
                    'publication_status': citation.publication_status,
                    'url': citation.url,
                    'source': citation.source,
                    'error': citation.error,
                    'metadata': citation.metadata or {}
                }
                processed_citations.append(citation_dict)
            
            return {
                'status': 'completed',
                'citations': processed_citations,
                'statistics': {
                    'total_citations': len(processed_citations),
                    'text_length': len(text)
                }
            }
            
        except Exception as e:
            logger.error(f"Citation processing failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'citations': [],
                'statistics': {}
            } 