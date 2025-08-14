"""
Direct test of the citation service with sample text.
This bypasses the web server and tests the core functionality directly.
"""
import sys
import os
import json
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock environment variables to avoid loading from .env file
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['COURTLISTENER_API_KEY'] = 'test-key'  # Mock API key for testing

# Import after setting environment variables
from src.api.services.citation_service import CitationService

def test_citation_processing():
    """Test citation processing with sample text directly using the service."""
    # Sample legal text with citations
    sample_text = """
    In Luis v. United States, 578 U.S. 5 (2016), the Supreme Court held that 
    a pretrial freeze of untainted assets violates a defendant's Sixth Amendment 
    right to counsel of choice. This decision was later cited in United States 
    v. Jones, 950 F.3d 1106 (9th Cir. 2020), where the court further clarified 
    the scope of this protection. Additionally, the case of Carpenter v. United States, 
    138 S. Ct. 2206 (2018) addressed Fourth Amendment issues in the digital age.
    """
    
    try:
        logger.info("Initializing CitationService...")
        
        # Initialize the service with test mode to skip Redis
        service = CitationService()
        
        # If the service has a way to disable Redis, use it
        if hasattr(service, 'disable_redis'):
            service.disable_redis()
            logger.info("Disabled Redis for testing")
        
        logger.info("Processing text...")
        
        # Create input data with test mode if supported
        input_data = {
            'type': 'text', 
            'text': sample_text,
            'test_mode': True  # If the service supports test mode
        }
        
        # Process the text
        logger.info("Calling process_immediately...")
        result = service.process_immediately(input_data)
        logger.info("Processing completed")
        
        # Ensure all citations have the required six data points
        citations = result.get('citations', [])
        for i, citation in enumerate(citations, 1):
            print(f"\nCitation {i}:")
            print(f"  Extracted Name: {citation.get('extracted_case_name')}")
            print(f"  Extracted Date: {citation.get('extracted_date')}")
            print(f"  Canonical Name: {citation.get('canonical_name')}")
            print(f"  Canonical Date: {citation.get('canonical_date')}")
            print(f"  Canonical URL: {citation.get('canonical_url')}")
            print(f"  Verified: {citation.get('verified')}")
        
        print(f"\nTotal citations found: {len(citations)}")
        print(f"Clusters: {json.dumps(result.get('clusters', []), indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing CitationService with sample text...")
    success = test_citation_processing()
    sys.exit(0 if success else 1)
