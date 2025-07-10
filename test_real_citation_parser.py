#!/usr/bin/env python3
"""
Test script using the real CitationParser from standalone_citation_parser.py
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.standalone_citation_parser import CitationParser
import re

def test_real_citation_parser():
    """Test the real CitationParser with our test cases."""
    
    # Initialize the real CitationParser
    parser = CitationParser()
    
    # Test cases from our previous debugging
    test_cases = [
        {
            "text": "In State v. Smith, 171 Wn.2d 486, 256 P.3d 321 (2011), the court held that...",
            "citation": "171 Wn.2d 486",
            "expected_case_name": "State v. Smith"
        },
        {
            "text": "The defendant in State v. Johnson, 123 Cal. 4th 456, 789 P.3d 123 (2010) argued that...",
            "citation": "123 Cal. 4th 456", 
            "expected_case_name": "State v. Johnson"
        },
        {
            "text": "As established in Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court...",
            "citation": "347 U.S. 483",
            "expected_case_name": "Brown v. Board of Education"
        },
        {
            "text": "The court in Department of Ecology v. PUD No. 1, 121 Wn.2d 179, 849 P.2d 646 (1993) ruled...",
            "citation": "121 Wn.2d 179",
            "expected_case_name": "Department of Ecology v. PUD No. 1"
        },
        {
            "text": "In the case of In re Estate of Smith, 158 Wn.2d 1, 139 P.3d 1034 (2006), the court...",
            "citation": "158 Wn.2d 1",
            "expected_case_name": "In re Estate of Smith"
        }
    ]
    
    print("=== Testing Real CitationParser ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected: {test_case['expected_case_name']}")
        
        try:
            # Use the real CitationParser's extract_from_text method
            result = parser.extract_from_text(test_case['text'], test_case['citation'])
            
            print(f"Result: {result}")
            print(f"Extracted case name: {result.get('case_name', 'None')}")
            print(f"Extraction method: {result.get('extraction_method', 'None')}")
            print(f"Full citation found: {result.get('full_citation_found', 'None')}")
            print(f"Year: {result.get('year', 'None')}")
            
            # Check if extraction was successful
            if result.get('case_name'):
                print("✅ SUCCESS: Case name extracted")
            else:
                print("❌ FAILED: No case name extracted")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 80)
    
    # Test the individual methods
    print("\n=== Testing Individual Methods ===\n")
    
    test_text = "In State v. Smith, 171 Wn.2d 486, 256 P.3d 321 (2011), the court held that..."
    test_citation = "171 Wn.2d 486"
    
    print(f"Test text: {test_text}")
    print(f"Test citation: {test_citation}")
    
    try:
        # Test find_full_citation_in_text
        print("\n1. Testing find_full_citation_in_text:")
        full_citation = parser.find_full_citation_in_text(test_text, test_citation)
        print(f"   Full citation found: {full_citation}")
        
        # Test find_case_name_before_citation
        print("\n2. Testing find_case_name_before_citation:")
        if full_citation:
            case_name = parser.find_case_name_before_citation(test_text, full_citation)
            print(f"   Case name found: {case_name}")
        
        # Test extract_year_from_citation
        print("\n3. Testing extract_year_from_citation:")
        if full_citation:
            year = parser.extract_year_from_citation(full_citation)
            print(f"   Year extracted: {year}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n=== Testing Case Name Validation ===\n")
    
    # Test the validation method
    test_names = [
        "State v. Smith",
        "Department of Ecology v. PUD No. 1", 
        "In re Estate of Smith",
        "Brown v. Board of Education",
        "This is not a case name",
        "v. Smith",  # Too short
        "A very long case name that exceeds reasonable limits and should be rejected because it's way too long to be a real case name in legal documents",
        "Smith v.",  # Incomplete
        "v. v. Smith"  # Invalid format
    ]
    
    for name in test_names:
        is_valid = parser._is_valid_case_name(name)
        print(f"'{name}' -> {'✅ Valid' if is_valid else '❌ Invalid'}")

    print("\n=== Testing Improved Validation on New Cases ===\n")
    improved_test_cases = [
        "Convoyant, LLC v. DeepThink, LLC",          # Should pass
        "Carlsen v. Global Client Solutions, LLC",   # Should pass  
        "Department of Ecology v. Campbell & Gwinn, LLC",  # Should pass
        "In re Marriage of Williams",                # Should NOW pass (was rejected before)
        "Ex parte Johnson",                          # Should NOW pass (was rejected before)
        "Dep't of Labor v. Smith",                   # Should NOW pass (was rejected before)
    ]
    for case_name in improved_test_cases:
        result = parser._is_valid_case_name(case_name)
        print(f"{case_name:50}  {'	✅ VALID' if result else '	❌ INVALID'}")

if __name__ == "__main__":
    test_real_citation_parser() 