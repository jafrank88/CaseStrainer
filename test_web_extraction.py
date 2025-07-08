#!/usr/bin/env python3
"""
Test script to verify web search extraction functionality.
"""

import asyncio
import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from web_search_extractor import WebSearchExtractor

def test_extractor():
    """Test the web search extractor directly."""
    print("Testing WebSearchExtractor directly...")
    
    extractor = WebSearchExtractor()
    
    # Test case name extraction
    test_texts = [
        "Roe v. Wade, 410 U.S. 113 (1973)",
        "Brown v. Board of Education, 347 U.S. 483",
        "In re Smith, 200 Wash. 2d 72",
        "Ex parte Johnson, 123 F.3d 456",
        "Smith and Jones v. State, 456 P.2d 789",
        "Johnson et al. v. City, 789 S.W.2d 123"
    ]
    
    print("\n=== Testing Case Name Extraction ===")
    for text in test_texts:
        case_name = extractor.extract_case_name(text)
        print(f"Text: {text}")
        print(f"Extracted: {case_name}")
        print()
    
    # Test date extraction
    test_dates = [
        "Roe v. Wade, 410 U.S. 113 (1973)",
        "Filed: January 22, 1973",
        "Decided: May 17, 1954",
        "Brown v. Board of Education (1954)",
        "Case decided on 01/22/1973"
    ]
    
    print("\n=== Testing Date Extraction ===")
    for text in test_dates:
        date = extractor.extract_date(text)
        print(f"Text: {text}")
        print(f"Extracted: {date}")
        print()
    
    # Test URL extraction
    test_html = """
    <html>
    <head><link rel="canonical" href="https://law.justia.com/cases/federal/us/410/113/"></head>
    <body>
        <a href="/cases/federal/us/410/113/">Roe v. Wade</a>
        <a href="https://caselaw.findlaw.com/us-supreme-court/410/113.html">FindLaw</a>
    </body>
    </html>
    """
    
    print("\n=== Testing URL Extraction ===")
    url = extractor.extract_canonical_url("https://law.justia.com", "https://law.justia.com/search", test_html)
    print(f"HTML: {test_html[:100]}...")
    print(f"Extracted URL: {url}")
    print()

def test_enhanced_verifier():
    """Test the enhanced verifier with extraction."""
    print("\nTesting EnhancedMultiSourceVerifier with extraction...")
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citations that should have good extraction
    test_cases = [
        {
            "citation": "410 U.S. 113",
            "expected_name": "Roe v. Wade",
            "expected_date": "1973-01-22"
        },
        {
            "citation": "347 U.S. 483",
            "expected_name": "Brown v. Board of Education",
            "expected_date": "1954-05-17"
        },
        {
            "citation": "200 Wash. 2d 72",
            "expected_name": None,  # Will be extracted from web search
            "expected_date": None   # Will be extracted from web search
        }
    ]
    
    for test_case in test_cases:
        citation = test_case["citation"]
        expected_name = test_case["expected_name"]
        expected_date = test_case["expected_date"]
        
        print(f"\n{'='*80}")
        print(f"Testing citation: {citation}")
        print(f"Expected name: {expected_name}")
        print(f"Expected date: {expected_date}")
        print(f"{'='*80}")
        
        # Test with web search
        result = verifier.verify_citation_unified_workflow(
            citation=citation,
            extracted_case_name=expected_name,
            extracted_date=expected_date
        )
        
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Check extraction results
        if result.get('verified') == 'true':
            print(f"✅ VERIFIED")
            if result.get('case_name'):
                print(f"✅ Case name extracted: {result['case_name']}")
            if result.get('canonical_name'):
                print(f"✅ Canonical name: {result['canonical_name']}")
            if result.get('canonical_date'):
                print(f"✅ Canonical date: {result['canonical_date']}")
            if result.get('url'):
                print(f"✅ URL: {result['url']}")
            if result.get('source'):
                print(f"✅ Source: {result['source']}")
        else:
            print(f"❌ NOT VERIFIED")
            if result.get('error'):
                print(f"❌ Error: {result['error']}")

def test_known_cases():
    """Test with known cases to verify extraction."""
    print("\nTesting with known cases...")
    
    extractor = WebSearchExtractor()
    
    # Known case data
    known_cases = [
        {
            "citation": "410 U.S. 113",
            "name": "Roe v. Wade",
            "date": "1973-01-22",
            "url": "https://law.justia.com/cases/federal/us/410/113/"
        },
        {
            "citation": "347 U.S. 483",
            "name": "Brown v. Board of Education",
            "date": "1954-05-17",
            "url": "https://law.justia.com/cases/federal/us/347/483/"
        },
        {
            "citation": "200 Wash. 2d 72",
            "name": "State v. Arlene's Flowers",
            "date": "2023-06-06",
            "url": "https://law.justia.com/cases/washington/supreme-court/2023/200-wash-2d-72.html"
        }
    ]
    
    for case in known_cases:
        print(f"\n--- Testing {case['citation']} ---")
        
        # Test case name extraction
        test_text = f"{case['name']}, {case['citation']} ({case['date'][:4]})"
        extracted_name = extractor.extract_case_name(test_text, case['citation'])
        print(f"Case name extraction: {extracted_name == case['name']} ({extracted_name})")
        
        # Test date extraction
        extracted_date = extractor.extract_date(test_text, case['citation'])
        print(f"Date extraction: {extracted_date == case['date']} ({extracted_date})")
        
        # Test URL extraction
        test_html = f'<link rel="canonical" href="{case["url"]}">'
        extracted_url = extractor.extract_canonical_url("https://law.justia.com", "https://law.justia.com/search", test_html)
        print(f"URL extraction: {extracted_url == case['url']} ({extracted_url})")

if __name__ == "__main__":
    print("Web Search Extraction Test Suite")
    print("=" * 50)
    
    # Test the extractor directly
    test_extractor()
    
    # Test with known cases
    test_known_cases()
    
    # Test the enhanced verifier
    test_enhanced_verifier()
    
    print("\n" + "=" * 50)
    print("Test suite completed!") 