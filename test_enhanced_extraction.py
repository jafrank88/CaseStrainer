#!/usr/bin/env python3
"""
Test script for enhanced case name and date extraction functions.
Demonstrates the improved regex-based extraction capabilities.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_enhanced_extraction():
    """Test the enhanced extraction functions with various legal text examples."""
    
    # Test cases with different formats
    test_cases = [
        {
            "text": "In Smith v. Jones, 123 Wn.2d 456 (2023), the court held...",
            "citation": "123 Wn.2d 456",
            "expected_case": "Smith v. Jones",
            "expected_year": "2023"
        },
        {
            "text": "The decision in Estate of Johnson, 456 P.3d 789 (2022) established...",
            "citation": "456 P.3d 789",
            "expected_case": "Estate of Johnson",
            "expected_year": "2022"
        },
        {
            "text": "State v. Williams, 789 Wn. App. 123, 456 P.3d 789 (2021)",
            "citation": "789 Wn. App. 123",
            "expected_case": "State v. Williams",
            "expected_year": "2021"
        },
        {
            "text": "In re Matter of Brown, decided on January 15, 2024, 321 Wn.2d 654",
            "citation": "321 Wn.2d 654",
            "expected_case": "In re Matter of Brown",
            "expected_year": "2024"
        },
        {
            "text": "United States v. Davis et al., 654 F.3d 123 (2020)",
            "citation": "654 F.3d 123",
            "expected_case": "United States v. Davis et al.",
            "expected_year": "2020"
        },
        {
            "text": "The case of Johnson and Smith v. Corporation, filed in 2019, 987 P.2d 321",
            "citation": "987 P.2d 321",
            "expected_case": "Johnson and Smith v. Corporation",
            "expected_year": "2019"
        }
    ]
    
    print("=== Enhanced Case Name and Date Extraction Test ===\n")
    
    # Import the enhanced extraction functions
    try:
        from src.enhanced_extraction_utils import (
            extract_case_name_enhanced,
            extract_date_enhanced,
            extract_year_enhanced,
            extract_case_info_enhanced
        )
        print("✅ Successfully imported enhanced extraction functions\n")
    except ImportError as e:
        print(f"❌ Failed to import enhanced extraction functions: {e}")
        print("Please ensure the enhanced_extraction_utils.py file exists in the src directory.")
        return
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        
        # Test individual functions
        case_name = extract_case_name_enhanced(test_case['text'], test_case['citation'])
        year = extract_year_enhanced(test_case['text'], test_case['citation'])
        date = extract_date_enhanced(test_case['text'], test_case['citation'])
        
        # Test combined function
        case_info = extract_case_info_enhanced(test_case['text'], test_case['citation'])
        
        print(f"Extracted Case Name: {case_name}")
        print(f"Extracted Year: {year}")
        print(f"Extracted Date: {date}")
        print(f"Combined Info: {case_info}")
        
        # Check results
        case_match = case_name == test_case['expected_case']
        year_match = year == test_case['expected_year']
        
        print(f"Case Name Match: {'✅' if case_match else '❌'}")
        print(f"Year Match: {'✅' if year_match else '❌'}")
        print("-" * 80)
    
    # Test with text that has no clear case name
    print("\nTest Case - No Clear Case Name:")
    text_without_case = "The court decided in 2023 that the statute was constitutional."
    case_name = extract_case_name_enhanced(text_without_case)
    year = extract_year_enhanced(text_without_case)
    print(f"Text: {text_without_case}")
    print(f"Extracted Case Name: {case_name}")
    print(f"Extracted Year: {year}")
    print(f"Expected: Case Name should be None, Year should be '2023'")
    print(f"Case Name Correct: {'✅' if case_name is None else '❌'}")
    print(f"Year Correct: {'✅' if year == '2023' else '❌'}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_enhanced_extraction() 