#!/usr/bin/env python3
"""
Test the unified citation validation with various citation formats
"""

import os
import sys
import json
import logging
import requests
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

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

def test_citation_direct(verifier, citation_text, description):
    """Test a single citation using the EnhancedMultiSourceVerifier directly"""
    print(f"\n{'='*80}")
    print(f"TESTING (Direct): {description}")
    print(f"INPUT: {citation_text}")
    
    try:
        result = verifier.verify_citation(citation_text)
        
        # Print the results
        print("\nRESULTS:")
        print(f"Citation: {result.get('citation')}")
        print(f"Verified: {result.get('verified')}")
        print(f"Case Name: {result.get('case_name')}")
        print(f"URL: {result.get('url')}")
        print(f"Source: {result.get('source')}")
        print(f"Confidence: {result.get('confidence', 0.0)}")
        
        if 'sources' in result and result['sources']:
            print(f"Sources: {', '.join(result['sources'])}")
        
        if 'details' in result and result['details']:
            print("\nDetails:")
            for key, value in result['details'].items():
                print(f"  {key}: {value}")
        
        if 'error' in result and result['error']:
            print(f"\nError: {result['error']}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_citation_api(citation_text, description, api_url="http://localhost:5000"):
    """Test a single citation using the unified /analyze API endpoint"""
    print(f"\n{'='*80}")
    print(f"TESTING (API): {description}")
    print(f"INPUT: {citation_text}")
    
    try:
        # Use the unified /analyze endpoint
        response = requests.post(
            f"{api_url}/analyze",
            json={
                "type": "text",
                "text": citation_text
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\nRESULTS:")
            print(f"Status: {result.get('status')}")
            
            if 'citations' in result and result['citations']:
                citation = result['citations'][0]
                print(f"Citation: {citation.get('citation')}")
                print(f"Verified: {citation.get('verified')}")
                print(f"Case Name: {citation.get('case_name')}")
                print(f"URL: {citation.get('url')}")
                print(f"Source: {citation.get('source')}")
                print(f"Confidence: {citation.get('confidence', 0.0)}")
                
                if 'sources' in citation and citation['sources']:
                    print(f"Sources: {', '.join(citation['sources'])}")
                
                if 'verification_details' in citation and citation['verification_details']:
                    print("\nVerification Details:")
                    for key, value in citation['verification_details'].items():
                        print(f"  {key}: {value}")
            else:
                print("No citations found in response")
                
            if 'metadata' in result:
                print(f"\nMetadata:")
                print(f"  Processing Time: {result['metadata'].get('processing_time', 'N/A')}")
                print(f"  Total Citations: {result['metadata'].get('total_citations', 0)}")
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to test the unified citation validation"""
    # Load config
    config = load_config()
    
    # Get API key from config
    api_key = config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    
    if not api_key:
        logger.error("No API key found in config.json")
        return
    
    logger.info(f"Using API key: {api_key[:6]}...")
    
    # Initialize verifier for direct testing
    verifier = EnhancedMultiSourceVerifier()
    
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
        if citation_text:  # Skip None values for API testing
            test_citation_api(citation_text, description)
        test_citation_direct(verifier, citation_text, description)
        input("\nPress Enter to test the next citation...")

if __name__ == "__main__":
    main()
