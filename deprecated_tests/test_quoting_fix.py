#!/usr/bin/env python3
"""
Test script to verify that case name extraction correctly handles "quoting" and other introductory phrases.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.extract_case_name import clean_case_name, extract_case_name_from_text
from enhanced_case_name_extractor import EnhancedCaseNameExtractor
from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from citation_extractor import CitationExtractor

def test_clean_case_name():
    """Test the clean_case_name function with various introductory phrases."""
    
    print("Testing clean_case_name function...")
    print("=" * 60)
    
    test_cases = [
        ("quoting Ellis v. City of Seattle", "Ellis v. City of Seattle"),
        ("cited in Smith v. Jones", "Smith v. Jones"),
        ("referenced in Brown v. Board of Education", "Brown v. Board of Education"),
        ("as stated in Roe v. Wade", "Roe v. Wade"),
        ("as held in Miranda v. Arizona", "Miranda v. Arizona"),
        ("the court in United States v. Nixon", "United States v. Nixon"),
        ("judge in State v. Johnson", "State v. Johnson"),
        ("opinion in In re Smith", "In re Smith"),
        ("see Doe v. Roe", "Doe v. Roe"),
        ("cf. Example v. Test", "Example v. Test"),
        ("e.g., Sample v. Case", "Sample v. Case"),
        ("i.e., Another v. Example", "Another v. Example"),
        ("according to Test v. Case", "Test v. Case"),
        ("per Sample v. Example", "Sample v. Example"),
        ("as per Another v. Test", "Another v. Test"),
        ("Unknown Case", "Unknown Case"),  # Should remain unchanged
        ("Case not found", "Case not found"),  # Should remain unchanged
    ]
    
    all_passed = True
    
    for input_text, expected in test_cases:
        result = clean_case_name(input_text)
        print(f"Input:  {repr(input_text)}")
        print(f"Output: {repr(result)}")
        print(f"Expected: {repr(expected)}")
        
        if result == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
        print("-" * 40)
    
    return all_passed

def test_extract_case_name_from_text():
    """Test the extract_case_name_from_text function with context containing introductory phrases."""
    
    print("\nTesting extract_case_name_from_text function...")
    print("=" * 60)
    
    test_cases = [
        {
            "text": "The court held that quoting Ellis v. City of Seattle, 142 Wash. 2d 450, 13 P.3d 1065 (2000), establishes the standard.",
            "citation": "142 Wash. 2d 450",
            "expected": "Ellis v. City of Seattle"
        },
        {
            "text": "As stated in Smith v. Jones, 123 U.S. 456 (2020), the principle applies.",
            "citation": "123 U.S. 456",
            "expected": "Smith v. Jones"
        },
        {
            "text": "The judge in Brown v. Board of Education, 347 U.S. 483 (1954), ruled that...",
            "citation": "347 U.S. 483",
            "expected": "Brown v. Board of Education"
        },
        {
            "text": "See Roe v. Wade, 410 U.S. 113 (1973), for the precedent.",
            "citation": "410 U.S. 113",
            "expected": "Roe v. Wade"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        text = test_case["text"]
        citation = test_case["citation"]
        expected = test_case["expected"]
        
        result = extract_case_name_from_text(text, citation)
        
        print(f"Text: {text}")
        print(f"Citation: {citation}")
        print(f"Extracted: {repr(result)}")
        print(f"Expected: {repr(expected)}")
        
        if result == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
        print("-" * 40)
    
    return all_passed

def test_enhanced_extractors():
    """Test the enhanced extractors with introductory phrases."""
    
    print("\nTesting enhanced extractors...")
    print("=" * 60)
    
    # Test EnhancedCaseNameExtractor
    print("Testing EnhancedCaseNameExtractor...")
    extractor = EnhancedCaseNameExtractor()
    
    test_text = "The court held that quoting Ellis v. City of Seattle, 142 Wash. 2d 450, establishes the standard."
    citation = "142 Wash. 2d 450"
    
    result = extractor.extract_case_name_from_context(test_text, citation)
    print(f"EnhancedCaseNameExtractor result: {repr(result)}")
    
    # Test EnhancedMultiSourceVerifier
    print("\nTesting EnhancedMultiSourceVerifier...")
    verifier = EnhancedMultiSourceVerifier()
    
    test_case_name = "quoting Ellis v. City of Seattle"
    cleaned = verifier._clean_case_name(test_case_name)
    is_valid = verifier._is_valid_case_name(test_case_name)
    
    print(f"Original: {repr(test_case_name)}")
    print(f"Cleaned: {repr(cleaned)}")
    print(f"Is valid: {is_valid}")
    
    # Test CitationExtractor
    print("\nTesting CitationExtractor...")
    citation_extractor = CitationExtractor()
    
    test_case_name2 = "quoting Smith v. Jones"
    cleaned2 = citation_extractor._clean_case_name(test_case_name2)
    is_valid2 = citation_extractor._is_valid_case_name(test_case_name2)
    
    print(f"Original: {repr(test_case_name2)}")
    print(f"Cleaned: {repr(cleaned2)}")
    print(f"Is valid: {is_valid2}")

def main():
    """Run all tests."""
    print("Testing case name extraction fixes for introductory phrases")
    print("=" * 80)
    
    # Test clean_case_name function
    test1_passed = test_clean_case_name()
    
    # Test extract_case_name_from_text function
    test2_passed = test_extract_case_name_from_text()
    
    # Test enhanced extractors
    test_enhanced_extractors()
    
    print("\n" + "=" * 80)
    if test1_passed and test2_passed:
        print("ALL TESTS PASSED! ✅")
        print("The case name extraction now correctly handles introductory phrases like 'quoting'.")
    else:
        print("SOME TESTS FAILED! ❌")
        print("The case name extraction still has issues with introductory phrases.")
    
    return test1_passed and test2_passed

if __name__ == "__main__":
    main() 