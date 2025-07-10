#!/usr/bin/env python3
"""
Debug script to test citation merging.
"""

# DEPRECATED: # DEPRECATED: from src.citation_extractor import CitationExtractor
from src.document_processing import extract_and_verify_citations

def test_citation_merging():
    """Test citation merging with a simple example."""
    print("Testing citation merging...")
    
    # Test with a simple citation
    test_text = "See State v. Richardson, 177 Wn.2d 351, 302 P.3d 156 (2013)."
    
    # First, test the citation extractor
    extractor = CitationExtractor(use_eyecite=False, use_regex=True)
    extraction_results = extractor.extract(test_text)
    
    print(f"Extraction results: {len(extraction_results)} citations")
    for i, result in enumerate(extraction_results, 1):
        print(f"  {i}. Citation: '{result.get('citation')}'")
        print(f"     Method: {result.get('method')}")
        print(f"     Pattern: {result.get('pattern')}")
        print(f"     Case name: {result.get('case_name')}")
        print()
    
    # Now test the full processing pipeline
    print("Testing full processing pipeline...")
    try:
        processed_results, metadata = extract_and_verify_citations(test_text)
        print(f"Processing results: {len(processed_results)} citations")
        for i, result in enumerate(processed_results, 1):
            print(f"  {i}. Citation: '{result.get('citation')}'")
            print(f"     Verified: {result.get('verified')}")
            print(f"     Canonical name: {result.get('canonical_name')}")
            print()
    except Exception as e:
        print(f"Error in processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_citation_merging() 