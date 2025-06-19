import requests
import tempfile
import os
from pdfminer.high_level import extract_text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_extraction(url):
    """Test PDF extraction from a URL using pdfminer.six"""
    logger.info(f"Testing PDF extraction from URL: {url}")
    
    try:
        # Download the PDF
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/pdf,*/*",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        logger.info("Downloading PDF...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
            logger.info(f"Saved PDF to temporary file: {tmp_path}")
        
        try:
            # Try to extract text
            logger.info("Attempting to extract text with pdfminer.six...")
            text = extract_text(tmp_path)
            
            # Log some basic stats
            text_length = len(text) if text else 0
            logger.info(f"Extracted text length: {text_length} characters")
            
            if text and text.strip():
                # Log first 500 characters as a sample
                sample = text[:500].replace('\n', ' ').strip()
                logger.info(f"Text sample (first 500 chars): {sample}")
                
                # Save full text to file for inspection
                output_file = "pdf_extracted_text.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text)
                logger.info(f"Full text saved to {output_file}")
                
                return True, text
            else:
                logger.error("No text content extracted from PDF")
                return False, "No text content found in PDF"
                
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
                logger.info("Temporary file cleaned up")
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading PDF: {e}")
        return False, f"Failed to download PDF: {str(e)}"
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        return False, f"Error processing PDF: {str(e)}"

if __name__ == "__main__":
    test_url = "https://www.courts.wa.gov/opinions/pdf/1028814.pdf"
    success, result = test_pdf_extraction(test_url)
    
    if success:
        print("\nPDF extraction successful!")
        print(f"Extracted {len(result)} characters of text")
        print("\nFirst 500 characters:")
        print("-" * 80)
        print(result[:500])
        print("-" * 80)
        print("\nFull text has been saved to pdf_extracted_text.txt")
    else:
        print("\nPDF extraction failed!")
        print(f"Error: {result}") 