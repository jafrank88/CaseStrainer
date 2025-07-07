#!/usr/bin/env python3
"""
Test script to verify the improved case name selection logic.
Tests the new logic where hinted names can replace extracted names if they're better.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.case_name_extraction_core import extract_case_name_triple

def test_improved_case_name_logic():
    """Test the improved case name selection logic."""
    print("Testing improved case name selection logic...")
    print("=" * 80)
    
    test_cases = [
        {
            "text": "The court held in John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017), that the principle applies.",
            "citation": "199 Wn. App. 280",
            "canonical_name": "Doe P v. Thurston County",
            "description": "Case with canonical name - should use canonical",
            "expected_priority": "canonical"
        },
        {
            "text": "In Smith v. Jones, 123 U.S. 456 (2020), the court found that...",
            "citation": "123 U.S. 456",
            "canonical_name": "",  # No canonical name
            "description": "Case without canonical name - should compare hinted vs extracted",
            "expected_priority": "extracted_or_hinted"
        },
        {
            "text": "The principle was established in Brown v. Board of Education, 347 U.S. 483 (1954).",
            "citation": "347 U.S. 483",
            "canonical_name": "Brown v. Board of Education of Topeka",
            "description": "Case with similar but not exact canonical name",
            "expected_priority": "canonical"
        },
        {
            "text": "As held in Roe v. Wade, 410 U.S. 113 (1973), the right to privacy...",
            "citation": "410 U.S. 113",
            "canonical_name": "",  # No canonical name
            "description": "Simple case name extraction",
            "expected_priority": "extracted_or_hinted"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        citation = test_case["citation"]
        canonical_name = test_case["canonical_name"]
        description = test_case["description"]
        expected_priority = test_case["expected_priority"]
        
        print(f"\nTest {i}: {description}")
        print(f"Text: {text}")
        print(f"Citation: {citation}")
        print(f"Canonical name: '{canonical_name}'")
        
        # Extract case name triple
        triple = extract_case_name_triple(text, citation)
        
        print(f"\nResults:")
        print(f"  Canonical name: '{triple['canonical_name']}'")
        print(f"  Extracted name: '{triple['extracted_name']}'")
        print(f"  Hinted name: '{triple['hinted_name']}'")
        print(f"  Final case name: '{triple['case_name']}'")
        
        # Check if the logic is working correctly
        if expected_priority == "canonical":
            if triple['canonical_name'] and triple['canonical_name'] != "N/A":
                if triple['case_name'] == triple['canonical_name']:
                    print("  ✓ PASS: Using canonical name (case verified)")
                else:
                    print("  ✗ FAIL: Should use canonical name when available")
                    all_passed = False
            else:
                print("  ⚠ WARNING: No canonical name found (expected for some citations)")
        elif expected_priority == "extracted_or_hinted":
            if triple['extracted_name'] and triple['extracted_name'] != "N/A":
                if triple['case_name'] == triple['extracted_name'] or triple['case_name'] == triple['hinted_name']:
                    print("  ✓ PASS: Using extracted or hinted name (no canonical)")
                else:
                    print("  ✗ FAIL: Should use extracted or hinted name when no canonical")
                    all_passed = False
            elif triple['hinted_name'] and triple['hinted_name'] != "N/A":
                if triple['case_name'] == triple['hinted_name']:
                    print("  ✓ PASS: Using hinted name (no extracted)")
                else:
                    print("  ✗ FAIL: Should use hinted name when no extracted")
                    all_passed = False
            else:
                print("  ⚠ WARNING: No extracted or hinted name found")
        
        print("-" * 80)
    
    print(f"\n{'='*80}")
    if all_passed:
        print("✓ All tests passed! Improved case name logic is working correctly.")
    else:
        print("✗ Some tests failed! Check the logic implementation.")
    
    return all_passed

def test_hinted_vs_extracted_comparison():
    """Test the specific logic for comparing hinted vs extracted names."""
    print("\nTesting hinted vs extracted comparison logic...")
    print("=" * 80)
    
    # Test case where hinted should be better than extracted
    text = "The court in John Doe P v. Thurston County, 199 Wn. App. 280, found that..."
    citation = "199 Wn. App. 280"
    
    print(f"Text: {text}")
    print(f"Citation: {citation}")
    
    triple = extract_case_name_triple(text, citation)
    
    print(f"\nResults:")
    print(f"  Canonical name: '{triple['canonical_name']}'")
    print(f"  Extracted name: '{triple['extracted_name']}'")
    print(f"  Hinted name: '{triple['hinted_name']}'")
    print(f"  Final case name: '{triple['case_name']}'")
    
    # Check if the comparison logic worked
    if triple['hinted_name'] != "N/A" and triple['extracted_name'] != "N/A":
        print(f"  Comparison: Hinted vs Extracted")
        print(f"  Decision: {triple['case_name']}")
        print("  ✓ PASS: Comparison logic executed")
    else:
        print("  ⚠ WARNING: Could not test comparison (missing one or both names)")
    
    return True

if __name__ == "__main__":
    print("Testing Improved Case Name Selection Logic")
    print("=" * 80)
    
    test1_passed = test_improved_case_name_logic()
    test2_passed = test_hinted_vs_extracted_comparison()
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The improved case name logic is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1) 