#!/usr/bin/env python3
"""
Debug script to test the extraction function directly
"""

from src.case_name_extraction_core import extract_case_name_triple
from src.standalone_citation_parser import CitationParser

def test_extraction_directly():
    """Test the extraction function directly"""
    
    text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions"
    citation = "200 Wn.2d 72, 514 P.3d 643"
    
    print("🔍 TESTING EXTRACTION DIRECTLY...")
    print(f"Text: '{text}'")
    print(f"Citation: '{citation}'")
    print("-" * 60)
    
    # Test 1: Direct extraction function
    print("📋 Test 1: extract_case_name_triple")
    try:
        result = extract_case_name_triple(text, citation)
        print(f"Result: {result}")
        print(f"extracted_name: '{result.get('extracted_name', 'NOT_FOUND')}'")
        print(f"extracted_date: '{result.get('extracted_date', 'NOT_FOUND')}'")
        print(f"case_name: '{result.get('case_name', 'NOT_FOUND')}'")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 2: CitationParser directly
    print("📋 Test 2: CitationParser directly")
    try:
        parser = CitationParser()
        parser_result = parser.extract_from_text(text, citation)
        print(f"Parser result: {parser_result}")
        print(f"case_name: '{parser_result.get('case_name', 'NOT_FOUND')}'")
        print(f"year: '{parser_result.get('year', 'NOT_FOUND')}'")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 3: Test with different citation format
    print("📋 Test 3: Different citation format")
    try:
        citation2 = "200 Wn.2d 72"
        result2 = extract_case_name_triple(text, citation2)
        print(f"Result with '{citation2}': {result2}")
        print(f"extracted_name: '{result2.get('extracted_name', 'NOT_FOUND')}'")
        print(f"extracted_date: '{result2.get('extracted_date', 'NOT_FOUND')}'")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_extraction_directly() 