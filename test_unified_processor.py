#!/usr/bin/env python3
"""
Test script for the unified citation processor.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor import unified_processor

def test_unified_processor():
    """Test the unified citation processor with complex citations."""
    
    # Test paragraph with complex citations
    test_paragraph = """Zink filed her first appeal after the trial court granted summary judgment to 
the Does. While the appeal was pending, this court decided John Doe A v. 
Washington State Patrol, which rejected a PRA exemption claim for sex offender 
registration records that was materially identical to one of the Does' claims in this 
case. 185 Wn.2d 363, 374 P.3d 63 (2016). Thus, following John Doe A, the Court 
of Appeals here reversed in part and held "that the registration records must be 
released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 
(2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. 
App. Oct. 2, 2018) (Doe II) (unpublished),"""
    
    print("=== TESTING UNIFIED CITATION PROCESSOR ===")
    print(f"Input text length: {len(test_paragraph)} characters")
    print()
    
    # Process the text
    print("Processing text...")
    results = unified_processor.process_text(test_paragraph)
    
    # Display results
    print("\n=== RESULTS ===")
    
    # Statistics
    stats = results.get('statistics', {})
    summary = results.get('summary', {})
    
    print(f"Total citations: {summary.get('total_citations', 0)}")
    print(f"Parallel citations: {summary.get('parallel_citations', 0)}")
    print(f"Verified citations: {summary.get('verified_citations', 0)}")
    print(f"Unverified citations: {summary.get('unverified_citations', 0)}")
    print(f"Unique cases: {summary.get('unique_cases', 0)}")
    
    # Individual citations
    citations = results.get('results', [])
    print(f"\nFound {len(citations)} citations:")
    
    for i, citation in enumerate(citations, 1):
        print(f"\n{i}. {citation.get('citation', 'Unknown')}")
        print(f"   Case name: {citation.get('case_name', 'Unknown')}")
        print(f"   Verified: {citation.get('verified', False)}")
        print(f"   Is complex: {citation.get('is_complex_citation', False)}")
        print(f"   Is parallel: {citation.get('is_parallel_citation', False)}")
        print(f"   Source: {citation.get('source', 'Unknown')}")
        print(f"   URL: {citation.get('url', 'None')}")
        
        # Show complex features
        complex_features = citation.get('complex_features', {})
        if complex_features:
            print(f"   Complex features:")
            for feature, value in complex_features.items():
                if value:
                    print(f"     - {feature}: {value}")
        
        # Show parallel info
        parallel_info = citation.get('parallel_info', {})
        if parallel_info:
            print(f"   Parallel info:")
            for key, value in parallel_info.items():
                print(f"     - {key}: {value}")
    
    # Metadata
    metadata = results.get('metadata', {})
    print(f"\n=== METADATA ===")
    print(f"Processing time: {metadata.get('processing_time', 0):.3f} seconds")
    print(f"Text length: {metadata.get('text_length', 0)} characters")
    
    if 'error' in results:
        print(f"Error: {results['error']}")
    
    return results

if __name__ == "__main__":
    test_unified_processor() 