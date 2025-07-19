#!/usr/bin/env python3
"""
Test script to verify the improved case name extraction function works correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.case_name_extraction_core import extract_case_name_improved

def test_improved_extraction():
    """Test the improved extraction on examples from the analysis."""
    
    test_cases = [
        {
            'context': "The court held in Smith v. Jones, 200 Wn.2d 72, 73, 514 P.3d 643 (2022) that...",
            'citation': "200 Wn.2d 72",
            'expected': "Smith v. Jones"
        },
        {
            'context': "As established in Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)...",
            'citation': "146 Wn.2d 1",
            'expected': "Department of Ecology v. Campbell & Gwinn, LLC"
        },
        {
            'context': "In re Estate of Smith, 170 Wn.2d 614, 316 P.3d 1020 (2010)...",
            'citation': "170 Wn.2d 614",
            'expected': "In re Estate of Smith"
        },
        {
            'context': "State v. Johnson, 93 Wn.2d 31, 604 P.2d 1293 (2002)...",
            'citation': "93 Wn.2d 31",
            'expected': "State v. Johnson"
        },
        {
            'context': "United States v. Smith, 446 U.S. 544 (1980)...",
            'citation': "446 U.S. 544",
            'expected': "United States v. Smith"
        },
        {
            'context': "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)...",
            'citation': "200 Wn.2d 72",
            'expected': "Convoyant, LLC v. DeepThink, LLC"
        },
        {
            'context': "Carlson v. Global Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)...",
            'citation': "171 Wn.2d 486",
            'expected': "Carlson v. Global Client Sols., LLC"
        }
    ]
    
    print("Testing Improved Case Name Extraction:")
    print("=" * 60)
    
    success_count = 0
    for i, test_case in enumerate(test_cases):
        result = extract_case_name_improved(test_case['context'], test_case['citation'])
        case_name, date, confidence = result
        success = case_name == test_case['expected']
        if success:
            success_count += 1
        
        print(f"Test {i+1}:")
        print(f"  Context: '{test_case['context']}'")
        print(f"  Citation: '{test_case['citation']}'")
        print(f"  Expected: '{test_case['expected']}'")
        print(f"  Result:   '{case_name}'")
        print(f"  Date:     '{date}'")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Status:   {'✓ PASS' if success else '✗ FAIL'}")
        print()
    
    print(f"Overall Success Rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    
    return success_count == len(test_cases)

def test_with_actual_failures():
    """Test with some of the actual failed extractions from the analysis."""
    
    # These are examples from the failed extractions analysis
    failure_cases = [
        {
            'context': "The court held in Smith v. Jones, 200 Wn.2d 72, 73, 514 P.3d 643 (2022) that the plaintiff...",
            'citation': "200 Wn.2d 72",
            'expected': "Smith v. Jones"
        },
        {
            'context': "As established in Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003), the agency...",
            'citation': "146 Wn.2d 1", 
            'expected': "Department of Ecology v. Campbell & Gwinn, LLC"
        },
        {
            'context': "According to the holding in State v. Johnson, 93 Wn.2d 31, 604 P.2d 1293 (2002), the defendant...",
            'citation': "93 Wn.2d 31",
            'expected': "State v. Johnson"
        }
    ]
    
    print("\nTesting with Actual Failure Cases:")
    print("=" * 60)
    
    success_count = 0
    for i, test_case in enumerate(failure_cases):
        result = extract_case_name_improved(test_case['context'], test_case['citation'])
        case_name, date, confidence = result
        success = case_name == test_case['expected']
        if success:
            success_count += 1
        
        print(f"Failure Test {i+1}:")
        print(f"  Context: '{test_case['context']}'")
        print(f"  Citation: '{test_case['citation']}'")
        print(f"  Expected: '{test_case['expected']}'")
        print(f"  Result:   '{case_name}'")
        print(f"  Date:     '{date}'")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Status:   {'✓ PASS' if success else '✗ FAIL'}")
        print()
    
    print(f"Failure Case Success Rate: {success_count}/{len(failure_cases)} ({success_count/len(failure_cases)*100:.1f}%)")
    
    return success_count == len(failure_cases)

if __name__ == "__main__":
    print("Testing Improved Case Name Extraction Integration")
    print("=" * 60)
    
    # Test basic functionality
    basic_success = test_improved_extraction()
    
    # Test with actual failure cases
    failure_success = test_with_actual_failures()
    
    # Additional: Print % of cases with non-N/A extraction
    print("\nChecking % of cases with non-N/A extraction:")
    test_cases = [
        {
            'context': "The court held in Smith v. Jones, 200 Wn.2d 72, 73, 514 P.3d 643 (2022) that...",
            'citation': "200 Wn.2d 72",
        },
        {
            'context': "As established in Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)...",
            'citation': "146 Wn.2d 1",
        },
        {
            'context': "In re Estate of Smith, 170 Wn.2d 614, 316 P.3d 1020 (2010)...",
            'citation': "170 Wn.2d 614",
        },
        {
            'context': "State v. Johnson, 93 Wn.2d 31, 604 P.2d 1293 (2002)...",
            'citation': "93 Wn.2d 31",
        },
        {
            'context': "United States v. Smith, 446 U.S. 544 (1980)...",
            'citation': "446 U.S. 544",
        },
        {
            'context': "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)...",
            'citation': "200 Wn.2d 72",
        },
        {
            'context': "Carlson v. Global Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)...",
            'citation': "171 Wn.2d 486",
        }
    ]
    non_na_count = 0
    for case in test_cases:
        result = extract_case_name_improved(case['context'], case['citation'])
        case_name, date, confidence = result
        if case_name and case_name != 'N/A':
            non_na_count += 1
    percent = 100.0 * non_na_count / len(test_cases)
    print(f"Non-N/A extraction: {non_na_count}/{len(test_cases)} ({percent:.1f}%)")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Basic Tests: {'✓ PASSED' if basic_success else '✗ FAILED'}")
    print(f"Failure Cases: {'✓ PASSED' if failure_success else '✗ FAILED'}")
    
    if basic_success and failure_success:
        print("\n🎉 All tests passed! The improved extraction function is working correctly.")
    else:
        print("\n⚠️  Some tests failed. The extraction function may need further refinement.") 