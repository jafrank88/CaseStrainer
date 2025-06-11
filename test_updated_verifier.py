#!/usr/bin/env python3
"""
Test the updated verify_with_courtlistener_citation_api method
"""

import os
import sys
import json
import logging
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

def main():
    """Test the updated verify_with_courtlistener_citation_api method"""
    # Load config
    config = load_config()
    
    # Get API key from config
    api_key = config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    
    if not api_key:
        logger.error("No API key found in config.json")
        return
    
    logger.info(f"Using API key: {api_key[:6]}...")
    
    # Initialize verifier
    verifier = CitationVerifier(api_key=api_key)
    
    # Test citation
    citation = "534 F.3d 1290"
    logger.info(f"Testing citation: {citation}")
    
    try:
        result = verifier.verify_with_courtlistener_citation_api(citation)
        
        # Print results
        print("\n=== Citation Verification Results ===")
        print(f"Citation: {result.get('citation')}")
        print(f"Found: {result.get('found')}")
        print(f"Valid: {result.get('valid')}")
        print(f"Case Name: {result.get('case_name')}")
        print(f"URL: {result.get('url')}")
        print(f"Status: {result.get('status')}")
        
        if 'details' in result and result['details']:
            print("\nDetails:")
            for key, value in result['details'].items():
                print(f"  {key}: {value}")
        
        if 'error_message' in result and result['error_message']:
            print(f"\nError: {result['error_message']}")
            
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
