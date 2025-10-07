#!/usr/bin/env python3
"""
Robust PDF Text Extraction with Multiple Fallback Libraries
Provides reliable text extraction from PDFs using multiple libraries with intelligent fallbacks.
"""

import logging
from typing import Optional, Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)

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

    def __init__(self, convert_footnotes: bool = True):
        """
        Initialize PDF extractor.
        
        Args:
            convert_footnotes: Whether to convert footnotes to endnotes (improves citation extraction)
        """
        self.available_libraries = self._check_available_libraries()
        self.convert_footnotes = convert_footnotes and FOOTNOTE_CONVERTER_AVAILABLE

    def _check_available_libraries(self) -> List[str]:
        """Check which PDF libraries are available."""
        libraries = []

        # Test PyMuPDF (best performer)
        try:
            import fitz
            libraries.append('fitz')
            logger.info("✅ PyMuPDF (fitz) available")
        except ImportError:
            logger.warning("❌ PyMuPDF (fitz) not available")

        # Test PDFMiner (good balance)
        try:
            from pdfminer.high_level import extract_text
            libraries.append('pdfminer')
            logger.info("✅ PDFMiner available")
        except ImportError:
            logger.warning("❌ PDFMiner not available")

        # Test PDFPlumber (good for structured docs)
        try:
            import pdfplumber
            libraries.append('pdfplumber')
            logger.info("✅ PDFPlumber available")
        except ImportError:
            logger.warning("❌ PDFPlumber not available")

        # Test PyPDF (basic functionality)
        try:
            import pypdf
            libraries.append('pypdf')
            logger.info("✅ PyPDF available")
        except ImportError:
            logger.warning("❌ PyPDF not available")

        # Test PyPDF2 (legacy)
        try:
            import PyPDF2
            libraries.append('PyPDF2')
            logger.info("✅ PyPDF2 available")
        except ImportError:
            logger.warning("❌ PyPDF2 not available")

        return libraries

    def extract_text(self, pdf_path: str, max_pages: Optional[int] = None) -> Tuple[str, str]:
        """
        Extract text from PDF using multiple fallback libraries.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process (None for all)

        Returns:
            Tuple of (extracted_text, library_used)
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Try libraries in order of performance
        for library in self.available_libraries:
            try:
                logger.info(f"Attempting PDF extraction with {library}")
                text = self._extract_with_library(pdf_path, library, max_pages)

                if text and len(text.strip()) > 100:  # Minimum viable text
                    # Validate extraction quality
                    quality_score = self._assess_text_quality(text)
                    logger.info(f"✅ {library} succeeded: {len(text):,} chars, quality score: {quality_score}")

                    if quality_score >= 0.3:  # Acceptable quality
                        # Convert footnotes to endnotes if enabled
                        if self.convert_footnotes:
                            try:
                                text, footnote_count = convert_footnotes_to_endnotes(text, enable=True)
                                if footnote_count > 0:
                                    logger.info(f"📝 Converted {footnote_count} footnotes to endnotes")
                            except Exception as e:
                                logger.warning(f"Footnote conversion failed: {e}, using original text")
                        
                        return text, library
                    else:
                        logger.warning(f"⚠️ {library} extracted text but quality is low ({quality_score:.2f})")
                        continue
                else:
                    logger.warning(f"⚠️ {library} extracted insufficient text ({len(text) if text else 0} chars)")
                    continue

            except Exception as e:
                logger.warning(f"❌ {library} failed: {e}")
                continue

        # All libraries failed
        logger.error("❌ All PDF extraction libraries failed")
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

    def _assess_text_quality(self, text: str) -> float:
        """
        Assess the quality of extracted text.

        Returns a score from 0.0 to 1.0 based on:
        - Presence of legal terminology
        - Sentence structure
        - Word length distribution
        - Citation indicators
        """
        if not text or len(text.strip()) < 50:
            return 0.0

        score = 0.0

        # Legal terminology indicators
        legal_terms = ['court', 'case', 'justice', 'opinion', 'plaintiff', 'defendant', 'appeal', 'motion']
        legal_score = sum(1 for term in legal_terms if term.lower() in text.lower()) / len(legal_terms)
        score += legal_score * 0.3

        # Citation indicators
        citation_indicators = ['u.s.', 'f.2d', 'f.3d', 's.ct.', 'supp.', 'cir.', 'dist.']
        citation_score = sum(1 for indicator in citation_indicators if indicator.lower() in text.lower()) / len(citation_indicators)
        score += citation_score * 0.4

        # Text structure indicators (sentences, paragraphs)
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        sentences_per_1000 = (sentence_count / len(text)) * 1000 if text else 0
        structure_score = min(sentences_per_1000 / 5, 1.0)  # Expect ~5 sentences per 1000 chars
        score += structure_score * 0.3

        return min(score, 1.0)


# Convenience function for easy use
def extract_pdf_text_robust(pdf_path: str, max_pages: Optional[int] = None, convert_footnotes: bool = True) -> Tuple[str, str]:
    """
    Convenience function to extract text from PDF with robust fallbacks.

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to process (None for all)
        convert_footnotes: Whether to convert footnotes to endnotes (improves citation extraction)

    Returns:
        Tuple of (extracted_text, library_used)
    """
    extractor = RobustPDFExtractor(convert_footnotes=convert_footnotes)
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
