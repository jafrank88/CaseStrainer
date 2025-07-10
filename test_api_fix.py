#!/usr/bin/env python3
"""
Test script to verify that the API fix works with the test paragraph.
"""

from src.api.services.citation_service import CitationService

def test_api_fix():
    """Test that the API can now extract citations from the test paragraph."""
    
    # Test paragraph from memory
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("Testing API fix with test paragraph:")
    print("=" * 60)
    print(f"Text length: {len(test_text)} characters")
    print("=" * 60)
    
    # Create service and process
    service = CitationService()
    result = service.process_immediately({'text': test_text})
    
    print(f"Status: {result['status']}")
    print(f"Citations found: {len(result['citations'])}")
    print(f"Statistics: {result['statistics']}")
    
    if result['citations']:
        print("\nCitations extracted:")
        for i, citation in enumerate(result['citations'][:5], 1):
            print(f"\n{i}. Citation: {citation['citation']}")
            print(f"   Case Name: {citation['extracted_case_name']}")
            print(f"   Date: {citation['extracted_date']}")
            print(f"   Verified: {citation['verified']}")
            print(f"   Method: {citation['method']}")
            if citation['verified']:
                print(f"   Canonical Name: {citation['canonical_name']}")
                print(f"   Canonical Date: {citation['canonical_date']}")
                print(f"   URL: {citation['url']}")
    else:
        print("\nNo citations found!")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_api_fix() 