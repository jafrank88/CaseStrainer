#!/usr/bin/env python3
"""
Test script to verify that all enhanced case name extraction functionality works correctly.
This tests the unified canonical module with all integrated features.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.extract_case_name import (
    # Core extraction functions
    extract_case_name_from_context_unified,
    extract_case_name_unified,
    extract_case_name_triple_from_text,
    
    # Validation and cleaning
    is_valid_case_name,
    clean_case_name,
    expand_abbreviations,
    
    # Citation URL generation
    get_citation_url,
    get_legal_database_url,
    get_general_legal_search_url,
    get_google_scholar_url,
    
    # CourtListener API integration
    get_canonical_case_name_from_courtlistener,
    extract_case_name_from_courtlistener_cluster,
    extract_canonical_date_from_courtlistener_cluster,
    
    # Washington citation variants
    generate_washington_citation_variants,
    
    # Google Scholar integration
    get_canonical_case_name_from_google_scholar,
    extract_case_name_from_scholar_result,
    
    # Utility functions
    normalize_citation_format,
    extract_year_from_line
)

def test_core_extraction():
    """Test core case name extraction functionality."""
    print("Testing core case name extraction...")
    print("=" * 60)
    
    test_cases = [
        {
            "context": "The court held in Smith v. Jones, 123 U.S. 456 (2020), that...",
            "citation": "123 U.S. 456",
            "expected": "Smith v. Jones"
        },
        {
            "context": "In re Estate of Johnson, 456 Wash. 789 (2019), the court...",
            "citation": "456 Wash. 789",
            "expected": "In re Estate of Johnson"
        },
        {
            "context": "State v. Brown, 789 F.2d 123 (2021), established...",
            "citation": "789 F.2d 123",
            "expected": "State v. Brown"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        context = test_case["context"]
        citation = test_case["citation"]
        expected = test_case["expected"]
        
        print(f"\nTest {i}: {citation}")
        print(f"Context: {context}")
        
        # Test unified context extraction
        result = extract_case_name_from_context_unified(context, citation)
        print(f"Unified extraction: '{result}'")
        
        if result == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_validation_and_cleaning():
    """Test validation and cleaning functions."""
    print("\nTesting validation and cleaning...")
    print("=" * 60)
    
    test_cases = [
        ("Smith v. Jones", True, "Smith v. Jones"),
        ("quoting Smith v. Jones", True, "Smith v. Jones"),
        ("In re Estate of Johnson", True, "In re Estate of Johnson"),
        ("Unknown Case", False, "Unknown Case"),
        ("", False, ""),
        ("Smith v. Jones, Inc.", True, "Smith v. Jones, Inc."),
    ]
    
    all_passed = True
    
    for case_name, should_be_valid, expected_clean in test_cases:
        print(f"\nTesting: '{case_name}'")
        
        # Test validation
        is_valid = is_valid_case_name(case_name)
        print(f"Valid: {is_valid} (expected: {should_be_valid})")
        
        # Test cleaning
        cleaned = clean_case_name(case_name)
        print(f"Cleaned: '{cleaned}' (expected: '{expected_clean}')")
        
        if is_valid == should_be_valid and cleaned == expected_clean:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_abbreviation_expansion():
    """Test abbreviation expansion functionality."""
    print("\nTesting abbreviation expansion...")
    print("=" * 60)
    
    test_cases = [
        ("Smith v. Dep", "Smith v. Department"),
        ("Jones v. Emp", "Jones v. Employment"),
        ("Brown v. Ass'n", "Brown v. Association"),
        ("Johnson v. Inc.", "Johnson v. Inc."),  # Should not change
    ]
    
    all_passed = True
    
    for input_name, expected in test_cases:
        print(f"\nTesting: '{input_name}'")
        
        expanded = expand_abbreviations(input_name)
        print(f"Expanded: '{expanded}' (expected: '{expected}')")
        
        if expanded == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_citation_url_generation():
    """Test citation URL generation functions."""
    print("\nTesting citation URL generation...")
    print("=" * 60)
    
    test_cases = [
        "123 U.S. 456",
        "456 Wash. 789",
        "789 F.2d 123",
    ]
    
    all_passed = True
    
    for citation in test_cases:
        print(f"\nTesting: {citation}")
        
        # Test different URL generation functions
        citation_url = get_citation_url(citation)
        legal_db_url = get_legal_database_url(citation)
        general_search_url = get_general_legal_search_url(citation)
        scholar_url = get_google_scholar_url(citation)
        
        print(f"Citation URL: {citation_url}")
        print(f"Legal DB URL: {legal_db_url}")
        print(f"General Search URL: {general_search_url}")
        print(f"Scholar URL: {scholar_url}")
        
        # Check that URLs are generated
        if citation_url and legal_db_url and general_search_url and scholar_url:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_washington_citation_variants():
    """Test Washington citation variant generation."""
    print("\nTesting Washington citation variants...")
    print("=" * 60)
    
    test_citations = [
        "456 Wn. 789",
        "123 Wn. App. 456",
        "789 Wn. 2d 123",
    ]
    
    all_passed = True
    
    for citation in test_citations:
        print(f"\nTesting: {citation}")
        
        variants = generate_washington_citation_variants(citation)
        print(f"Generated {len(variants)} variants:")
        for variant in variants:
            print(f"  - {variant}")
        
        # Check that variants are generated
        if len(variants) > 0:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_citation_normalization():
    """Test citation format normalization."""
    print("\nTesting citation normalization...")
    print("=" * 60)
    
    test_cases = [
        ("123 L. Ed. 2d 456", "123 L.Ed.2d 456"),
        ("456 S. Ct. 789", "456 S.Ct. 789"),
        ("789 U. S. 123", "789 U.S. 123"),
    ]
    
    all_passed = True
    
    for input_citation, expected in test_cases:
        print(f"\nTesting: '{input_citation}'")
        
        normalized = normalize_citation_format(input_citation)
        print(f"Normalized: '{normalized}' (expected: '{expected}')")
        
        if normalized == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_year_extraction():
    """Test year extraction functionality."""
    print("\nTesting year extraction...")
    print("=" * 60)
    
    test_cases = [
        ("Smith v. Jones, 123 U.S. 456 (2020)", "2020"),
        ("In re Johnson, 456 Wash. 789 (2019)", "2019"),
        ("State v. Brown, 789 F.2d 123", ""),  # No year in parentheses
    ]
    
    all_passed = True
    
    for line, expected in test_cases:
        print(f"\nTesting: '{line}'")
        
        year = extract_year_from_line(line)
        print(f"Extracted year: '{year}' (expected: '{expected}')")
        
        if year == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_triple_extraction():
    """Test triple extraction functionality."""
    print("\nTesting triple extraction...")
    print("=" * 60)
    
    text = "The court held in Smith v. Jones, 123 U.S. 456 (2020), that the principle applies."
    citation = "123 U.S. 456"
    canonical_name = "Smith v. Jones"
    
    print(f"Text: {text}")
    print(f"Citation: {citation}")
    print(f"Canonical name: {canonical_name}")
    
    result = extract_case_name_triple_from_text(text, citation, canonical_name)
    
    print(f"\nTriple extraction result:")
    print(f"  Canonical name: {result['canonical_name']}")
    print(f"  Extracted name: {result['extracted_name']}")
    print(f"  Hinted name: {result['hinted_name']}")
    
    # Check that all fields are present
    if all(key in result for key in ['canonical_name', 'extracted_name', 'hinted_name']):
        print("✓ PASS")
        return True
    else:
        print("✗ FAIL")
        return False

def main():
    """Run all tests."""
    print("Testing Enhanced Case Name Extraction Functionality")
    print("=" * 80)
    
    tests = [
        ("Core Extraction", test_core_extraction),
        ("Validation and Cleaning", test_validation_and_cleaning),
        ("Abbreviation Expansion", test_abbreviation_expansion),
        ("Citation URL Generation", test_citation_url_generation),
        ("Washington Citation Variants", test_washington_citation_variants),
        ("Citation Normalization", test_citation_normalization),
        ("Year Extraction", test_year_extraction),
        ("Triple Extraction", test_triple_extraction),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The enhanced case name extraction is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main() 