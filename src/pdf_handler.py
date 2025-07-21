import os
import sys
import io
import tempfile
import shutil
import subprocess
import PyPDF2
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.high_level import extract_text as pdfminer_extract_text
import re
import traceback
import time
import logging
from typing import Optional, Tuple, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
# Note: extract_case_name is deprecated, functionality moved to case_name_extraction_core
from src.case_name_extraction_core import CaseNameExtractor
import warnings
warnings.warn('src/pdf_handler.py is deprecated. Use src.document_processing_unified.extract_text_from_file instead.', DeprecationWarning)


class PDFExtractionMethod(Enum):
    """Enum for different PDF extraction methods."""
    PYPDF2 = "pypdf2"
    PDFMINER = "pdfminer"
    PDFTOTEXT = "pdftotext"
    CUSTOM = "custom"


@dataclass
class PDFExtractionConfig:
    """Configuration for PDF extraction."""
    timeout: int = 25
    quick_test_timeout: int = 5
    max_text_length: int = 200
    preferred_method: PDFExtractionMethod = PDFExtractionMethod.PDFMINER
    use_fallback: bool = True
    clean_text: bool = True
    debug: bool = False
    custom_laparams: Optional[LAParams] = None


class PDFHandler:
    """Enhanced PDF handling class with robust text extraction and error handling."""
    
    def __init__(self, config: Optional[PDFExtractionConfig] = None):
        """Initialize PDF handler with optional configuration."""
        self.config = config or PDFExtractionConfig()
        self.logger = logging.getLogger(__name__)
        self._known_problematic_files = {
            "999562 Plaintiff Opening Brief.pdf": "Known problematic file requiring special handling"
        }
        
    def _setup_logging(self):
        """Set up logging configuration."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG if self.config.debug else logging.INFO)
    
    def _sanitize_text_for_logging(self, text: str, max_length: Optional[int] = None) -> str:
        """Sanitize text for logging by removing non-printable characters and limiting length."""
        if not text:
            return ""
        # Convert to string if bytes
        if isinstance(text, bytes):
            try:
                text = text.decode('utf-8', errors='replace')
            except Exception:
                return "[Binary data]"
        # Remove non-printable characters
        text = ''.join(c for c in text if c.isprintable())
        # Limit length and add ellipsis
        max_len = max_length or self.config.max_text_length
        if len(text) > max_len:
            text = text[:max_len] + "..."
        return text
    
    def _sanitize_bytes_for_logging(self, bytes_data: bytes, max_length: Optional[int] = None) -> str:
        """Sanitize bytes for logging by converting to hex representation."""
        if not bytes_data:
            return ""
        # Convert bytes to hex representation
        hex_str = bytes_data.hex()
        # Add spaces between bytes for readability
        hex_str = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
        # Limit length and add ellipsis
        max_len = max_length or self.config.max_text_length
        if len(hex_str) > max_len:
            hex_str = hex_str[:max_len] + "..."
        return hex_str
    
    def _validate_pdf_header(self, file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate PDF header and return validation status, message, and metadata."""
        try:
            with open(file_path, 'rb') as f:
                # Read first 1024 bytes to check header and encoding
                header = f.read(1024)
                
                # Log sanitized header bytes
                self.logger.debug(f"PDF header (hex): {self._sanitize_bytes_for_logging(header[:20])}")
                
                metadata = {
                    'version': None,
                    'has_metadata': False,
                    'is_encrypted': False,
                    'header_valid': False
                }
                
                # Check for PDF signature
                if not header.startswith(b'%PDF-'):
                    return False, "Invalid PDF file: Missing PDF header", metadata
                    
                metadata['header_valid'] = True
                
                # Try to find PDF version
                version_match = re.search(rb'%PDF-(\d+\.\d+)', header)
                if version_match:
                    metadata['version'] = version_match.group(1).decode('ascii')
                    self.logger.info(f"PDF version: {metadata['version']}")
                else:
                    self.logger.warning("PDF version not found in header")
                    
                # Check for common PDF metadata
                metadata['has_metadata'] = b'/Metadata' in header
                metadata['is_encrypted'] = b'/Encrypt' in header
                
                if metadata['has_metadata']:
                    self.logger.info("PDF contains metadata")
                if metadata['is_encrypted']:
                    return False, "PDF file is encrypted", metadata
                    
                return True, "Valid PDF header detected", metadata
                
        except Exception as e:
            self.logger.error(f"Error reading PDF header: {str(e)}")
            return False, f"Error reading PDF header: {str(e)}", {}
    
    def _extract_with_pypdf2(self, file_path: str, start_time: float) -> Tuple[Optional[str], Optional[str]]:
        """Extract text using PyPDF2 (DEPRECATED: use isolation-aware logic instead)."""
        warnings.warn(
            "_extract_with_pypdf2 is deprecated. Use isolation-aware PDF extraction instead.",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is encrypted
                if reader.is_encrypted:
                    return None, "PDF file is encrypted"
                    
                num_pages = len(reader.pages)
                self.logger.info(f"PDF has {num_pages} pages")
                
                if num_pages == 0:
                    return None, "PDF file has no pages"
                    
                text = ""
                for i, page in enumerate(reader.pages):
                    # Check for timeout
                    if time.time() - start_time > self.config.timeout:
                        return None, f"PDF extraction timed out after {self.config.timeout} seconds"
                        
                    try:
                        self.logger.debug(f"Extracting text from page {i+1}/{num_pages}")
                        page_text = page.extract_text()
                        if not page_text:
                            self.logger.warning(f"No text extracted from page {i+1}")
                            continue
                            
                        # Sanitize page text before logging
                        sanitized_sample = self._sanitize_text_for_logging(page_text)
                        self.logger.debug(f"Extracted {len(page_text)} characters from page {i+1}")
                        if sanitized_sample:
                            self.logger.debug(f"Sample from page {i+1}: {sanitized_sample}")
                            
                        text += page_text + "\n"
                        
                    except Exception as page_error:
                        self.logger.error(f"Error extracting text from page {i+1}: {str(page_error)}")
                        continue
                        
                if not text.strip():
                    return None, "No text extracted with PyPDF2"
                    
                # Sanitize final text before logging
                sanitized_sample = self._sanitize_text_for_logging(text)
                self.logger.info(f"Successfully extracted {len(text)} characters with PyPDF2")
                if sanitized_sample:
                    self.logger.debug(f"Sample of extracted text: {sanitized_sample}")
                return text, None
                
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return None, str(e)
    
    def _extract_with_pdfminer(self, file_path: str, start_time: float) -> Tuple[Optional[str], Optional[str]]:
        """Extract text using pdfminer."""
        try:
            # Check for timeout
            if time.time() - start_time > self.config.timeout:
                return None, f"PDF extraction timed out after {self.config.timeout} seconds"
                
            # Use custom LAParams if provided
            laparams = self.config.custom_laparams or LAParams(
                line_margin=0.5,
                char_margin=2.0,
                word_margin=0.1,
                all_texts=True
            )
            
            # Use pdfminer_extract_text without custom laparams to avoid tuple return
            text = pdfminer_extract_text(file_path)
            
            if not text or not text.strip():
                return None, "No text could be extracted with pdfminer"
                
            # Sanitize text before logging
            sanitized_sample = self._sanitize_text_for_logging(text)
            self.logger.info(f"Successfully extracted {len(text)} characters with pdfminer")
            if sanitized_sample:
                self.logger.debug(f"Sample of extracted text: {sanitized_sample}")
            self.logger.debug("Raw extracted text (sample): %s", text[:1000] if text else "None")
            return text, None
            
        except Exception as e:
            self.logger.error(f"pdfminer extraction failed: {str(e)}")
            return None, str(e)
    
    def _extract_with_pdftotext(self, file_path: str, start_time: float) -> Tuple[Optional[str], Optional[str]]:
        """Extract text using pdftotext command line tool."""
        try:
            # Check for timeout
            if time.time() - start_time > self.config.timeout:
                return None, f"PDF extraction timed out after {self.config.timeout} seconds"
                
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                output_file = temp_file.name
                
            try:
                # Try pdftotext from poppler
                result = subprocess.run(
                    [
                        "pdftotext",
                        "-layout",
                        "-enc",
                        "UTF-8",
                        file_path,
                        output_file,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout,
                )
                
                if result.returncode == 0 and os.path.exists(output_file):
                    # Read the extracted text
                    with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                        
                    if text and text.strip():
                        self.logger.info(f"Successfully extracted {len(text)} characters with pdftotext")
                        return text, None
                    else:
                        return None, "pdftotext extracted empty text"
                else:
                    return None, f"pdftotext failed with return code {result.returncode}: {result.stderr}"
                    
            except FileNotFoundError:
                return None, "pdftotext command not available"
            except subprocess.TimeoutExpired:
                return None, "pdftotext process timed out"
            except Exception as e:
                return None, f"Error with pdftotext: {str(e)}"
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(output_file)
                except Exception as e:
                    self.logger.warning(f"Error cleaning up temporary file: {e}")
                    
        except Exception as e:
            self.logger.error(f"pdftotext extraction failed: {str(e)}")
            return None, str(e)
    
    def _extract_with_ocr(self, file_path: str, start_time: float) -> Tuple[Optional[str], Optional[str]]:
        """Extract text from PDF using OCR (Tesseract) as a last resort."""
        try:
            from pdf2image import convert_from_path  # type: ignore
            import pytesseract  # type: ignore
        except ImportError as e:
            self.logger.error(f"OCR dependencies not installed: {e}")
            return None, "OCR dependencies not installed"
        try:
            self.logger.info("Converting PDF pages to images for OCR fallback...")
            images = convert_from_path(file_path)
            ocr_text = ""
            for i, image in enumerate(images):
                if time.time() - start_time > self.config.timeout * 2:
                    return None, f"OCR extraction timed out after {self.config.timeout * 2} seconds"
                self.logger.info(f"Running OCR on page {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(image)
                ocr_text += page_text + "\n"
            if not ocr_text.strip():
                return None, "No text extracted with OCR"
            self.logger.info(f"Successfully extracted {len(ocr_text)} characters with OCR")
            # Apply OCR correction only to OCR text
            try:
                from .document_processing_unified import UnifiedDocumentProcessor as DocumentProcessor
            except ImportError:
                from document_processing_unified import UnifiedDocumentProcessor as DocumentProcessor
            processor = DocumentProcessor()
            ocr_text_corrected = processor.preprocess_text(ocr_text, skip_ocr_correction=False)
            return ocr_text_corrected, None
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {str(e)}")
            return None, str(e)
    
    def _handle_problematic_pdf(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Special handling for known problematic PDF files."""
        self.logger.info(f"Using special handling for problematic PDF: {file_path}")
        
        # Create a temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix="pdf_processing_")
        try:
            # Copy the file to the temp directory
            temp_file_path = os.path.join(temp_dir, "temp.pdf")
            shutil.copy2(file_path, temp_file_path)
            self.logger.debug(f"Copied file to temporary location: {temp_file_path}")
            
            # Try all methods in sequence
            methods = [
                (self._extract_with_pdftotext, "pdftotext"),
                (self._extract_with_pdfminer, "pdfminer"),
                (self._extract_with_pypdf2, "PyPDF2")
            ]
            
            for method_func, method_name in methods:
                self.logger.info(f"Trying {method_name} with special handling...")
                text, error = method_func(temp_file_path, time.time())
                if text:
                    return text, None
                self.logger.warning(f"{method_name} failed: {error}")
            
            return None, "All extraction methods failed for problematic PDF"
            
        except Exception as e:
            self.logger.error(f"Error in special handling: {str(e)}")
            return None, str(e)
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
                self.logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"Error cleaning up temporary directory: {e}")
    
    def preprocess_pdf_text(self, text: str) -> str:
        """Preprocess PDF text: minimally remove only obvious page numbers and very short all-uppercase lines."""
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

    def extract_case_name_global(self, text: str) -> Optional[str]:
        """Extract a likely case name from anywhere in the document (global search)."""
        if not text:
            return None
        
        # Look for case name patterns with better filtering
        patterns = [
            # Pattern for "Plaintiff v. Defendant" format
            r'([A-Z][A-Za-z0-9\s\.,&\-\']+)\s+v\.\s+([A-Z][A-Za-z0-9\s\.,&\-\']+)',
            # Pattern for "In re Case Name" format
            r'In\s+re\s+([A-Z][A-Za-z0-9\s\.,&\-\']+)',
            # Pattern for "Case Name v. Defendant" (more flexible)
            r'([A-Z][A-Za-z0-9\s\.,&\-\']{3,50})\s+v\.\s+([A-Z][A-Za-z0-9\s\.,&\-\']{3,50})',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if pattern.startswith(r'In\s+re'):
                    # For "In re" cases, return the case name
                    case_name = match.group(1).strip()
                else:
                    # For "v." cases, combine plaintiff and defendant
                    plaintiff = match.group(1).strip()
                    defendant = match.group(2).strip()
                    case_name = f"{plaintiff} v. {defendant}"
                
                # Use canonical cleaning and validation functions
                extractor = CaseNameExtractor()
                case_name = extractor._clean_case_name(case_name)
                
                # Filter out very short or very long case names
                if case_name and 5 <= len(case_name) <= 200:
                    # Use canonical validation function
                    if extractor._validate_case_name(case_name):
                        # Additional filtering to avoid header/footer text
                        if not any(skip_word in case_name.upper() for skip_word in [
                            'SUPREME COURT', 'FILED', 'RECORD', 'CLERK', 'OFFICE', 'STATE OF',
                            'MAY 29', '2025', 'SARAH', 'PENDLETON', 'THIS OPINION'
                        ]):
                            return case_name
        
        return None

    def extract_text(self, file_path: str) -> str:
        """Extract text from a PDF file, always using pdfminer.six first, then fallbacks, then OCR."""
        start_time = time.time()
        file_size = os.path.getsize(file_path)
        self.logger.info(f"Extracting text from PDF: {file_path} ({file_size} bytes)")
        
        # Disable verbose pdfminer logging to speed up extraction
        import logging
        logging.getLogger("pdfminer").setLevel(logging.WARNING)
        logging.getLogger("pdfminer.cmapdb").setLevel(logging.ERROR)
        logging.getLogger("pdfminer.psparser").setLevel(logging.ERROR)
        logging.getLogger("pdfminer.pdfinterp").setLevel(logging.ERROR)
        
        try:
            # Always use pdfminer.six as the primary extractor
            self.logger.info("Extracting text with pdfminer.six (primary)...")
            text = pdfminer_extract_text(file_path)
            if text and text.strip():
                self.logger.info(f"Successfully extracted {len(text)} characters with pdfminer.six")
                # Clean text if enabled
                if self.config.clean_text and file_size <= 10 * 1024 * 1024:
                    self.logger.info("Cleaning extracted text...")
                    text = clean_extracted_text(text)
                elif file_size > 10 * 1024 * 1024:
                    self.logger.info("Skipping text cleaning for very large file to improve performance")
                preprocessed_text = self.preprocess_pdf_text(text)
                self.logger.info(f"Preprocessed text sample: {preprocessed_text[:300]}")
                case_name = self.extract_case_name_global(preprocessed_text)
                if case_name:
                    self.logger.info(f"[PDFHandler] Global case name extraction: {case_name}")
                else:
                    self.logger.info("[PDFHandler] No case name found in global search.")
                return text
            else:
                self.logger.warning("pdfminer.six extracted no text, trying fallbacks...")
                # Try fallbacks only if pdfminer fails
                methods = [
                    (self._extract_with_pdftotext, "pdftotext"),
                    (self._extract_with_pypdf2, "PyPDF2")
                ]
                for method_func, method_name in methods:
                    self.logger.info(f"Trying {method_name} as fallback...")
                    text, error = method_func(file_path, time.time())
                    if text:
                        if self.config.clean_text:
                            text = clean_extracted_text(text)
                        return text
                    self.logger.warning(f"{method_name} failed: {error}")
                # OCR fallback
                self.logger.warning("All text-based extraction methods failed, trying OCR fallback...")
                ocr_text, ocr_error = self._extract_with_ocr(file_path, time.time())
                if ocr_text:
                    return ocr_text
                self.logger.error(f"OCR fallback failed: {ocr_error}")
                error_msg = "All extraction methods (including OCR) failed for PDF"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"PDF extraction failed: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error("Stack trace:", exc_info=True)
            return f"Error: {error_msg}"
        finally:
            elapsed_time = time.time() - start_time
            self.logger.info(f"\nPDF extraction completed in {elapsed_time:.1f}s")


# For backward compatibility
def extract_text_from_pdf(file_path: str, timeout: int = 25) -> str:
    """Legacy function that uses PDFHandler with default settings."""
    handler = PDFHandler(PDFExtractionConfig(timeout=timeout))
    return handler.extract_text(file_path)


# Keep existing clean_extracted_text function for backward compatibility
def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text to improve citation detection."""
    if not text:
        return ""

    try:
        # Remove non-printable characters but preserve citation patterns
        text = "".join(
            char for char in text if char.isprintable() or char in ".,;:()[]{}"
        )

        # Fix common OCR errors in citations - using raw strings and simpler patterns
        text = re.sub(
            r"(\d+)\s*[Uu]\.?\s*[Ss]\.?\s*(\d+)", r"\1 U.S. \2", text
        )  # Fix U.S. spacing
        text = re.sub(
            r"(\d+)\s*[Ss]\.?\s*[Cc][Tt]\.?\s*(\d+)", r"\1 S.Ct. \2", text
        )  # Fix S.Ct. spacing
        text = re.sub(
            r"(\d+)\s*[Ll]\.?\s*[Ee][Dd]\.?\s*(\d+)", r"\1 L.Ed. \2", text
        )  # Fix L.Ed. spacing
        text = re.sub(
            r"(\d+)\s*[Ff]\.?\s*(2[Dd]|3[Dd]|4[Tt][Hh])?\s*(\d+)", r"\1 F.\2 \3", text
        )  # Fix F. spacing and preserve series

        # Fix line breaks within citations
        text = re.sub(r"(\d+)\s*U\.?\s*S\.?\s*\n\s*(\d+)", r"\1 U.S. \2", text)
        text = re.sub(r"(\d+)\s*S\.?\s*Ct\.?\s*\n\s*(\d+)", r"\1 S.Ct. \2", text)
        text = re.sub(r"(\d+)\s*L\.?\s*Ed\.?\s*\n\s*(\d+)", r"\1 L.Ed. \2", text)
        text = re.sub(r"(\d+)\s*F\.?\s*(2d|3d|4th)?\s*\n\s*(\d+)", r"\1 F.\2 \3", text)

        # Fix page breaks within citations
        text = re.sub(
            r"(\d+)\s*U\.?\s*S\.?\s*-\s*(\d+)", r"\1 U.S. \2", text
        )  # Fix page break markers
        text = re.sub(r"(\d+)\s*S\.?\s*Ct\.?\s*-\s*(\d+)", r"\1 S.Ct. \2", text)
        text = re.sub(r"(\d+)\s*L\.?\s*Ed\.?\s*-\s*(\d+)", r"\1 L.Ed. \2", text)
        text = re.sub(r"(\d+)\s*F\.?\s*(2d|3d|4th)?\s*-\s*(\d+)", r"\1 F.\2 \3", text)

        # Fix common OCR errors in numbers - using simpler patterns
        text = re.sub(r"[Oo](\d)", r"0\1", text)  # Fix O/0 confusion
        text = re.sub(r"(\d)[Oo]", r"\g<1>0", text)  # Fix O/0 confusion at end of numbers
        text = re.sub(r"[lI](\d)", r"1\1", text)  # Fix l/I/1 confusion
        text = re.sub(
            r"(\d)[lI]", r"\g<1>1", text
        )  # Fix l/I/1 confusion at end of numbers

        # Fix spacing in abbreviations
        text = re.sub(r"([A-Z])\.\s+([A-Z])", r"\1.\2", text)

        # Normalize whitespace while preserving citation patterns
        text = re.sub(r"\s+", " ", text)

        # Remove any remaining page numbers or headers/footers
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

        return text.strip()
    except Exception as e:
        logger.error(f"Error in clean_extracted_text: {e}")
        # Return the original text if cleaning fails
        return text.strip()


# Simple test function to check if the module works
if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        logger.info(f"Testing PDF extraction on: {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        logger.info(f"Extracted {len(text)} characters")
        logger.info("First 500 characters:")
        logger.info(text[:500])
    else:
        logger.info("Usage: python pdf_handler.py <path_to_pdf>")
