"""
Test the actual PDF extraction pipeline with the same functions used in the application.
"""

import sys
import os
import logging
from pathlib import Path
import tempfile
import requests
from typing import Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the actual extraction functions from the application
from src.pdf_extraction_optimized import (
    extract_text_from_pdf_smart,
    extract_text_from_pdf_ultra_fast,
    SmartPDFExtractor,
    UltraFastPDFExtractor
)

def download_pdf(url: str, filename: str) -> str:
    """Download PDF from URL and save to a temporary file."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/pdf,application/x-pdf,application/octet-stream',
    }
    
    logger.info(f"Downloading PDF from: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    # Save to temp file
    temp_dir = Path(tempfile.gettempdir()) / "pdf_tests"
    temp_dir.mkdir(exist_ok=True)
    
    filepath = temp_dir / filename
    with open(filepath, 'wb') as f:
        f.write(response.content)
    
    logger.info(f"Saved PDF to: {filepath}")
    return str(filepath)

def test_extraction(pdf_path: str):
    """Test extraction with different methods and log results."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing extraction for: {pdf_path}")
    
    # Test 1: extract_text_from_pdf_smart
    try:
        logger.info("\nTesting extract_text_from_pdf_smart...")
        text = extract_text_from_pdf_smart(pdf_path)
        logger.info(f"extract_text_from_pdf_smart success. Text length: {len(text)}")
        logger.info(f"First 500 chars: {text[:500]}")
    except Exception as e:
        logger.error(f"extract_text_from_pdf_smart failed: {str(e)}")
    
    # Test 2: extract_text_from_pdf_ultra_fast
    try:
        logger.info("\nTesting extract_text_from_pdf_ultra_fast...")
        text = extract_text_from_pdf_ultra_fast(pdf_path)
        logger.info(f"extract_text_from_pdf_ultra_fast success. Text length: {len(text)}")
        logger.info(f"First 500 chars: {text[:500]}")
    except Exception as e:
        logger.error(f"extract_text_from_pdf_ultra_fast failed: {str(e)}")
    
    # Test 3: Direct UltraFastPDFExtractor
    try:
        logger.info("\nTesting UltraFastPDFExtractor directly...")
        extractor = UltraFastPDFExtractor()
        text = extractor.extract_text_ultra_fast(pdf_path)
        logger.info(f"UltraFastPDFExtractor success. Text length: {len(text)}")
        logger.info(f"First 500 chars: {text[:500]}")
    except Exception as e:
        logger.error(f"UltraFastPDFExtractor failed: {str(e)}")
    
    # Test 4: Try with pdfminer directly
    try:
        logger.info("\nTesting pdfminer directly...")
        from pdfminer.high_level import extract_text as pdfminer_extract_text
        text = pdfminer_extract_text(pdf_path)
        logger.info(f"pdfminer direct success. Text length: {len(text)}")
        logger.info(f"First 500 chars: {text[:500]}")
        
        # Save the raw extracted text
        output_file = Path(pdf_path).with_suffix('.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"Saved raw extracted text to: {output_file}")
        
    except Exception as e:
        logger.error(f"pdfminer direct failed: {str(e)}")

def main():
    """Main function to test PDF extraction."""
    # Test with the provided URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    try:
        # Download the PDF
        pdf_path = download_pdf(test_url, "test_opinion.pdf")
        
        # Test extraction with different methods
        test_extraction(pdf_path)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
