#!/usr/bin/env python3
"""
Test script to verify citation using CourtListener API
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

def test_citation(citation):
    """Test citation verification"""
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
    
    # Test citation
    logger.info(f"Testing citation: {citation}")
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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_citation(sys.argv[1])
    else:
        # Test with a default citation if none provided
        test_citation("534 F.3d 1290")
