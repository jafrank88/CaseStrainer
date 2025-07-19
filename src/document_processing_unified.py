"""
Unified Document Processing Module - FIXED VERSION

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
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# Try to import the unified citation processor
try:
    from .unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    UNIFIED_PROCESSOR_AVAILABLE = True
except ImportError:
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        UNIFIED_PROCESSOR_AVAILABLE = True
    except ImportError:
        UNIFIED_PROCESSOR_AVAILABLE = False
        logger.warning("Unified citation processor v2 not available")

# Try to import the enhanced processor as fallback
try:
    from .unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    ENHANCED_PROCESSOR_AVAILABLE = True
except ImportError:
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        ENHANCED_PROCESSOR_AVAILABLE = True
    except ImportError:
        try:
            # Try alternative import path
            from enhanced_citation_processor import EnhancedCitationProcessor as UnifiedCitationProcessor
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
        """Apply OCR corrections to text, being very conservative to avoid corrupting citations."""
        corrected = text
        
        # Apply word-level corrections (these are generally safe)
        for error, correction in self.ocr_corrections['word_corrections'].items():
            corrected = re.sub(rf'\b{error}\b', correction, corrected, flags=re.IGNORECASE)
        
        # Apply character-level corrections very conservatively
        # Only apply corrections that are unlikely to affect citations
        safe_corrections = {
            'feclera1': 'federal',
            'rnay': 'may', 
            'ansv.v.er': 'answer',
            '1av.v.': 'law',
            'reso1v.e': 'resolve',
            'Conv.oy': 'Convoy',
            'v.v.hen': 'when',
            'v.v.': 'v.',
            # Only include character corrections that are very unlikely to affect citations
            'rn': 'm',  # rn to m (rare in citations)
            'vv': 'w',  # vv to w (rare in citations)
            'cl': 'd',  # cl to d (rare in citations)
        }
        
        for error, correction in safe_corrections.items():
            # Only apply if the error is not part of a citation pattern
            # Use negative lookahead to avoid citation contexts
            pattern = rf'\b{error}(?=\d)(?!\s*(?:U\.?S\.?|S\.?Ct\.?|L\.?Ed\.?|F\.?|P\.?|Wn\.?|Wash\.?))'
            corrected = re.sub(pattern, correction, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text to improve citation detection."""
        if not text:
            return ""
        try:
            # Remove non-printable characters but preserve citation patterns
            text = "".join(
                char for char in text if char.isprintable() or char in ".,;:()[]{}"
            )
            # Fix common OCR errors in citations - be very conservative
            text = re.sub(
                r"(\d+)\s*[Uu]\.\s*[Ss]\.\s*(\d+)", r"\1 U.S. \2", text)
            text = re.sub(
                r"(\d+)\s*[Ss]\.\s*[Cc][Tt]\.\s*(\d+)", r"\1 S.Ct. \2", text)
            text = re.sub(
                r"(\d+)\s*[Ll]\.\s*[Ee][Dd]\.\s*(\d+)", r"\1 L.Ed. \2", text)
            text = re.sub(
                r"(\d+)\s*[Ff]\.\s*(2[Dd]|3[Dd]|4[Tt][Hh])?\s*(\d+)", r"\1 F.\2 \3", text)
            # Fix line breaks within citations
            text = re.sub(r"(\d+)\s*U\.\s*S\.\s*\n\s*(\d+)", r"\1 U.S. \2", text)
            text = re.sub(r"(\d+)\s*S\.\s*Ct\.\s*\n\s*(\d+)", r"\1 S.Ct. \2", text)
            text = re.sub(r"(\d+)\s*L\.\s*Ed\.\s*\n\s*(\d+)", r"\1 L.Ed. \2", text)
            text = re.sub(r"(\d+)\s*F\.\s*(2d|3d|4th)?\s*\n\s*(\d+)", r"\1 F.\2 \3", text)
            # Fix page breaks within citations
            text = re.sub(r"(\d+)\s*U\.\s*S\.\s*-\s*(\d+)", r"\1 U.S. \2", text)
            text = re.sub(r"(\d+)\s*S\.\s*Ct\.\s*-\s*(\d+)", r"\1 S.Ct. \2", text)
            text = re.sub(r"(\d+)\s*L\.\s*Ed\.\s*-\s*(\d+)", r"\1 L.Ed. \2", text)
            text = re.sub(r"(\d+)\s*F\.\s*(2d|3d|4th)?\s*-\s*(\d+)", r"\1 F.\2 \3", text)
            
            # REMOVED: Problematic OCR corrections that corrupt citations
            # text = re.sub(r"[Oo](\d)", r"0\1", text)  # O to 0
            # text = re.sub(r"(\d)[Oo]", r"\g<1>0", text)  # O to 0
            # text = re.sub(r"[lI](\d)", r"1\1", text)  # l/I to 1
            # text = re.sub(r"(\d)[lI]", r"\g<1>1", text)  # l/I to 1
            
            # Fix spacing in abbreviations
            text = re.sub(r"([A-Z])\.\s+([A-Z])", r"\1.\2", text)
            # Normalize whitespace
            text = re.sub(r"\s+", " ", text)
            # Remove page numbers/headers/footers
            text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
            return text.strip()
        except Exception as e:
            logger.error(f"Error in clean_extracted_text: {e}")
            return text.strip()

    def preprocess_pdf_text(self, text: str) -> str:
        """Preprocess PDF text for better citation extraction."""
        if not text:
            return ""
        lines = text.splitlines()
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove standalone page numbers
            if re.match(r'^\d{1,3}$', line):
                continue
            # Remove very short all-uppercase lines (1-3 chars)
            if len(line) <= 3 and line.isupper():
                continue
            filtered_lines.append(line)
        text = " ".join(filtered_lines)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def convert_pdf_to_markdown(self, pdf_path: str) -> str:
        """Convert a PDF file to markdown format using pdf2md or pdfminer as fallback."""
        # Try pdf2md command line tool
        try:
            result = None
            with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp_file:
                temp_path = temp_file.name
            try:
                proc = subprocess.run(
                    ['pdf2md', '-o', temp_path, pdf_path],
                    capture_output=True,
                    text=True
                )
                if proc.returncode == 0 and os.path.exists(temp_path):
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return content
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"pdf2md command failed: {str(e)}")
        # Fallback to pdfminer with basic markdown formatting
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract_text
            text = pdfminer_extract_text(pdf_path)
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            return '\n\n'.join(paragraphs)
        except Exception as e:
            logger.warning(f"pdfminer fallback failed: {str(e)}")
        return None

    def _extract_text_from_pdf(self, file_path: str, convert_to_md: bool = False) -> str:
        """Extract text from PDF file with robust fallbacks and cleaning."""
        import PyPDF2
        import re
        import logging
        import os
        import time
        logger = logging.getLogger(__name__)
        start_time = time.time()
        file_size = os.path.getsize(file_path)
        logger.info(f"Extracting text from PDF: {file_path} ({file_size} bytes)")
        # Optionally convert to markdown
        if convert_to_md:
            md = self.convert_pdf_to_markdown(file_path)
            if md:
                logger.info("PDF to Markdown conversion succeeded.")
                return md
            else:
                logger.warning("PDF to Markdown conversion failed, falling back to text extraction.")
        # Validate PDF header
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                if not header.startswith(b'%PDF-'):
                    logger.error("Invalid PDF file: Missing PDF header")
                    return "Error: Invalid PDF header"
                if b'/Encrypt' in header:
                    logger.error("PDF file is encrypted")
                    return "Error: PDF file is encrypted"
        except Exception as e:
            logger.error(f"Error reading PDF header: {str(e)}")
            return f"Error: {str(e)}"
        # Try pdfminer.six first
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract_text
            import threading
            import time
            
            text = None
            extraction_error = None
            
            def extract_with_timeout():
                nonlocal text, extraction_error
                try:
                    text = pdfminer_extract_text(file_path)
                except Exception as e:
                    extraction_error = e
            
            # Run extraction in a thread with timeout (2 minutes)
            extraction_thread = threading.Thread(target=extract_with_timeout)
            extraction_thread.daemon = True
            extraction_thread.start()
            
            # Wait for extraction to complete with timeout
            extraction_thread.join(timeout=120)
            
            if extraction_thread.is_alive():
                logger.warning("pdfminer.six extraction timed out after 2 minutes")
                raise TimeoutError("pdfminer.six extraction timed out")
            
            if extraction_error:
                raise extraction_error
            
            logger.info(f"[PDF] Raw extracted text (first 500 chars): {text[:500] if text else 'EMPTY'}")
            if text and text.strip():
                logger.info(f"Successfully extracted {len(text)} characters with pdfminer.six")
                if file_size <= 10 * 1024 * 1024:
                    text = self.clean_extracted_text(text)
                else:
                    logger.info("Skipping text cleaning for very large file to improve performance")
                logger.info(f"[PDF] Cleaned text (first 500 chars): {text[:500] if text else 'EMPTY'}")
                preprocessed_text = self.preprocess_pdf_text(text)
                logger.info(f"[PDF] Preprocessed text (first 500 chars): {preprocessed_text[:500] if preprocessed_text else 'EMPTY'}")
                return preprocessed_text
        except Exception as e:
            logger.warning(f"pdfminer.six extraction failed: {str(e)}")
        # Try PyPDF2
        try:
            import threading
            import time
            
            text = None
            extraction_error = None
            
            def extract_with_timeout():
                nonlocal text, extraction_error
                try:
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        if reader.is_encrypted:
                            raise ValueError("PDF file is encrypted")
                        text = ""
                        for page in reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                except Exception as e:
                    extraction_error = e
            
            # Run extraction in a thread with timeout (2 minutes)
            extraction_thread = threading.Thread(target=extract_with_timeout)
            extraction_thread.daemon = True
            extraction_thread.start()
            
            # Wait for extraction to complete with timeout
            extraction_thread.join(timeout=120)
            
            if extraction_thread.is_alive():
                logger.warning("PyPDF2 extraction timed out after 2 minutes")
                raise TimeoutError("PyPDF2 extraction timed out")
            
            if extraction_error:
                if "encrypted" in str(extraction_error):
                    logger.error("PDF file is encrypted (PyPDF2)")
                    return "Error: PDF file is encrypted"
                raise extraction_error
            
            if text and text.strip():
                logger.info(f"Successfully extracted {len(text)} characters with PyPDF2")
                text = self.clean_extracted_text(text)
                preprocessed_text = self.preprocess_pdf_text(text)
                return preprocessed_text
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
        # Try pdftotext if available
        try:
            result = subprocess.run(['pdftotext', file_path, '-'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"Successfully extracted {len(result.stdout)} characters with pdftotext")
                text = self.clean_extracted_text(result.stdout)
                preprocessed_text = self.preprocess_pdf_text(text)
                return preprocessed_text
        except Exception as e:
            logger.warning(f"pdftotext extraction failed: {str(e)}")
        # Try OCR fallback (not implemented here, but could be added)
        logger.error("All extraction methods failed for PDF")
        return "Error: All extraction methods failed for PDF"

    def extract_text_from_file(self, file_path: str, convert_pdf_to_md: bool = False) -> str:
        """Extract text from various file formats, with PDF enhancements."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.pdf':
            return self._extract_text_from_pdf(file_path, convert_to_md=convert_pdf_to_md)
        elif file_ext == '.docx':
            return self._extract_text_from_docx(file_path)
        elif file_ext == '.rtf':
            return self._extract_text_from_rtf(file_path)
        elif file_ext in ['.html', '.htm']:
            return self._extract_text_from_html_file(file_path)
        elif file_ext in ['.txt', '.md']:
            return self._extract_text_from_text_file(file_path)
        else:
            return self._extract_text_from_text_file(file_path)
    
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
            import tempfile
            import os
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            logger.info(f"Content type: {content_type}")
            
            # Handle document types by downloading to temp file
            content_type_to_extension = {
                'application/pdf': '.pdf',
                'application/msword': '.doc',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                'application/rtf': '.rtf',
                'application/vnd.oasis.opendocument.text': '.odt'
            }
            
            # Check if content type corresponds to a document format
            for ct, ext in content_type_to_extension.items():
                if ct in content_type:
                    logger.info(f"Handling {ct} content by downloading to temp file")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    
                    try:
                        text = self.extract_text_from_file(temp_file_path)
                        logger.info(f"Successfully extracted {len(text)} characters from {ct} URL")
                        return text
                    finally:
                        os.unlink(temp_file_path)  # Clean up temporary file
                        logger.info(f"Deleted temporary file: {temp_file_path}")
            
            # Handle text content types
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
    
    def _convert_citation_to_dict(self, citation) -> Dict[str, Any]:
        """Convert a citation object to a dictionary, handling various types."""
        if isinstance(citation, dict):
            return citation
        
        # Handle CitationResult objects
        if hasattr(citation, '__dict__'):
            citation_dict = {}
            
            # Standard fields that should always be present
            standard_fields = [
                'citation', 'case_name', 'extracted_case_name', 'canonical_name',
                'extracted_date', 'canonical_date', 'verified', 'court', 'confidence',
                'method', 'pattern', 'context', 'is_parallel', 'is_cluster',
                'parallel_citations', 'cluster_members', 'pinpoint_pages',
                'docket_numbers', 'case_history', 'publication_status',
                'url', 'source', 'start_index', 'end_index', 'error', 'metadata'
            ]
            
            # Extract available fields
            for field in standard_fields:
                if hasattr(citation, field):
                    value = getattr(citation, field)
                    citation_dict[field] = value
                else:
                    # Set default values for missing fields
                    if field in ['case_name', 'extracted_case_name', 'canonical_name']:
                        citation_dict[field] = 'N/A'
                    elif field in ['verified', 'is_parallel', 'is_cluster']:
                        citation_dict[field] = False
                    elif field in ['confidence']:
                        citation_dict[field] = 0.0
                    elif field in ['parallel_citations', 'cluster_members', 'pinpoint_pages', 'docket_numbers', 'case_history']:
                        citation_dict[field] = []
                    elif field in ['start_index', 'end_index']:
                        citation_dict[field] = -1
                    else:
                        citation_dict[field] = None
            
            return citation_dict
        
        # If it's some other object type, try to convert it
        try:
            return dict(citation)
        except:
            logger.warning(f"Unable to convert citation object to dict: {type(citation)}")
            return {
                'citation': str(citation),
                'case_name': 'N/A',
                'error': 'Unable to convert citation object'
            }
    
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
            logger.info(f"[PROCESS] Input text (first 500 chars): {text[:500] if text else 'EMPTY'}")
            
            # Step 2: Preprocess text
            # Skip OCR correction for direct text submissions to avoid corruption
            skip_ocr = source_type == 'text'
            preprocessed_text = self.preprocess_text(text, skip_ocr_correction=skip_ocr)
            logger.info(f"Text preprocessing: {len(text)} -> {len(preprocessed_text)} characters")
            logger.info(f"[PROCESS] Preprocessed text (first 500 chars): {preprocessed_text[:500] if preprocessed_text else 'EMPTY'}")
            
            # Step 3: Extract citations using unified processor
            formatted_citations = []
            statistics = {'total_citations': 0}
            
            if self.citation_processor is None:
                logger.warning("No citation processor available - returning empty results")
            else:
                try:
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
                        
                        # Convert CitationResult objects to dictionaries
                        for citation in citation_results:
                            try:
                                citation_dict = self._convert_citation_to_dict(citation)
                                formatted_citations.append(citation_dict)
                            except Exception as e:
                                logger.error(f"Error converting citation to dict: {e}")
                                continue
                        
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
                        if source_type == 'text' and hasattr(self.citation_processor, 'enable_ocr_correction'):
                            self.citation_processor.enable_ocr_correction(False)
                            logger.debug("Disabled OCR correction in processor for direct text submission")
                        
                        # Handle different processor interfaces
                        if hasattr(self.citation_processor, 'process_text'):
                            processing_result = self.citation_processor.process_text(preprocessed_text, extract_case_names=extract_case_names)
                            
                            if isinstance(processing_result, dict):
                                citations = processing_result.get('results', [])
                                statistics = processing_result.get('statistics', {'total_citations': 0})
                            else:
                                # If process_text returns a list directly
                                citations = processing_result if isinstance(processing_result, list) else []
                                statistics = {'total_citations': len(citations)}
                        else:
                            logger.error("Citation processor doesn't have process_text method")
                            citations = []
                            statistics = {'total_citations': 0}
                        
                        # Re-enable OCR correction for future use
                        if source_type == 'text' and hasattr(self.citation_processor, 'enable_ocr_correction'):
                            self.citation_processor.enable_ocr_correction(True)
                            logger.debug("Re-enabled OCR correction in processor")
                        
                        # Convert CitationResult objects to dictionaries
                        for citation in citations:
                            try:
                                citation_dict = self._convert_citation_to_dict(citation)
                                formatted_citations.append(citation_dict)
                            except Exception as e:
                                logger.error(f"Error converting citation to dict: {e}")
                                continue
                                
                except Exception as e:
                    logger.error(f"Error during citation processing: {e}", exc_info=True)
                    formatted_citations = []
                    statistics = {'total_citations': 0}
            
            # Step 4: Extract case names
            case_names = []
            if extract_case_names:
                try:
                    case_names = self._extract_case_names(formatted_citations, preprocessed_text)
                except Exception as e:
                    logger.error(f"Error extracting case names: {e}")
                    case_names = []
            
            # Step 5: Apply verification if available
            if hasattr(self, 'verify_citations'):
                try:
                    logger.info("Applying citation verification")
                    formatted_citations = self.verify_citations(formatted_citations, preprocessed_text)
                except Exception as e:
                    logger.error(f"Error during citation verification: {e}")
            
            processing_time = time.time() - start_time
            
            # Ensure all required fields are present in the result
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
            logger.info(f"   Citations data structure: {[type(c) for c in formatted_citations[:3]]}")  # Debug info
            
            # Final validation - ensure citations are serializable
            try:
                import json
                json.dumps(result)
                logger.info("✅ Result is JSON serializable")
            except Exception as e:
                logger.error(f"❌ Result is not JSON serializable: {e}")
                # Try to fix by converting any remaining objects
                result["citations"] = [self._convert_citation_to_dict(c) for c in result["citations"]]
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "citations": [],
                "case_names": [],
                "statistics": {'total_citations': 0},
                "processing_time": time.time() - start_time,
                "source_type": "unknown",
                "source_name": "unknown"
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

def extract_and_verify_citations(text: str, api_key: str = None) -> tuple:
    """
    Backward compatibility function for extract_and_verify_citations.
    Returns a tuple of (citations, metadata) for compatibility with existing tests.
    """
    processor = UnifiedDocumentProcessor()
    result = processor.process_document(content=text, extract_case_names=True)
    
    if result.get("success"):
        citations = result.get("citations", [])
        metadata = {
            "statistics": result.get("statistics", {}),
            "processing_time": result.get("processing_time", 0),
            "text_length": result.get("text_length", 0),
            "case_names": result.get("case_names", [])
        }
        return citations, metadata
    else:
        return [], {"error": result.get("error", "Unknown error")} 