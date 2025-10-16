#!/usr/bin/env python3
"""
Unified Text Extraction for All File Formats
Fast and reliable text extraction from multiple document formats.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import time

logger = logging.getLogger(__name__)

# Extract timeout per format (seconds)
EXTRACTION_TIMEOUT = 30


class UnifiedTextExtractor:
    """
    Unified text extraction for all supported formats.
    
    Supported formats:
    - PDF: via robust_pdf_extractor
    - DOCX: via python-docx
    - DOC: via antiword or textract
    - HTML/HTM/XML: via BeautifulSoup
    - RTF: via striprtf
    - TXT/MD: direct read
    """
    
    def __init__(self, verbose: bool = False):
        """Initialize extractor with format detection."""
        self.verbose = verbose
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check which libraries are available."""
        self.has_docx = self._check_import('docx')
        self.has_bs4 = self._check_import('bs4')
        self.has_striprtf = self._check_import('striprtf')
        
        if self.verbose:
            logger.info(f"Text extraction capabilities: DOCX={self.has_docx}, HTML={self.has_bs4}, RTF={self.has_striprtf}")
    
    def _check_import(self, module_name: str) -> bool:
        """Check if a module is available."""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    
    def extract_text(self, file_path: str) -> Tuple[str, str]:
        """
        Extract text from any supported file format.
        
        Args:
            file_path: Path to file
            
        Returns:
            Tuple of (extracted_text, method_used)
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        start_time = time.time()
        file_path_obj = Path(file_path)
        ext = file_path_obj.suffix.lower().lstrip('.')
        
        try:
            # Route to appropriate extractor
            if ext == 'pdf':
                text, method = self._extract_pdf(file_path)
            elif ext in ['docx', 'doc']:
                text, method = self._extract_word(file_path, ext)
            elif ext in ['html', 'htm', 'xml', 'xhtml']:
                text, method = self._extract_html(file_path)
            elif ext == 'rtf':
                text, method = self._extract_rtf(file_path)
            elif ext in ['txt', 'md', 'markdown']:
                text, method = self._extract_plaintext(file_path)
            else:
                # Fallback: try as plain text
                text, method = self._extract_plaintext(file_path)
                method = f"{ext}:fallback_plaintext"
            
            elapsed = time.time() - start_time
            
            if text and len(text.strip()) > 50:
                logger.info(f"✅ Extracted {len(text):,} chars from {ext} in {elapsed:.1f}s using {method}")
                return text, method
            else:
                logger.warning(f"⚠️ Insufficient text extracted from {ext}: {len(text) if text else 0} chars")
                return "", f"{ext}:insufficient_text"
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Failed to extract {ext} after {elapsed:.1f}s: {e}")
            return "", f"{ext}:error"
    
    def _extract_pdf(self, file_path: str) -> Tuple[str, str]:
        """Extract text from PDF using robust extractor."""
        from src.robust_pdf_extractor import extract_pdf_text_robust
        text, library = extract_pdf_text_robust(file_path, verbose=self.verbose)
        return text, f"pdf:{library}"
    
    def _extract_word(self, file_path: str, ext: str) -> Tuple[str, str]:
        """Extract text from Word documents (.docx or .doc)."""
        if ext == 'docx' and self.has_docx:
            return self._extract_docx(file_path)
        elif ext == 'doc':
            # .doc requires external tools - try multiple methods
            return self._extract_doc_legacy(file_path)
        else:
            # No docx library available
            logger.warning("python-docx not available, cannot extract .docx files")
            return "", "docx:not_available"
    
    def _extract_docx(self, file_path: str) -> Tuple[str, str]:
        """Extract text from .docx using python-docx."""
        try:
            import docx
            doc = docx.Document(file_path)
            
            # Extract all paragraphs
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            text = '\n\n'.join(paragraphs)
            
            # Also extract tables if present
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        text += '\n' + row_text
            
            return text, "docx:python-docx"
            
        except Exception as e:
            if self.verbose:
                logger.warning(f"python-docx extraction failed: {e}")
            return "", "docx:error"
    
    def _extract_doc_legacy(self, file_path: str) -> Tuple[str, str]:
        """
        Extract text from legacy .doc format.
        Tries multiple methods: antiword, textract, direct read.
        """
        # Method 1: Try antiword (if available)
        try:
            import subprocess
            result = subprocess.run(
                ['antiword', file_path],
                capture_output=True,
                text=True,
                timeout=EXTRACTION_TIMEOUT
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout, "doc:antiword"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Method 2: Try textract (if available)
        try:
            import textract
            text = textract.process(file_path, encoding='utf-8').decode('utf-8')
            if text:
                return text, "doc:textract"
        except ImportError:
            pass
        except Exception:
            pass
        
        # Method 3: Try reading as plain text (low quality)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            if text and len(text.strip()) > 100:
                logger.warning("⚠️ Using low-quality plain text extraction for .doc file")
                return text, "doc:plaintext_fallback"
        except:
            pass
        
        logger.error("❌ No method available to extract .doc file. Install antiword or textract.")
        return "", "doc:no_extractor"
    
    def _extract_html(self, file_path: str) -> Tuple[str, str]:
        """Extract text from HTML/XML files."""
        if not self.has_bs4:
            logger.warning("BeautifulSoup not available, using plain text extraction")
            return self._extract_plaintext(file_path)
        
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'head', 'meta']):
                element.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            return text, "html:beautifulsoup"
            
        except Exception as e:
            if self.verbose:
                logger.warning(f"BeautifulSoup extraction failed: {e}, trying plain text")
            return self._extract_plaintext(file_path)
    
    def _extract_rtf(self, file_path: str) -> Tuple[str, str]:
        """Extract text from RTF files."""
        if not self.has_striprtf:
            logger.warning("striprtf not available, using plain text extraction")
            return self._extract_plaintext(file_path)
        
        try:
            from striprtf.striprtf import rtf_to_text
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()
            
            text = rtf_to_text(rtf_content)
            return text, "rtf:striprtf"
            
        except Exception as e:
            if self.verbose:
                logger.warning(f"striprtf extraction failed: {e}, trying plain text")
            return self._extract_plaintext(file_path)
    
    def _extract_plaintext(self, file_path: str) -> Tuple[str, str]:
        """Extract plain text file."""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return text, "txt:utf8"
        except UnicodeDecodeError:
            # Try with error handling
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                return text, "txt:utf8_ignore"
            except Exception as e:
                logger.error(f"Failed to read plain text file: {e}")
                return "", "txt:error"


# Convenience function
def extract_text_from_file_unified(file_path: str, verbose: bool = False) -> Tuple[str, str]:
    """
    Extract text from any supported file format.
    
    Args:
        file_path: Path to file
        verbose: Enable verbose logging
        
    Returns:
        Tuple of (extracted_text, method_used)
    """
    extractor = UnifiedTextExtractor(verbose=verbose)
    return extractor.extract_text(file_path)


# Backward compatibility wrapper
def extract_text_from_file_smart(file_path: str) -> str:
    """
    Extract text from file (backward compatible).
    Returns only text (not method).
    """
    text, _ = extract_text_from_file_unified(file_path, verbose=False)
    return text
