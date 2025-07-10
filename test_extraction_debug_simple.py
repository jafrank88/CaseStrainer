#!/usr/bin/env python3
"""
Simple test to debug extraction with the specific example
"""

import logging
from src.case_name_extraction_core import extract_case_name_triple
from src.standalone_citation_parser import CitationParser

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def test_specific_example():
    """Test the specific example that's failing"""
    
    text = "Punx v Smithers, 534 F.3d 1290 (1921)"
    
    # Test different citation formats
    citations = [
        "534 F.3d 1290",  # Original format
        "534 F.3d 1290 (1921)",  # With year
        "534 F.3d 1290, 1921",  # Alternative format
    ]
    
    print("🔍 TESTING SPECIFIC EXAMPLE...")
    print(f"Text: '{text}'")
    print("-" * 60)
    
    for i, citation in enumerate(citations, 1):
        print(f"📋 Test {i}: Citation '{citation}'")
        
        # Test 1: Direct extraction function
        try:
            result = extract_case_name_triple(text, citation)
            print(f"  extract_case_name_triple result:")
            print(f"    extracted_name: '{result.get('extracted_name', 'NOT_FOUND')}'")
            print(f"    extracted_date: '{result.get('extracted_date', 'NOT_FOUND')}'")
            print(f"    case_name: '{result.get('case_name', 'NOT_FOUND')}'")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Test 2: CitationParser directly
        try:
            parser = CitationParser()
            parser_result = parser.extract_from_text(text, citation)
            print(f"  CitationParser result:")
            print(f"    case_name: '{parser_result.get('case_name', 'NOT_FOUND')}'")
            print(f"    year: '{parser_result.get('year', 'NOT_FOUND')}'")
            print(f"    full_citation_found: {parser_result.get('full_citation_found', False)}")
            print(f"    matched_citation: '{parser_result.get('matched_citation', 'NOT_FOUND')}'")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()

def test_simple_extraction():
    """Test simple extraction without complex patterns"""
    
    print("🔍 TESTING SIMPLE EXTRACTION...")
    
    # Simple test case
    text = "In the case of Smith v. Jones, 123 F.2d 456 (2020), the court held..."
    citation = "123 F.2d 456"
    
    print(f"Text: '{text}'")
    print(f"Citation: '{citation}'")
    print("-" * 60)
    
    try:
        parser = CitationParser()
        result = parser.extract_from_text(text, citation)
        print(f"Result: {result}")
        print(f"case_name: '{result.get('case_name', 'NOT_FOUND')}'")
        print(f"year: '{result.get('year', 'NOT_FOUND')}'")
        print(f"full_citation_found: {result.get('full_citation_found', False)}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_debug_context():
    """Test to see exactly what context is being used"""
    
    print("🔍 DEBUGGING CONTEXT...")
    
    text = "Punx v Smithers, 534 F.3d 1290 (1921)"
    citation = "534 F.3d 1290"
    
    print(f"Text: '{text}'")
    print(f"Citation: '{citation}'")
    print("-" * 60)
    
    try:
        parser = CitationParser()
        
        # Find citation in text
        citation_index = text.find(citation)
        print(f"Citation index: {citation_index}")
        
        if citation_index != -1:
            # Get context before citation (200 chars)
            context_start = max(0, citation_index - 200)
            context = text[context_start:citation_index]
            print(f"Full context: '{context}'")
            
            # Get recent context (last 100 chars)
            recent_context = context[-100:] if len(context) > 100 else context
            print(f"Recent context: '{recent_context}'")
            
            # Test the case name patterns directly
            import re
            for i, pattern in enumerate(parser.case_name_patterns):
                print(f"Pattern {i+1}: {pattern}")
                matches = list(re.finditer(pattern, recent_context, re.IGNORECASE))
                print(f"  Matches: {len(matches)}")
                for match in matches:
                    print(f"    Match: '{match.group(1)}'")
        else:
            print("Citation not found in text")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_specific_example()
    print("\n" + "="*60 + "\n")
    test_simple_extraction()
    print("\n" + "="*60 + "\n")
    test_debug_context() 