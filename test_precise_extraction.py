#!/usr/bin/env python3
"""
Test script for the new precise extraction functions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.standalone_citation_parser import DateExtractor
from src.extract_case_name import extract_case_name_precise_boundaries

def test_precise_date_extraction():
    """Test the new precise date extraction function."""
    print("=== Testing Precise Date Extraction ===")
    
    # Test cases
    test_cases = [
        {
            "text": "In State v. Smith, 123 Wn.2d 456 (2020), the court held...",
            "citation_start": 15,
            "citation_end": 30,
            "expected": "2020-01-01"
        },
        {
            "text": "The case was decided in Brown v. Board, 123 Wn.2d 456, 789 P.2d 123 (1995).",
            "citation_start": 25,
            "citation_end": 40,
            "expected": "1995-01-01"
        },
        {
            "text": "According to the ruling in Doe v. Roe (2023), the plaintiff...",
            "citation_start": 35,
            "citation_end": 45,
            "expected": "2023-01-01"
        },
        {
            "text": "The court in Johnson v. State, 123 Wn.2d 456, ruled that...",
            "citation_start": 20,
            "citation_end": 35,
            "expected": None  # No year in parentheses
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation position: {test_case['citation_start']}-{test_case['citation_end']}")
        
        result = DateExtractor.extract_date_from_context_precise(
            test_case['text'], 
            test_case['citation_start'], 
            test_case['citation_end']
        )
        
        print(f"Result: {result}")
        print(f"Expected: {test_case['expected']}")
        print(f"✓ PASS" if result == test_case['expected'] else f"✗ FAIL")

def test_precise_case_name_extraction():
    """Test the new precise case name extraction function."""
    print("\n=== Testing Precise Case Name Extraction ===")
    
    # Test cases
    test_cases = [
        {
            "context": "In State v. Smith, the court held that...",
            "expected": "State v. Smith"
        },
        {
            "context": "The case of Brown v. Board of Education, established...",
            "expected": "Brown v. Board of Education"
        },
        {
            "context": "According to In re Estate of Johnson, the probate...",
            "expected": "In re Estate of Johnson"
        },
        {
            "context": "The Department of Transportation v. City of Seattle, case...",
            "expected": "Department of Transportation v. City of Seattle"
        },
        {
            "context": "Some random text without a proper case name pattern.",
            "expected": None
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}:")
        print(f"Context: {test_case['context']}")
        
        result = extract_case_name_precise_boundaries(test_case['context'])
        
        print(f"Result: {result}")
        print(f"Expected: {test_case['expected']}")
        print(f"✓ PASS" if result == test_case['expected'] else f"✗ FAIL")

def test_integration():
    """Test the integration of both functions with a real citation."""
    print("\n=== Testing Integration ===")
    
    test_text = "In State v. Johnson, 123 Wn.2d 456 (2020), the Washington Supreme Court held that the defendant's rights were violated."
    
    # Find the citation position
    citation = "123 Wn.2d 456"
    citation_start = test_text.find(citation)
    citation_end = citation_start + len(citation)
    
    print(f"Test text: {test_text}")
    print(f"Citation: {citation}")
    print(f"Citation position: {citation_start}-{citation_end}")
    
    # Extract date
    extracted_date = DateExtractor.extract_date_from_context_precise(
        test_text, citation_start, citation_end
    )
    print(f"Extracted date: {extracted_date}")
    
    # Extract case name
    context_before = test_text[:citation_start]
    extracted_case_name = extract_case_name_precise_boundaries(context_before)
    print(f"Extracted case name: {extracted_case_name}")
    
    # Expected results
    expected_date = "2020-01-01"
    expected_case_name = "State v. Johnson"
    
    print(f"\nResults:")
    print(f"Date: {extracted_date} (expected: {expected_date})")
    print(f"Case name: {extracted_case_name} (expected: {expected_case_name})")
    
    date_correct = extracted_date == expected_date
    name_correct = extracted_case_name == expected_case_name
    
    print(f"\nSummary:")
    print(f"Date extraction: {'✓ PASS' if date_correct else '✗ FAIL'}")
    print(f"Case name extraction: {'✓ PASS' if name_correct else '✗ FAIL'}")

if __name__ == "__main__":
    test_precise_date_extraction()
    test_precise_case_name_extraction()
    test_integration()
    
    print("\n=== Test Complete ===") 