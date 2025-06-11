#!/usr/bin/env python3
"""
Test script for verifying CourtListener API integration.
"""

import os
import sys
import json
import logging
from citation_verification import CitationVerifier

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
    """Load configuration from config.json."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        return {}

def test_citation_verification(citation, api_key):
    """Test citation verification with the given citation."""
    print(f"\n{'='*80}")
    print(f"Testing citation: {citation}")
    print("-" * 80)
    
    if not api_key:
        print("ERROR: No API key provided. Please check your config.json file.")
        return None
    
    print(f"Using API key: {api_key[:6]}...")
    
    # Initialize the verifier with the API key from config
    verifier = CitationVerifier(api_key=api_key, debug_mode=True)
    
    # Verify the citation
    result = verifier.verify_with_courtlistener_citation_api(citation)
    
    # Print the result
    print("\nVerification Result:")
    print("-" * 80)
    for key, value in result.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
    
    return result

if __name__ == "__main__":
    # Test with some sample citations
    # Load configuration
    config = load_config()
    # Try both possible key names for backward compatibility
    api_key = config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    
    if not api_key:
        print("ERROR: No COURT_LISTENER_API_KEY found in config.json")
        sys.exit(1)

    test_citations = [
        "534 F.3d 1290",  # Federal Reporter 3rd
        "410 U.S. 113",   # US Supreme Court
        "123 F. Supp. 2d 456",  # Federal Supplement
    ]
    
    for citation in test_citations:
        test_citation_verification(citation, api_key)
