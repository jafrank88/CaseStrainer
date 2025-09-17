"""
Test script to verify PDF text extraction from a URL using different libraries.
"""

import sys
import io
import requests
from pathlib import Path
from typing import Optional, Tuple
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test URL
TEST_PDF_URL = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"

def download_pdf(url: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Download PDF content from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,application/x-pdf,application/octet-stream',
        }
        
        logger.info(f"Downloading PDF from: {url}")
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            logger.warning(f"URL does not appear to be a PDF. Content-Type: {content_type}")
            return None, content_type
            
        return response.content, content_type
        
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        return None, None

def extract_with_pypdf2(pdf_content: bytes) -> str:
    """Extract text using PyPDF2."""
    try:
        import PyPDF2
        logger.info("Extracting with PyPDF2...")
        
        pdf_content_io = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_content_io)
        text_parts = []
        
        for i, page in enumerate(pdf_reader.pages, 1):
            try:
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Page {i} ---\n{text}")
            except Exception as e:
                logger.warning(f"Error extracting text from page {i}: {str(e)}")
        
        return '\n\n'.join(text_parts) if text_parts else "No text extracted"
        
    except Exception as e:
        logger.error(f"PyPDF2 extraction failed: {str(e)}")
        return f"PyPDF2 extraction error: {str(e)}"

def extract_with_pdfminer(pdf_content: bytes) -> str:
    """Extract text using pdfminer.six."""
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract_text
        logger.info("Extracting with pdfminer.six...")
        
        # Save to temp file as pdfminer.six works better with files
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_content)
            temp_path = temp_file.name
        
        try:
            text = pdfminer_extract_text(temp_path)
            return text if text.strip() else "No text extracted"
        finally:
            # Clean up temp file
            try:
                import os
                os.unlink(temp_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"pdfminer.six extraction failed: {str(e)}")
        return f"pdfminer.six extraction error: {str(e)}"

def extract_with_pdfplumber(pdf_content: bytes) -> str:
    """Extract text using pdfplumber."""
    try:
        import pdfplumber
        logger.info("Extracting with pdfplumber...")
        
        pdf_content_io = io.BytesIO(pdf_content)
        text_parts = []
        
        with pdfplumber.open(pdf_content_io) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"--- Page {i} ---\n{text}")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {i}: {str(e)}")
        
        return '\n\n'.join(text_parts) if text_parts else "No text extracted"
        
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {str(e)}")
        return f"pdfplumber extraction error: {str(e)}"

def save_extraction(method: str, text: str, output_dir: str = "extraction_results"):
    """Save extraction results to a file."""
    try:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        filename = f"extraction_{method.lower().replace('.', '_')}.txt"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
            
        logger.info(f"Saved {method} extraction to: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error saving {method} extraction: {str(e)}")
        return None

def main():
    """Main function to test PDF extraction."""
    # Download the PDF
    pdf_content, content_type = download_pdf(TEST_PDF_URL)
    if not pdf_content:
        logger.error("Failed to download PDF")
        return
        
    logger.info(f"PDF downloaded successfully. Size: {len(pdf_content):,} bytes, Content-Type: {content_type}")
    
    # Test each extraction method
    extraction_methods = [
        ("PyPDF2", extract_with_pypdf2),
        ("pdfminer.six", extract_with_pdfminer),
        ("pdfplumber", extract_with_pdfplumber)
    ]
    
    for method_name, extract_func in extraction_methods:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing extraction with {method_name}...")
            
            # Extract text
            text = extract_func(pdf_content)
            
            # Save results
            filepath = save_extraction(method_name, text)
            
            # Print summary
            logger.info(f"Extraction completed with {method_name}")
            if filepath:
                logger.info(f"Results saved to: {filepath}")
            
            # Print first 500 chars as preview
            preview = text[:500].replace('\n', ' ').strip()
            logger.info(f"Preview: {preview}...")
            
        except Exception as e:
            logger.error(f"Error during {method_name} extraction: {str(e)}")

if __name__ == "__main__":
    main()
