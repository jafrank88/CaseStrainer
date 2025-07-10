"""
Unified Document Processing Module

This module consolidates the best parts of all existing document processing implementations
and uses the new unified citation processor for consistent, high-quality results.
"""

import os
import re
import time
import logging
import unicodedata
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import PyPDF2
import docx

logger = logging.getLogger(__name__)

# Try to import the unified citation processor
try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    UNIFIED_PROCESSOR_AVAILABLE = True
except ImportError:
    UNIFIED_PROCESSOR_AVAILABLE = False
    logger.warning("Unified citation processor v2 not available")

# Try to import the enhanced processor as fallback
try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    ENHANCED_PROCESSOR_AVAILABLE = True
except ImportError:
    ENHANCED_PROCESSOR_AVAILABLE = False
    logger.warning("Enhanced citation processor not available")

class UnifiedDocumentProcessor:
    """
    Unified document processor that consolidates the best parts of all existing implementations.
    """
    
    def __init__(self):
        self.ocr_corrections = self._init_ocr_corrections()
        
        # Initialize citation processor
        if UNIFIED_PROCESSOR_AVAILABLE:
            self.citation_processor = UnifiedCitationProcessorV2()
        elif ENHANCED_PROCESSOR_AVAILABLE:
            self.citation_processor = UnifiedCitationProcessor()
        else:
            self.citation_processor = None
            logger.warning("No citation processor available")
    
    def _init_ocr_corrections(self) -> Dict[str, str]:
        """Initialize OCR correction patterns."""
        return {
            'character_corrections': {
                'feclera1': 'federal',
                'rnay': 'may',
                'ansv.v.er': 'answer',
                '1av.v.': 'law',
                'reso1v.e': 'resolve',
                'Conv.oy': 'Convoy',
                'v.v.hen': 'when',
                'v.v.': 'v.',
                '1': 'l',
                '0': 'o',
                '5': 's',
                '3': 'e',
                '7': 't',
                '8': 'b',
                '9': 'g',
                '6': 'g',
                '2': 'z',
                '4': 'a',
            },
            'word_corrections': {
                'feclera1': 'federal',
                'rnay': 'may',
                'ansv.v.er': 'answer',
                'reso1v.e': 'resolve',
                'Conv.oy': 'Convoy',
                'v.v.hen': 'when',
            }
        }
    
    def preprocess_text(self, text: str, skip_ocr_correction: bool = False) -> str:
        """
        Preprocess text with cleaning and optional OCR correction.
        
        Args:
            text: Text to preprocess
            skip_ocr_correction: Whether to skip OCR correction
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Basic cleaning
        cleaned = text.strip()
        
        # Normalize unicode
        cleaned = unicodedata.normalize('NFKC', cleaned)
        
        # Fix common encoding issues
        cleaned = cleaned.replace('\ufeff', '')  # BOM
        cleaned = cleaned.replace('\u200b', '')  # Zero-width space
        
        # Apply OCR corrections only if not skipped
        if not skip_ocr_correction:
            cleaned = self._apply_ocr_corrections(cleaned)
        
        # Final whitespace normalization
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _apply_ocr_corrections(self, text: str) -> str:
        """Apply OCR corrections to text."""
        corrected = text
        
        # Apply word-level corrections
        for error, correction in self.ocr_corrections['word_corrections'].items():
            corrected = re.sub(rf'\b{error}\b', correction, corrected, flags=re.IGNORECASE)
        
        # Apply character-level corrections in numeric contexts
        for error, correction in self.ocr_corrections['character_corrections'].items():
            # Only apply in numeric/citation contexts
            corrected = re.sub(rf'\b{error}(?=\d)', correction, corrected)
        
        return corrected
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_ext == '.docx':
                return self._extract_text_from_docx(file_path)
            elif file_ext == '.rtf':
                return self._extract_text_from_rtf(file_path)
            elif file_ext in ['.html', '.htm']:
                return self._extract_text_from_html_file(file_path)
            elif file_ext in ['.txt', '.md']:
                return self._extract_text_from_text_file(file_path)
            else:
                # Try as text file
                return self._extract_text_from_text_file(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            # Try pdfminer.six first (preferred)
            from pdfminer.high_level import extract_text
            text = extract_text(file_path)
            if text.strip():
                return text
        except ImportError:
            logger.debug("pdfminer.six not available")
        except Exception as e:
            logger.debug(f"pdfminer.six extraction failed: {e}")
        
        try:
            # Fallback to PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            raise
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            raise
    
    def _extract_text_from_rtf(self, file_path: str) -> str:
        """Extract text from RTF file."""
        try:
            import striprtf
            with open(file_path, 'r', encoding='utf-8') as file:
                rtf_content = file.read()
                text = striprtf.rtf_to_text(rtf_content)
                return text
        except ImportError:
            logger.warning("striprtf not available, trying basic RTF parsing")
            # Basic RTF parsing fallback
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Remove RTF markup
                text = re.sub(r'\\[a-z0-9-]+\d?', '', content)
                text = re.sub(r'[{}]', '', text)
                return text
        except Exception as e:
            logger.error(f"RTF extraction failed: {e}")
            raise
    
    def _extract_text_from_html_file(self, file_path: str) -> str:
        """Extract text from HTML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                soup = BeautifulSoup(content, 'html.parser')
                return soup.get_text()
        except Exception as e:
            logger.error(f"HTML extraction failed: {e}")
            raise
    
    def _extract_text_from_text_file(self, file_path: str) -> str:
        """Extract text from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Text file extraction failed: {e}")
                raise
        except Exception as e:
            logger.error(f"Text file extraction failed: {e}")
            raise
    
    def extract_text_from_url(self, url: str) -> str:
        """Extract text from URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup.get_text()
            elif 'text/plain' in content_type:
                return response.text
            else:
                # Try to parse as HTML anyway
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup.get_text()
                
        except Exception as e:
            logger.error(f"URL extraction failed: {e}")
            raise
    
    def process_document(self, 
                        content: str = None,
                        file_path: str = None,
                        url: str = None,
                        extract_case_names: bool = True,
                        debug_mode: bool = False) -> Dict[str, Any]:
        """
        Main document processing function.
        
        Args:
            content: Direct text content
            file_path: Path to file to process
            url: URL to process
            extract_case_names: Whether to extract case names
            debug_mode: Whether to enable debug mode
            
        Returns:
            Processing results dictionary
        """
        start_time = time.time()
        
        try:
            # Step 1: Determine source type and extract text
            if content:
                text = content
                source_type = 'text'
                source_name = 'direct_input'
            elif file_path:
                text = self.extract_text_from_file(file_path)
                source_type = 'file'
                source_name = os.path.basename(file_path)
            elif url:
                text = self.extract_text_from_url(url)
                source_type = 'url'
                source_name = urlparse(url).netloc
            else:
                raise ValueError("Must provide content, file_path, or url")
            
            logger.info(f"Processing {source_type}: {source_name}")
            logger.info(f"Input text length: {len(text)} characters")
            
            # Step 2: Preprocess text
            # Skip OCR correction for direct text submissions to avoid corruption
            skip_ocr = source_type == 'text'
            preprocessed_text = self.preprocess_text(text, skip_ocr_correction=skip_ocr)
            logger.info(f"Text preprocessing: {len(text)} -> {len(preprocessed_text)} characters")
            
            # Step 3: Extract citations using unified processor
            if UNIFIED_PROCESSOR_AVAILABLE:
                logger.info("Using unified citation processor v2")
                
                # Configure processor
                config = ProcessingConfig(
                    use_eyecite=True,
                    use_regex=True,
                    extract_case_names=extract_case_names,
                    extract_dates=True,
                    enable_clustering=True,
                    enable_deduplication=True,
                    debug_mode=debug_mode
                )
                
                processor = UnifiedCitationProcessorV2(config)
                citation_results = processor.process_text(preprocessed_text)
                
                # Convert CitationResult objects to dictionaries for compatibility
                formatted_citations = []
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
                        'start_index': citation.start_index,
                        'end_index': citation.end_index,
                        'error': citation.error,
                        'metadata': citation.metadata
                    }
                    formatted_citations.append(citation_dict)
                
                # Calculate statistics
                statistics = {
                    'total_citations': len(formatted_citations),
                    'unique_cases': len(set(c.get('case_name') for c in formatted_citations if c.get('case_name') and c.get('case_name') != 'N/A')),
                    'verified_citations': len([c for c in formatted_citations if c.get('verified')]),
                    'unverified_citations': len([c for c in formatted_citations if not c.get('verified')]),
                    'parallel_citations': len([c for c in formatted_citations if c.get('is_parallel')]),
                    'clusters': len([c for c in formatted_citations if c.get('is_cluster')])
                }
                
            elif ENHANCED_PROCESSOR_AVAILABLE:
                logger.info("Using enhanced citation processor")
                
                # Disable OCR correction in the processor for direct text submissions
                if source_type == 'text':
                    self.citation_processor.enable_ocr_correction(False)
                    logger.debug("Disabled OCR correction in processor for direct text submission")
                
                processing_result = self.citation_processor.process_text(preprocessed_text, extract_case_names=extract_case_names)
                
                # Re-enable OCR correction for future use
                if source_type == 'text':
                    self.citation_processor.enable_ocr_correction(True)
                    logger.debug("Re-enabled OCR correction in processor")
                
                citations = processing_result.get('results', [])
                statistics = processing_result.get('statistics')
                
                # Convert CitationResult objects to dictionaries for compatibility
                formatted_citations = []
                for citation in citations:
                    if hasattr(citation, '__dict__'):
                        # It's a CitationResult object
                        citation_dict = {
                            'citation': citation.citation,
                            'case_name': citation.case_name,
                            'extracted_case_name': citation.extracted_case_name,
                            'canonical_name': citation.canonical_name,
                            'extracted_date': citation.extracted_date,
                            'canonical_date': citation.canonical_date,
                            'verified': citation.verified,
                            'court': citation.court,
                            'confidence': citation.confidence,
                            'method': citation.method,
                            'context': citation.context,
                            'is_parallel': citation.is_parallel,
                            'parallel_citations': citation.parallel_citations,
                            'url': citation.url,
                            'source': citation.source
                        }
                    else:
                        # It's already a dictionary
                        citation_dict = citation
                    
                    formatted_citations.append(citation_dict)
                
            else:
                logger.warning("No citation processor available")
                formatted_citations = []
                statistics = {'total_citations': 0}
            
            # Step 4: Extract case names
            case_names = []
            if extract_case_names:
                case_names = self._extract_case_names(formatted_citations, preprocessed_text)
            
            # Step 5: Apply verification if available
            if hasattr(self, 'verify_citations'):
                logger.info("Applying citation verification")
                formatted_citations = self.verify_citations(formatted_citations, preprocessed_text)
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "text_length": len(text),
                "processed_text_length": len(preprocessed_text),
                "source_type": source_type,
                "source_name": source_name,
                "citations": formatted_citations,
                "case_names": case_names,
                "statistics": statistics,
                "processing_time": processing_time,
                "ocr_corrections_applied": len(text) != len(preprocessed_text),
                "processor_used": "unified_processor_v2" if UNIFIED_PROCESSOR_AVAILABLE else "enhanced_processor" if ENHANCED_PROCESSOR_AVAILABLE else "none"
            }
            
            logger.info(f"✅ Document processing completed in {processing_time:.2f}s")
            logger.info(f"   Found {len(formatted_citations)} citations, {len(case_names)} case names")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "citations": [],
                "case_names": [],
                "processing_time": time.time() - start_time
            }
    
    def _extract_case_names(self, citations: List[Dict], text: str) -> List[str]:
        """Extract unique case names from citations and text."""
        case_names = set()
        
        # Extract from citations
        for citation in citations:
            for field in ['case_name', 'extracted_case_name', 'canonical_name']:
                name = citation.get(field)
                if name and name != "N/A" and len(name) > 3:
                    case_names.add(name)
        
        return list(case_names)

# Convenience functions for backward compatibility
def process_document(content: str = None, file_path: str = None, url: str = None, 
                    extract_case_names: bool = True, debug_mode: bool = False) -> Dict[str, Any]:
    """Convenience function for document processing."""
    processor = UnifiedDocumentProcessor()
    return processor.process_document(content, file_path, url, extract_case_names, debug_mode)

def extract_text_from_file(file_path: str) -> str:
    """Convenience function for text extraction from file."""
    processor = UnifiedDocumentProcessor()
    return processor.extract_text_from_file(file_path)

def extract_text_from_url(url: str) -> str:
    """Convenience function for text extraction from URL."""
    processor = UnifiedDocumentProcessor()
    return processor.extract_text_from_url(url) 