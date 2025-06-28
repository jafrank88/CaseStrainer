#!/usr/bin/env python3
"""
Test script to verify citation extraction fix.
"""

from src.citation_extractor import CitationExtractor, extract_citation_text_from_eyecite

def test_citation_extraction():
    """Test citation extraction with a simple example."""
    print("Testing citation extraction fix...")
    
    # Test the extract_citation_text_from_eyecite function with a mock eyecite object
    class MockEyeciteObject:
        def __init__(self, citation_text):
            self.citation_text = citation_text
        
        def __str__(self):
            return f"FullCaseCitation('{self.citation_text}')"
    
    test_obj = MockEyeciteObject("121 Wn.2d 205, 848 P.2d 1258")
    extracted = extract_citation_text_from_eyecite(test_obj)
    print(f"Test eyecite object: {test_obj}")
    print(f"Extracted: {extracted}")
    print(f"Success: {extracted == '121 Wn.2d 205, 848 P.2d 1258'}")
    
    # Test with a real citation extractor
    extractor = CitationExtractor(use_eyecite=True, use_regex=True)
    test_text = "See State v. Richardson, 177 Wn.2d 351, 302 P.3d 156 (2013)."
    
    print(f"\nTesting with text: {test_text}")
    results = extractor.extract(test_text)
    
    print(f"Found {len(results)} citations:")
    for i, result in enumerate(results):
        citation = result.get('citation', '')
        print(f"  {i+1}. Citation: '{citation}'")
        print(f"     Method: {result.get('method', 'unknown')}")
        print(f"     Verified: {result.get('verified', 'unknown')}")

if __name__ == "__main__":
    test_citation_extraction() 