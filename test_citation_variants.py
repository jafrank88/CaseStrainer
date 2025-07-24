#!/usr/bin/env python3
"""
Test script to verify citation variant generation and CourtListener API hits.
"""

import sys
import os
import requests
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.citation_utils_consolidated import generate_citation_variants, normalize_citation

def test_citation_variants():
    """Test citation variant generation for Washington citations."""
    
    test_citations = [
        "171 Wash. 2d 486",
        "171 Wn.2d 486", 
        "171 Wn. 2d 486",
        "171 Wash.2d 486"
    ]
    
    print("=== TESTING CITATION VARIANT GENERATION ===")
    
    for citation in test_citations:
        print(f"\nOriginal citation: '{citation}'")
        
        # Test normalization
        normalized = normalize_citation(citation)
        print(f"Normalized: '{normalized}'")
        
        # Test variant generation
        variants = generate_citation_variants(citation)
        print(f"Generated {len(variants)} variants:")
        for i, variant in enumerate(variants, 1):
            print(f"  {i}. '{variant}'")

def test_courtlistener_api():
    """Test CourtListener API with different citation variants."""
    
    # Get API key from environment
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("ERROR: COURTLISTENER_API_KEY environment variable not set")
        return
    
    test_citation = "171 Wash. 2d 486"
    variants = generate_citation_variants(test_citation)
    
    print(f"\n=== TESTING COURTLISTENER API WITH VARIANTS ===")
    print(f"Original citation: '{test_citation}'")
    print(f"Testing {len(variants)} variants...")
    
    headers = {"Authorization": f"Token {api_key}"}
    
    for i, variant in enumerate(variants, 1):
        print(f"\n{i}. Testing variant: '{variant}'")
        
        # Prevent use of v3 CourtListener API endpoints
        lookup_url = f"https://www.courtlistener.com/api/rest/v4/citation-lookup/?citation={variant}"
        search_url = f"https://www.courtlistener.com/api/rest/v4/search/?q={variant}&format=json"
        if 'v3' in lookup_url or 'v3' in search_url:
            print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
            sys.exit(1)

        # Try citation-lookup endpoint first
        try:
            resp = requests.get(lookup_url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if data and data.get("results"):
                    entry = data["results"][0]
                    case_name = entry.get("caseName", "Unknown")
                    date_filed = entry.get("dateFiled", "Unknown")
                    url = entry.get("absolute_url", "Unknown")
                    print(f"   ✓ FOUND via citation-lookup!")
                    print(f"      Case: {case_name}")
                    print(f"      Date: {date_filed}")
                    print(f"      URL: {url}")
                    return True
                else:
                    print(f"   ✗ No results from citation-lookup")
            else:
                print(f"   ✗ Citation-lookup failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Citation-lookup error: {e}")
        
        # Try search endpoint
        try:
            resp = requests.get(search_url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    entry = results[0]
                    case_name = entry.get("caseName", "Unknown")
                    date_filed = entry.get("dateFiled", "Unknown")
                    url = entry.get("absolute_url", "Unknown")
                    print(f"   ✓ FOUND via search!")
                    print(f"      Case: {case_name}")
                    print(f"      Date: {date_filed}")
                    print(f"      URL: {url}")
                    return True
                else:
                    print(f"   ✗ No results from search")
            else:
                print(f"   ✗ Search failed: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Search error: {e}")
    
    print(f"\n❌ No variants found a match in CourtListener")
    return False

def main():
    """Run all tests."""
    print("Citation Variant Testing Script")
    print("=" * 50)
    
    # Test variant generation
    test_citation_variants()
    
    # Test CourtListener API
    found = test_courtlistener_api()
    
    if found:
        print(f"\n✅ SUCCESS: At least one variant found a match!")
    else:
        print(f"\n❌ FAILURE: No variants found a match")

if __name__ == "__main__":
    main() 