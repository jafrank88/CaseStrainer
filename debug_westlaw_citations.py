#!/usr/bin/env python3
"""
Debug script to test case name extraction for Westlaw citations that are failing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.extract_case_name import extract_case_name_from_context, extract_case_name_from_text

def test_westlaw_citations():
    """Test case name extraction for the failing Westlaw citations"""
    
    # Test cases from the user's data
    test_cases = [
        {
            "citation": "2006 WL 3801910",
            "context": "Courts have consistently held that evidence with a high potential for prejudice",
            "expected": "Wyoming v. U.S. Department of Energy"  # This should be the actual case name
        },
        {
            "citation": "2018 WL 2446162",
            "context": "In Holland v. Keller",
            "expected": "Holland v. Keller"
        },
        {
            "citation": "2019 WL 2516279",
            "context": "United States v. Hargrove",
            "expected": "United States v. Hargrove"
        },
        {
            "citation": "2017 WL 3461055",
            "context": "Meyer v. City of Cheyenne",
            "expected": "Meyer v. City of Cheyenne"
        },
        {
            "citation": "2010 WL 4683851",
            "context": "Federal Rules of Evidence intend to protect against. In Benson v. State",
            "expected": "Benson v. State of Wyoming"
        },
        {
            "citation": "2011 WL 2160468",
            "context": "Plaintiff. Federal courts have consistently held that testimony regarding alcohol use is",
            "expected": "Smith v. United States"
        },
        {
            "citation": "2016 WL 165971",
            "context": "In Woods v. BNSF Railway Co",
            "expected": "Woods v. BNSF Railway Co"
        },
        {
            "citation": "2018 WL 3037217",
            "context": "Fitzgerald v. City of New York",
            "expected": "Fitzgerald v. City of New York"
        },
        {
            "citation": "534 F.3d 1290",
            "context": "Evidence is unfairly prejudicial if it has ôan undue tendency to suggest [a] decision on an improper basis, commonly, though not necessarily, an emotional one.ö U.S. v. Caraway , 534 F.3d 1290, 1301 (10th Cir. 2008) (quoting Rule 402 adv. comm. notes).",
            "expected": "U.S. v. Caraway"
        }
    ]
    
    print("Testing Westlaw citation case name extraction:")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        citation = test_case["citation"]
        context = test_case["context"]
        expected = test_case["expected"]
        
        print(f"\nTest {i}: {citation}")
        print(f"Context: {context}")
        print(f"Expected: {expected}")
        
        # Test the context extraction
        extracted_from_context = extract_case_name_from_context(context, citation)
        print(f"From context: '{extracted_from_context}'")
        
        # Test the full text extraction
        # Create a mock full text with the context and citation
        full_text = f"{context} {citation}"
        extracted_from_text = extract_case_name_from_text(full_text, citation)
        print(f"From text: '{extracted_from_text}'")
        
        # Check which method worked
        context_match = extracted_from_context == expected
        text_match = extracted_from_text == expected
        
        if context_match or text_match:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            
        print("-" * 80)
    
    # Now let's test with more realistic context that might be in the PDF
    print("\n" + "=" * 80)
    print("Testing with more realistic PDF context:")
    print("=" * 80)
    
    realistic_tests = [
        {
            "citation": "2006 WL 3801910",
            "context": "The court in Wyoming v. U.S. Department of Energy, 2006 WL 3801910, held that...",
            "expected": "Wyoming v. U.S. Department of Energy"
        },
        {
            "citation": "2010 WL 4683851",
            "context": "As stated in Benson v. State of Wyoming, 2010 WL 4683851, the evidence...",
            "expected": "Benson v. State of Wyoming"
        },
        {
            "citation": "2011 WL 2160468",
            "context": "In Smith v. United States, 2011 WL 2160468, the court found...",
            "expected": "Smith v. United States"
        }
    ]
    
    for i, test_case in enumerate(realistic_tests, 1):
        citation = test_case["citation"]
        context = test_case["context"]
        expected = test_case["expected"]
        
        print(f"\nRealistic Test {i}: {citation}")
        print(f"Context: {context}")
        print(f"Expected: {expected}")
        
        extracted = extract_case_name_from_context(context, citation)
        print(f"Extracted: '{extracted}'")
        
        if extracted == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            
        print("-" * 80)

if __name__ == "__main__":
    test_westlaw_citations() 