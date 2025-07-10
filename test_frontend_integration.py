#!/usr/bin/env python3
"""
Test script to verify frontend integration with the fixed verification logic.
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
import json

def test_frontend_format():
    """Test that the processor returns the correct format for the frontend."""
    
    # Sample text with citations
    text = """
    Certified questions are questions of law we review de novo. RCW 2.60.020; 
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). 
    Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 
    171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. 
    Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    """
    
    processor = UnifiedCitationProcessorV2()
    
    print("Processing text with citations...")
    print("=" * 60)
    
    # Process the text
    result = processor.process_text(text)
    
    print(f"Processing completed in {result.get('metadata', {}).get('processing_time', 0):.2f} seconds")
    print(f"Found {len(result.get('results', []))} citations")
    print(f"Verified: {sum(1 for c in result.get('results', []) if c.get('verified') == 'true')}")
    print()
    
    # Display results in frontend format
    print("CITATIONS:")
    print("-" * 60)
    
    for i, citation in enumerate(result.get('results', []), 1):
        print(f"{i}. Citation: {citation.get('citation', 'N/A')}")
        print(f"   Case name: {citation.get('case_name', 'N/A')}")
        print(f"   Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
        print(f"   Extracted date: {citation.get('extracted_date', 'N/A')}")
        print(f"   Canonical name: {citation.get('canonical_name', 'N/A')}")
        print(f"   Canonical date: {citation.get('canonical_date', 'N/A')}")
        print(f"   Verified: {citation.get('verified', 'N/A')}")
        print(f"   URL: {citation.get('url', 'N/A')}")
        print(f"   Source: {citation.get('source', 'N/A')}")
        
        # Check if this would be displayed as green (verified) or yellow (unverified)
        if citation.get('verified') == 'true' and citation.get('url'):
            print(f"   Frontend display: GREEN (verified with canonical URL)")
        elif citation.get('verified') == 'true':
            print(f"   Frontend display: YELLOW (verified but no URL)")
        else:
            print(f"   Frontend display: DEFAULT (unverified)")
        print()
    
    # Display case names
    print("CASE NAMES:")
    print("-" * 60)
    for case_name in result.get('case_names', []):
        print(f"- {case_name}")
    
    print()
    print("SUMMARY:")
    print("-" * 60)
    summary = result.get('summary', {})
    print(f"Total citations: {summary.get('total_citations', 0)}")
    print(f"Verified citations: {summary.get('verified_citations', 0)}")
    print(f"Unverified citations: {summary.get('unverified_citations', 0)}")
    print(f"Unique cases: {summary.get('unique_cases', 0)}")
    
    return result

if __name__ == "__main__":
    result = test_frontend_format() 