#!/usr/bin/env python3
"""
Debug script to test citation extraction.
"""

# DEPRECATED: # DEPRECATED: from src.citation_extractor import CitationExtractor

def test_citation_extraction():
    """Test citation extraction with a simple example."""
    print("Testing citation extraction...")
    
    # Test with a simple citation
    test_text = "See State v. Richardson, 177 Wn.2d 351, 302 P.3d 156 (2013)."
    
    extractor = CitationExtractor(use_eyecite=False, use_regex=True)
    results = extractor.extract(test_text)
    
    print(f"Found {len(results)} citations:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. Citation: '{result.get('citation')}'")
        print(f"     Method: {result.get('method')}")
        print(f"     Pattern: {result.get('pattern')}")
        print(f"     Case name: {result.get('case_name')}")
        print()

if __name__ == "__main__":
    test_citation_extraction() 