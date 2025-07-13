#!/usr/bin/env python3

from src.api.services.citation_service import CitationService

def test_core_extraction():
    """Test the updated backend with core case name extraction."""
    
    # Initialize service
    svc = CitationService()
    
    # Test text
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # Process text
    result = svc.process_immediately({'type': 'text', 'text': test_text})
    
    print("✅ Updated backend test with core extraction!")
    print(f"Found {len(result.get('citations', []))} citations")
    print(f"Found {len(result.get('clusters', []))} clusters")
    
    print("\n=== CASE NAMES ===")
    for i, citation in enumerate(result.get('citations', [])[:5]):
        print(f"{i+1}. Citation: {citation.get('citation', 'N/A')}")
        print(f"   Extracted case name: {citation.get('extracted_case_name', 'N/A')}")
        print(f"   Canonical name: {citation.get('canonical_name', 'N/A')}")
        print()
    
    # Check if case names are being extracted properly
    citations_with_names = [c for c in result.get('citations', []) if c.get('extracted_case_name') and c.get('extracted_case_name') != 'N/A']
    print(f"Citations with extracted case names: {len(citations_with_names)}/{len(result.get('citations', []))}")
    
    if citations_with_names:
        print("✅ Core extraction is working!")
    else:
        print("❌ Core extraction may need debugging")

if __name__ == "__main__":
    test_core_extraction() 