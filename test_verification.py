"""
Test script to verify citation verification functionality.
"""
import logging
import os
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class Citation:
    """Simple citation class for testing verification."""
    def __init__(self, text, citation_type="federal"):
        self.text = text
        self.citation = text
        self.type = citation_type
        self.extracted_case_name = None
        self.extracted_date = None
        self.verification = {}
    
    def __repr__(self):
        return f"Citation('{self.text}')"

def test_verification():
    """Test the verification functionality."""
    try:
        from src.verification_services import CourtListenerService
        from src.config import get_citation_config
        
        logger.info("=== Starting Verification Test ===")
        
        # Create test citation
        citation = Citation("505 U.S. 1003")  # Known good citation
        
        # Get config
        config = get_citation_config()
        
        # Initialize verifier
        logger.info("Initializing verifier...")
        verifier = CourtListenerService()
        
        # Test verification with search method (more reliable for single citations)
        logger.info(f"Verifying citation: {citation.text}")
        search_url = f"{verifier.base_url}/search/"
        params = {
            'q': f'citation:({citation.text})',
            'type': 'o',  # Search only opinions
            'order_by': 'score desc',
            'stat_Precedential': 'on',
            'filed_after': '1900-01-01',
            'format': 'json'
        }
        
        try:
            response = verifier.session.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    result = {
                        'status': 'success',
                        'source': 'courtlistener_search',
                        'result': data['results'][0],
                        'confidence': 0.9
                    }
                else:
                    result = {
                        'status': 'not_found',
                        'source': 'courtlistener_search',
                        'message': 'No matching opinions found'
                    }
            else:
                result = {
                    'status': 'error',
                    'source': 'courtlistener_search',
                    'error': f'API error: {response.status_code}',
                    'details': response.text
                }
        except Exception as e:
            result = {
                'status': 'error',
                'source': 'courtlistener_search',
                'error': str(e)
            }
        
        # Add result to citation object for consistency
        citation.verification = result
        
        # Log results
        logger.info("Verification result:")
        pprint(result, width=120)
        
        # Check if verification was successful
        if result and result.get('status') == 'success':
            logger.info("Verification successful!")
            return True
        else:
            logger.warning("Verification failed or returned no results")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    test_verification()
