"""
Test script to diagnose PDF text extraction and Redis serialization issues.
"""
import os
import sys
import json
import redis
import requests
from urllib.parse import urlparse
from io import BytesIO
import PyPDF2
import fitz  # PyMuPDF
import pdfplumber
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@localhost:6380/0')

class PDFTextExtractor:
    """Helper class to extract text from PDFs using different libraries."""
    
    @staticmethod
    def extract_with_pypdf2(pdf_data):
        """Extract text using PyPDF2."""
        try:
            text = ""
            with BytesIO(pdf_data) as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return None
    
    @staticmethod
    def extract_with_pymupdf(pdf_data):
        """Extract text using PyMuPDF (fitz)."""
        try:
            text = ""
            with fitz.open(stream=pdf_data, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return None
    
    @staticmethod
    def extract_with_pdfplumber(pdf_data):
        """Extract text using pdfplumber."""
        try:
            text = ""
            with pdfplumber.open(BytesIO(pdf_data)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return None

class RedisTester:
    """Helper class to test Redis serialization."""
    
    def __init__(self, redis_url):
        self.redis = redis.Redis.from_url(redis_url)
    
    def test_serialization(self, key, data):
        """Test serialization of data to Redis."""
        try:
            # Try JSON serialization first
            try:
                json_data = json.dumps(data)
                self.redis.set(f"test:json:{key}", json_data)
                retrieved = json.loads(self.redis.get(f"test:json:{key}"))
                logger.info("JSON serialization successful")
                return True
            except (TypeError, OverflowError) as e:
                logger.error(f"JSON serialization failed: {e}")
            
            # Try string serialization
            try:
                str_data = str(data)
                self.redis.set(f"test:str:{key}", str_data)
                logger.info("String serialization successful")
                return True
            except Exception as e:
                logger.error(f"String serialization failed: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Serialization test failed: {e}")
            return False

def download_pdf(url):
    """Download PDF from URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Failed to download PDF: {e}")
        return None

def main():
    # Test URL from the issue
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    logger.info(f"Testing PDF extraction and Redis serialization for: {test_url}")
    
    # Download the PDF
    logger.info("Downloading PDF...")
    pdf_data = download_pdf(test_url)
    if not pdf_data:
        logger.error("Failed to download PDF")
        return
    
    logger.info(f"PDF downloaded successfully ({len(pdf_data)} bytes)")
    
    # Extract text using different libraries
    extractor = PDFTextExtractor()
    
    logger.info("\n=== Extracting text with PyPDF2 ===")
    text_pypdf2 = extractor.extract_with_pypdf2(pdf_data)
    logger.info(f"PyPDF2 extracted {len(text_pypdf2) if text_pypdf2 else 0} characters")
    
    logger.info("\n=== Extracting text with PyMuPDF ===")
    text_pymupdf = extractor.extract_with_pymupdf(pdf_data)
    logger.info(f"PyMuPDF extracted {len(text_pymupdf) if text_pymupdf else 0} characters")
    
    logger.info("\n=== Extracting text with pdfplumber ===")
    text_pdfplumber = extractor.extract_with_pdfplumber(pdf_data)
    logger.info(f"pdfplumber extracted {len(text_pdfplumber) if text_pdfplumber else 0} characters")
    
    # Test Redis serialization
    logger.info("\n=== Testing Redis Serialization ===")
    redis_tester = RedisTester(REDIS_URL)
    
    # Test with PyPDF2 text
    if text_pypdf2:
        logger.info("\nTesting Redis serialization with PyPDF2 text...")
        success = redis_tester.test_serialization("pypdf2", {"text": text_pypdf2, "source": "PyPDF2"})
        logger.info(f"PyPDF2 Redis serialization: {'SUCCESS' if success else 'FAILED'}")
    
    # Test with PyMuPDF text
    if text_pymupdf:
        logger.info("\nTesting Redis serialization with PyMuPDF text...")
        success = redis_tester.test_serialization("pymupdf", {"text": text_pymupdf, "source": "PyMuPDF"})
        logger.info(f"PyMuPDF Redis serialization: {'SUCCESS' if success else 'FAILED'}")
    
    # Test with pdfplumber text
    if text_pdfplumber:
        logger.info("\nTesting Redis serialization with pdfplumber text...")
        success = redis_tester.test_serialization("pdfplumber", {"text": text_pdfplumber, "source": "pdfplumber"})
        logger.info(f"pdfplumber Redis serialization: {'SUCCESS' if success else 'FAILED'}")
    
    logger.info("\nTest completed.")

if __name__ == "__main__":
    main()
