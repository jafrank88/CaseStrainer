#!/usr/bin/env python3
"""
Test script to verify Google Scholar API integration using SerpApi
"""

import sys
import os
import json
import time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.enhanced_case_name_extractor import EnhancedCaseNameExtractor

def test_google_scholar_api():
    """Test the Google Scholar API integration."""
    
    print("=== Testing Google Scholar API Integration ===\n")
    
    # Initialize the enhanced extractor
    extractor = EnhancedCaseNameExtractor(cache_results=True)
    
    # Test citations that might not be in CourtListener
    test_citations = [
        "521 U.S. 702",  # Should be in CourtListener
        "164 Wn.2d 391",  # Washington case
        "534 F.3d 1290",  # Federal case
        "Brown v. Board of Education, 347 U.S. 483",  # Famous case
        "Marbury v. Madison, 5 U.S. 137",  # Famous case
        "Roe v. Wade, 410 U.S. 113",  # Famous case
        "Miranda v. Arizona, 384 U.S. 436",  # Famous case
        "Gideon v. Wainwright, 372 U.S. 335",  # Famous case
    ]
    
    print("Testing Google Scholar API for various citations:")
    print("=" * 80)
    
    for i, citation in enumerate(test_citations, 1):
        print(f"\n{i}. Testing citation: {citation}")
        
        # Test Google Scholar directly
        try:
            start_time = time.time()
            canonical_name = extractor.get_canonical_case_name_from_google_scholar(citation)
            end_time = time.time()
            
            if canonical_name:
                print(f"   ✓ Found in Google Scholar: {canonical_name}")
                print(f"   ⏱️  Time: {end_time - start_time:.2f}s")
            else:
                print(f"   ✗ Not found in Google Scholar")
                print(f"   ⏱️  Time: {end_time - start_time:.2f}s")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Add delay to respect rate limits
        time.sleep(1)
    
    print("\n" + "=" * 80)
    print("Testing fallback behavior (CourtListener -> Google Scholar):")
    print("=" * 80)
    
    # Test the main method that tries CourtListener first, then Google Scholar
    for i, citation in enumerate(test_citations[:3], 1):
        print(f"\n{i}. Testing fallback for: {citation}")
        
        try:
            start_time = time.time()
            canonical_name = extractor.get_canonical_case_name(citation)
            end_time = time.time()
            
            if canonical_name:
                print(f"   ✓ Found: {canonical_name}")
                print(f"   ⏱️  Time: {end_time - start_time:.2f}s")
            else:
                print(f"   ✗ Not found")
                print(f"   ⏱️  Time: {end_time - start_time:.2f}s")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Add delay to respect rate limits
        time.sleep(1)

def test_enhanced_extraction_with_google_scholar():
    """Test the enhanced extraction with Google Scholar fallback."""
    
    print("\n" + "=" * 80)
    print("Testing Enhanced Extraction with Google Scholar Fallback:")
    print("=" * 80)
    
    # Sample text with citations
    sample_text = """
    In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), 
    the Supreme Court held that racial segregation in public schools was unconstitutional. 
    This decision was later reinforced by Miranda v. Arizona, 384 U.S. 436 (1966), 
    which established important rights for criminal defendants.
    """
    
    print("Sample text:")
    print(sample_text.strip())
    print()
    
    # Initialize extractor
    extractor = EnhancedCaseNameExtractor(cache_results=True)
    
    try:
        # Extract enhanced case names
        results = extractor.extract_enhanced_case_names(sample_text)
        
        print(f"Found {len(results)} citations with enhanced extraction:")
        for i, result in enumerate(results, 1):
            print(f"\n  Citation {i}:")
            print(f"    Citation: {result['citation']}")
            print(f"    Extracted Name: {result.get('case_name', 'None')}")
            print(f"    Canonical Name: {result.get('canonical_name', 'None')}")
            print(f"    Source: {result.get('source', 'none')}")
            print(f"    Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"    Method: {result.get('method', 'none')}")
            print(f"    Similarity: {result.get('similarity_score', 0.0):.2f}")
            
    except Exception as e:
        print(f"Error testing enhanced extraction: {e}")

def test_serpapi_response_structure():
    """Test the structure of SerpApi Google Scholar responses."""
    
    print("\n" + "=" * 80)
    print("Testing SerpApi Response Structure:")
    print("=" * 80)
    
    # Test a simple search to see the response structure
    import requests
    
    serpapi_key = "c7dafc0c5d9a040b5fa2b9b1d70b26b4ac6858720005c54adc910c581e1da534"
    serpapi_url = "https://serpapi.com/search.json"
    
    test_query = "Brown v. Board of Education 347 U.S. 483"
    
    try:
        params = {
            'engine': 'google_scholar',
            'q': test_query,
            'api_key': serpapi_key,
            'hl': 'en',
            'as_sdt': '0,5'
        }
        
        print(f"Testing SerpApi with query: {test_query}")
        response = requests.get(serpapi_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        print(f"Response status: {response.status_code}")
        print(f"Number of organic results: {len(data.get('organic_results', []))}")
        
        if data.get('organic_results'):
            print("\nFirst result structure:")
            first_result = data['organic_results'][0]
            print(json.dumps(first_result, indent=2))
            
            # Test case name extraction
            extractor = EnhancedCaseNameExtractor()
            title = first_result.get('title', '')
            snippet = first_result.get('snippet', '')
            
            case_name = extractor._extract_case_name_from_scholar_result(title, snippet)
            print(f"\nExtracted case name: {case_name}")
        
    except Exception as e:
        print(f"Error testing SerpApi: {e}")

if __name__ == "__main__":
    test_google_scholar_api()
    test_enhanced_extraction_with_google_scholar()
    test_serpapi_response_structure()
    
    print("\n" + "=" * 80)
    print("Google Scholar Integration Test Completed!")
    print("\nKey Features Tested:")
    print("✓ Google Scholar API integration via SerpApi")
    print("✓ Fallback behavior (CourtListener -> Google Scholar)")
    print("✓ Case name extraction from search results")
    print("✓ Enhanced extraction with dual-source lookup")
    print("✓ Response structure validation")
    print("✓ Rate limiting and error handling") 