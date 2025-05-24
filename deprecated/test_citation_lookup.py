import sys
import os
from dotenv import load_dotenv
import logging

# Add src directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_citation_lookup(citation):
    """Test the citation lookup functionality with enhanced error handling."""
    try:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing citation: {citation}")
        
        # Import inside function to ensure environment is loaded
        from src.enhanced_validator_production import check_courtlistener_api, CIRCUIT_BREAKER
        import requests
        
        # Log environment variables (safely)
        logger.info("\nEnvironment:")
        logger.info(f"- Python: {sys.version.split()[0]}")
        logger.info(f"- Requests: {requests.__version__}")
        logger.info(f"- API Key: {'*' * 10}{os.getenv('COURTLISTENER_API_KEY', '')[-4:] if os.getenv('COURTLISTENER_API_KEY') else 'NOT SET'}")
        
        # Reset circuit breaker for testing
        api_url = 'https://www.courtlistener.com/api/rest/v4/citation-lookup/'
        if api_url in CIRCUIT_BREAKER:
            logger.warning("Resetting circuit breaker for testing")
            CIRCUIT_BREAKER[api_url].update({
                'circuit_open': False,
                'half_open': False,
                'failures': 0,
                'consecutive_failures': 0,
                'last_attempt': 0
            })
        
        # Log circuit breaker state
        logger.info("Circuit Breaker State:")
        for key, value in CIRCUIT_BREAKER.items():
            logger.info(f"- {key}: {value}")
        
        # Make the API call
        logger.info("\nMaking API call...")
        result = check_courtlistener_api(citation)
        
        if result is None:
            logger.error("API call returned None. Possible issues:")
            logger.error("1. Circuit breaker is open")
            logger.error("2. API key is invalid or rate limited")
            logger.error("3. Network connectivity issues")
            logger.error("4. Server returned an error")
            
            # Check circuit breaker state again
            logger.info("\nUpdated Circuit Breaker State:")
            for key, value in CIRCUIT_BREAKER.items():
                logger.info(f"- {key}: {value}")
                
            return False
            
        logger.info("\nAPI Response:")
        logger.info(f"- Verified: {result.get('verified', False)}")
        
        if 'case_name' in result and result['case_name']:
            logger.info(f"- Case Name: {result['case_name']}")
            
        if 'details' in result and result['details']:
            logger.info("- Details:")
            for key, value in result['details'].items():
                logger.info(f"  - {key}: {value}")
                
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        logger.error("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during citation lookup: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # Test with a well-known citation (Roe v. Wade)
    test_cases = [
        "410 U.S. 113",  # Roe v. Wade
        "347 U.S. 483"   # Brown v. Board of Education
    ]
    
    for citation in test_cases:
        logger.info("\n" + "="*50)
        logger.info(f"TESTING CITATION: {citation}")
        success = test_citation_lookup(citation)
        if not success:
            logger.error(f"Test failed for citation: {citation}")
            break
    else:
        logger.info("\nAll tests completed successfully!")
