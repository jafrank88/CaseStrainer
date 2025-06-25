#!/usr/bin/env python3
"""
Test script to verify Washington citations from the PDF.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import json

def test_wa_citations():
    """Test the Washington citations from the PDF."""
    
    verifier = EnhancedMultiSourceVerifier()
    
    # The citations from the PDF
    test_citations = [
        "199 Wn.2d 282",
        "505 P.3d 529", 
        "192 Wn.2d 350",
        "214 P. 146",
        "197 Wn.2d 170",
        "481 P.3d 521",
    ]
    
    print("=" * 80)
    print("WASHINGTON CITATIONS VERIFICATION TEST")
    print("=" * 80)
    
    for citation in test_citations:
        print(f"\nTesting citation: {citation}")
        print("-" * 50)
        
        # Test normalization
        normalized = verifier._normalize_citation(citation)
        print(f"Normalized: {normalized}")
        
        # Test component extraction
        components = verifier._extract_citation_components(citation)
        print(f"Components: {json.dumps(components, indent=2)}")
        
        # Test full verification
        print("Running full verification...")
        result = verifier._verify_with_api(citation)
        
        if result.get("verified", False):
            print(f"✅ VERIFIED by: {', '.join(result.get('sources', []))}")
            print(f"Case name: {result.get('case_name', 'Unknown')}")
        else:
            print("❌ NOT VERIFIED")
            # Show detailed results from each source
            for source_name, source_result in result.get('results', []):
                status = "✅" if source_result.get("verified", False) else "❌"
                error = source_result.get("error", "")
                print(f"  {status} {source_name}: {error}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_wa_citations() 