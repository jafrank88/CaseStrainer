#!/usr/bin/env python3
"""
Test the improved hinted extraction with a canonical name and misspelled party name.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Disable API calls for testing
os.environ['DISABLE_API_CALLS'] = '1'

from src.case_name_extraction_core import extract_case_name_hinted, extract_case_name_from_text

def test_hinted_extraction():
    """Test hinted extraction with canonical name and misspelled party name."""
    
    # Test case: misspelled party name with canonical name
    text = 'In Doe v. Wdae, 123 U.S. 456 (1973), the court ruled...'
    citation = '123 U.S. 456'
    canonical_name = 'Roe v. Wade'  # The correct canonical name
    
    print("=== Testing Hinted Extraction ===")
    print(f"Text: {text}")
    print(f"Citation: {citation}")
    print(f"Canonical Name: {canonical_name}")
    print()
    
    # Test hinted extraction
    hinted_result = extract_case_name_hinted(text, citation, canonical_name)
    print(f"Hinted Extraction Result: '{hinted_result}'")
    
    # Test regular extraction (should fail)
    regular_result = extract_case_name_from_text(text, citation)
    print(f"Regular Extraction Result: '{regular_result}'")
    
    # Test extraction with canonical name hint
    hinted_regular_result = extract_case_name_from_text(text, citation, canonical_name=canonical_name)
    print(f"Regular Extraction with Canonical Hint: '{hinted_regular_result}'")
    
    print()
    if hinted_result and hinted_result != "N/A":
        print("✅ PASS - Hinted extraction worked")
    else:
        print("❌ FAIL - Hinted extraction failed")
    
    print("\n" + "="*80 + "\n")

def test_multiple_variants():
    """Test extraction of multiple variants from the same text."""
    
    test_cases = [
        {
            'text': 'In Doe v. Wdae, 123 U.S. 456 (1973), the court ruled...',
            'citation': '123 U.S. 456',
            'canonical': 'Roe v. Wade',
            'expected_variants': ['In Doe v. Wdae', 'Doe v. Wdae']
        },
        {
            'text': 'The case of Johnson v. Brown, 456 P.3d 789 (2021) established...',
            'citation': '456 P.3d 789',
            'canonical': 'Johnson v. Brown',
            'expected_variants': ['Johnson v. Brown']
        },
        {
            'text': 'State v. Smith, 789 Wn.2d 123, 456 P.3d 789 (2020) further clarified...',
            'citation': '789 Wn.2d 123',
            'canonical': 'State v. Smith',
            'expected_variants': ['State v. Smith']
        }
    ]
    
    print("=== Testing Multiple Variants ===")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Canonical: {test_case['canonical']}")
        print(f"Expected Variants: {test_case['expected_variants']}")
        
        result = extract_case_name_hinted(test_case['text'], test_case['citation'], test_case['canonical'])
        print(f"Extracted: '{result}'")
        
        if result and result != "N/A":
            print("✅ PASS")
        else:
            print("❌ FAIL")
        print()

if __name__ == "__main__":
    test_hinted_extraction()
    test_multiple_variants() 