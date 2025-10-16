#!/usr/bin/env python3
"""
Robust PDF Text Extraction with Multiple Fallback Libraries
Provides reliable text extraction from PDFs using multiple libraries with intelligent fallbacks.
"""

import logging
from typing import Optional, Tuple, List
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)

# USER OPTIMIZATION: Per-library timeout to prevent hanging
EXTRACTION_TIMEOUT = 45  # seconds per library
FAST_EXTRACTION_TIMEOUT = 20  # seconds for fast libraries

# Import footnote converter
try:
    from src.footnote_to_endnote_converter import convert_footnotes_to_endnotes
    FOOTNOTE_CONVERTER_AVAILABLE = True
except ImportError:
    logger.warning("Footnote converter not available")
    FOOTNOTE_CONVERTER_AVAILABLE = False

class RobustPDFExtractor:
    """
    Robust PDF text extraction with multiple library fallbacks.

    Performance ranking (based on testing):
    1. PyMuPDF (fitz) - Best overall performance
    2. PDFMiner - Good balance of speed and accuracy
    3. PDFPlumber - Good for structured documents
    4. PyPDF - Basic functionality
    5. PyPDF2 - Legacy, least reliable
    """

    def __init__(self, convert_footnotes: bool = True, verbose: bool = False):
        """
        Initialize PDF extractor.
        
        Args:
            convert_footnotes: Whether to convert footnotes to endnotes (improves citation extraction)
            verbose: Enable verbose logging (default: False for speed)
        """
        self.available_libraries = self._check_available_libraries()
        self.convert_footnotes = convert_footnotes and FOOTNOTE_CONVERTER_AVAILABLE
        self.verbose = verbose

    def _check_available_libraries(self) -> List[str]:
        """Check which PDF libraries are available. USER OPTIMIZATION: Silent checks for speed."""
        libraries = []

        # Test PyMuPDF (best performer) - FASTEST
        try:
            import fitz
            libraries.append('fitz')
        except ImportError:
            pass

        # Test PDFPlumber (fast and accurate) - SECOND FASTEST
        try:
            import pdfplumber
            libraries.append('pdfplumber')
        except ImportError:
            pass

        # Test PyPDF (basic, fast)
        try:
            import pypdf
            libraries.append('pypdf')
        except ImportError:
            pass

        # Test PyPDF2 (legacy, slower)
        try:
            import PyPDF2
            libraries.append('PyPDF2')
        except ImportError:
            pass
            
        # Test PDFMiner (SLOWEST but thorough) - LAST RESORT
        try:
            from pdfminer.high_level import extract_text
            libraries.append('pdfminer')
        except ImportError:
            pass

        if libraries:
            logger.info(f"PDF extraction libraries available: {', '.join(libraries)}")
        else:
            logger.error("No PDF extraction libraries available!")
            
        return libraries

    def extract_text(self, pdf_path: str, max_pages: Optional[int] = None) -> Tuple[str, str]:
        """
        USER OPTIMIZED: Extract text from PDF with timeout protection and early exit.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process (None for all)

        Returns:
            Tuple of (extracted_text, library_used)
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        start_time = time.time()
        
        # Try libraries in order of SPEED (fitz/pdfplumber fastest)
        for library in self.available_libraries:
            try:
                if self.verbose:
                    logger.info(f"Trying {library}...")
                
                # USER OPTIMIZATION: Use timeout to prevent hanging
                timeout = FAST_EXTRACTION_TIMEOUT if library in ['fitz', 'pdfplumber', 'pypdf'] else EXTRACTION_TIMEOUT
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._extract_with_library, pdf_path, library, max_pages)
                    try:
                        text = future.result(timeout=timeout)
                    except FutureTimeoutError:
                        logger.warning(f"⚠️ {library} timed out after {timeout}s")
                        continue

                if text and len(text.strip()) > 100:  # Minimum viable text
                    # USER OPTIMIZATION: Quick quality check (no complex scoring for speed)
                    quality_score = self._assess_text_quality_fast(text)
                    
                    if self.verbose:
                        logger.info(f"✅ {library}: {len(text):,} chars, quality={quality_score:.2f}")

                    # USER OPTIMIZATION: Lower threshold for fast libraries (they're reliable)
                    threshold = 0.2 if library in ['fitz', 'pdfplumber'] else 0.3
                    
                    if quality_score >= threshold:
                        # Convert footnotes if enabled (fast operation)
                        if self.convert_footnotes:
                            try:
                                text, footnote_count = convert_footnotes_to_endnotes(text, enable=True)
                                if self.verbose and footnote_count > 0:
                                    logger.info(f"📝 Converted {footnote_count} footnotes")
                            except:
                                pass  # Fail silently, use original
                        
                        elapsed = time.time() - start_time
                        logger.info(f"✅ PDF extracted in {elapsed:.1f}s using {library}")
                        return text, library
                    else:
                        if self.verbose:
                            logger.warning(f"⚠️ {library} quality too low ({quality_score:.2f})")
                        continue
                else:
                    if self.verbose:
                        logger.warning(f"⚠️ {library} insufficient text ({len(text) if text else 0} chars)")
                    continue

            except Exception as e:
                if self.verbose:
                    logger.warning(f"❌ {library} failed: {e}")
                continue

        # All libraries failed
        elapsed = time.time() - start_time
        logger.error(f"❌ All PDF extraction libraries failed after {elapsed:.1f}s")
        return "", "failed"

    def _extract_with_library(self, pdf_path: str, library: str, max_pages: Optional[int]) -> str:
        """Extract text using a specific library."""
        if library == 'fitz':
            return self._extract_fitz(pdf_path, max_pages)
        elif library == 'pdfminer':
            return self._extract_pdfminer(pdf_path, max_pages)
        elif library == 'pdfplumber':
            return self._extract_pdfplumber(pdf_path, max_pages)
        elif library == 'pypdf':
            return self._extract_pypdf(pdf_path, max_pages)
        elif library == 'PyPDF2':
            return self._extract_pypdf2(pdf_path, max_pages)
        else:
            raise ValueError(f"Unknown library: {library}")

    def _extract_fitz(self, pdf_path: str, max_pages: Optional[int]) -> str:
        """Extract text using PyMuPDF (fitz) - Best performer."""
        import fitz

        doc = fitz.open(pdf_path)
        text = ''

        try:
            pages_to_process = range(min(max_pages, len(doc))) if max_pages else range(len(doc))

            for page_num in pages_to_process:
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text += page_text + '\n'

        finally:
            doc.close()

        return text

    def _extract_pdfminer(self, pdf_path: str, max_pages: Optional[int]) -> str:
        """Extract text using PDFMiner - Good balance."""
        from pdfminer.high_level import extract_text
        from pdfminer.layout import LAParams
        from io import StringIO
        import logging as pdfminer_logging
        
        # USER OPTIMIZATION: Disable verbose PDFMiner logging for speed
        pdfminer_logger = pdfminer_logging.getLogger('pdfminer')
        original_level = pdfminer_logger.level
        pdfminer_logger.setLevel(pdfminer_logging.WARNING)  # Suppress DEBUG spam
        
        try:
            laparams = LAParams(
                line_margin=0.5,
                word_margin=0.1,
                char_margin=2.0,
                detect_vertical=True,
                all_texts=True
            )

            # PDFMiner doesn't have direct page limit, so we'll extract all and truncate if needed
            text = extract_text(pdf_path, laparams=laparams)

            if max_pages and text:
                # Rough estimation: ~2000 chars per page
                max_chars = max_pages * 2000
                if len(text) > max_chars:
                    text = text[:max_chars]

            return text
        finally:
            # Restore original logging level
            pdfminer_logger.setLevel(original_level)

    def _extract_pdfplumber(self, pdf_path: str, max_pages: Optional[int]) -> str:
        """Extract text using PDFPlumber - Good for structured documents."""
        import pdfplumber

        text = ''
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_process = pdf.pages[:max_pages] if max_pages else pdf.pages

            for page in pages_to_process:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'

        return text

    def _extract_pypdf(self, pdf_path: str, max_pages: Optional[int]) -> str:
        """Extract text using PyPDF - Basic functionality."""
        import pypdf

        text = ''
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            pages_to_process = range(min(max_pages, len(pdf_reader.pages))) if max_pages else range(len(pdf_reader.pages))

            for page_num in pages_to_process:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + '\n'

        return text

    def _extract_pypdf2(self, pdf_path: str, max_pages: Optional[int]) -> str:
        """Extract text using PyPDF2 - Legacy library."""
        import PyPDF2

        text = ''
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages_to_process = range(min(max_pages, len(pdf_reader.pages))) if max_pages else range(len(pdf_reader.pages))

            for page_num in pages_to_process:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + '\n'

        return text

    def _assess_text_quality_fast(self, text: str) -> float:
        """
        USER OPTIMIZED: Fast quality check (no complex string operations).
        Returns a score from 0.0 to 1.0.
        """
        if not text or len(text.strip()) < 50:
            return 0.0

        text_lower = text.lower()
        score = 0.0

        # Quick legal/citation indicator check (most important)
        indicators = ['court', 'v.', 'f.', 'u.s.', 'p.', 'supp', 'plaintiff', 'defendant']
        matches = sum(1 for ind in indicators if ind in text_lower)
        score += min(matches / len(indicators), 1.0) * 0.7

        # Quick structure check (periods indicate sentences)
        period_ratio = text.count('.') / len(text) if text else 0
        if 0.01 < period_ratio < 0.1:  # Reasonable range
            score += 0.3

        return min(score, 1.0)
    
    def _assess_text_quality(self, text: str) -> float:
        """Backward compatibility wrapper."""
        return self._assess_text_quality_fast(text)


# Convenience function for easy use
def extract_pdf_text_robust(pdf_path: str, max_pages: Optional[int] = None, convert_footnotes: bool = True, verbose: bool = False) -> Tuple[str, str]:
    """
    USER OPTIMIZED: Fast PDF extraction with robust fallbacks.

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to process (None for all)
        convert_footnotes: Whether to convert footnotes to endnotes (improves citation extraction)
        verbose: Enable verbose logging (default: False for speed)

    Returns:
        Tuple of (extracted_text, library_used)
    """
    extractor = RobustPDFExtractor(convert_footnotes=convert_footnotes, verbose=verbose)
    return extractor.extract_text(pdf_path, max_pages)


# Compatibility aliases for old function names
def extract_text_from_pdf_smart(pdf_path: str, max_pages: Optional[int] = None) -> str:
    """
    Compatibility wrapper for extract_pdf_text_robust.
    Returns only the text (not the library name) for backward compatibility.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to process (None for all)
    
    Returns:
        Extracted text as string
    """
    text, _ = extract_pdf_text_robust(pdf_path, max_pages)
    return text


def extract_text_from_pdf_ultra_fast(pdf_path: str) -> str:
    """
    Compatibility wrapper for fast PDF extraction.
    Uses the same robust extraction as extract_text_from_pdf_smart.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Extracted text as string
    """
    return extract_text_from_pdf_smart(pdf_path)


if __name__ == "__main__":
    # Test the robust extractor
    import sys

    if len(sys.argv) < 2:
        print("Usage: python robust_pdf_extractor.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    extractor = RobustPDFExtractor()

    print(f"🔍 Testing robust PDF extraction on: {pdf_path}")
    text, library = extractor.extract_text(pdf_path)

    print(f"✅ Extraction completed using: {library}")
    print(f"📊 Text length: {len(text):,} characters")

    if text:
        # Count citation indicators
        citation_count = text.count('U.S.') + text.count('F.3d') + text.count('F.2d') + text.count('F. Supp')
        print(f"📋 Citation indicators found: {citation_count}")

        # Show sample
        sample = text[:500].replace('\n', ' ').strip()
        print(f"📖 Sample text: {sample}...")
    else:
        print("❌ No text extracted")
