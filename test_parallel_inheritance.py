#!/usr/bin/env python3
"""
Test script to verify parallel citation inheritance logic.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from document_processing import extract_and_verify_citations
# DEPRECATED: # DEPRECATED: from src.citation_extractor import CitationExtractor
import logging

# Set up debug logging
logging.basicConfig(level=logging.INFO)

def test_parallel_inheritance():
    """Test that parallel citations inherit canonical metadata from primary citations."""
    
    # Test with a complex citation that has both primary and parallel citations
    complex_citation = "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    
    print(f"Testing parallel citation inheritance with: {complex_citation}")
    print("=" * 80)
    
    # Test what CitationExtractor finds
    print("\nTesting CitationExtractor:")
    extractor = CitationExtractor(use_eyecite=False, use_regex=True, extract_case_names=True)
    extracted_citations = extractor.extract_citations(complex_citation)
    print(f"CitationExtractor found {len(extracted_citations)} citations:")
    for i, citation in enumerate(extracted_citations, 1):
        print(f"  {i}. {citation.get('citation', 'N/A')}")
    
    try:
        # Process the complex citation
        results, metadata = extract_and_verify_citations(complex_citation)
        
        print(f"\nProcessing completed. Found {len(results)} results.")
        print(f"Metadata: {metadata}")
        
        if results:
            print(f"\nResults:")
            for i, result in enumerate(results, 1):
                print(f"\n--- Result {i} ---")
                print(f"Citation: {result.get('citation', 'N/A')}")
                print(f"Verified: {result.get('verified', 'N/A')}")
                print(f"Case Name: {result.get('case_name', 'N/A')}")
                print(f"Canonical Name: {result.get('canonical_name', 'N/A')}")
                print(f"Canonical Date: {result.get('canonical_date', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
                print(f"Court: {result.get('court', 'N/A')}")
                print(f"Docket: {result.get('docket_number', 'N/A')}")
                print(f"Source: {result.get('source', 'N/A')}")
                print(f"Is Parallel: {result.get('is_parallel_citation', False)}")
                print(f"Primary Citation: {result.get('primary_citation', 'N/A')}")
                print(f"Method: {result.get('method', 'N/A')}")
                print(f"Pattern: {result.get('pattern', 'N/A')}")
                
                # Check if this is a parallel citation that should have inherited data
                if result.get('is_parallel_citation'):
                    print("  ✓ This is a parallel citation")
                    if result.get('verified') == 'true_by_parallel':
                        print("  ✓ Marked as verified by parallel")
                    if result.get('canonical_name') and result.get('canonical_name') != 'N/A':
                        print("  ✓ Has inherited canonical name")
                    if result.get('canonical_date'):
                        print("  ✓ Has inherited canonical date")
                    if result.get('url'):
                        print("  ✓ Has inherited URL")
                    else:
                        print("  ✗ Missing inherited URL")
                else:
                    print("  This is a primary citation")
        else:
            print("No results returned from processing.")
            
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parallel_inheritance() 