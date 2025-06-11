#!/usr/bin/env python3
"""
Test the validate_citation method with various citation formats
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

def test_citation(verifier, citation_text, description):
    """Test a single citation and print the results"""
    print(f"\n{'='*80}")
    print(f"TESTING: {description}")
    print(f"INPUT: {citation_text}")
    
    try:
        result = verifier.validate_citation(citation_text)
        
        # Print the results
        print("\nRESULTS:")
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
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to test the validate_citation method"""
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
    
    # Test cases
    test_cases = [
        # Clean citation
        ("534 F.3d 1290", "Clean citation"),
        
        # Citation with extra whitespace
        ("  534   F.3d   1290  ", "Citation with extra whitespace"),
        
        # Citation with prefix
        ("See 534 F.3d 1290", "Citation with 'See' prefix"),
        ("See also 534 F.3d 1290", "Citation with 'See also' prefix"),
        ("e.g., 534 F.3d 1290", "Citation with 'e.g.,' prefix"),
        ("cf. 534 F.3d 1290", "Citation with 'cf.' prefix"),
        ("id. at 534 F.3d 1290", "Citation with 'id. at' prefix"),
        
        # Citation with quotes
        ('"534 F.3d 1290"', 'Citation with quotes'),
        ("'534 F.3d 1290'", "Citation with single quotes"),
        
        # Citation with brackets/parentheses
        ("[534 F.3d 1290]", "Citation with square brackets"),
        ("(534 F.3d 1290)", "Citation with parentheses"),
        
        # Invalid citation
        ("This is not a citation", "Invalid citation"),
        ("", "Empty string"),
        (None, "None value"),
    ]
    
    # Run all test cases
    for citation_text, description in test_cases:
        test_citation(verifier, citation_text, description)
        input("\nPress Enter to test the next citation...")

if __name__ == "__main__":
    main()
