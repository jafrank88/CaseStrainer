"""
Test script for production environment.
This script tests the production API endpoints to verify they're working correctly.
"""

import requests
import json
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Production base URL
BASE_URL = 'https://wolf.law.uw.edu/casestrainer/api'

def test_health_check():
    """Test the health check endpoint."""
    try:
        url = urljoin(BASE_URL, 'health')
        logger.info(f"Testing health check at {url}")
        response = requests.get(url, verify=True)
        response.raise_for_status()
        logger.info(f"Health check response: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

def test_citation_analysis():
    """Test the citation analysis endpoint."""
    try:
        url = urljoin(BASE_URL, 'analyze')
        logger.info(f"Testing citation analysis at {url}")
        
        test_text = "This is a test citation to Brown v. Board of Education, 347 U.S. 483 (1954)."
        
        response = requests.post(
            url,
            json={
                'text': test_text,
                'type': 'text'
            },
            verify=True
        )
        
        response.raise_for_status()
        result = response.json()
        logger.info(f"Analysis response: {json.dumps(result, indent=2)}")
        
        if 'error' in result:
            logger.error(f"Analysis error: {result['error']}")
            return False
            
        logger.info("Citation analysis test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Citation analysis test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    logger.info("=== Starting Production Environment Tests ===")
    
    tests = [
        ("Health Check", test_health_check),
        ("Citation Analysis", test_citation_analysis)
    ]
    
    all_passed = True
    for name, test_func in tests:
        logger.info(f"\nRunning test: {name}")
        if not test_func():
            all_passed = False
            logger.error(f"❌ {name} FAILED")
        else:
            logger.info(f"✅ {name} PASSED")
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Production environment is working correctly.")
    else:
        logger.error("\n❌ Some tests failed. Please check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    import sys
    if not main():
        sys.exit(1)
