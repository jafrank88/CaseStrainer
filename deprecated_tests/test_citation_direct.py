#!/usr/bin/env python3
"""
Test direct API call to CourtListener with different citation formats
"""

import os
import sys
import json
import requests
import logging
from urllib.parse import quote_plus

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Get API key from config (try both uppercase and lowercase)
    API_KEY = config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    if not API_KEY:
        logger.error("No API key found in config.json")
        sys.exit(1)
        
    logger.info(f"Using API key: {API_KEY[:6]}...")
    
except Exception as e:
    logger.error(f"Error loading config: {e}")
    sys.exit(1)

# API endpoint
BASE_URL = "https://www.courtlistener.com/api/rest/v4/"
CITATION_LOOKUP_URL = f"{BASE_URL}citation-lookup/"

# Headers
headers = {
    'Authorization': f'Token {API_KEY}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def test_citation(citation):
    """Test a citation with the CourtListener API"""
    print(f"\n{'='*50}")
    print(f"Testing citation: {citation}")
    
    # Prepare the request data
    data = {
        "text": citation,  # Using 'text' parameter as suggested by the API
        "full_case": True
    }
    
    try:
        # Make the request
        response = requests.post(
            CITATION_LOOKUP_URL,
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print("Response Headers:", response.headers)
        
        try:
            response_json = response.json()
            print("Response JSON:")
            print(json.dumps(response_json, indent=2))
        except ValueError:
            print("Response Text:", response.text)
            
        return response.status_code, response.json() if response.status_code == 200 else None
        
    except Exception as e:
        print(f"Error: {e}")
        return None, str(e)

def main():
    """Main function to test different citation formats"""
    # Test different citation formats
    citations = [
        # Standard format
        "534 F.3d 1290",
        
        # With court and year
        "534 F.3d 1290 (10th Cir. 2008)",
        
        # Different order
        "F.3d 534 1290",
        "1290 F.3d 534",
        
        # With pin cite
        "534 F.3d 1290, 1295",
        "534 F.3d 1290, 1295 (10th Cir. 2008)",
        
        # URL encoded
        "534%20F.3d%201290",
        
        # With quotes
        '"534 F.3d 1290"',
        
        # Just the numbers
        "534 3d 1290",
        "534 F3d 1290",
    ]
    
    for citation in citations:
        test_citation(citation)
        input("Press Enter to test the next citation...")

if __name__ == "__main__":
    main()
