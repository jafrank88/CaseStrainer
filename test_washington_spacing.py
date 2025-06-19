#!/usr/bin/env python3
"""
Test script to verify Washington citation spacing rules are working correctly.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.citation_format_utils import apply_washington_spacing_rules, normalize_washington_synonyms
from src.citation_utils import normalize_citation_text
from src.citation_correction_engine import CitationCorrectionEngine
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_washington_spacing_rules():
    """Test the Washington spacing rules function directly."""
    print("=== Testing Washington Spacing Rules ===")
    
    test_cases = [
        # Washington Reports - should have no space between Wn. and 2d
        ("123 Wn. 2d 456", "123 Wn.2d 456"),
        ("123 Wn.2d 456", "123 Wn.2d 456"),
        ("123 Wash. 2d 456", "123 Wn.2d 456"),
        ("123 Wash.2d 456", "123 Wn.2d 456"),
        
        # Washington Appellate Reports - should have space between Wn. and App.
        ("45 Wn.App. 678", "45 Wn. App. 678"),
        ("45 Wn. App. 678", "45 Wn. App. 678"),
        ("45 Wash.App. 678", "45 Wn. App. 678"),
        ("45 Wash. App. 678", "45 Wn. App. 678"),
        
        # Mixed cases
        ("123 Wn. 2d 456, 45 Wn.App. 678", "123 Wn.2d 456, 45 Wn. App. 678"),
        ("Smith v. Jones, 123 Wn. 2d 456 (2015)", "Smith v. Jones, 123 Wn.2d 456 (2015)"),
    ]
    
    all_passed = True
    for input_text, expected in test_cases:
        result = apply_washington_spacing_rules(input_text)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: '{input_text}' -> '{result}' (expected: '{expected}')")
        if not passed:
            all_passed = False
    
    print(f"\nWashington spacing rules test: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed

def test_citation_utils_normalization():
    """Test the citation utils normalization function."""
    print("\n=== Testing Citation Utils Normalization ===")
    
    test_cases = [
        ("123 Wn. 2d 456", "123 Wn.2d 456"),
        ("45 Wn.App. 678", "45 Wn. App. 678"),
        ("123 Wash. 2d 456", "123 Wn.2d 456"),
        ("45 Wash.App. 678", "45 Wn. App. 678"),
    ]
    
    all_passed = True
    for input_text, expected in test_cases:
        result = normalize_citation_text(input_text)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: '{input_text}' -> '{result}' (expected: '{expected}')")
        if not passed:
            all_passed = False
    
    print(f"\nCitation utils normalization test: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed

def test_citation_correction_engine():
    """Test the citation correction engine normalization."""
    print("\n=== Testing Citation Correction Engine ===")
    
    try:
        engine = CitationCorrectionEngine()
        
        test_cases = [
            ("123 Wn. 2d 456", "123 Wn.2d 456"),
            ("45 Wn.App. 678", "45 Wn. App. 678"),
        ]
        
        all_passed = True
        for input_text, expected in test_cases:
            result = engine._normalize_citation(input_text)
            passed = result == expected
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: '{input_text}' -> '{result}' (expected: '{expected}')")
            if not passed:
                all_passed = False
        
        print(f"\nCitation correction engine test: {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
        
    except Exception as e:
        print(f"✗ FAIL: Error initializing citation correction engine: {e}")
        return False

def test_enhanced_multi_source_verifier():
    """Test the enhanced multi-source verifier normalization."""
    print("\n=== Testing Enhanced Multi-Source Verifier ===")
    
    try:
        verifier = EnhancedMultiSourceVerifier()
        
        test_cases = [
            ("123 Wn. 2d 456", "123 Wn.2d 456"),
            ("45 Wn.App. 678", "45 Wn. App. 678"),
        ]
        
        all_passed = True
        for input_text, expected in test_cases:
            result = verifier._normalize_citation(input_text)
            passed = result == expected
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: '{input_text}' -> '{result}' (expected: '{expected}')")
            if not passed:
                all_passed = False
        
        print(f"\nEnhanced multi-source verifier test: {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
        
    except Exception as e:
        print(f"✗ FAIL: Error initializing enhanced multi-source verifier: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Washington Citation Spacing Rules Implementation")
    print("=" * 60)
    
    tests = [
        test_washington_spacing_rules,
        test_citation_utils_normalization,
        test_citation_correction_engine,
        test_enhanced_multi_source_verifier,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ FAIL: Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "PASSED" if result else "FAILED"
        print(f"Test {i+1}: {test.__name__} - {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Washington spacing rules are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 