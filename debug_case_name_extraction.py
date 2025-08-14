#!/usr/bin/env python3
"""
Debug case name extraction to understand why it's extracting context text instead of proper case names
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_name_extractor import extract_case_name_and_date_unified
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_case_name_extraction():
    """Test case name extraction with known examples"""
    print("=" * 60)
    print("CASE NAME EXTRACTION DEBUG TEST")
    print("=" * 60)
    
    # Test cases with known case names
    test_cases = [
        {
            'text': 'The Supreme Court decided in Brown v. Board of Education, 347 U.S. 483 (1954), that separate educational facilities are inherently unequal.',
            'citation': '347 U.S. 483',
            'expected_case_name': 'Brown v. Board of Education',
            'expected_year': '1954'
        },
        {
            'text': 'This landmark case overturned Plessy v. Ferguson, 163 U.S. 537 (1896).',
            'citation': '163 U.S. 537',
            'expected_case_name': 'Plessy v. Ferguson',
            'expected_year': '1896'
        },
        {
            'text': 'Another important case is Miranda v. Arizona, 384 U.S. 436 (1966), which established the Miranda rights.',
            'citation': '384 U.S. 436',
            'expected_case_name': 'Miranda v. Arizona',
            'expected_year': '1966'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected Case Name: {test_case['expected_case_name']}")
        print(f"Expected Year: {test_case['expected_year']}")
        
        # Find citation position in text
        citation_start = test_case['text'].find(test_case['citation'])
        if citation_start == -1:
            print(f"❌ Citation not found in text!")
            continue
            
        citation_end = citation_start + len(test_case['citation'])
        
        print(f"Citation position: {citation_start}-{citation_end}")
        
        try:
            # Extract using unified method
            result = extract_case_name_and_date_unified(
                text=test_case['text'],
                citation=test_case['citation'],
                citation_start=citation_start,
                citation_end=citation_end
            )
            
            print(f"Extracted Case Name: '{result.get('case_name', 'None')}'")
            print(f"Extracted Year: '{result.get('year', 'None')}'")
            print(f"Confidence: {result.get('confidence', 0.0)}")
            print(f"Method: {result.get('method', 'unknown')}")
            
            # Check if extraction is correct
            extracted_name = result.get('case_name', '')
            extracted_year = result.get('year', '')
            
            name_correct = test_case['expected_case_name'].lower() in extracted_name.lower() if extracted_name else False
            year_correct = test_case['expected_year'] == extracted_year
            
            print(f"Case Name Correct: {'✓' if name_correct else '✗'}")
            print(f"Year Correct: {'✓' if year_correct else '✗'}")
            
            if not name_correct:
                print(f"❌ Expected: '{test_case['expected_case_name']}', Got: '{extracted_name}'")
            if not year_correct:
                print(f"❌ Expected: '{test_case['expected_year']}', Got: '{extracted_year}'")
                
        except Exception as e:
            print(f"❌ Error in extraction: {e}")
            import traceback
            traceback.print_exc()

def test_simple_regex_patterns():
    """Test basic regex patterns to see if they work"""
    print("\n" + "=" * 60)
    print("SIMPLE REGEX PATTERN TEST")
    print("=" * 60)
    
    import re
    
    # Simple case name pattern
    pattern = r'([A-Z][A-Za-z\s,\.\'-]+?)\s+v\.\s+([A-Za-z\s,\.\'-]+?)(?=\s*,\s*\d|\s*\(|$)'
    
    test_texts = [
        'Brown v. Board of Education, 347 U.S. 483 (1954)',
        'Plessy v. Ferguson, 163 U.S. 537 (1896)',
        'Miranda v. Arizona, 384 U.S. 436 (1966)'
    ]
    
    for text in test_texts:
        print(f"\nTesting: {text}")
        matches = list(re.finditer(pattern, text))
        print(f"Matches found: {len(matches)}")
        
        for match in matches:
            full_match = match.group(0)
            plaintiff = match.group(1) if len(match.groups()) >= 1 else "N/A"
            defendant = match.group(2) if len(match.groups()) >= 2 else "N/A"
            
            print(f"  Full match: '{full_match}'")
            print(f"  Plaintiff: '{plaintiff}'")
            print(f"  Defendant: '{defendant}'")
            print(f"  Combined: '{plaintiff} v. {defendant}'")

if __name__ == "__main__":
    print("Debugging case name extraction...")
    
    # Test simple regex patterns first
    test_simple_regex_patterns()
    
    # Test unified extraction
    test_case_name_extraction()
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)
