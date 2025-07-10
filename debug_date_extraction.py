#!/usr/bin/env python3
"""
Debug script to test date extraction from user documents.
This will help identify why extracted_date fields are empty.
"""

import sys
import os
import re
from typing import Optional, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.standalone_citation_parser import DateExtractor, extract_date_enhanced, extract_year_enhanced

def test_date_extraction():
    """Test date extraction with sample legal text."""
    
    print("=== DEBUGGING DATE EXTRACTION ===")
    print()
    
    # Sample legal text with citations and dates
    test_texts = [
        {
            "name": "Standard citation with year in parentheses",
            "text": "In State v. Smith, 171 Wash. 2d 486 (2011), the court held...",
            "citation": "171 Wash. 2d 486",
            "expected_year": "2011"
        },
        {
            "name": "Citation with full date",
            "text": "The case was decided on May 12, 2011. State v. Smith, 171 Wash. 2d 486.",
            "citation": "171 Wash. 2d 486", 
            "expected_year": "2011"
        },
        {
            "name": "Citation with year after comma",
            "text": "State v. Smith, 171 Wash. 2d 486, 2011",
            "citation": "171 Wash. 2d 486",
            "expected_year": "2011"
        },
        {
            "name": "Citation with year in context",
            "text": "The 2011 decision in State v. Smith, 171 Wash. 2d 486, established...",
            "citation": "171 Wash. 2d 486",
            "expected_year": "2011"
        }
    ]
    
    for i, test_case in enumerate(test_texts, 1):
        print(f"TEST {i}: {test_case['name']}")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected year: {test_case['expected_year']}")
        print()
        
        # Test 1: Enhanced extraction
        print("1. Testing DateExtractor.extract_date:")
        try:
            extractor = DateExtractor()
            result = extractor.extract_date(test_case['text'], test_case['citation'])
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   ERROR: {e}")
        print()
        
        # Test 2: Direct date extraction
        print("2. Testing extract_date_enhanced:")
        try:
            date_result = extract_date_enhanced(test_case['text'], test_case['citation'])
            print(f"   Result: {date_result}")
        except Exception as e:
            print(f"   ERROR: {e}")
        print()
        
        # Test 3: Direct year extraction
        print("3. Testing extract_year_enhanced:")
        try:
            year_result = extract_year_enhanced(test_case['text'], test_case['citation'])
            print(f"   Result: {year_result}")
        except Exception as e:
            print(f"   ERROR: {e}")
        print()
        
        # Test 4: DateExtractor from unified processor
        print("4. Testing DateExtractor.extract_date_from_context:")
        try:
            citation_start = test_case['text'].find(test_case['citation'])
            citation_end = citation_start + len(test_case['citation'])
            date_result = DateExtractor.extract_date_from_context(
                test_case['text'], citation_start, citation_end
            )
            print(f"   Result: {date_result}")
        except Exception as e:
            print(f"   ERROR: {e}")
        print()
        
        print("-" * 80)
        print()

def test_with_real_document_sample():
    """Test with a sample from a real document."""
    
    print("=== TESTING WITH REAL DOCUMENT SAMPLE ===")
    print()
    
    # This is a sample from what might be in a real legal document
    real_text = """
    The Washington Supreme Court in State v. Smith, 171 Wash. 2d 486 (2011), 
    addressed the issue of search and seizure. The court decided this case on 
    May 12, 2011. This decision was later cited in State v. Johnson, 200 Wash. 2d 72 (2023).
    
    In another case, Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court 
    held that separate educational facilities are inherently unequal.
    """
    
    citations_to_test = [
        "171 Wash. 2d 486",
        "200 Wash. 2d 72", 
        "347 U.S. 483"
    ]
    
    for citation in citations_to_test:
        print(f"Testing citation: {citation}")
        print(f"Full text: {real_text}")
        print()
        
        # Test enhanced extraction
        extractor = DateExtractor()
        result = extractor.extract_date(real_text, citation)
        print(f"Enhanced extraction result: {result}")
        print()
        
        # Test direct year extraction
        year = extract_year_enhanced(real_text, citation)
        print(f"Direct year extraction: {year}")
        print()
        
        print("-" * 60)
        print()

def debug_date_patterns():
    """Debug the date patterns to see what's being matched."""
    
    print("=== DEBUGGING DATE PATTERNS ===")
    print()
    
    extractor = DateExtractor()
    
    test_text = "State v. Smith, 171 Wash. 2d 486 (2011)"
    citation = "171 Wash. 2d 486"
    
    print(f"Test text: {test_text}")
    print(f"Citation: {citation}")
    print()
    
    # Test each pattern individually
    for i, pattern in enumerate(extractor.date_patterns):
        print(f"Pattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, test_text, re.IGNORECASE))
        print(f"  Matches found: {len(matches)}")
        for match in matches:
            print(f"    Groups: {match.groups()}")
            print(f"    Full match: {match.group(0)}")
        print()

if __name__ == "__main__":
    test_date_extraction()
    print("\n" + "="*80 + "\n")
    test_with_real_document_sample()
    print("\n" + "="*80 + "\n")
    debug_date_patterns() 