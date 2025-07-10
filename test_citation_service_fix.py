#!/usr/bin/env python3
"""
Test script to verify that the citation service correctly marks citations as verified when they have canonical data.
"""

import json
from src.api.services.citation_service import CitationService

def test_citation_service_verification():
    """Test that citations with canonical data are marked as verified."""
    
    service = CitationService()
    
    # Test text with citations that should be verified
    test_text = """A federal court may ask this court to answer a question of Washington law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("Testing citation service verification logic:")
    print("=" * 60)
    print(f"Test text: {test_text[:100]}...")
    print("=" * 60)
    
    # Process the text
    result = service.process_immediately({
        'type': 'text',
        'text': test_text
    })
    
    print(f"Processing result: {result['status']}")
    print(f"Total citations: {len(result.get('citations', []))}")
    
    # Check each citation
    for i, citation in enumerate(result.get('citations', []), 1):
        print(f"\n{i}. Citation: {citation.get('citation', 'N/A')}")
        print(f"   Verified: {citation.get('verified', 'N/A')}")
        print(f"   Source: {citation.get('source', 'N/A')}")
        print(f"   Canonical name: {citation.get('canonical_name', 'N/A')}")
        print(f"   Canonical date: {citation.get('canonical_date', 'N/A')}")
        print(f"   URL: {citation.get('url', 'N/A')}")
        
        # Check if verification logic is correct
        has_canonical_data = (
            citation.get('canonical_name') and citation.get('canonical_name') != 'N/A' or
            citation.get('canonical_date') and citation.get('canonical_date') != 'N/A' or
            citation.get('url')
        )
        
        if has_canonical_data:
            if citation.get('verified') == 'true':
                print(f"   ✅ Correctly marked as verified")
            else:
                print(f"   ❌ Should be verified but marked as {citation.get('verified')}")
        else:
            if citation.get('verified') == 'false':
                print(f"   ✅ Correctly marked as unverified")
            else:
                print(f"   ❌ Should be unverified but marked as {citation.get('verified')}")
    
    # Check statistics
    stats = result.get('statistics', {})
    print(f"\nStatistics:")
    print(f"  Total citations: {stats.get('total_citations', 0)}")
    print(f"  Verified citations: {stats.get('verified_citations', 0)}")
    print(f"  Unverified citations: {stats.get('unverified_citations', 0)}")
    
    return result

if __name__ == "__main__":
    test_citation_service_verification() 