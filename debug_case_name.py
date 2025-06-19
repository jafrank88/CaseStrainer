#!/usr/bin/env python3
"""
Debug script to test case name extraction
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.extract_case_name import extract_case_name_from_text

def test_case_name_extraction():
    """Test case name extraction with real examples"""
    
    # Test cases from the logs
    test_cases = [
        {
            "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court held that racial segregation in public schools was unconstitutional.",
            "citation": "347 U.S. 483",
            "expected": "Brown v. Board of Education"
        },
        {
            "text": "The case of Terhune v. A. H. Robins Co., 90 Wn.2d 9, established important precedent.",
            "citation": "90 Wn.2d 9",
            "expected": "Terhune v. A. H. Robins Co."
        },
        {
            "text": "Frias v. Asset Foreclosure Services, Inc., 181 Wn.2d 412, addressed foreclosure procedures.",
            "citation": "181 Wn.2d 412",
            "expected": "Frias v. Asset Foreclosure Services, Inc."
        }
    ]
    
    print("=== Testing Case Name Extraction ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected: {test_case['expected']}")
        
        # Test the extraction
        extracted = extract_case_name_from_text(test_case['text'], test_case['citation'])
        print(f"Extracted: {extracted}")
        print(f"Match: {extracted == test_case['expected']}")
        print("-" * 80)
    
    # Test with a more complex example
    complex_text = """
    The Washington Supreme Court in State v. Smith, 123 Wn.2d 456, 
    and the Court of Appeals in Jones v. Johnson, 456 P.3d 789, 
    both addressed similar issues regarding search and seizure.
    """
    
    print("Complex Test:")
    print(f"Text: {complex_text}")
    
    citations = ["123 Wn.2d 456", "456 P.3d 789"]
    for citation in citations:
        extracted = extract_case_name_from_text(complex_text, citation)
        print(f"Citation: {citation} -> Extracted: {extracted}")

if __name__ == "__main__":
    test_case_name_extraction() 