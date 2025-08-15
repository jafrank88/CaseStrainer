"""
Unified Input Processor
Consolidates all input types (file, URL, text) into a single text processing pipeline.
"""

import os
import sys
import time
import logging
import tempfile
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse
from werkzeug.datastructures import FileStorage

# Import text extraction modules
from src.pdf_extraction_optimized import extract_text_from_pdf_smart
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
            # Step 1: Convert input to text (regardless of input type)
            text_result = self._extract_text_from_input(input_data, input_type, request_id)
            
            if not text_result['success']:
                return text_result
            
            text = text_result['text']
            metadata = text_result.get('metadata', {})
            
            # Step 2: Process citations using unified pipeline (same for all input types)
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
            return self._extract_from_text(input_data, request_id)
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
            # Validate URL
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
            # Fetch content from URL
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
    
    def _extract_from_file(self, file: FileStorage, request_id: str) -> Dict[str, Any]:
        """Extract text from uploaded file."""
        logger.info(f"[Unified Processor {request_id}] Extracting text from file: {file.filename}")
        
        try:
            # Validate file
            if not file or not file.filename:
                return {
                    'success': False,
                    'error': 'No file provided or empty filename',
                    'text': '',
                    'metadata': {'input_type': 'file', 'error': 'no_file'}
                }
            
            # Get file extension
            filename = file.filename
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
            
            # Save file temporarily for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Extract text based on file type
                if file_ext == 'pdf':
                    text = extract_text_from_pdf_smart(temp_file_path)
                elif file_ext == 'txt':
                    with open(temp_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                else:
                    # For other file types, try basic text extraction
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
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"[Unified Processor {request_id}] Error processing file {file.filename}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to process file: {str(e)}',
                'text': '',
                'metadata': {
                    'input_type': 'file',
                    'filename': file.filename if file else 'unknown',
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
            # Use CitationService to determine processing mode (immediate vs queued)
            input_data = {'type': 'text', 'text': text}
            logger.info(f"[Unified Processor {request_id}] Checking if should process immediately...")
            
            should_process_immediately = self.citation_service.should_process_immediately(input_data)
            logger.info(f"[Unified Processor {request_id}] Should process immediately: {should_process_immediately}")
            
            if should_process_immediately:
                logger.info(f"[Unified Processor {request_id}] Processing immediately (short content)")
                try:
                    result = self.citation_service.process_immediately(input_data)
                    logger.info(f"[Unified Processor {request_id}] Immediate processing result: {result}")
                    
                    return {
                        'success': True,
                        'citations': result.get('citations', []),
                        'clusters': result.get('clusters', []),
                        'request_id': request_id,
                        'metadata': {
                            **input_metadata,
                            'processing_mode': 'immediate',
                            'source': source_name
                        }
                    }
                except Exception as e:
                    logger.error(f"[Unified Processor {request_id}] Error in immediate processing: {str(e)}", exc_info=True)
                    # Fall back to async processing
                    should_process_immediately = False
            
            # If we reach here, either immediate processing failed or wasn't applicable
            if not should_process_immediately:
                logger.info(f"[Unified Processor {request_id}] Queuing for async processing (large content)")
                
                try:
                    # Import RQ for async processing
                    from rq import Queue
                    from redis import Redis
                    from src.progress_manager import process_citation_task_direct
                    
                    # Connect to Redis
                    redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
                    redis_conn = Redis.from_url(redis_url)
                    queue = Queue('casestrainer', connection=redis_conn)
                    
                    # Enqueue processing task with the request_id as the job ID
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
        
        # This should never be reached, but ensures all code paths return a value
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
            
            # Allow common schemes
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Basic safety checks (can be expanded)
            unsafe_domains = ['localhost', '127.0.0.1', '0.0.0.0']
            if parsed.netloc.lower() in unsafe_domains:
                return False
            
            return True
            
        except Exception:
            return False


# Convenience functions for backward compatibility
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
