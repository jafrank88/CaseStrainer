#!/usr/bin/env python3
"""
Test script to validate the new case name structure rules.
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_case_structure_validation():
    """Test the case name structure validation rules."""
    
    processor = UnifiedCitationProcessorV2()
    
    test_cases = [
        # Valid case names
        ("Smith v. Jones", True),
        ("Carlson v. Glob. Client Sols., LLC", True),
        ("Dep't of Ecology v. Campbell & Gwinn, LLC", True),
        ("In re Smith", True),
        ("State ex rel. Smith", True),
        ("Smith & Jones", True),
        ("Smith et al.", True),
        
        # Invalid case names (too many lowercase words in a row)
        ("the quick brown fox jumps over the lazy dog v. Smith", False),  # 8 lowercase words
        ("a very long sequence of lowercase words that should be rejected v. Jones", False),  # 9 lowercase words
        ("this is a test case with too many lowercase words in sequence v. Defendant", False),  # 8 lowercase words
        
        # Edge cases
        ("A v. B", True),
        ("A B C D v. E F G H", True),  # 4 words each side
        ("A B C D E v. F G H I J", True),  # 5 words each side (should be valid)
        ("a b c d e v. f g h i j", False),  # All lowercase
        ("A b c d e v. F g h i j", True),  # Mixed case, but reasonable
    ]
    
    print("Testing case name structure validation:")
    print("=" * 50)
    
    for case_name, expected in test_cases:
        result = processor._has_reasonable_case_structure(case_name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | '{case_name}' -> {result} (expected {expected})")
    
    print("\n" + "=" * 50)
    print("Testing full validation (including regex patterns):")
    
    for case_name, expected_structure in test_cases:
        if expected_structure:  # Only test cases that should pass structure validation
            result = processor._is_valid_case_name(case_name)
            print(f"'{case_name}' -> {result}")

if __name__ == "__main__":
    test_case_structure_validation() 