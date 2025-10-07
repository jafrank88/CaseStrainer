"""
Test script to verify citation extraction from 1033940.pdf
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
from models import ProcessingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_citation_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise

def test_citation_extraction():
    """Test citation extraction from 1033940.pdf."""
    pdf_path = '1033940.pdf'
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    try:
        # Initialize processor
        config = ProcessingConfig(
            enable_verification=True,
            debug_mode=True,
            request_id='test_1033940'
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Extract text from PDF
        logger.info(f"Extracting text from {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        
        # Process text
        logger.info("Processing text for citations")
        result = processor.process_text(text)
        
        # Save results
        output_file = '1033940_citations_test.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        # Print summary
        num_citations = len(result.get('citations', []))
        logger.info(f"Extracted {num_citations} citations")
        logger.info(f"Results saved to {output_file}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in citation extraction: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    test_citation_extraction()
