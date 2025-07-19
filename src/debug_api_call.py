#!/usr/bin/env python3
"""
Debug script to test CourtListener API call directly.
"""

import json
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_courtlistener_api():
    """Test the CourtListener API call directly."""
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('courtlistener_api_key')
        logger.info(f"API Key loaded: {api_key[:10]}..." if api_key else "No API key found")
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return
    
    if not api_key:
        logger.info("No API key available")
        return
    
    # Test citations - one that should be found, one that might not be
    test_citations = [
        "347 U.S. 483",  # Brown v. Board of Education - should be found
        "399 P.3d 1195",  # Washington citation - might not be found
        "199 Wn. App. 280"  # Washington citation - might be found
    ]
    
    # Set up headers
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # API endpoint
    endpoint = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    for test_citation in test_citations:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing citation: {test_citation}")
        logger.info(f"Endpoint: {endpoint}")
        
        try:
            # Make the API request
            response = requests.post(
                endpoint,
                headers=headers,
                json={"text": test_citation},
                timeout=15
            , timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    citation_data = data[0]
                    if citation_data.get("status") == 200 and citation_data.get("clusters"):
                        logger.info("✓ Citation found!")
                        cluster = citation_data["clusters"][0]
                        logger.info(f"Case name: {cluster.get('case_name', 'N/A')}")
                        logger.info(f"Date filed: {cluster.get('date_filed', 'N/A')}")
                        logger.info(f"URL: {cluster.get('absolute_url', 'N/A')}")
                    else:
                        logger.info("✗ Citation not found in clusters")
                        logger.info(f"Status: {citation_data.get('status')}")
                        logger.error(f"Error: {citation_data.get('error_message', 'N/A')}")
                else:
                    logger.info("✗ No results in response")
            else:
                logger.error(f"✗ API error: {response.status_code}")
                logger.info(f"Response text: {response.text}")
                
        except Exception as e:
            logger.error(f"✗ Request failed: {e}")

if __name__ == "__main__":
    test_courtlistener_api() 