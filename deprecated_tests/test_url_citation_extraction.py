import os
import logging
from src.citation_utils import extract_citations_from_file

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_url_extraction():
    """
    Simulate processing a PDF from a URL by using a local file.
    In a real scenario, this would download the PDF from a URL.
    """
    logger.info("Starting test for URL citation extraction (simulated with local file).")
    local_pdf_path = 'gov.uscourts.wyd.64014.141.0_1.pdf'
    
    if not os.path.exists(local_pdf_path):
        logger.error(f"Local PDF file not found: {local_pdf_path}")
        return
    
    logger.info(f"Processing local PDF as if downloaded from URL: {local_pdf_path}")
    results = extract_citations_from_file(local_pdf_path)
    logger.info(f"Completed URL citation extraction test.")
    print(f"Results from URL (simulated with local file):", results)

if __name__ == "__main__":
    test_url_extraction()
