#!/usr/bin/env python3
"""
Debug script to trace through the hinted extraction logic step by step.
"""

import os
import sys
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Disable API calls for testing
os.environ['DISABLE_API_CALLS'] = '1'

from src.extract_case_name import generate_hinted_names, best_hinted_name, clean_case_name_enhanced, is_valid_case_name

def test_hinted_debug():
    """Debug the hinted extraction logic step by step."""
    
    text = 'In Doe v. Wdae, 123 U.S. 456 (1973), the court ruled...'
    citation = '123 U.S. 456'
    canonical_name = 'Roe v. Wade'
    
    print("=== Debugging Hinted Extraction ===")
    print(f"Text: {text}")
    print(f"Citation: {citation}")
    print(f"Canonical Name: {canonical_name}")
    print()
    
    # Step 1: Get context before citation
    citation_index = text.find(citation)
    context_before = text[max(0, citation_index - 100):citation_index]
    print(f"Context before citation: '{context_before}'")
    print()
    
    # Step 2: Test generate_hinted_names
    print("=== Testing generate_hinted_names ===")
    hinted_names = generate_hinted_names(context_before)
    print(f"Generated hinted names: {hinted_names}")
    print()
    
    # Step 3: Test best_hinted_name
    print("=== Testing best_hinted_name ===")
    best_name = best_hinted_name(context_before, canonical_name)
    print(f"Best hinted name: '{best_name}'")
    print()
    
    # Step 4: Test regex patterns manually
    print("=== Testing Regex Patterns ===")
    patterns = [
        r'(In\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'([A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'([A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)\.\s*,\s*' + re.escape(citation),
    ]
    
    for i, pattern in enumerate(patterns, 1):
        match = re.search(pattern, context_before, re.IGNORECASE)
        if match:
            print(f"Pattern {i} matched: '{match.group(1)}'")
        else:
            print(f"Pattern {i} did not match")
    print()
    
    # Step 5: Test validation functions
    print("=== Testing Validation Functions ===")
    test_names = ['In Doe v. Wdae', 'Doe v. Wdae', 'Roe v. Wade']
    
    for name in test_names:
        cleaned = clean_case_name_enhanced(name)
        is_valid = is_valid_case_name(cleaned)
        print(f"Name: '{name}' -> Cleaned: '{cleaned}' -> Valid: {is_valid}")
    print()

if __name__ == "__main__":
    test_hinted_debug() 