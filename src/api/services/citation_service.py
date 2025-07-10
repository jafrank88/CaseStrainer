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

# Import the new unified citation processor V2
try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    UNIFIED_PROCESSOR_V2_AVAILABLE = True
    logging.info("UnifiedCitationProcessorV2 available")
except ImportError as e:
    UNIFIED_PROCESSOR_V2_AVAILABLE = False
    logging.warning(f"UnifiedCitationProcessorV2 not available: {e}")

# Import your existing processors as fallbacks
try:
    from src.document_processing import enhanced_processor
    ENHANCED_PROCESSOR_AVAILABLE = True
except ImportError:
    ENHANCED_PROCESSOR_AVAILABLE = False
    logging.warning("Enhanced processor not available")

try:
    from src.unified_citation_processor import unified_processor
    UNIFIED_PROCESSOR_AVAILABLE = True
except ImportError:
    UNIFIED_PROCESSOR_AVAILABLE = False
    logging.warning("Unified processor not available")

# Try to import the new unified document processor
try:
    from src.document_processing_unified import process_document
    UNIFIED_DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError:
    UNIFIED_DOCUMENT_PROCESSOR_AVAILABLE = False
    # Fallback to original document processing
    try:
        from src.document_processing import process_document
    except ImportError:
        process_document = None
        logging.warning("No document processor available")

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
        if UNIFIED_PROCESSOR_V2_AVAILABLE:
            # Use the new UnifiedCitationProcessorV2 as primary processor
            config = ProcessingConfig(
                use_eyecite=True,
                use_regex=True,
                extract_case_names=True,
                extract_dates=True,
                enable_clustering=True,
                enable_deduplication=True,
                debug_mode=True,
                min_confidence=0.0  # Force all citations to be included
            )
            self.processor = UnifiedCitationProcessorV2(config)
            self.logger.info("Using UnifiedCitationProcessorV2")
        elif ENHANCED_PROCESSOR_AVAILABLE:
            self.processor = enhanced_processor
            self.logger.info("Using enhanced document processor (fallback)")
        elif UNIFIED_PROCESSOR_AVAILABLE:
            self.processor = unified_processor
            self.logger.info("Using unified citation processor (fallback)")
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
                # Use unified processor V2
                self.logger.info("Using processor.process_text method")
                citation_results = self.processor.process_text(text)
                self.logger.info(f"[DEBUG] Extracted {len(citation_results)} citations after extraction.")
                
                # UnifiedCitationProcessorV2.process_text() returns List[CitationResult], not a dict
                if isinstance(citation_results, list):
                    # Convert CitationResult objects to dictionaries
                    citations = []
                    for citation_result in citation_results:
                        citation_dict = {
                            'citation': citation_result.citation,
                            'extracted_case_name': citation_result.extracted_case_name,
                            'extracted_date': citation_result.extracted_date,
                            'case_name': citation_result.canonical_name,  # Vue frontend expects case_name for canonical
                            'canonical_name': citation_result.canonical_name,
                            'canonical_date': citation_result.canonical_date,
                            'verified': citation_result.verified,
                            'url': citation_result.url,
                            'court': citation_result.court,
                            'docket_number': citation_result.docket_number,
                            'confidence': citation_result.confidence,
                            'method': citation_result.method,
                            'pattern': citation_result.pattern,
                            'context': citation_result.context,
                            'start_index': citation_result.start_index,
                            'end_index': citation_result.end_index,
                            'is_parallel': citation_result.is_parallel,
                            'is_cluster': citation_result.is_cluster,
                            'parallel_citations': citation_result.parallel_citations,
                            'cluster_members': citation_result.cluster_members,
                            'pinpoint_pages': citation_result.pinpoint_pages,
                            'docket_numbers': citation_result.docket_numbers,
                            'case_history': citation_result.case_history,
                            'publication_status': citation_result.publication_status,
                            'source': citation_result.source,
                            'error': citation_result.error,
                            'metadata': citation_result.metadata or {}
                        }
                        citations.append(citation_dict)
                    self.logger.info(f"[DEBUG] {len(citations)} citations after conversion to dict.")
                    # Calculate statistics
                    statistics = self._calculate_statistics(citations)
                else:
                    # Fallback: treat as dictionary (legacy format)
                    if citation_results.get('error'):
                        return {
                            'status': 'error',
                            'message': citation_results.get('error', 'Processing failed')
                        }
                    citations = citation_results.get('results', [])
                    statistics = citation_results.get('summary', {})
                self.logger.info(f"[DEBUG] {len(citations)} citations after legacy fallback.")
            
            elif self.processor and hasattr(self.processor, 'process_document'):
                # Use enhanced processor
                self.logger.info("Using processor.process_document method")
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
                self.logger.info("Using fallback process_document method")
                if process_document:
                    result = process_document(content=text, extract_case_names=True)
                else:
                    return {
                        'status': 'error',
                        'message': 'No document processor available'
                    }
                
                if not result['success']:
                    return {
                        'status': 'error',
                        'message': result.get('error', 'Processing failed')
                    }
                
                citations = result['citations']
            
            # Format citations for frontend (always apply formatting for verification logic)
            if self.processor and hasattr(self.processor, 'process_text'):
                # Unified processor returns dictionaries, but we still need to apply formatting logic
                formatted_citations = self._format_citations_for_frontend(citations)
                self.logger.info(f"[DEBUG] {len(formatted_citations)} citations after formatting.")
                # Use statistics from unified processor if available
                if not statistics:
                    statistics = self._calculate_statistics(formatted_citations)
            else:
                # Format citations for other processors
                formatted_citations = self._format_citations_for_frontend(citations)
                self.logger.info(f"[DEBUG] {len(formatted_citations)} citations after formatting.")
                # Calculate statistics
                statistics = self._calculate_statistics(formatted_citations)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"Immediate processing completed in {processing_time:.2f}s: "
                           f"{len(formatted_citations)} citations found")
            
            # Prepare metadata
            metadata = {
                'processing_type': 'immediate',
                'text_length': len(text),
                'processing_time': processing_time,
                'processor_used': self._get_processor_name()
            }
            
            # Add unified processor metadata if available
            if self.processor and hasattr(self.processor, 'process_text') and hasattr(citation_results, 'metadata'):
                metadata.update(citation_results.metadata)
            
            return {
                'status': 'completed',
                'citations': formatted_citations,
                'results': formatted_citations,  # For backward compatibility with unified processor
                'statistics': statistics,
                'summary': statistics,  # For backward compatibility
                'metadata': metadata
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
                if self.processor and hasattr(self.processor, 'process_text'):
                    # Use unified processor V2
                    chunk_result = self.processor.process_text(chunk)
                    
                    # Convert CitationResult objects to dictionaries
                    chunk_citations = []
                    # Handle both List[CitationResult] and dict formats
                    if isinstance(chunk_result, list):
                        # UnifiedCitationProcessorV2 returns List[CitationResult]
                        citation_results = chunk_result
                    else:
                        # Legacy processors return dict with 'results' key
                        citation_results = chunk_result.get('results', [])
                    
                    for citation_result in citation_results:
                        # Handle both CitationResult objects and dictionaries
                        if hasattr(citation_result, 'citation'):
                            # It's a CitationResult object
                            citation_dict = {
                                'citation': citation_result.citation,
                                'extracted_case_name': citation_result.extracted_case_name,
                                'extracted_date': citation_result.extracted_date,
                                'case_name': citation_result.canonical_name,  # Vue frontend expects case_name for canonical
                                'confidence': citation_result.confidence,
                                'source': citation_result.source,
                                'context': citation_result.context,
                                'canonical_name': citation_result.canonical_name,
                                'canonical_date': citation_result.canonical_date,
                                'verified': citation_result.verified,
                                'url': citation_result.url,
                                'court': citation_result.court,
                                'method': citation_result.method,
                                'parallel_citations': citation_result.parallel_citations
                            }
                        else:
                            # It's already a dictionary
                            citation_dict = {
                                'citation': citation_result.get('citation', ''),
                                'extracted_case_name': citation_result.get('extracted_case_name', citation_result.get('case_name', 'N/A')),
                                'extracted_date': citation_result.get('extracted_date', 'N/A'),
                                'confidence': citation_result.get('confidence', 0.0),
                                'source': citation_result.get('source', 'Unknown'),
                                'context': citation_result.get('context', ''),
                                'canonical_name': citation_result.get('canonical_name', 'N/A'),
                                'canonical_date': citation_result.get('canonical_date', 'N/A'),
                                'verified': citation_result.get('verified', False),
                                'case_name': citation_result.get('case_name', 'N/A'),
                                'court': citation_result.get('court', 'N/A'),
                                'url': citation_result.get('url', ''),
                                'method': citation_result.get('method', ''),
                                'parallel_citations': citation_result.get('parallel_citations', [])
                            }
                        
                        chunk_citations.append(citation_dict)
                    
                    all_citations.extend(chunk_citations)
                    # Extract case names from the results
                    for citation in chunk_citations:
                        if citation.get('extracted_case_name') and citation['extracted_case_name'] != 'N/A':
                            all_case_names.add(citation['extracted_case_name'])
                
                elif self.processor and hasattr(self.processor, 'process_document'):
                    chunk_result = self.processor.process_document(
                        content=chunk,
                        extract_case_names=True
                    )
                    
                    if chunk_result.get('success'):
                        all_citations.extend(chunk_result.get('citations', []))
                        all_case_names.update(chunk_result.get('case_names', []))
                
                elif process_document:
                    chunk_result = process_document(content=chunk, extract_case_names=True)
                    
                    if chunk_result.get('success'):
                        all_citations.extend(chunk_result.get('citations', []))
                        all_case_names.update(chunk_result.get('case_names', []))
                else:
                    self.logger.warning("No document processor available for chunk processing")
                    continue
                
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
        Always includes extracted_case_name, extracted_date, canonical_name, and canonical_date.
        """
        formatted = []
        
        for citation in citations:
            # Handle both CitationResult objects and dictionaries
            if hasattr(citation, '__dict__'):
                # It's a CitationResult object
                citation_dict = {
                    'citation': getattr(citation, 'citation', ''),
                    'verified': getattr(citation, 'verified', False),
                    'case_name': getattr(citation, 'canonical_name', 'N/A'),  # Vue frontend expects case_name for canonical
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

            # Always ensure extracted_case_name and extracted_date are present and never blank
            if not citation_dict['extracted_case_name']:
                citation_dict['extracted_case_name'] = 'N/A'
            if not citation_dict['extracted_date']:
                citation_dict['extracted_date'] = 'N/A'
            # Always ensure canonical_name and canonical_date are present
            if not citation_dict['canonical_name']:
                citation_dict['canonical_name'] = 'N/A'
            if not citation_dict['canonical_date']:
                citation_dict['canonical_date'] = 'N/A'

            # Ensure boolean values are properly formatted
            # A citation is considered verified if it has canonical data
            has_canonical_data = (
                citation_dict.get('canonical_name') and citation_dict.get('canonical_name') != 'N/A' or
                citation_dict.get('canonical_date') and citation_dict.get('canonical_date') != 'N/A' or
                citation_dict.get('url')
            )
            citation_dict['verified'] = 'true' if (citation_dict['verified'] or has_canonical_data) else 'false'
            
            # Update source field if canonical data is present but source is still "extracted_only"
            if has_canonical_data and citation_dict.get('source') == 'extracted_only':
                citation_dict['source'] = 'CourtListener'
            
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
        if UNIFIED_PROCESSOR_V2_AVAILABLE:
            return "UnifiedCitationProcessorV2"
        elif ENHANCED_PROCESSOR_AVAILABLE:
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