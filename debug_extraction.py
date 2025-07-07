#!/usr/bin/env python3
import logging
import sys
sys.path.append('.')

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

from src.extract_case_name import extract_case_name_from_text

def test_direct_extraction():
    """Test the extraction function directly."""
    print("Testing direct extraction...")
    
    # Test case 1: Simple v. pattern
    text = "The court in Doe P v. Thurston County, 199 Wn. App. 280, found that the principle applies."
    citation = "199 Wn. App. 280"
    
    print(f"\nText: {text}")
    print(f"Citation: {citation}")
    
    result = extract_case_name_from_text(text, citation)
    print(f"Extracted: '{result}'")
    
    # Test case 2: In re pattern
    text2 = "In re Estate of Johnson, 456 Wash. 789 (2019), the court..."
    citation2 = "456 Wash. 789"
    
    print(f"\nText: {text2}")
    print(f"Citation: {citation2}")
    
    result2 = extract_case_name_from_text(text2, citation2)
    print(f"Extracted: '{result2}'")
    
    # Test case 3: State v. pattern
    text3 = "State v. Smith, 123 U.S. 456, established..."
    citation3 = "123 U.S. 456"
    
    print(f"\nText: {text3}")
    print(f"Citation: {citation3}")
    
    result3 = extract_case_name_from_text(text3, citation3)
    print(f"Extracted: '{result3}'")

if __name__ == "__main__":
    test_direct_extraction() 