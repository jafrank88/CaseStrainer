#!/usr/bin/env python

import json
import requests
import os
import sys

# Import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.tokenizers import HyperscanTokenizer, AhocorasickTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    print("Eyecite not available, falling back to regex patterns")
    EYECITE_AVAILABLE = False
    import re

# Load API key from config.json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        API_KEY = config.get('courtlistener_api_key', '')
        print(f"Loaded API key: {API_KEY[:5]}...")
except Exception as e:
    print(f"Error loading config.json: {e}")
    API_KEY = input("Enter your CourtListener API key: ")

# CourtListener API URL
COURTLISTENER_API_URL = "https://www.courtlistener.com/api/rest/v3/citation-lookup/"

def extract_citations(text):
    """Extract citations using eyecite if available, otherwise use regex patterns."""
    if EYECITE_AVAILABLE:
        print("Using eyecite for citation extraction")
        try:
            # Try to use the faster HyperscanTokenizer first
            try:
                tokenizer = HyperscanTokenizer()
            except Exception:
                print("Falling back to AhocorasickTokenizer...")
                tokenizer = AhocorasickTokenizer()
                
            # Get citations using eyecite
            citation_objects = get_citations(text, tokenizer=tokenizer)
            
            # Extract the citation strings
            citations = []
            for citation in citation_objects:
                citation_str = citation.corrected_citation() if hasattr(citation, 'corrected_citation') else str(citation)
                if citation_str not in citations:
                    citations.append(citation_str)
            
            print(f"Found {len(citations)} citations using eyecite")
            return citations
        except Exception as e:
            print(f"Error using eyecite: {e}")
            if EYECITE_AVAILABLE:
                import traceback
                traceback.print_exc()
    
    # Fall back to regex patterns
    print("Using regex patterns for citation extraction")
    # Normalize the text to make citation matching more reliable
    text = re.sub(r'\s+', ' ', text)
    
    # Example patterns for common citation formats
    patterns = [
        # US Reports (e.g., 347 U.S. 483)
        r'\b\d+\s+U\.?\s*S\.?\s+\d+\b',
    ]
    
    citations = []
    for pattern in patterns:
        try:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation = match.group(0).strip()
                if citation not in citations:
                    citations.append(citation)
        except Exception as e:
            print(f"Error searching for pattern {pattern}: {e}")
    
    print(f"Found {len(citations)} citations using regex patterns")
    return citations

def query_courtlistener_api(citation, api_key):
    """Query the CourtListener API to verify a single citation."""
    print(f"Querying CourtListener API with citation: {citation}")
    
    if not api_key:
        print("No API key provided")
        return {'error': 'No API key provided'}
    
    try:
        # Prepare the request
        headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Prepare the data with just the citation
        data = {
            'text': citation
        }
        
        # Make the request
        print(f"Sending request to {COURTLISTENER_API_URL}")
        response = requests.post(COURTLISTENER_API_URL, headers=headers, json=data)
        
        # Check the response
        if response.status_code == 200:
            print("API request successful")
            result = response.json()
            
            # Save the API response to a file for inspection
            try:
                with open('api_response.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                print("API response saved to api_response.json")
            except Exception as e:
                print(f"Error saving API response to file: {e}")
            
            return result
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return {'error': f"API request failed with status code {response.status_code}: {response.text}"}
    
    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f"Error querying CourtListener API: {str(e)}"}

def main():
    # Test citation
    test_citation = "550 U.S. 544"
    
    print(f"Testing citation: {test_citation}")
    
    # Query the API
    result = query_courtlistener_api(test_citation, API_KEY)
    
    # Print the result
    print("\nAPI Response:")
    print(json.dumps(result, indent=2))
    
    # Extract specific information if available
    if 'citations' in result:
        for citation_key, citation_info in result['citations'].items():
            print(f"\nCitation: {citation_key}")
            print(f"Match Level: {citation_info.get('match_level', 'unknown')}")
            print(f"Match URL: {citation_info.get('match_url', 'unknown')}")
            print(f"Match ID: {citation_info.get('match_id', 'unknown')}")
            
            # Print case details if available
            if 'case_name' in citation_info:
                print(f"Case Name: {citation_info['case_name']}")
            if 'court' in citation_info:
                print(f"Court: {citation_info['court']}")
            if 'date_filed' in citation_info:
                print(f"Date Filed: {citation_info['date_filed']}")

if __name__ == "__main__":
    main()
