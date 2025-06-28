#!/usr/bin/env python3
"""
Test script to verify the improved case name extraction logic.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.case_name_extraction_core import extract_case_name_triple

def test_improved_case_name_logic():
    """Test the improved case name extraction logic."""
    
    test_cases = [
        {
            "text": "The court held in Smith v. Jones, 123 U.S. 456 (2020), that the principle applies.",
            "citation": "123 U.S. 456",
            "description": "Standard case with extracted name (no canonical expected)"
        },
        {
            "text": "In re Estate of Johnson, 456 Wash. 789 (2019), the court ruled...",
            "citation": "456 Wash. 789", 
            "description": "In re case with extracted name"
        },
        {
            "text": "The judge in Brown v. Board of Education, 347 U.S. 483 (1954), ruled that...",
            "citation": "347 U.S. 483",
            "description": "Well-known case (might have canonical name)"
        }
    ]
    
    print("Testing improved case name extraction logic...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        citation = test_case["citation"]
        description = test_case["description"]
        
        print(f"\nTest {i}: {description}")
        print(f"Text: {text}")
        print(f"Citation: {citation}")
        
        # Extract case name triple
        triple = extract_case_name_triple(text, citation)
        
        print(f"Results:")
        print(f"  Canonical name: '{triple['canonical_name']}'")
        print(f"  Extracted name: '{triple['extracted_name']}'")
        print(f"  Hinted name: '{triple['hinted_name']}'")
        print(f"  Best case name: '{triple['case_name']}'")
        
        # Check if the logic is working correctly
        if triple['canonical_name']:
            # Case is verified - should use canonical name
            if triple['case_name'] == triple['canonical_name']:
                print("  ✓ PASS: Using canonical name (case verified)")
            else:
                print("  ✗ FAIL: Should use canonical name when available")
        else:
            # Case not verified - should use extracted name
            if triple['extracted_name'] and triple['case_name'] == triple['extracted_name']:
                print("  ✓ PASS: Using extracted name (case not verified)")
            elif not triple['extracted_name'] and not triple['case_name']:
                print("  ✓ PASS: No names available")
            else:
                print("  ✗ FAIL: Should use extracted name when no canonical")
        
        print("-" * 40)

if __name__ == "__main__":
    test_improved_case_name_logic() 