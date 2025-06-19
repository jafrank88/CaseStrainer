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
    preferred_method: PDFExtractionMethod = PDFExtractionMethod.PYPDF2
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
        """Extract text using PyPDF2."""
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
            
            text = pdfminer_extract_text(file_path, laparams=laparams)
            
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
    
    def extract_text(self, file_path: str) -> str:
        """Main entry point for text extraction with enhanced error handling and logging."""
        self.logger.info(f"\n=== PDF EXTRACTION DEBUG ===")
        self.logger.info(f"Starting PDF extraction from: {file_path}")
        start_time = time.time()
        
        try:
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                error_msg = f"PDF file does not exist: {file_path}"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
                
            # Get file size
            file_size = os.path.getsize(file_path)
            self.logger.info(f"PDF file size: {file_size/1024:.1f}KB")
            
            if file_size == 0:
                error_msg = f"PDF file is empty: {file_path}"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
                
            # Check for known problematic files
            filename = os.path.basename(file_path)
            if filename in self._known_problematic_files:
                self.logger.warning(f"Known problematic file detected: {filename}")
                text, error = self._handle_problematic_pdf(file_path)
                if text:
                    return text
                return f"Error: {error or 'Failed to extract text from problematic PDF'}"
                
            # Validate PDF header
            is_valid, header_msg, metadata = self._validate_pdf_header(file_path)
            if not is_valid:
                self.logger.error(header_msg)
                return f"Error: {header_msg}"
            self.logger.info(header_msg)
            
            # Try multiple extraction methods with a quick test to select the fastest for large files
            if file_size > 5 * 1024 * 1024:  # For files >5MB, test methods quickly
                self.logger.info("Large file detected, testing extraction methods for fastest result...")
                methods = [
                    (self._extract_with_pdfminer, "pdfminer"),
                    (self._extract_with_pypdf2, "PyPDF2"),
                    (self._extract_with_pdftotext, "pdftotext")
                ]
                best_method = None
                best_time = float('inf')
                original_timeout = self.config.timeout
                self.config.timeout = self.config.quick_test_timeout  # Short timeout for testing
                
                for method_func, method_name in methods:
                    test_start_time = time.time()
                    text, error = method_func(file_path, test_start_time)
                    test_time = time.time() - test_start_time
                    if text and test_time < best_time:
                        best_method = (method_func, method_name)
                        best_time = test_time
                    elif error:
                        self.logger.warning(f"Quick test with {method_name} failed: {error}")
                
                self.config.timeout = original_timeout  # Restore original timeout
                
                if best_method:
                    method_func, method_name = best_method
                    self.logger.info(f"Selected {method_name} as fastest method based on quick test")
                    text, error = method_func(file_path, start_time)
                    if text:
                        # Clean text if enabled
                        if self.config.clean_text:
                            text = clean_extracted_text(text)
                        return text
                    else:
                        self.logger.error(f"Full extraction with {method_name} failed: {error}")
                        return f"Error: {error or 'Failed to extract text with selected method'}"
                else:
                    self.logger.warning("No method succeeded in quick test, falling back to pdfminer.six")
            
            # Default extraction with pdfminer.six for smaller files or if quick test fails
            self.logger.info("Extracting text with pdfminer.six...")
            text = pdfminer_extract_text(file_path)
            
            if not text or not text.strip():
                error_msg = "No text content extracted from PDF"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
                
            # Log success
            text_length = len(text)
            self.logger.info(f"Successfully extracted {text_length} characters")
            if text_length > 0:
                sample = text[:500].replace('\n', ' ').strip()
                self.logger.info(f"Text sample (first 500 chars): {sample}")
            
            # Clean text if enabled
            if self.config.clean_text and file_size <= 10 * 1024 * 1024:  # Skip for very large files
                self.logger.info("Cleaning extracted text...")
                text = clean_extracted_text(text)
            elif file_size > 10 * 1024 * 1024:
                self.logger.info("Skipping text cleaning for very large file to improve performance")
                
            return text
                
        except Exception as e:
            error_msg = f"PDFMiner extraction failed: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error("Stack trace:", exc_info=True)
            return f"Error: {error_msg}"
            
        except Exception as e:
            error_msg = f"Unexpected error in PDF extraction: {str(e)}"
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
        print(f"Error in clean_extracted_text: {e}")
        # Return the original text if cleaning fails
        return text.strip()


# Simple test function to check if the module works
if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Testing PDF extraction on: {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters")
        print("First 500 characters:")
        print(text[:500])
    else:
        print("Usage: python pdf_handler.py <path_to_pdf>")
