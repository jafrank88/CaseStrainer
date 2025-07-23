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
import warnings
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import docx
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# Try to import the unified citation processor
_unified_processor_available = False
_enhanced_processor_available = False

try:
    from .unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
    _unified_processor_available = True
except ImportError:
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        _unified_processor_available = True
    except ImportError:
        logger.warning("Unified citation processor v2 not available")

# Try to import the enhanced processor as fallback
try:
    from .unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
    _enhanced_processor_available = True
except ImportError:
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        _enhanced_processor_available = True
    except ImportError:
        try:
            # Try alternative import path
            from enhanced_citation_processor import EnhancedCitationProcessor as UnifiedCitationProcessor
            _enhanced_processor_available = True
        except ImportError:
            logger.warning("Enhanced citation processor not available")

# Try to import the enhanced v2 processor
try:
    from .enhanced_v2_processor import EnhancedV2Processor
    _enhanced_v2_processor_available = True
except ImportError:
    try:
        from enhanced_v2_processor import EnhancedV2Processor
        _enhanced_v2_processor_available = True
    except ImportError:
        _enhanced_v2_processor_available = False
        logger.warning("Enhanced v2 processor not available")

# Public constants (read-only) - use different names to avoid conflicts
UNIFIED_PROCESSOR_AVAILABLE_UNIFIED = _unified_processor_available
ENHANCED_PROCESSOR_AVAILABLE_UNIFIED = _enhanced_processor_available

# Legacy aliases for backward compatibility
UNIFIED_PROCESSOR_AVAILABLE = UNIFIED_PROCESSOR_AVAILABLE_UNIFIED
ENHANCED_PROCESSOR_AVAILABLE = ENHANCED_PROCESSOR_AVAILABLE_UNIFIED


class UltraFastPDFProcessor:
    """
    Ultra-fast PDF processor - prioritizes speed over everything else.
    """
    
    def __init__(self):
        super().__init__()
        # Single compiled regex for critical citation fixes only
        self._critical_fixes = re.compile(
            r'(\d+)\s*([USF])\.\s*([SCtEd]+)\.\s*[\n\-]\s*(\d+)'
        )
        self._whitespace_normalize = re.compile(r'\s+')

    def extract_text_super_fast(self, file_path: str) -> str:
        """
        Super fast PDF extraction - no frills, maximum speed.
        """
        # Skip all validation except basic file existence
        if not os.path.exists(file_path):
            return "Error: File not found"
        
        # Try pdfminer.six directly - it's usually the fastest
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(file_path)
            
            if text and text.strip():
                # MINIMAL cleaning - only fix broken citations and normalize whitespace
                text = self._critical_fixes.sub(r'\1 \2.\3. \4', text)
                text = self._whitespace_normalize.sub(' ', text)
                return text.strip()
                
        except Exception as e:
            logger.warning(f"pdfminer failed: {e}")
        
        # Fast PyPDF2 fallback
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if reader.is_encrypted:
                    return "Error: Encrypted PDF"
                
                # Extract all pages at once
                text = "".join(page.extract_text() for page in reader.pages)
                if text:
                    return self._whitespace_normalize.sub(' ', text).strip()
                    
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")
        
        return "Error: Extraction failed"

    def preprocess_minimal(self, text: str) -> str:
        """
        Absolute minimal preprocessing - just whitespace normalization.
        """
        if not text:
            return ""
        
        # ONLY normalize whitespace - skip everything else
        return self._whitespace_normalize.sub(' ', text).strip()


class OCROptimizedPDFProcessor:
    """
    PDF processor optimized for OCR'ed documents with fast fallbacks.
    """
    
    def __init__(self):
        super().__init__()
        # Pre-compiled patterns for OCR-specific fixes
        self._ocr_citation_fixes = {
            # Common OCR errors in citations - compiled once for speed
            'us_reports': re.compile(r'(\d+)\s*[Uu0o]\s*[.,]?\s*[Ss5]\s*[.,]?\s*(\d+)', re.IGNORECASE),
            'supreme_court': re.compile(r'(\d+)\s*[Ss5]\s*[.,]?\s*[CcGg][Tt7]\s*[.,]?\s*(\d+)', re.IGNORECASE),
            'lawyers_edition': re.compile(r'(\d+)\s*[Ll1I]\s*[.,]?\s*[Ee3]\s*[dD]\s*[.,]?\s*(\d+)', re.IGNORECASE),
            'federal_reporter': re.compile(r'(\d+)\s*[Ff]\s*[.,]?\s*(2[dD]|3[dD]|4th)?\s*(\d+)', re.IGNORECASE),
        }
        
        # Common OCR character substitutions (most critical ones only)
        self._ocr_char_fixes = {
            re.compile(r'\b[Il1|]\b'): 'I',  # Standalone I/l/1/| to I
            re.compile(r'\b[0O]\b'): 'O',     # Standalone 0/O to O
            re.compile(r'(\d)[Il1|](\d)'): r'\g<1>1\g<2>',  # Between digits: I/l/| to 1
            re.compile(r'(\d)[0O](\d)'): r'\g<1>0\g<2>',    # Between digits: O to 0
            re.compile(r'([A-Za-z])[0O]([A-Za-z])'): r'\g<1>o\g<2>',  # Between letters: O to o
        }
        
        # Single whitespace normalizer
        self._whitespace = re.compile(r'\s+')
        
        # Page number/header patterns
        self._page_patterns = re.compile(r'^\s*(?:\d{1,4}|Page\s+\d+|\d+\s*$)\s*$', re.MULTILINE | re.IGNORECASE)

    def extract_text_ocr_optimized(self, file_path: str) -> str:
        """
        Extract text optimized for OCR'ed documents.
        
        Strategy:
        1. Try PyPDF2 (fastest and extracts most text)
        2. Fall back to pdfplumber (best for complex OCR'ed PDFs)
        3. Fall back to pdfminer.six
        4. Apply targeted OCR fixes
        """
        
        # Method 1: PyPDF2 - fastest and extracts most text
        text = self._extract_with_pypdf2(file_path)
        if text:
            return self._apply_ocr_fixes(text)
        
        # Method 2: pdfplumber - excellent for complex OCR'ed PDFs
        text = self._extract_with_pdfplumber(file_path)
        if text:
            return self._apply_ocr_fixes(text)
        
        # Method 3: pdfminer.six - reliable general fallback
        text = self._extract_with_pdfminer(file_path)
        if text:
            return self._apply_ocr_fixes(text)
        
        return "Error: All extraction methods failed"

    def _extract_with_pdfplumber(self, file_path: str) -> Optional[str]:
        """
        Extract using pdfplumber - often best for OCR'ed documents.
        pdfplumber is excellent at extracting text that has been OCR'ed.
        
        Note: pdfplumber is an optional dependency. If not installed,
        this method will gracefully fall back to other extraction methods.
        """
        try:
            import pdfplumber  # type: ignore # Optional dependency - see requirements.txt
            
            text_parts = []
            with pdfplumber.open(file_path) as pdf:  # type: ignore[unknown-variable-type]
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            if text_parts:
                text = "\n".join(text_parts)
                logger.info(f"pdfplumber extracted {len(text)} characters")
                return text
                
        except ImportError as e:
            logger.debug(f"pdfplumber not available - skipping pdfplumber extraction: {e}")
            return None
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return None

    def _extract_with_pdfminer(self, file_path: str) -> Optional[str]:
        """Extract using pdfminer.six - reliable fallback."""
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(file_path)
            
            if text and text.strip():
                logger.info(f"pdfminer.six extracted {len(text)} characters")
                return text
                
        except Exception as e:
            logger.warning(f"pdfminer.six extraction failed: {e}")
        
        return None

    def _extract_with_pypdf2(self, file_path: str) -> Optional[str]:
        """Extract using PyPDF2 - fast fallback (DEPRECATED: use isolation-aware logic instead)."""
        warnings.warn(
            "_extract_with_pypdf2 is deprecated. Use isolation-aware PDF extraction instead.",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:  # type: ignore[unknown-member-type]
                reader = PyPDF2.PdfReader(file)
                if reader.is_encrypted:
                    return None
                
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                if text_parts:
                    text = "\n".join(text_parts)
                    logger.info(f"PyPDF2 extracted {len(text)} characters")
                    return text
                    
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
        
        return None

    def _apply_ocr_fixes(self, text: str) -> str:
        """
        Apply OCR-specific fixes efficiently.
        
        This is optimized for speed while fixing the most common OCR issues
        that affect citation detection.
        """
        if not text:
            return ""
        
        # Step 1: Fix citation patterns (most important for legal documents)
        text = self._ocr_citation_fixes['us_reports'].sub(r'\1 U.S. \2', text)
        text = self._ocr_citation_fixes['supreme_court'].sub(r'\1 S.Ct. \2', text)
        text = self._ocr_citation_fixes['lawyers_edition'].sub(r'\1 L.Ed. \2', text)
        text = self._ocr_citation_fixes['federal_reporter'].sub(r'\1 F.\2 \3', text)
        
        # Step 2: Fix common OCR character errors (only the most critical ones)
        for pattern, replacement in self._ocr_char_fixes.items():
            text = pattern.sub(replacement, text)
        
        # Step 3: Remove page numbers and normalize whitespace
        text = self._page_patterns.sub('', text)
        text = self._whitespace.sub(' ', text)
        
        return text.strip()

    def extract_text_non_ocr_fallback(self, file_path: str) -> str:
        """
        DEPRECATED: Use isolation-aware PDF extraction logic instead.
        Fallback extraction for non-OCR'ed documents (born-digital PDFs).
        Uses minimal processing for maximum speed.
        """
        warnings.warn(
            "extract_text_non_ocr_fallback is deprecated. Use isolation-aware PDF extraction instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # PyPDF2 first - fastest for born-digital PDFs
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if not reader.is_encrypted:
                    text = "".join(page.extract_text() for page in reader.pages)
                    if text:
                        return self._whitespace.sub(' ', text).strip()
        except:
            pass
        
        # pdfminer.six fallback
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(file_path)
            if text:
                # Minimal processing - just normalize whitespace
                return self._whitespace.sub(' ', text).strip()
        except:
            pass
        
        return "Error: Extraction failed"


def detect_ocr_characteristics(text: str) -> Dict[str, Any]:
    """
    Analyze text to determine if it's likely from OCR and what fixes might be needed.
    """
    if not text:
        return {"is_likely_ocr": False}
    
    sample = text[:5000]  # Analyze first 5000 characters
    
    # OCR indicators
    ocr_indicators = {
        "common_ocr_errors": len(re.findall(r'[Il1|0O]', sample)),
        "broken_citations": len(re.findall(r'\d+\s*[Uu0o]\s*[Ss5]\s*\d+', sample)),
        "spacing_issues": len(re.findall(r'[A-Za-z]\s+[.,;:]', sample)),
        "character_substitutions": len(re.findall(r'[Il1|]{2,}|[0O]{2,}', sample)),
    }
    
    # Score OCR likelihood
    ocr_score = sum(ocr_indicators.values())
    total_chars = len(sample)
    ocr_ratio = ocr_score / total_chars if total_chars > 0 else 0
    
    return {
        "is_likely_ocr": ocr_ratio > 0.01,  # 1% OCR error rate threshold
        "ocr_score": ocr_score,
        "ocr_ratio": ocr_ratio,
        "indicators": ocr_indicators,
        "recommendations": {
            "use_ocr_fixes": ocr_ratio > 0.005,
            "focus_on_citations": ocr_indicators["broken_citations"] > 0,
            "fix_spacing": ocr_indicators["spacing_issues"] > 5,
        }
    }


def extract_text_smart_strategy(file_path: str, assume_ocr: bool = True) -> str:
    """
    Smart extraction strategy that assumes OCR first, then falls back.
    
    Args:
        file_path: Path to PDF file
        assume_ocr: If True, optimize for OCR'ed documents first
        
    Returns:
        Extracted text
    """
    processor = OCROptimizedPDFProcessor()
    
    if assume_ocr:
        # Try OCR-optimized extraction first
        result = processor.extract_text_ocr_optimized(file_path)
        
        # If OCR extraction gives very little text, try non-OCR method
        if result and not result.startswith("Error:") and len(result) > 100:
            return result
        else:
            logger.info("OCR extraction yielded little text, trying non-OCR fallback")
            return processor.extract_text_non_ocr_fallback(file_path)
    else:
        # Use non-OCR method first
        return processor.extract_text_non_ocr_fallback(file_path)


class OptimizedPDFProcessor:
    """
    Optimized PDF processor focused on speed while maintaining quality.
    """
    
    def __init__(self):
        super().__init__()
        # Pre-compile regex patterns for better performance
        self._citation_patterns = {
            'us_reports': re.compile(r'(\d+)\s*U\.\s*S\.\s*(\d+)'),
            'supreme_court': re.compile(r'(\d+)\s*S\.\s*Ct\.\s*(\d+)'),
            'lawyers_edition': re.compile(r'(\d+)\s*L\.\s*Ed\.\s*(\d+)'),
            'federal': re.compile(r'(\d+)\s*F\.\s*(2d|3d|4th)?\s*(\d+)'),
        }
        
        # Pre-compile cleaning patterns
        self._cleaning_patterns = {
            'line_breaks_in_citations': re.compile(r'(\d+)\s*([USF])\.\s*([SCtEd]+)\.\s*\n\s*(\d+)'),
            'page_breaks_in_citations': re.compile(r'(\d+)\s*([USF])\.\s*([SCtEd]+)\.\s*-\s*(\d+)'),
            'abbreviation_spacing': re.compile(r'([A-Z])\.\s+([A-Z])'),
            'whitespace_normalize': re.compile(r'\s+'),
            'standalone_page_numbers': re.compile(r'^\s*\d{1,3}\s*$', re.MULTILINE),
            'short_uppercase': re.compile(r'^[A-Z]{1,3}$')
        }

    def extract_text_from_pdf_fast(self, file_path: str) -> str:
        """
        Fast PDF text extraction with minimal overhead.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        start_time = time.time()
        file_size = os.path.getsize(file_path)
        logger.info(f"Extracting text from PDF: {file_path} ({file_size} bytes)")
        
        # Quick validation without reading entire header
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)  # Read only first 8 bytes instead of 1024
                if not header.startswith(b'%PDF-'):
                    return "Error: Invalid PDF header"
        except Exception as e:
            return f"Error: {str(e)}"
        
        # Try pdfminer.six first (usually fastest)
        text = self._extract_with_pdfminer(file_path, file_size)
        if text:
            extraction_time = time.time() - start_time
            logger.info(f"PDF extraction completed in {extraction_time:.2f}s")
            return text
        
        # Fallback to PyPDF2 if pdfminer fails
        text = self._extract_with_pypdf2(file_path)
        if text:
            extraction_time = time.time() - start_time
            logger.info(f"PDF extraction (PyPDF2 fallback) completed in {extraction_time:.2f}s")
            return text
        
        return "Error: All extraction methods failed"

    def _extract_with_pdfminer(self, file_path: str, file_size: int) -> Optional[str]:
        """Extract text using pdfminer.six with optimizations."""
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract_text
            
            # Remove threading overhead - pdfminer is generally reliable
            # The timeout mechanism was adding significant overhead
            text = pdfminer_extract_text(file_path)
            
            if text and text.strip():
                logger.info(f"Successfully extracted {len(text)} characters with pdfminer.six")
                
                # Apply progressive cleaning based on file size
                if file_size <= 1024 * 1024:  # 1MB - full cleaning
                    cleaned_text = self._clean_text_comprehensive(text)
                elif file_size <= 10 * 1024 * 1024:  # 10MB - medium cleaning
                    cleaned_text = self._clean_text_medium(text)
                else:  # Large files - minimal cleaning
                    cleaned_text = self._clean_text_minimal(text)
                
                return cleaned_text
                
        except Exception as e:
            logger.warning(f"pdfminer.six extraction failed: {str(e)}")
            return None

    def _extract_with_pypdf2(self, file_path: str) -> Optional[str]:
        """Extract text using PyPDF2 as fallback."""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if reader.is_encrypted:
                    return "Error: PDF file is encrypted"
                
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                if text_parts:
                    text = "\n".join(text_parts)
                    logger.info(f"Successfully extracted {len(text)} characters with PyPDF2")
                    return self._clean_text_medium(text)
                    
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
            return None

    def _clean_text_minimal(self, text: str) -> str:
        """Minimal text cleaning for large files."""
        # Only essential cleaning for performance
        text = self._cleaning_patterns['whitespace_normalize'].sub(' ', text)
        text = text.strip()
        return text

    def _clean_text_medium(self, text: str) -> str:
        """Medium text cleaning - balance of speed and quality."""
        # Remove non-printable characters efficiently
        text = "".join(char for char in text if char.isprintable() or char in "\n\t ")
        
        # Fix critical citation patterns only
        text = self._cleaning_patterns['line_breaks_in_citations'].sub(r'\1 \2.\3. \4', text)
        text = self._cleaning_patterns['page_breaks_in_citations'].sub(r'\1 \2.\3. \4', text)
        
        # Normalize whitespace
        text = self._cleaning_patterns['whitespace_normalize'].sub(' ', text)
        
        return text.strip()

    def _clean_text_comprehensive(self, text: str) -> str:
        """Comprehensive text cleaning for smaller files."""
        # Remove non-printable characters
        text = "".join(
            char for char in text if char.isprintable() or char in ".,;:()[]{}\n\t "
        )
        
        # Fix all citation patterns
        for pattern_name, pattern in self._citation_patterns.items():
            if pattern_name == 'us_reports':
                text = pattern.sub(r'\1 U.S. \2', text)
            elif pattern_name == 'supreme_court':
                text = pattern.sub(r'\1 S.Ct. \2', text)
            elif pattern_name == 'lawyers_edition':
                text = pattern.sub(r'\1 L.Ed. \2', text)
            elif pattern_name == 'federal':
                text = pattern.sub(r'\1 F.\2 \3', text)
        
        # Fix line and page breaks in citations
        text = self._cleaning_patterns['line_breaks_in_citations'].sub(r'\1 \2.\3. \4', text)
        text = self._cleaning_patterns['page_breaks_in_citations'].sub(r'\1 \2.\3. \4', text)
        
        # Fix abbreviation spacing
        text = self._cleaning_patterns['abbreviation_spacing'].sub(r'\1.\2', text)
        
        # Normalize whitespace
        text = self._cleaning_patterns['whitespace_normalize'].sub(' ', text)
        
        # Remove standalone page numbers (only for comprehensive cleaning)
        lines = text.splitlines()
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip standalone page numbers and very short uppercase lines
            if (self._cleaning_patterns['standalone_page_numbers'].match(line) or 
                (len(line) <= 3 and self._cleaning_patterns['short_uppercase'].match(line))):
                continue
            filtered_lines.append(line)
        
        text = " ".join(filtered_lines)
        return text.strip()

    def preprocess_text_fast(self, text: str, skip_ocr_correction: bool = True) -> str:
        """
        Fast text preprocessing with minimal overhead.
        
        Args:
            text: Text to preprocess
            skip_ocr_correction: Skip OCR correction (recommended for speed)
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Basic cleaning only
        cleaned = text.strip()
        
        # Only normalize unicode if necessary (check for non-ASCII chars first)
        if any(ord(char) > 127 for char in cleaned[:100]):  # Check first 100 chars
            cleaned = unicodedata.normalize('NFKC', cleaned)
        
        # Remove BOM and zero-width spaces
        cleaned = cleaned.replace('\ufeff', '').replace('\u200b', '')
        
        # Skip OCR corrections by default for speed
        if not skip_ocr_correction:
            cleaned = self._apply_minimal_ocr_corrections(cleaned)
        
        # Final whitespace normalization
        cleaned = self._cleaning_patterns['whitespace_normalize'].sub(' ', cleaned)
        
        return cleaned.strip()

    def _apply_minimal_ocr_corrections(self, text: str) -> str:
        """Apply only the most critical OCR corrections for speed."""
        # Only apply the most common and safe corrections
        safe_corrections = {
            'feclera1': 'federal',
            'rnay': 'may',
            'ansv.v.er': 'answer',
            'Conv.oy': 'Convoy',
            'v.v.hen': 'when',
            'v.v.': 'v.',
        }
        
        corrected = text
        for error, correction in safe_corrections.items():
            # Use word boundaries for safer replacement
            corrected = re.sub(rf'\b{error}\b', correction, corrected, flags=re.IGNORECASE)
        
        return corrected


# Drop-in replacement for the slow method
def extract_text_from_pdf_optimized(file_path: str, convert_to_md: bool = False) -> str:
    """
    Optimized drop-in replacement for _extract_text_from_pdf method.
    
    This removes the major performance bottlenecks:
    - Threading overhead for timeout management
    - Excessive text cleaning operations
    - Redundant preprocessing steps
    - Large file processing inefficiencies
    """
    processor = OptimizedPDFProcessor()
    
    # Skip markdown conversion for speed (unless specifically requested)
    if convert_to_md:
        logger.info("Markdown conversion requested - this may impact performance")
        # Add markdown conversion logic here if needed
    
    return processor.extract_text_from_pdf_fast(file_path)


# Ultra-fast replacement - drops all the expensive operations
def extract_text_from_pdf_ULTRA_FAST(file_path: str) -> str:
    """
    Ultra-fast replacement that eliminates all performance bottlenecks.
    This should be 10-50x faster than the original.
    """
    processor = UltraFastPDFProcessor()
    return processor.extract_text_super_fast(file_path)


# Performance comparison helper
def benchmark_extraction_methods(file_path: str) -> Dict[str, Any]:
    """
    Benchmark different extraction methods to identify the fastest approach.
    """
    results = {}
    
    # Test optimized method
    start_time = time.time()
    try:
        optimized_text = extract_text_from_pdf_optimized(file_path)
        results['optimized'] = {
            'time': time.time() - start_time,
            'length': len(optimized_text) if optimized_text else 0,
            'success': bool(optimized_text and not optimized_text.startswith('Error:'))
        }
    except Exception as e:
        results['optimized'] = {'time': time.time() - start_time, 'error': str(e)}
    
    # Test ultra-fast method
    start_time = time.time()
    try:
        ultra_fast_text = extract_text_from_pdf_ULTRA_FAST(file_path)
        results['ultra_fast'] = {
            'time': time.time() - start_time,
            'length': len(ultra_fast_text) if ultra_fast_text else 0,
            'success': bool(ultra_fast_text and not ultra_fast_text.startswith('Error:'))
        }
    except Exception as e:
        results['ultra_fast'] = {'time': time.time() - start_time, 'error': str(e)}
    
    # Test basic pdfminer
    start_time = time.time()
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract_text
        basic_text = pdfminer_extract_text(file_path)
        results['basic_pdfminer'] = {
            'time': time.time() - start_time,
            'length': len(basic_text) if basic_text else 0,
            'success': bool(basic_text)
        }
    except Exception as e:
        results['basic_pdfminer'] = {'time': time.time() - start_time, 'error': str(e)}
    
    return results


# Benchmarking function to test OCR vs non-OCR performance
def benchmark_ocr_strategies(file_path: str):
    """
    Test different strategies to see which is fastest for your documents.
    """
    print(f"Benchmarking OCR strategies for: {file_path}")
    
    # Test OCR-optimized approach
    start = time.time()
    ocr_text = extract_text_smart_strategy(file_path, assume_ocr=True)
    ocr_time = time.time() - start
    print(f"📄 OCR-optimized: {ocr_time:.3f}s ({len(ocr_text)} chars)")
    
    # Test non-OCR approach
    start = time.time()
    non_ocr_text = extract_text_smart_strategy(file_path, assume_ocr=False)
    non_ocr_time = time.time() - start
    print(f"📝 Non-OCR method: {non_ocr_time:.3f}s ({len(non_ocr_text)} chars)")
    
    # Analyze the results
    if len(ocr_text) > 50:
        analysis = detect_ocr_characteristics(ocr_text)
        print(f"🔍 OCR analysis: {analysis}")
        
        if analysis['is_likely_ocr']:
            print("✅ Document appears to be OCR'ed - use OCR-optimized strategy")
        else:
            print("✅ Document appears to be born-digital - use non-OCR strategy")
    
    return {
        'ocr_time': ocr_time,
        'non_ocr_time': non_ocr_time,
        'ocr_length': len(ocr_text),
        'non_ocr_length': len(non_ocr_text),
        'faster_method': 'ocr' if ocr_time < non_ocr_time else 'non_ocr'
    }


class UnifiedDocumentProcessor:
    """
    Unified document processor that consolidates the best parts of all existing implementations.
    """
    
    def __init__(self):
        super().__init__()
        self.ocr_corrections = self._init_ocr_corrections()
        
        # Initialize citation processor
        if UNIFIED_PROCESSOR_AVAILABLE:
            # Use enhanced v2 processor for better accuracy
            try:
                from .enhanced_v2_processor import EnhancedV2Processor
                self.citation_processor = EnhancedV2Processor()
                logger.info("Using EnhancedV2Processor for improved accuracy")
            except ImportError:
                self.citation_processor = UnifiedCitationProcessorV2()
                logger.info("Using standard UnifiedCitationProcessorV2")
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
        """
        Smart PDF text extraction with OCR detection and ultra-fast fallback.
        
        This uses intelligent strategies to choose the best extraction method:
        1. OCR-optimized extraction for scanned documents
        2. Ultra-fast extraction for born-digital PDFs
        3. Smart fallback strategies for maximum performance
        """
        # Optionally convert to markdown
        if convert_to_md:
            md = self.convert_pdf_to_markdown(file_path)
            if md:
                logger.info("PDF to Markdown conversion succeeded.")
                return md
            else:
                logger.warning("PDF to Markdown conversion failed, falling back to text extraction.")
        
        # Use smart strategy - assumes OCR first, then falls back to ultra-fast
        return extract_text_smart_strategy(file_path, assume_ocr=True)

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
                        logger.info("Using enhanced citation processor")
                        
                        # Check if we're using the enhanced processor
                        if isinstance(self.citation_processor, EnhancedV2Processor):
                            logger.info("Processing with EnhancedV2Processor")
                            enhanced_results = self.citation_processor.process_text(preprocessed_text)
                            
                            # Convert enhanced results to standard format with clustering
                            for result in enhanced_results:
                                citation_dict = {
                                    'citation': result['citation'],
                                    'case_name': result.get('shared_case_name') or result['enhanced_case_name'] or result['original_case_name'],
                                    'extracted_case_name': result.get('shared_case_name') or result['enhanced_case_name'] or result['original_case_name'],
                                    'canonical_name': result['canonical_name'],
                                    'extracted_date': result.get('shared_year') or result['enhanced_year'] or result['original_year'],
                                    'canonical_date': result['canonical_date'],
                                    'verified': result['api_verified'],
                                    'court': '',  # Enhanced processor doesn't extract court
                                    'confidence': result['confidence'],
                                    'method': result['method'],
                                    'context': '',  # Enhanced processor doesn't extract context
                                    'is_parallel': result.get('is_parallel', False),
                                    'parallel_citations': result.get('parallel_citations', []),
                                    'url': '',  # Enhanced processor doesn't extract URLs
                                    'source': result['method'],
                                    'cluster_id': result.get('cluster_id'),
                                    'total_citations': result.get('total_citations_in_cluster', 1)
                                }
                                formatted_citations.append(citation_dict)
                        else:
                            logger.info("Using standard UnifiedCitationProcessorV2")
                            
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
    
    # Use smart PDF extraction strategy for better performance
    if file_path.lower().endswith('.pdf'):
        return extract_text_smart_strategy(file_path, assume_ocr=True)
    
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