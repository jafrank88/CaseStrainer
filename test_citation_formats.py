#!/usr/bin/env python3
"""
Test different citation formats with CourtListener API
"""

import os
import sys
import json
import logging
import time
from src.citation_verification import CitationVerifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config.json: {e}")
        return {}

def test_citation_format(citation_format, verifier):
    """Test a specific citation format"""
    logger.info(f"\nTesting format: {citation_format}")
    try:
        result = verifier.verify_with_courtlistener_citation_api(citation_format)
        print(f"\n=== Results for '{citation_format}' ===")
        print(f"Status: {result.get('status')}")
        print(f"Found: {result.get('found')}")
        print(f"Case Name: {result.get('case_name')}")
        print(f"Error: {result.get('error_message', 'None')}")
        if 'details' in result and result['details']:
            print("Details:", json.dumps(result['details'], indent=2))
        return result
    except Exception as e:
        logger.error(f"Error testing format '{citation_format}': {e}")
        return None

def main():
    """Main function to test different citation formats"""
    # Load config
    config = load_config()
    
    # Get API key from config (try both uppercase and lowercase)
    api_key = config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    
    if not api_key:
        logger.error("No API key found in config.json")
        return
    
    logger.info(f"Using API key: {api_key[:6]}...")
    
    # Initialize verifier
    verifier = CitationVerifier(api_key=api_key)
    
    # Test different citation formats
    citation_formats = [
        "534 F.3d 1290",
        "534 F.3d 1290 (10th Cir. 2008)",
        "F.3d 534 1290",
        "1290 F.3d 534",
        "534 F.3d 1290, 1295 (10th Cir. 2008)",
        "534 F.3d 1290, 1295",
    ]
    
    for citation in citation_formats:
        test_citation_format(citation, verifier)
        time.sleep(1)  # Be nice to the API

if __name__ == "__main__":
    main()
