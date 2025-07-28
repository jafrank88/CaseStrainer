#!/usr/bin/env python3
"""
Test the two-step CourtListener API workflow:
1. citation-lookup API for batch identification
2. search API for canonical data retrieval
"""

import sys
import os
import requests
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config_value

def test_citation_lookup_api(api_key, citation):
    """Test the citation-lookup API (step 1)"""
    print(f"\n=== STEP 1: Testing citation-lookup API for '{citation}' ===")
    
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test different request formats
    formats_to_test = [
        {"text": citation},
        {"citation": citation},
        citation  # Direct string
    ]
    
    for i, data in enumerate(formats_to_test):
        print(f"\n--- Format {i+1}: {data} ---")
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                try:
                    results = response.json()
                    print(f"Parsed results: {len(results)} items")
                    if results:
                        return results[0]  # Return first result for step 2
                except:
                    print("Failed to parse JSON")
        except Exception as e:
            print(f"Error: {e}")
    
    return None

def test_search_api(api_key, citation):
    """Test the search API (step 2)"""
    print(f"\n=== STEP 2: Testing search API for '{citation}' ===")
    
    url = "https://www.courtlistener.com/api/rest/v4/search/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Search parameters
    params = {
        "type": "o",  # opinions
        "q": citation,
        "format": "json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:1000]}")
        
        if response.status_code == 200:
            try:
                results = response.json()
                print(f"Search results count: {results.get('count', 0)}")
                if results.get('results'):
                    first_result = results['results'][0]
                    print(f"First result case name: {first_result.get('caseName')}")
                    print(f"First result date: {first_result.get('dateFiled')}")
                    return first_result
            except Exception as e:
                print(f"Failed to parse search results: {e}")
    except Exception as e:
        print(f"Search API error: {e}")
    
    return None

def main():
    print("=== TESTING TWO-STEP COURTLISTENER API WORKFLOW ===")
    
    # Get API key
    api_key = get_config_value("COURTLISTENER_API_KEY")
    if not api_key:
        print("ERROR: No CourtListener API key found")
        return
    
    print(f"API Key loaded: {api_key[:10]}...")
    
    # Test citations
    test_citations = [
        "578 U.S. 5",
        "136 S. Ct. 1083", 
        "194 L. Ed. 2d 256"
    ]
    
    for citation in test_citations:
        print(f"\n{'='*60}")
        print(f"TESTING CITATION: {citation}")
        print(f"{'='*60}")
        
        # Step 1: Try citation-lookup
        lookup_result = test_citation_lookup_api(api_key, citation)
        
        # Step 2: If lookup fails, try search
        if not lookup_result:
            print("\nCitation-lookup failed, trying search API...")
            search_result = test_search_api(api_key, citation)
        else:
            print(f"\nCitation-lookup succeeded for {citation}")

if __name__ == "__main__":
    main()
