"""
Unified Input Processor
Consolidates all input types (file, URL, text) into a single text processing pipeline.
"""

import os
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import sys
import time
import logging
import tempfile
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse
from werkzeug.datastructures import FileStorage

from src.robust_pdf_extractor import extract_text_from_pdf_smart
from src.progress_manager import fetch_url_content
from src.api.services.citation_service import CitationService

logger = logging.getLogger(__name__)

class UnifiedInputProcessor:
    """
    Unified processor that converts any input type to text and processes citations.
    Eliminates redundancy between file, URL, and text handlers.
    """
    
    def __init__(self):
        self.citation_service = CitationService()
        self.supported_file_extensions = {
            'pdf', 'txt', 'doc', 'docx', 'rtf', 'md', 'html', 'htm', 'xml', 'xhtml'
        }
    
    def process_any_input(self, input_data: Any, input_type: str, request_id: str, 
                         source_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Universal input processor - converts any input to text, then processes citations.
        
        Args:
            input_data: The input data (file, URL string, or text string)
            input_type: Type of input ('file', 'url', 'text')
            request_id: Unique request identifier
            source_name: Optional source name for metadata
            
        Returns:
            Dictionary with citation processing results
        """
        logger.info(f"[Unified Processor {request_id}] Processing {input_type} input")
        
        try:
            text_result = self._extract_text_from_input(input_data, input_type, request_id)
            
            if not text_result['success']:
                return text_result
            
            text = text_result['text']
            metadata = text_result.get('metadata', {})
            
            return self._process_citations_unified(
                text=text,
                request_id=request_id,
                source_name=source_name or input_type,
                input_metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error processing {input_type}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error processing {input_type} input: {str(e)}',
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'metadata': {
                    'input_type': input_type,
                    'error_type': 'processing_error'
                }
            }
    
    def _extract_text_from_input(self, input_data: Any, input_type: str, request_id: str) -> Dict[str, Any]:
        """
        Extract text from any input type.
        
        Returns:
            Dictionary with success status, text, and metadata
        """
        if input_type == 'text':
            # Extract text from dict if needed
            if isinstance(input_data, dict):
                text = input_data.get('text', '')
            else:
                text = input_data
            return self._extract_from_text(text, request_id)
        elif input_type == 'url':
            return self._extract_from_url(input_data, request_id)
        elif input_type == 'file':
            return self._extract_from_file(input_data, request_id)
        else:
            return {
                'success': False,
                'error': f'Unsupported input type: {input_type}',
                'text': '',
                'metadata': {'input_type': input_type}
            }
    
    def _extract_from_text(self, text: str, request_id: str) -> Dict[str, Any]:
        """Extract text from direct text input (passthrough)."""
        logger.info(f"[Unified Processor {request_id}] Processing direct text input ({len(text)} chars)")
        
        if not text or len(text.strip()) < 10:
            return {
                'success': False,
                'error': 'Text input is empty or too short for analysis',
                'text': '',
                'metadata': {'input_type': 'text', 'text_length': len(text)}
            }
        
        return {
            'success': True,
            'text': text,
            'metadata': {
                'input_type': 'text',
                'text_length': len(text),
                'source': 'direct_text'
            }
        }
    
    def _extract_from_url(self, url: str, request_id: str) -> Dict[str, Any]:
        """Extract text from URL by fetching and processing content."""
        logger.info(f"[Unified Processor {request_id}] Extracting text from URL: {url}")
        
        try:
            logger.info(f"[Unified Processor {request_id}] Validating URL...")
            if not self._validate_url(url):
                logger.warning(f"[Unified Processor {request_id}] URL validation failed: {url}")
                return {
                    'success': False,
                    'error': 'Invalid or unsafe URL provided',
                    'text': '',
                    'metadata': {'input_type': 'url', 'url': url, 'error': 'validation_failed'}
                }
            
            logger.info(f"[Unified Processor {request_id}] URL validation passed, fetching content...")
            content = fetch_url_content(url)
            logger.info(f"[Unified Processor {request_id}] Content fetched, length: {len(content) if content else 0}")
            
            if not content or len(content.strip()) < 10:
                logger.warning(f"[Unified Processor {request_id}] Insufficient content from URL: {len(content) if content else 0} chars")
                return {
                    'success': False,
                    'error': 'URL returned empty or insufficient content for analysis',
                    'text': '',
                    'metadata': {
                        'input_type': 'url',
                        'url': url,
                        'content_length': len(content),
                        'error': 'insufficient_content'
                    }
                }
            
            logger.info(f"[Unified Processor {request_id}] Successfully extracted {len(content)} characters from URL")
            return {
                'success': True,
                'text': content,
                'metadata': {
                    'input_type': 'url',
                    'url': url,
                    'url_domain': urlparse(url).netloc,
                    'content_length': len(content),
                    'source': 'url_fetch'
                }
            }
            
        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error fetching URL {url}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to fetch content from URL: {str(e)}',
                'text': '',
                'metadata': {
                    'input_type': 'url',
                    'url': url,
                    'error': 'fetch_failed',
                    'error_details': str(e)
                }
            }
    
    def _extract_from_file(self, input_data: Union[FileStorage, Dict], request_id: str) -> Dict[str, Any]:
        """Extract text from uploaded file."""
        if isinstance(input_data, dict):
            file = input_data.get('file')
            filename = input_data.get('filename', 'unknown')
        else:
            file = input_data
            filename = getattr(file, 'filename', 'unknown') if file else 'unknown'
        
        logger.info(f"[Unified Processor {request_id}] Extracting text from file: {filename}")
        
        try:
            if not file or not filename:
                return {
                    'success': False,
                    'error': 'No file provided or empty filename',
                    'text': '',
                    'metadata': {'input_type': 'file', 'error': 'no_file'}
                }
            
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_ext not in self.supported_file_extensions:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_ext}',
                    'text': '',
                    'metadata': {
                        'input_type': 'file',
                        'filename': filename,
                        'file_extension': file_ext,
                        'error': 'unsupported_type'
                    }
                }
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                if file_ext == 'pdf':
                    text = extract_text_from_pdf_smart(temp_file_path)
                elif file_ext == 'txt':
                    with open(temp_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                else:
                    with open(temp_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                
                if not text or len(text.strip()) < 10:
                    return {
                        'success': False,
                        'error': 'File contains no extractable text or text is too short',
                        'text': '',
                        'metadata': {
                            'input_type': 'file',
                            'filename': filename,
                            'file_extension': file_ext,
                            'text_length': len(text),
                            'error': 'no_extractable_text'
                        }
                    }
                
                return {
                    'success': True,
                    'text': text,
                    'metadata': {
                        'input_type': 'file',
                        'filename': filename,
                        'file_extension': file_ext,
                        'text_length': len(text),
                        'source': 'file_upload'
                    }
                }
                
            finally:
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error processing file {filename}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to process file: {str(e)}',
                'text': '',
                'metadata': {
                    'input_type': 'file',
                    'filename': filename,
                    'error': 'processing_failed',
                    'error_details': str(e)
                }
            }
    
    def _process_citations_unified(self, text: str, request_id: str, source_name: str, 
                                 input_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process citations using the unified pipeline (same for all input types).
        """
        logger.info(f"[Unified Processor {request_id}] Processing citations from {source_name}")
        logger.info(f"[Unified Processor {request_id}] Text length: {len(text)} characters")
        logger.info(f"[Unified Processor {request_id}] Text preview: {text[:200]}...")
        
        try:
            input_data = {'type': 'text', 'text': text}
            logger.info(f"[Unified Processor {request_id}] Checking if should process immediately...")
            
            should_process_immediately = self.citation_service.should_process_immediately(input_data)
            logger.info(f"[Unified Processor {request_id}] Should process immediately: {should_process_immediately}")
            
            if should_process_immediately:
                logger.warning(f"[Unified Processor {request_id}] *** SYNC PATH: Processing immediately (short content) - using UnifiedCitationProcessorV2 directly")
                try:
                    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                    import asyncio
                    
                    processor = UnifiedCitationProcessorV2()
                    result = asyncio.run(processor.process_text(input_data.get('text', '')))
                    
                    logger.info(f"[Unified Processor {request_id}] Immediate processing result: {result}")
                    
                    # Convert CitationResult objects to dictionaries for API response
                    citations = result.get('citations', [])
                    converted_citations = []
                    for citation in citations:
                        if hasattr(citation, 'to_dict'):
                            # Use the fixed to_dict method that doesn't include case_name
                            citation_dict = citation.to_dict()
                            
                            cluster_case_name = citation_dict.get('cluster_case_name')
                            extracted_case_name = citation_dict.get('extracted_case_name')
                            canonical_name = citation_dict.get('canonical_name')
                            logger.debug(f"SYNC_DATA_SEPARATION: cluster='{cluster_case_name}', extracted='{extracted_case_name}', canonical='{canonical_name}'")
                            
                            converted_citations.append(citation_dict)
                        else:
                            # Already a dictionary - maintain data separation
                            citation_dict = citation.copy()
                            
                            # REMOVED: case_name field eliminated to prevent contamination
                            # Frontend will use extracted_case_name and canonical_name directly
                            
                            cluster_case_name = citation_dict.get('cluster_case_name')
                            extracted_case_name = citation_dict.get('extracted_case_name')
                            canonical_name = citation_dict.get('canonical_name')
                            logger.debug(f"SYNC_DICT_DATA_SEPARATION: cluster='{cluster_case_name}', extracted='{extracted_case_name}', canonical='{canonical_name}'")
                                
                            converted_citations.append(citation_dict)
                    
                    return {
                        'success': True,
                        'citations': converted_citations,
                        'clusters': result.get('clusters', []),
                        'request_id': request_id,
                        'metadata': {
                            **input_metadata,
                            'processing_mode': 'immediate',
                            'source': source_name,
                            'processing_strategy': 'unified_v2_direct'
                        }
                    }
                except Exception as e:
                    logger.error(f"[Unified Processor {request_id}] Error in immediate processing: {str(e)}", exc_info=True)
                    should_process_immediately = False
            
            if not should_process_immediately:
                logger.info(f"[Unified Processor {request_id}] Queuing for async processing (large content)")
                
                try:
                    from rq import Queue
                    from redis import Redis
                    from src.progress_manager import process_citation_task_direct
                    
                    # Try multiple Redis configurations for better connectivity
                    redis_configs = [
                        os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0'),
                        'redis://localhost:6379/0',  # Local Redis fallback
                        'redis://127.0.0.1:6379/0'   # Alternative local Redis
                    ]
                    
                    redis_conn = None
                    for redis_url in redis_configs:
                        try:
                            redis_conn = Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
                            redis_conn.ping()  # Test connection
                            logger.info(f"[Unified Processor {request_id}] Connected to Redis: {redis_url}")
                            break
                        except Exception as e:
                            logger.debug(f"[Unified Processor {request_id}] Redis connection failed for {redis_url}: {e}")
                            continue
                    
                    if not redis_conn:
                        raise Exception("No Redis instance available")
                        
                    queue = Queue('casestrainer', connection=redis_conn)
                    
                    job = queue.enqueue(
                        process_citation_task_direct,
                        args=(request_id, 'text', {'text': text}),
                        job_id=request_id,  # Use request_id as the job ID
                        job_timeout=600,  # 10 minutes timeout
                        result_ttl=86400,
                        failure_ttl=86400
                    )
                    
                    logger.info(f"[Unified Processor {request_id}] Task enqueued with job_id: {job.id}")
                    
                    return {
                        'success': True,
                        'task_id': request_id,
                        'status': 'processing',
                        'message': f'{source_name.title()} processing started',
                        'request_id': request_id,
                        'metadata': {
                            **input_metadata,
                            'processing_mode': 'queued',
                            'source': source_name,
                            'job_id': job.id
                        }
                    }
                except Exception as e:
                    logger.error(f"[Unified Processor {request_id}] Error enqueueing async task: {str(e)}", exc_info=True)
                    
                    # Fallback to sync processing when Redis is unavailable
                    redis_error_indicators = [
                        "loading the dataset in memory",
                        "connection",
                        "getaddrinfo failed",
                        "redis",
                        "timeout",
                        "refused"
                    ]
                    should_fallback = any(indicator in str(e).lower() for indicator in redis_error_indicators)
                    
                    if should_fallback:
                        logger.warning(f"[Unified Processor {request_id}] Redis unavailable, falling back to sync processing for large document")
                        
                        try:
                            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                            import asyncio
                            
                            processor = UnifiedCitationProcessorV2()
                            result = asyncio.run(processor.process_text(text))
                            
                            logger.info(f"[Unified Processor {request_id}] Sync fallback processing completed successfully")
                            
                            # Convert CitationResult objects to dictionaries for API response
                            citations = result.get('citations', [])
                            converted_citations = []
                            for citation in citations:
                                if hasattr(citation, 'to_dict'):
                                    # Use the fixed to_dict method that doesn't include case_name
                                    citation_dict = citation.to_dict()
                                    
                                    cluster_case_name = citation_dict.get('cluster_case_name')
                                    extracted_case_name = citation_dict.get('extracted_case_name')
                                    canonical_name = citation_dict.get('canonical_name')
                                    logger.debug(f"FALLBACK_DATA_SEPARATION: cluster='{cluster_case_name}', extracted='{extracted_case_name}', canonical='{canonical_name}'")
                                    
                                    converted_citations.append(citation_dict)
                                else:
                                    # Already a dictionary - maintain data separation
                                    citation_dict = citation.copy()
                                    
                                    # REMOVED: case_name field eliminated to prevent contamination
                                    # Frontend will use extracted_case_name and canonical_name directly
                                    
                                    cluster_case_name = citation_dict.get('cluster_case_name')
                                    extracted_case_name = citation_dict.get('extracted_case_name')
                                    canonical_name = citation_dict.get('canonical_name')
                                    logger.debug(f"FALLBACK_DICT_DATA_SEPARATION: cluster='{cluster_case_name}', extracted='{extracted_case_name}', canonical='{canonical_name}'")
                                        
                                    converted_citations.append(citation_dict)
                            
                            return {
                                'success': True,
                                'citations': converted_citations,
                                'clusters': result.get('clusters', []),
                                'request_id': request_id,
                                'metadata': {
                                    **input_metadata,
                                    'processing_mode': 'sync_fallback',
                                    'source': source_name,
                                    'fallback_reason': 'redis_unavailable'
                                }
                            }
                        except Exception as fallback_error:
                            logger.error(f"[Unified Processor {request_id}] Sync fallback also failed: {str(fallback_error)}", exc_info=True)
                    
                    return {
                        'success': False,
                        'error': f'Failed to enqueue processing task: {str(e)}',
                        'citations': [],
                        'clusters': [],
                        'request_id': request_id,
                        'metadata': {
                            **input_metadata,
                            'processing_mode': 'enqueue_failed',
                            'source': source_name,
                            'error_details': str(e)
                        }
                    }
        
        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error in citation processing: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error processing citations: {str(e)}',
                'citations': [],
                'clusters': [],
                'request_id': request_id,
                'metadata': {
                    **input_metadata,
                    'error': 'citation_processing_failed',
                    'error_details': str(e)
                }
            }
        
        logger.error(f"[Unified Processor {request_id}] Unexpected end of function reached")
        return {
            'success': False,
            'error': 'Unexpected processing state',
            'citations': [],
            'clusters': [],
            'request_id': request_id,
            'metadata': {
                **input_metadata,
                'error': 'unexpected_state',
                'error_details': 'Function reached unexpected end'
            }
        }
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format and safety."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            if parsed.scheme not in ['http', 'https']:
                return False
            
            unsafe_domains = ['localhost', '127.0.0.1', '0.0.0.0']
            if parsed.netloc.lower() in unsafe_domains:
                return False
            
            return True
            
        except Exception:
            return False


def process_file_input(file: FileStorage, request_id: str) -> Dict[str, Any]:
    """Process file input using unified processor."""
    processor = UnifiedInputProcessor()
    return processor.process_any_input(file, 'file', request_id, 'file_upload')

def process_url_input(url: str, request_id: str) -> Dict[str, Any]:
    """Process URL input using unified processor."""
    processor = UnifiedInputProcessor()
    return processor.process_any_input(url, 'url', request_id, 'url_input')

def process_text_input(text: str, request_id: str) -> Dict[str, Any]:
    """Process text input using unified processor."""
    processor = UnifiedInputProcessor()
    return processor.process_any_input(text, 'text', request_id, 'text_input')
