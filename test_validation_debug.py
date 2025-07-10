#!/usr/bin/env python3
"""
Test to debug the case name validation logic
"""

from src.standalone_citation_parser import CitationParser

def test_validation():
    """Test the validation logic"""
    
    parser = CitationParser()
    case_name = "Punx v Smithers"
    
    print(f"Testing case name: '{case_name}'")
    print("-" * 50)
    
    # Test validation
    is_valid = parser._is_valid_case_name(case_name)
    print(f"_is_valid_case_name: {is_valid}")
    
    # Test cleaning
    cleaned = parser._clean_case_name(case_name)
    print(f"_clean_case_name: '{cleaned}'")
    
    # Test extraction
    extracted = parser._extract_just_case_name(case_name)
    print(f"_extract_just_case_name: '{extracted}'")
    
    # Test the full chain
    context = "Punx v Smithers, "
    result = parser._extract_case_name_from_context(context)
    print(f"_extract_case_name_from_context: '{result}'")

if __name__ == "__main__":
    test_validation() 