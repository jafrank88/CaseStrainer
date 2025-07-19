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
from typing import Dict, Any, List, Optional, Tuple, Union, TYPE_CHECKING
from datetime import datetime

# Import configuration
from src.config import get_citation_config, get_external_api_config, get_file_config

# Import processors
try:
    from ...unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig, CitationResult
    UNIFIED_PROCESSOR_V2_AVAILABLE = True
    logging.info("UnifiedCitationProcessorV2 available")
except ImportError:
    try:
        # Try absolute import as fallback
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig, CitationResult
        UNIFIED_PROCESSOR_V2_AVAILABLE = True
        logging.info("UnifiedCitationProcessorV2 available via absolute import")
    except ImportError:
        UNIFIED_PROCESSOR_V2_AVAILABLE = False
        CitationResult = None
        logging.warning("UnifiedCitationProcessorV2 not available")

# Type annotations for type checking
if TYPE_CHECKING:
    from ...unified_citation_processor_v2 import CitationResult as CitationResultType
else:
    CitationResultType = Any

# Legacy enhanced processor (deprecated - removed)
ENHANCED_PROCESSOR_AVAILABLE = False
enhanced_processor = None

# Try to import the new unified document processor
try:
    from src.document_processing_unified import process_document
    UNIFIED_DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError:
    UNIFIED_DOCUMENT_PROCESSOR_AVAILABLE = False
    process_document = None
    logging.warning("Unified document processor not available")

# Use the faster pdf_handler for PDF extraction
try:
    from src.document_processing_unified import extract_text_from_file
    PDF_HANDLER_AVAILABLE = True
    logging.info("PDF handler available for fast PDF extraction")
except ImportError:
    PDF_HANDLER_AVAILABLE = False
    logging.warning("PDF handler not available, falling back to document_processing_unified")

from src.document_processing_unified import extract_text_from_url

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
        
        # Debug: Log processor availability
        self.logger.info(f"UNIFIED_PROCESSOR_V2_AVAILABLE: {UNIFIED_PROCESSOR_V2_AVAILABLE}")
        self.logger.info(f"ENHANCED_PROCESSOR_AVAILABLE: {ENHANCED_PROCESSOR_AVAILABLE}")
        self.logger.info(f"UNIFIED_PROCESSOR_AVAILABLE: {UNIFIED_DOCUMENT_PROCESSOR_AVAILABLE}")
        
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
                enable_verification=True,  # <--- FORCE VERIFICATION ENABLED
                debug_mode=True,
                min_confidence=0.0  # Force all citations to be included
            )
            self.logger.info(f"Using UnifiedCitationProcessorV2 with config: {config}")
            self.processor = UnifiedCitationProcessorV2(config)
            self.logger.info("Using UnifiedCitationProcessorV2 (FORCED enable_verification=True)")
            self.logger.info("Successfully created UnifiedCitationProcessorV2 instance")
        elif ENHANCED_PROCESSOR_AVAILABLE:
            self.logger.info("Using enhanced document processor (fallback)")
            self.processor = enhanced_processor
            self.logger.info("Using enhanced document processor (fallback)")
        elif UNIFIED_DOCUMENT_PROCESSOR_AVAILABLE:
            self.logger.info("Using unified citation processor (fallback)")
            self.processor = process_document
            self.logger.info("Using unified citation processor (fallback)")
        else:
            self.logger.warning("No advanced processors available - using fallback methods")
            self.processor = None
            self.logger.warning("No advanced processors available - using fallback methods")
        
        self.logger.info(f"Final processor type: {type(self.processor)}")
        if self.processor:
            self.logger.info(f"Processor methods: {[method for method in dir(self.processor) if not method.startswith('_')]}")
    
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
        
        # Get thresholds from configuration - increased for better performance
        max_length = self.citation_config.get('immediate_max_length', 500)  # Increased to handle standard test text
        max_words = self.citation_config.get('immediate_max_words', 50)     # Increased to handle standard test text
        
        # Quick checks for immediate processing
        is_short = len(text) < max_length
        has_numbers = any(char.isdigit() for char in text)
        # More flexible citation pattern matching
        text_upper = text.upper()
        has_citation_patterns = any(
            pattern in text_upper 
            for pattern in [
                'U.S.', 'F.', 'F.2D', 'F.3D', 'F.2d', 'F.3d', 'S.CT.', 'L.ED.', 
                'P.2D', 'P.3D', 'P.2d', 'P.3d', 'A.2D', 'A.3D', 'A.2d', 'A.3d',
                'WN.2D', 'WN.APP.', 'WN.2d', 'WN.APP', 'WASH.2D', 'WASH.APP.',
                'WASH.2d', 'WASH.APP'
            ]
        )
        is_few_words = len(text.split()) <= max_words
        
        # TEMPORARY: Force immediate processing for all text inputs to fix timeout issue
        should_process = True  # Force immediate processing for all text
        
        self.logger.info(f"Immediate processing decision: {should_process} "
                        f"(short={is_short}, numbers={has_numbers}, "
                        f"patterns={has_citation_patterns}, few_words={is_few_words}, "
                        f"max_length={max_length}, max_words={max_words}, "
                        f"text_length={len(text)}, word_count={len(text.split())})")
        
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
                # Use unified processor V2 with fast processing (no verification for immediate processing)
                # Create a fast config for immediate processing
                fast_config = ProcessingConfig(
                    use_eyecite=True,
                    use_regex=True,
                    extract_case_names=True,
                    extract_dates=True,
                    enable_clustering=True,
                    enable_deduplication=True,
                    enable_verification=True,  # Enable verification to get canonical names
                    debug_mode=False,
                    min_confidence=0.0
                )
                self.logger.info(f"[DEBUG] Fast config enable_verification: {fast_config.enable_verification}")
                fast_processor = UnifiedCitationProcessorV2(fast_config)
                self.logger.info(f"[DEBUG] Fast processor config enable_verification: {fast_processor.config.enable_verification}")
                self.logger.info(f"[DEBUG] Fast processor id: {id(fast_processor)}")
                self.logger.info(f"[DEBUG] Fast processor type: {type(fast_processor)}")
                self.logger.info(f"[DEBUG] About to call fast_processor.process_text")
                citation_results = fast_processor.process_text(text)
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
                            'canonical_name': citation_result.canonical_name,  # Vue frontend expects case_name for canonical
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
                    
                    # Generate clusters from citations
                    clusters = self.processor.group_citations_into_clusters(citation_results) if hasattr(self.processor, 'group_citations_into_clusters') else []
                    
                    self.logger.info(f"[DEBUG] {len(citations)} citations after conversion to dict.")
                    # Calculate statistics
                    statistics = self._calculate_statistics(citations)
                    # Add unified processor metadata if available
                    metadata = {}
                
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
                clusters = []
                
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
                clusters = result.get('clusters', [])
                statistics = result.get('statistics', {})
            
            # Format citations for frontend (always apply formatting for verification logic)
            if self.processor and hasattr(self.processor, 'process_text'):
                # Unified processor returns dictionaries, but we still need to apply formatting logic
                formatted_citations = self._format_citations_for_frontend(citations, clusters)
                self.logger.info(f"[DEBUG] {len(formatted_citations)} citations after formatting.")
                # Use statistics from unified processor if available
                if not statistics:
                    statistics = self._calculate_statistics(formatted_citations)
            else:
                # Format citations for other processors
                formatted_citations = self._format_citations_for_frontend(citations, clusters)
                self.logger.info(f"[DEBUG] {len(formatted_citations)} citations after formatting.")
                # Calculate statistics
                statistics = self._calculate_statistics(formatted_citations)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"Immediate processing completed in {processing_time:.2f}s: "
                           f"{len(formatted_citations)} citations found")
            
            # Prepare metadata
            if 'metadata' not in locals() or not metadata:
                metadata = {
                    'processing_type': 'immediate',
                    'text_length': len(text),
                    'processing_time': processing_time,
                    'processor_used': self._get_processor_name()
                }
            
            return {
                'status': 'completed',
                'citations': formatted_citations,
                'clusters': clusters,  # Include clusters in response
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
        self.logger.info(f"[DEBUG process_citation_task] Starting citation task {task_id} (type: {task_type})")
        start_time = time.time()
        
        try:
            text = None
            metadata = {}
            
            # Extract text based on task type
            self.logger.info(f"[DEBUG process_citation_task] Processing task type: {task_type}")
            if task_type == 'text':
                self.logger.info(f"[DEBUG process_citation_task] Processing text input")
                text = task_data.get('text', '')
                metadata = {
                    'text_length': len(text),
                    'source_type': task_data.get('source_type', 'text'),
                    'filename': task_data.get('filename', 'unknown'),
                    'file_ext': task_data.get('file_ext', '')
                }
                self.logger.info(f"[DEBUG process_citation_task] Text input length: {len(text)}")
            elif task_type == 'file':
                self.logger.info(f"[DEBUG process_citation_task] Processing file input")
                text, metadata = self._process_file_task(task_data)
                self.logger.info(f"[DEBUG process_citation_task] File processing completed. Text length: {len(text) if text else 0}")
            elif task_type == 'url':
                self.logger.info(f"[DEBUG process_citation_task] Calling _process_url_task")
                text, metadata = self._process_url_task(task_data)
                self.logger.info(f"[DEBUG process_citation_task] URL processing completed. Text length: {len(text) if text else 0}")
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            if not text or not text.strip():
                self.logger.warning(f"[DEBUG process_citation_task] No text content extracted for task {task_id}")
                return {
                    'status': 'failed',
                    'error': 'No text content extracted',
                    'citations': [],
                    'case_names': []
                }
            
            self.logger.info(f"[DEBUG process_citation_task] Starting text processing in chunks for task {task_id}")
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
            
            citations_count = len(result.get('citations', []))
            self.logger.info(f"[DEBUG process_citation_task] Task {task_id} completed successfully: {citations_count} citations found")
            self.logger.info(f"[DEBUG process_citation_task] Returning result for task {task_id}")
            
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
            # No file cleanup needed since PDF extraction happens in API endpoint
            pass
    
    def _process_file_task(self, task_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Process file upload task."""
        file_path = task_data.get('file_path')
        filename = task_data.get('filename', 'unknown')
        file_ext = task_data.get('file_ext', '')
        
        self.logger.info(f"[DEBUG _process_file_task] Starting file processing for: {filename}")
        self.logger.info(f"[DEBUG _process_file_task] File path: {file_path}")
        self.logger.info(f"[DEBUG _process_file_task] File exists: {os.path.exists(file_path) if file_path else False}")
        
        if not file_path or not os.path.exists(file_path):
            self.logger.error(f"[DEBUG _process_file_task] File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Extract text from file using the unified document processor only
            self.logger.info(f"[DEBUG _process_file_task] Starting text extraction from: {file_path}")
            
            # Add timeout for text extraction to prevent hanging
            import signal
            import threading
            import time
            
            text_result = None
            extraction_error = None
            
            def extract_with_timeout():
                nonlocal text_result, extraction_error
                try:
                    # Use the faster pdf_handler for PDF files
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext == '.pdf' and PDF_HANDLER_AVAILABLE:
                        self.logger.info(f"[DEBUG _process_file_task] Using fast PDF handler for: {file_path}")
                        text_result = extract_text_from_file(file_path)
                    else:
                        # Fallback to document_processing_unified for non-PDF files
                        # Use the already imported extract_text_from_file from the top of the file
                        text_result = extract_text_from_file(file_path)
                except Exception as e:
                    extraction_error = e
            
            # Run extraction in a thread with timeout
            extraction_thread = threading.Thread(target=extract_with_timeout)
            extraction_thread.daemon = True
            extraction_thread.start()
            
            # OPTIMIZATION: Reduced timeout for faster failure detection
            extraction_thread.join(timeout=20)  # Reduced from 30 to 20 seconds
            
            if extraction_thread.is_alive():
                self.logger.error(f"[DEBUG _process_file_task] Text extraction timed out after 20 seconds")
                raise TimeoutError("Text extraction timed out after 20 seconds")
            
            if extraction_error:
                raise extraction_error
            
            self.logger.info(f"[DEBUG _process_file_task] Text extraction completed. Length: {len(text_result)}")
            self.logger.info(f"[DEBUG _process_file_task] Text sample (first 500 chars): {text_result[:500]}")
            
            if not text_result or not text_result.strip():
                self.logger.warning(f"[DEBUG _process_file_task] Extracted text is empty or whitespace only")
            else:
                self.logger.info(f"[DEBUG _process_file_task] Text extraction successful, returning text")
            
            return text_result, {}
            
        except Exception as e:
            self.logger.error(f"[DEBUG _process_file_task] Error during text extraction: {e}", exc_info=True)
            raise

    def _process_url_task(self, task_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Process URL task."""
        url = task_data.get('url')
        self.logger.info(f"Processing URL: {url}")
        if not url:
            raise ValueError("No URL provided")
        # Extract text from URL using the unified document processor only
        text = extract_text_from_url(url)
        return text, {}
    
    def _process_text_in_chunks(self, text: str, task_id: str = None) -> Dict[str, Any]:
        """
        Process large text in chunks to handle memory efficiently.
        OPTIMIZED: Added intelligent chunking, early termination, and parallel processing.
        """
        # OPTIMIZATION: Use larger chunks for better performance
        chunk_size = self.citation_config.get('chunk_size', 10000)  # Increased from 5000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        total_chunks = len(chunks)
        
        self.logger.info(f"Processing text in {total_chunks} chunks (optimized chunk size: {chunk_size})")
        
        all_citations = []
        all_case_names = set()
        
        # OPTIMIZATION: Process chunks in parallel for better performance
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        # Thread-safe collections
        citations_lock = threading.Lock()
        case_names_lock = threading.Lock()
        
        def process_chunk(chunk_data):
            idx, chunk = chunk_data
            chunk_citations = []
            chunk_case_names = set()
            
            try:
                # OPTIMIZATION: Early termination for empty or very short chunks
                if len(chunk.strip()) < 50:
                    return chunk_citations, chunk_case_names
                
                # Process chunk - use sync processing for production stability
                if self.processor and hasattr(self.processor, 'process_text'):
                    # Use unified processor V2 sync method for chunks
                    chunk_result = self.processor.process_text(chunk)
                    
                    # Convert CitationResult objects to dictionaries
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
                                'extracted_case_name': citation_result.extracted_case_name or 'N/A',
                                'extracted_date': citation_result.extracted_date or 'N/A',
                                'canonical_name': citation_result.canonical_name or 'N/A',
                                'confidence': citation_result.confidence,
                                'source': citation_result.source,
                                'context': citation_result.context,
                                'verified': citation_result.verified,
                                'url': getattr(citation_result, 'url', ''),
                                'parallel_citations': getattr(citation_result, 'parallel_citations', []),
                                'court': getattr(citation_result, 'court', 'N/A'),
                                'canonical_date': getattr(citation_result, 'canonical_date', 'N/A'),
                                'metadata': getattr(citation_result, 'metadata', {})
                            }
                        else:
                            # It's already a dictionary
                            citation_dict = {
                                'citation': citation_result.get('citation', ''),
                                'extracted_case_name': citation_result.get('extracted_case_name', 'N/A'),
                                'extracted_date': citation_result.get('extracted_date', 'N/A'),
                                'canonical_name': citation_result.get('canonical_name', 'N/A'),
                                'confidence': citation_result.get('confidence', 0.0),
                                'source': citation_result.get('source', 'Unknown'),
                                'context': citation_result.get('context', ''),
                                'verified': citation_result.get('verified', False),
                                'url': citation_result.get('url', ''),
                                'parallel_citations': citation_result.get('parallel_citations', []),
                                'court': citation_result.get('court', 'N/A'),
                                'canonical_date': citation_result.get('canonical_date', 'N/A'),
                                'metadata': citation_result.get('metadata', {})
                            }
                        
                        chunk_citations.append(citation_dict)
                        
                        # Extract case names
                        case_name = citation_dict.get('canonical_name') or citation_dict.get('extracted_case_name')
                        if case_name and case_name != 'N/A':
                            chunk_case_names.add(case_name)
                    
                    self.logger.debug(f"[DEBUG] Citations found in chunk {idx+1}: {len(chunk_citations)}")
                    if chunk_citations:
                        self.logger.debug(f"[DEBUG] First 3 citations in chunk {idx+1}: {[c['citation'] for c in chunk_citations[:3]]}")
                
                elif self.processor and hasattr(self.processor, 'process_document'):
                    chunk_result = self.processor.process_document(
                        content=chunk,
                        extract_case_names=True
                    )
                    
                    if chunk_result.get('success'):
                        chunk_citations.extend(chunk_result.get('citations', []))
                        chunk_case_names.update(chunk_result.get('case_names', []))
                
                elif process_document:
                    chunk_result = process_document(content=chunk, extract_case_names=True)
                    
                    if chunk_result.get('success'):
                        chunk_citations.extend(chunk_result.get('citations', []))
                        chunk_case_names.update(chunk_result.get('case_names', []))
                else:
                    self.logger.warning("No document processor available for chunk processing")
                
                # Log progress
                progress = int(((idx + 1) / total_chunks) * 100)
                self.logger.debug(f"Chunk {idx + 1}/{total_chunks} processed ({progress}%)")
                
            except Exception as e:
                self.logger.warning(f"Error processing chunk {idx + 1}: {e}")
            
            return chunk_citations, chunk_case_names
        
        # OPTIMIZATION: Use ThreadPoolExecutor for parallel processing
        max_workers = min(4, total_chunks)  # Limit to 4 workers to avoid overwhelming the system
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(process_chunk, (idx, chunk)): idx 
                for idx, chunk in enumerate(chunks)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    chunk_citations, chunk_case_names = future.result()
                    
                    # Thread-safe addition to shared collections
                    with citations_lock:
                        all_citations.extend(chunk_citations)
                    with case_names_lock:
                        all_case_names.update(chunk_case_names)
                        
                except Exception as e:
                    self.logger.error(f"Error processing chunk {chunk_idx + 1}: {e}")
        
        # OPTIMIZATION: Early termination if no citations found
        if not all_citations:
            self.logger.info("No citations found in any chunk, returning early")
            return {
                'status': 'success',
                'citations': [],
                'clusters': [],
                'case_names': [],
                'statistics': {'total_citations': 0},
                'summary': {'total_citations': 0}
            }
        
        # Deduplicate citations
        deduplicated_citations = self._deduplicate_citations(all_citations)
        
        # OPTIMIZATION: Skip clustering if few citations (performance improvement)
        all_clusters = []
        if len(deduplicated_citations) > 5 and self.processor and hasattr(self.processor, 'group_citations_into_clusters'):
            try:
                # Convert deduplicated citations to proper CitationResult objects for clustering
                citation_objects = []
                for citation_dict in deduplicated_citations:
                    # Create a proper CitationResult object with all required attributes
                    class CitationResultObject:
                        def __init__(self, data):
                            self.citation = data.get('citation', '')
                            self.extracted_case_name = data.get('extracted_case_name', 'N/A')
                            self.extracted_date = data.get('extracted_date', 'N/A')
                            self.canonical_name = data.get('canonical_name', 'N/A')
                            self.canonical_date = data.get('canonical_date', 'N/A')
                            self.verified = data.get('verified', False)
                            self.url = data.get('url', '')
                            self.court = data.get('court', 'N/A')
                            self.confidence = data.get('confidence', 0.0)
                            self.method = data.get('method', '')
                            self.pattern = data.get('pattern', '')
                            self.context = data.get('context', '')
                            self.start_index = data.get('start_index', None)
                            self.end_index = data.get('end_index', None)
                            self.is_parallel = data.get('is_parallel', False)
                            self.is_cluster = data.get('is_cluster', False)
                            self.parallel_citations = data.get('parallel_citations', [])
                            self.cluster_members = data.get('cluster_members', [])
                            self.pinpoint_pages = data.get('pinpoint_pages', [])
                            self.docket_numbers = data.get('docket_numbers', [])
                            self.case_history = data.get('case_history', [])
                            self.publication_status = data.get('publication_status', '')
                            self.source = data.get('source', 'Unknown')
                            self.error = data.get('error', '')
                            # Preserve the original metadata from the processor (including cluster info)
                            self.metadata = data.get('metadata', {})
                    
                    citation_objects.append(CitationResultObject(citation_dict))
                
                # Apply clustering to all citations
                # Pass the original text if available for better clustering
                all_clusters = self.processor.group_citations_into_clusters(citation_objects, original_text=text)
                self.logger.info(f"Applied clustering to {len(deduplicated_citations)} citations, created {len(all_clusters)} clusters")
                
            except Exception as e:
                self.logger.warning(f"Error applying clustering to all citations: {e}")
                all_clusters = []
        else:
            self.logger.info(f"Skipping clustering for {len(deduplicated_citations)} citations (optimization)")
        
        # Format citations for frontend with cluster metadata
        try:
            self.logger.debug(f"[DEBUG] About to call _format_citations_for_frontend with {len(deduplicated_citations)} citations and {len(all_clusters)} clusters")
            formatted_citations = self._format_citations_for_frontend(deduplicated_citations, all_clusters)
            self.logger.debug(f"[DEBUG] _format_citations_for_frontend returned {len(formatted_citations)} formatted citations")
        except Exception as e:
            self.logger.error(f"[DEBUG] Error in _format_citations_for_frontend: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: return citations without formatting
            formatted_citations = deduplicated_citations
        
        # Calculate statistics
        statistics = self._calculate_statistics(formatted_citations)
        
        return {
            'status': 'success',
            'citations': formatted_citations,
            'clusters': all_clusters,  # Include clusters in response
            'case_names': list(all_case_names),
            'statistics': statistics,
            'summary': statistics  # For backward compatibility
        }
    
    def _format_citations_for_frontend(self, citations: List[Union[CitationResultType, Dict[str, Any]]], clusters: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Format citations for frontend consumption.
        Always includes extracted_case_name, extracted_date, canonical_name, and canonical_date.
        Adds cluster metadata to each citation if clusters are provided.
        """
        self.logger.info(f"[DEBUG] _format_citations_for_frontend called with {len(citations)} citations and {len(clusters) if clusters else 0} clusters")
        formatted_citations = []
        
        # Create a mapping from normalized citation text to cluster info
        citation_to_cluster = {}
        cluster_norm_keys = []
        if clusters:
            for cluster in clusters:
                cluster_id = cluster.get('cluster_id', 'unknown')
                cluster_size = len(cluster.get('citations', []))
                cluster_members = [c.get('citation', '') for c in cluster.get('citations', [])]
                cluster_metadata = {
                    'is_in_cluster': True,
                    'cluster_id': cluster_id,
                    'cluster_size': cluster_size,
                    'cluster_members': cluster_members,
                    'canonical_name': cluster.get('canonical_name'),
                    'canonical_date': cluster.get('canonical_date'),
                    'extracted_case_name': cluster.get('extracted_case_name'),
                    'extracted_date': cluster.get('extracted_date'),
                    'url': cluster.get('url'),
                    'source': cluster.get('source')
                }
                for citation in cluster.get('citations', []):
                    citation_text = citation.get('citation', '')
                    if citation_text:
                        normalized_text = self._normalize_citation_for_matching(citation_text)
                        citation_to_cluster[normalized_text] = cluster_metadata
                        cluster_norm_keys.append(normalized_text)
        self.logger.info(f"[DEBUG] Cluster normalized keys: {cluster_norm_keys}")
        main_norm_keys = []
        for citation in citations:
            if hasattr(citation, 'citation'):
                citation_text = citation.citation
            else:
                citation_text = citation.get('citation', '')
            normalized_citation_text = self._normalize_citation_for_matching(citation_text) if citation_text else ''
            main_norm_keys.append(normalized_citation_text)
        self.logger.info(f"[DEBUG] Main citation normalized keys: {main_norm_keys}")
        for citation in citations:
            if hasattr(citation, 'citation'):
                citation_text = citation.citation
            else:
                citation_text = citation.get('citation', '')
            normalized_citation_text = self._normalize_citation_for_matching(citation_text) if citation_text else ''
            # Try exact match by normalized text
            cluster_metadata = citation_to_cluster.get(normalized_citation_text)
            # Fallback to partial/robust match if needed
            if not cluster_metadata:
                for cluster_text, metadata in citation_to_cluster.items():
                    if (normalized_citation_text in cluster_text or 
                        cluster_text in normalized_citation_text):
                        cluster_metadata = metadata
                        break
            # Build citation_dict as before
            if hasattr(citation, 'citation'):
                citation_dict = {
                    'citation': citation.citation,
                    'verified': citation.verified,
                    'extracted_case_name': getattr(citation, 'extracted_case_name', 'N/A'),
                    'canonical_name': getattr(citation, 'canonical_name', 'N/A'),
                    'extracted_date': getattr(citation, 'extracted_date', 'N/A'),
                    'canonical_date': getattr(citation, 'canonical_date', 'N/A'),
                    'court': getattr(citation, 'court', 'N/A'),
                    'confidence': citation.confidence,
                    'source': citation.source,
                    'url': getattr(citation, 'url', ''),
                    'parallel_citations': getattr(citation, 'parallel_citations', []),
                    'context': getattr(citation, 'context', '')
                }
            else:
                citation_dict = {
                    'citation': citation.get('citation', ''),
                    'verified': citation.get('verified', False),
                    'extracted_case_name': citation.get('extracted_case_name', 'N/A'),
                    'canonical_name': citation.get('canonical_name', 'N/A'),
                    'extracted_date': citation.get('extracted_date', 'N/A'),
                    'canonical_date': citation.get('canonical_date', 'N/A'),
                    'court': citation.get('court', 'N/A'),
                    'confidence': citation.get('confidence', 0.0),
                    'source': citation.get('source', 'Unknown'),
                    'url': citation.get('url', ''),
                    'parallel_citations': citation.get('parallel_citations', []),
                    'context': citation.get('context', '')
                }
            # Always ensure extracted_case_name and extracted_date are present and never blank
            if not citation_dict['extracted_case_name']:
                citation_dict['extracted_case_name'] = 'N/A'
            if not citation_dict['extracted_date']:
                citation_dict['extracted_date'] = 'N/A'
            # Add cluster metadata if available
            if cluster_metadata:
                citation_dict['metadata'] = cluster_metadata
            else:
                citation_dict['metadata'] = {
                    'is_in_cluster': False,
                    'cluster_id': None,
                    'cluster_size': 0,
                    'cluster_members': []
                }
            formatted_citations.append(citation_dict)
        return formatted_citations
    
    def _normalize_citation_for_matching(self, citation_text: str) -> str:
        """Normalize citation text for matching by removing common variations."""
        if not citation_text:
            return ""
        
        # Remove extra whitespace and newlines
        normalized = ' '.join(citation_text.split())
        
        # Remove common variations in spacing
        normalized = normalized.replace('  ', ' ')
        
        # Normalize common reporter abbreviations
        normalized = normalized.replace('Wn.2d', 'Wn.2d')
        normalized = normalized.replace('Wn. App.', 'Wn.App.')
        normalized = normalized.replace('P.3d', 'P.3d')
        normalized = normalized.replace('P.2d', 'P.2d')
        
        return normalized.strip()
    
    def _calculate_statistics(self, citations: List[Dict]) -> Dict[str, int]:
        """Calculate citation statistics."""
        total = len(citations)
        verified = sum(1 for c in citations if c.get('verified') == 'true' or c.get('verified') is True)
        unverified = total - verified
        parallel = sum(1 for c in citations if c.get('parallel_citations'))
        
        # Count unique case names
        unique_cases = set()
        for c in citations:
            case_name = c.get('canonical_name') or c.get('extracted_case_name')
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
        elif UNIFIED_DOCUMENT_PROCESSOR_AVAILABLE:
            return "unified_processor"
        else:
            return "fallback_processor"

# ============================================================================
# Testing the extracted service
# ============================================================================

def test_citation_service():
    """Test the extracted citation service."""
    import logging
    logger = logging.getLogger(__name__)
    
    service = CitationService()
    
    # Test immediate processing
    test_input = {
        'type': 'text',
        'text': '123 Wn.2d 456'
    }
    
    should_immediate = service.should_process_immediately(test_input)
    logger.info(f"Should process immediately: {should_immediate}")
    
    if should_immediate:
        result = service.process_immediately(test_input)
        logger.info(f"Immediate result: {result['status']}")
        logger.info(f"Citations found: {len(result.get('citations', []))}")
    
    # Test async processing
    task_result = service.process_citation_task('test-task', 'text', test_input)
    logger.info(f"Async result: {task_result['status']}")
    logger.info(f"Citations found: {len(task_result.get('citations', []))}")

if __name__ == "__main__":
    test_citation_service() 