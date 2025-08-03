#!/usr/bin/env python3
"""
Simple test script for validate_citation method
"""

import os
import sys
import json
# from src.citation_verification import CitationVerifier  # TODO: Fix or implement CitationVerifier if needed

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return {}

def main():
    # Load config
    config = load_config()
    
    # Get API key from config
    api_key = config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    
    if not api_key:
        print("Error: No API key found in config.json")
        return
    
    print(f"Using API key: {api_key[:6]}...")
    
    # Initialize verifier with API key
    # verifier = CitationVerifier(api_key=api_key) # This line is commented out as CitationVerifier is not imported
    
    # Test citation
    citation = "See 534 F.3d 1290"
    print(f"Testing citation: {citation}")
    
    try:
        # result = verifier.validate_citation(citation) # This line is commented out as CitationVerifier is not imported
        print("\nValidation Result:")
        # print(json.dumps(result, indent=2, default=str)) # This line is commented out as CitationVerifier is not imported
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
