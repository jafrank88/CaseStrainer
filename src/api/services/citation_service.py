"""
Extracted citation processing business logic from the main API file.
This separates concerns and makes the code more testable and maintainable.
"""

import os
import time
import uuid
import json
import logging
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import configuration
from src.config import get_citation_config, get_external_api_config, get_file_config

# Import your existing processors
try:
    from src.document_processing import enhanced_processor
    ENHANCED_PROCESSOR_AVAILABLE = True
except ImportError:
    from src.document_processing import process_document
    ENHANCED_PROCESSOR_AVAILABLE = False
    logging.warning("Enhanced processor not available, using fallback")

try:
    from src.unified_citation_processor import unified_processor
    UNIFIED_PROCESSOR_AVAILABLE = True
except ImportError:
    UNIFIED_PROCESSOR_AVAILABLE = False
    logging.warning("Unified processor not available")

class CitationService:
    """
    Service class for handling all citation processing logic.
    Extracted from the main API to separate business logic from API concerns.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.citation_config = get_citation_config()
        self.api_config = get_external_api_config()
        self.file_config = get_file_config()
        
        self.logger.info(f"CitationService initialized with config: {self.citation_config}")
        
        # Initialize the best available processor
        if ENHANCED_PROCESSOR_AVAILABLE:
            self.processor = enhanced_processor
            self.logger.info("Using enhanced document processor")
        elif UNIFIED_PROCESSOR_AVAILABLE:
            self.processor = unified_processor
            self.logger.info("Using unified citation processor")
        else:
            self.processor = None
            self.logger.warning("No advanced processors available - using fallback methods")
    
    def should_process_immediately(self, input_data: Dict[str, Any]) -> bool:
        """
        Determine if input should be processed immediately or queued.
        
        Criteria for immediate processing:
        - Text input only
        - Short text (< configured max length)
        - Contains citation patterns
        - <= configured max words
        - Contains numbers (likely a citation)
        """
        if input_data.get('type') != 'text':
            return False
        
        text = input_data.get('text', '').strip()
        
        # Get thresholds from configuration
        max_length = self.citation_config.get('immediate_max_length', 50)
        max_words = self.citation_config.get('immediate_max_words', 10)
        
        # Quick checks for immediate processing
        is_short = len(text) < max_length
        has_numbers = any(char.isdigit() for char in text)
        has_citation_patterns = any(
            pattern in text.upper() 
            for pattern in [
                'U.S.', 'F.', 'F.2D', 'F.3D', 'S.CT.', 'L.ED.', 
                'P.2D', 'P.3D', 'A.2D', 'A.3D', 'WN.2D', 'WN.APP.',
                'WASH.2D', 'WASH.APP.'
            ]
        )
        is_few_words = len(text.split()) <= max_words
        
        should_process = is_short and has_numbers and has_citation_patterns and is_few_words
        
        self.logger.info(f"Immediate processing decision: {should_process} "
                        f"(short={is_short}, numbers={has_numbers}, "
                        f"patterns={has_citation_patterns}, few_words={is_few_words}, "
                        f"max_length={max_length}, max_words={max_words})")
        
        return should_process
    
    def process_immediately(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input immediately and return formatted results.
        Used for simple citations that can be processed quickly.
        """
        start_time = time.time()
        
        try:
            text = input_data.get('text', '').strip()
            self.logger.info(f"Processing immediately: '{text}'")
            
            # Use the best available processor
            if self.processor and hasattr(self.processor, 'process_text'):
                # Use unified processor
                result = self.processor.process_text(text, options={
                    'extract_case_names': True,
                    'use_enhanced': True
                })
                
                if not result.get('success', True):
                    return {
                        'status': 'error',
                        'message': result.get('error', 'Processing failed')
                    }
                
                citations = result.get('results', [])
                
            elif self.processor and hasattr(self.processor, 'process_document'):
                # Use enhanced processor
                result = self.processor.process_document(
                    content=text,
                    extract_case_names=True
                )
                
                if not result['success']:
                    return {
                        'status': 'error',
                        'message': result.get('error', 'Processing failed')
                    }
                
                citations = result['citations']
                
            else:
                # Fallback to document processing
                from src.document_processing import process_document
                result = process_document(content=text, extract_case_names=True)
                
                if not result['success']:
                    return {
                        'status': 'error',
                        'message': result.get('error', 'Processing failed')
                    }
                
                citations = result['citations']
            
            # Format citations for frontend
            formatted_citations = self._format_citations_for_frontend(citations)
            
            # Calculate statistics
            statistics = self._calculate_statistics(formatted_citations)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"Immediate processing completed in {processing_time:.2f}s: "
                           f"{len(formatted_citations)} citations found")
            
            return {
                'status': 'completed',
                'citations': formatted_citations,
                'statistics': statistics,
                'summary': statistics,  # For backward compatibility
                'metadata': {
                    'processing_type': 'immediate',
                    'text_length': len(text),
                    'processing_time': processing_time,
                    'processor_used': self._get_processor_name()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in immediate processing: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Processing failed: {str(e)}'
            }
    
    def process_citation_task(self, task_id: str, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a citation task asynchronously.
        This is the main worker function extracted from your API.
        """
        self.logger.info(f"Starting citation task {task_id} (type: {task_type})")
        start_time = time.time()
        
        try:
            text = None
            metadata = {}
            
            # Extract text based on task type
            if task_type == 'file':
                text, metadata = self._process_file_task(task_data)
            elif task_type == 'text':
                text = task_data.get('text', '')
                metadata = {'text_length': len(text)}
            elif task_type == 'url':
                text, metadata = self._process_url_task(task_data)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            if not text or not text.strip():
                return {
                    'status': 'failed',
                    'error': 'No text content extracted',
                    'citations': [],
                    'case_names': []
                }
            
            # Process text in chunks for large documents
            result = self._process_text_in_chunks(text, task_id)
            
            # Add metadata
            result['metadata'] = {
                **metadata,
                'task_id': task_id,
                'task_type': task_type,
                'processing_time': time.time() - start_time,
                'processor_used': self._get_processor_name()
            }
            
            self.logger.info(f"Task {task_id} completed successfully: "
                           f"{len(result.get('citations', []))} citations found")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e),
                'citations': [],
                'case_names': []
            }
        
        finally:
            # Clean up uploaded files
            if task_type == 'file' and task_data.get('file_path'):
                self._cleanup_file(task_data['file_path'])
    
    def _process_file_task(self, task_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Process file upload task."""
        file_path = task_data.get('file_path')
        filename = task_data.get('filename', 'unknown')
        file_ext = task_data.get('file_ext', '')
        
        self.logger.info(f"Processing file: {filename}")
        
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text from file
        if ENHANCED_PROCESSOR_AVAILABLE:
            text = self.processor.extract_text_from_file(file_path)
        else:
            from src.file_utils import extract_text_from_file
            text_result = extract_text_from_file(file_path, file_ext=file_ext)
            if isinstance(text_result, tuple):
                text, _ = text_result
            else:
                text = text_result
        
        metadata = {
            'filename': filename,
            'file_type': file_ext,
            'file_size': os.path.getsize(file_path),
            'text_length': len(text)
        }
        
        return text, metadata
    
    def _process_url_task(self, task_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Process URL task."""
        url = task_data.get('url')
        
        self.logger.info(f"Processing URL: {url}")
        
        if not url:
            raise ValueError("No URL provided")
        
        # Extract text from URL
        if ENHANCED_PROCESSOR_AVAILABLE:
            text = self.processor.extract_text_from_url(url)
        else:
            from src.enhanced_validator_production import extract_text_from_url
            url_result = extract_text_from_url(url)
            text = url_result.get('text', '')
        
        metadata = {
            'url': url,
            'domain': url.split('/')[2] if '/' in url else url,
            'text_length': len(text)
        }
        
        return text, metadata
    
    def _process_text_in_chunks(self, text: str, task_id: str = None) -> Dict[str, Any]:
        """
        Process large text in chunks to handle memory efficiently.
        """
        chunk_size = self.citation_config.get('chunk_size', 5000)  # characters per chunk
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        total_chunks = len(chunks)
        
        self.logger.info(f"Processing text in {total_chunks} chunks")
        
        all_citations = []
        all_case_names = set()
        
        for idx, chunk in enumerate(chunks):
            try:
                # Process chunk
                if self.processor and hasattr(self.processor, 'process_document'):
                    chunk_result = self.processor.process_document(
                        content=chunk,
                        extract_case_names=True
                    )
                else:
                    from src.document_processing import process_document
                    chunk_result = process_document(content=chunk, extract_case_names=True)
                
                if chunk_result.get('success'):
                    all_citations.extend(chunk_result.get('citations', []))
                    all_case_names.update(chunk_result.get('case_names', []))
                
                # Log progress
                progress = int(((idx + 1) / total_chunks) * 100)
                self.logger.debug(f"Chunk {idx + 1}/{total_chunks} processed ({progress}%)")
                
            except Exception as e:
                self.logger.warning(f"Error processing chunk {idx + 1}: {e}")
                continue
        
        # Deduplicate citations
        deduplicated_citations = self._deduplicate_citations(all_citations)
        formatted_citations = self._format_citations_for_frontend(deduplicated_citations)
        
        return {
            'status': 'success',
            'citations': formatted_citations,
            'case_names': list(all_case_names),
            'statistics': self._calculate_statistics(formatted_citations),
            'summary': self._calculate_statistics(formatted_citations),
            'extraction_metadata': {
                'text_length': len(text),
                'total_chunks': total_chunks,
                'total_citations_found': len(all_citations),
                'unique_citations': len(deduplicated_citations)
            }
        }
    
    def _format_citations_for_frontend(self, citations: List[Dict]) -> List[Dict]:
        """
        Format citations for frontend consumption.
        Ensures consistent structure regardless of processor used.
        """
        formatted = []
        
        for citation in citations:
            # Handle both CitationResult objects and dictionaries
            if hasattr(citation, '__dict__'):
                # It's a CitationResult object
                citation_dict = {
                    'citation': getattr(citation, 'citation', ''),
                    'verified': getattr(citation, 'verified', False),
                    'case_name': getattr(citation, 'case_name', 'N/A'),
                    'extracted_case_name': getattr(citation, 'extracted_case_name', 'N/A'),
                    'canonical_name': getattr(citation, 'canonical_name', 'N/A'),
                    'extracted_date': getattr(citation, 'extracted_date', 'N/A'),
                    'canonical_date': getattr(citation, 'canonical_date', 'N/A'),
                    'court': getattr(citation, 'court', 'N/A'),
                    'confidence': getattr(citation, 'confidence', 0.0),
                    'source': getattr(citation, 'source', 'Unknown'),
                    'url': getattr(citation, 'url', ''),
                    'parallel_citations': getattr(citation, 'parallel_citations', []),
                    'context': getattr(citation, 'context', ''),
                    'method': getattr(citation, 'method', ''),
                    'error': getattr(citation, 'error', '')
                }
            else:
                # It's already a dictionary
                citation_dict = {
                    'citation': citation.get('citation', ''),
                    'verified': citation.get('verified', False),
                    'case_name': citation.get('case_name', 'N/A'),
                    'extracted_case_name': citation.get('extracted_case_name', 'N/A'),
                    'canonical_name': citation.get('canonical_name', 'N/A'),
                    'extracted_date': citation.get('extracted_date', 'N/A'),
                    'canonical_date': citation.get('canonical_date', 'N/A'),
                    'court': citation.get('court', 'N/A'),
                    'confidence': citation.get('confidence', 0.0),
                    'source': citation.get('source', 'Unknown'),
                    'url': citation.get('url', ''),
                    'parallel_citations': citation.get('parallel_citations', []),
                    'context': citation.get('context', ''),
                    'method': citation.get('method', ''),
                    'error': citation.get('error', '')
                }
            
            # Ensure boolean values are properly formatted
            citation_dict['verified'] = 'true' if citation_dict['verified'] else 'false'
            
            # Handle parallel citations formatting
            if citation_dict['parallel_citations']:
                citation_dict['parallels'] = []
                for parallel in citation_dict['parallel_citations']:
                    parallel_obj = {
                        'citation': parallel if isinstance(parallel, str) else parallel.get('citation', ''),
                        'verified': citation_dict['verified'],
                        'true_by_parallel': False,
                        'case_name': citation_dict['case_name'],
                        'extracted_case_name': citation_dict['extracted_case_name'],
                        'extracted_date': citation_dict['extracted_date']
                    }
                    citation_dict['parallels'].append(parallel_obj)
            else:
                citation_dict['parallels'] = []
            
            # Add additional frontend-specific fields
            citation_dict.update({
                'valid': citation_dict['verified'],
                'is_complex_citation': citation.get('is_complex_citation', False),
                'is_parallel_citation': citation.get('is_parallel_citation', False),
                'docket_number': citation.get('docket_number', 'N/A'),
                'display_text': citation_dict['citation'],
                'complex_features': {},
                'parallel_info': {},
                'metadata': {}
            })
            
            formatted.append(citation_dict)
        
        return formatted
    
    def _calculate_statistics(self, citations: List[Dict]) -> Dict[str, int]:
        """Calculate citation statistics."""
        total = len(citations)
        verified = sum(1 for c in citations if c.get('verified') == 'true' or c.get('verified') is True)
        unverified = total - verified
        parallel = sum(1 for c in citations if c.get('parallel_citations'))
        
        # Count unique case names
        unique_cases = set()
        for c in citations:
            case_name = c.get('case_name') or c.get('canonical_name')
            if case_name and case_name != 'N/A':
                unique_cases.add(case_name.lower().strip())
        
        return {
            'total_citations': total,
            'verified_citations': verified,
            'unverified_citations': unverified,
            'parallel_citations': parallel,
            'unique_cases': len(unique_cases)
        }
    
    def _deduplicate_citations(self, citations: List[Dict]) -> List[Dict]:
        """Remove duplicate citations based on citation text."""
        seen = set()
        unique_citations = []
        
        for citation in citations:
            citation_text = citation.get('citation', '')
            if citation_text and citation_text not in seen:
                seen.add(citation_text)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _cleanup_file(self, file_path: str):
        """Clean up uploaded file after processing."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to clean up file {file_path}: {e}")
    
    def _get_processor_name(self) -> str:
        """Get the name of the processor being used."""
        if ENHANCED_PROCESSOR_AVAILABLE:
            return "enhanced_processor"
        elif UNIFIED_PROCESSOR_AVAILABLE:
            return "unified_processor"
        else:
            return "fallback_processor"

# ============================================================================
# Testing the extracted service
# ============================================================================

def test_citation_service():
    """Test the extracted citation service."""
    service = CitationService()
    
    # Test immediate processing
    test_input = {
        'type': 'text',
        'text': '123 Wn.2d 456'
    }
    
    should_immediate = service.should_process_immediately(test_input)
    print(f"Should process immediately: {should_immediate}")
    
    if should_immediate:
        result = service.process_immediately(test_input)
        print(f"Immediate result: {result['status']}")
        print(f"Citations found: {len(result.get('citations', []))}")
    
    # Test async processing
    task_result = service.process_citation_task('test-task', 'text', test_input)
    print(f"Async result: {task_result['status']}")
    print(f"Citations found: {len(task_result.get('citations', []))}")

if __name__ == "__main__":
    test_citation_service() 