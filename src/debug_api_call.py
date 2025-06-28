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
        print(f"API Key loaded: {api_key[:10]}..." if api_key else "No API key found")
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    if not api_key:
        print("No API key available")
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
        print(f"\n{'='*60}")
        print(f"Testing citation: {test_citation}")
        print(f"Endpoint: {endpoint}")
        
        try:
            # Make the API request
            response = requests.post(
                endpoint,
                headers=headers,
                json={"text": test_citation},
                timeout=15
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    citation_data = data[0]
                    if citation_data.get("status") == 200 and citation_data.get("clusters"):
                        print("✓ Citation found!")
                        cluster = citation_data["clusters"][0]
                        print(f"Case name: {cluster.get('case_name', 'N/A')}")
                        print(f"Date filed: {cluster.get('date_filed', 'N/A')}")
                        print(f"URL: {cluster.get('absolute_url', 'N/A')}")
                    else:
                        print("✗ Citation not found in clusters")
                        print(f"Status: {citation_data.get('status')}")
                        print(f"Error: {citation_data.get('error_message', 'N/A')}")
                else:
                    print("✗ No results in response")
            else:
                print(f"✗ API error: {response.status_code}")
                print(f"Response text: {response.text}")
                
        except Exception as e:
            print(f"✗ Request failed: {e}")

if __name__ == "__main__":
    test_courtlistener_api() 