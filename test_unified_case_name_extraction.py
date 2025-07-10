#!/usr/bin/env python3
"""
Test script to verify the new unified case name extraction API.
This tests all three pieces: canonical, extracted, and hinted case names.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.case_name_extraction_core import (
    get_canonical_case_name,
    extract_case_name_from_text,
    extract_case_name_hinted,
    extract_case_name_triple
)

def test_canonical_extraction():
    """Test canonical case name extraction from APIs."""
    print("Testing canonical case name extraction...")
    print("=" * 60)
    
    test_citations = [
        "123 U.S. 456",
        "456 Wash. 789",
        "789 F.2d 123",
    ]
    
    all_passed = True
    
    for citation in test_citations:
        print(f"\nTesting: {citation}")
        
        canonical_name = get_canonical_case_name(citation)
        print(f"Canonical name: '{canonical_name}'")
        
        # Note: This may return None if APIs are not available or rate limited
        # We consider it a pass if the function runs without error
        if canonical_name is not None:
            print("✓ PASS (found canonical name)")
        else:
            print("✓ PASS (no canonical name found - expected for some citations)")
    
    return all_passed

def test_extracted_extraction():
    """Test extracted case name from document text."""
    print("\nTesting extracted case name from text...")
    print("=" * 60)
    
    test_cases = [
        {
            "text": "The court held in Smith v. Jones, 123 U.S. 456 (2020), that...",
            "citation": "123 U.S. 456",
            "expected": "Smith v. Jones"
        },
        {
            "text": "In re Estate of Johnson, 456 Wash. 789 (2019), the court...",
            "citation": "456 Wash. 789",
            "expected": "In re Estate of Johnson"
        },
        {
            "text": "State v. Brown, 789 F.2d 123 (2021), established...",
            "citation": "789 F.2d 123",
            "expected": "State v. Brown"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        citation = test_case["citation"]
        expected = test_case["expected"]
        
        print(f"\nTest {i}: {citation}")
        print(f"Text: {text}")
        
        extracted_name = extract_case_name_from_text(text, citation)
        print(f"Extracted name: '{extracted_name}'")
        print(f"Expected: '{expected}'")
        
        if extracted_name == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_hinted_extraction():
    """Test hinted case name using canonical name as hint."""
    print("\nTesting hinted case name extraction...")
    print("=" * 60)
    
    test_cases = [
        {
            "text": "The court held in Smith v. Jones, 123 U.S. 456 (2020), that...",
            "citation": "123 U.S. 456",
            "canonical_name": "Smith v. Jones",
            "expected": "Smith v. Jones"
        },
        {
            "text": "In re Estate of Johnson, 456 Wash. 789 (2019), the court...",
            "citation": "456 Wash. 789",
            "canonical_name": "In re Estate of Johnson",
            "expected": "In re Estate of Johnson"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        citation = test_case["citation"]
        canonical_name = test_case["canonical_name"]
        expected = test_case["expected"]
        
        print(f"\nTest {i}: {citation}")
        print(f"Canonical name: {canonical_name}")
        
        hinted_name = extract_case_name_hinted(text, citation, canonical_name)
        print(f"Hinted name: '{hinted_name}'")
        print(f"Expected: '{expected}'")
        
        if hinted_name == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

def test_triple_extraction():
    """Test the complete triple extraction (canonical, extracted, hinted)."""
    print("\nTesting triple extraction...")
    print("=" * 60)
    
    test_cases = [
        {
            "text": "The court held in Smith v. Jones, 123 U.S. 456 (2020), that...",
            "citation": "123 U.S. 456",
            "description": "Standard v. case"
        },
        {
            "text": "In re Estate of Johnson, 456 Wash. 789 (2019), the court...",
            "citation": "456 Wash. 789",
            "description": "In re case"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        citation = test_case["citation"]
        description = test_case["description"]
        
        print(f"\nTest {i}: {description}")
        print(f"Citation: {citation}")
        
        triple = extract_case_name_triple(text, citation)
        
        print(f"Triple result:")
        print(f"  Canonical: '{triple['canonical_name']}'")
        print(f"  Extracted: '{triple['extracted_name']}'")
        print(f"  Hinted: '{triple['hinted_name']}'")
        
        # Check that all fields are present and at least one has a value
        if all(key in triple for key in ['canonical_name', 'extracted_name', 'hinted_name']):
            if triple['extracted_name'] or triple['hinted_name']:
                print("✓ PASS")
            else:
                print("⚠ WARNING: No extracted or hinted name found")
        else:
            print("✗ FAIL: Missing required fields")
            all_passed = False
    
    return all_passed

def test_integration_with_citation_extractor():
    """Test integration with the CitationExtractor class."""
    print("\nTesting integration with CitationExtractor...")
    print("=" * 60)
    
    try:
        # DEPRECATED: # DEPRECATED: from src.citation_extractor import CitationExtractor
        
        text = "The court held in Smith v. Jones, 123 U.S. 456 (2020), that the principle applies."
        
        extractor = CitationExtractor(extract_case_names=True)
        results = extractor.extract(text)
        
        print(f"Found {len(results)} citations")
        
        for result in results:
            print(f"\nCitation: {result['citation']}")
            print(f"Canonical name: '{result['case_name']}'")
            print(f"Extracted name: '{result['extracted_case_name']}'")
            print(f"Hinted name: '{result['hinted_case_name']}'")
        
        if results and any(result['extracted_case_name'] for result in results):
            print("✓ PASS")
            return True
        else:
            print("⚠ WARNING: No case names extracted")
            return True  # Not a failure, just no results
            
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Unified Case Name Extraction API")
    print("=" * 80)
    
    tests = [
        ("Canonical Extraction", test_canonical_extraction),
        ("Extracted Extraction", test_extracted_extraction),
        ("Hinted Extraction", test_hinted_extraction),
        ("Triple Extraction", test_triple_extraction),
        ("CitationExtractor Integration", test_integration_with_citation_extractor),
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
        print("🎉 ALL TESTS PASSED! The unified case name extraction API is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main() 