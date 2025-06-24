#!/usr/bin/env python3
"""
Test script to verify enhanced citation parsing and new sources.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import json

def test_enhanced_citation_formats():
    """Test various citation formats including international and regional citations."""
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citations with various formats
    test_citations = [
        # Standard US citations
        "219 L.Ed. 2d 420",
        "144 S.Ct. 1785", 
        "515 P.3d 1029",
        "129 S.Ct. 2529",
        
        # Regional reporters
        "123 Cal. App. 4th 456",
        "456 N.Y. App. Div. 789",
        "789 Tex. App. 123",
        "321 Fla. App. 654",
        
        # International citations
        "[2020] UKSC 1",
        "[2019] SCC 1", 
        "[2018] HCA 1",
        "[2017] FCA 1",
        
        # Edge cases
        "123 F.Supp.2d 456",
        "456 A.3d 789",
        "789 S.E.2d 123",
        "321 N.W.2d 654",
    ]
    
    print("=" * 80)
    print("ENHANCED CITATION FORMAT TESTING")
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
        
        # Test full verification with new sources
        print("Running full verification...")
        result = verifier._verify_with_api(citation)
        
        if result.get("verified", False):
            print(f"✅ VERIFIED by: {', '.join(result.get('sources', []))}")
            print(f"Case name: {result.get('case_name', 'Unknown')}")
        else:
            print("❌ NOT VERIFIED")
            print(f"Errors: {[r.get('error', '') for _, r in result.get('results', []) if r.get('error')]}")
        
        print("-" * 50)

def test_new_sources():
    """Test the new sources specifically."""
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test a few citations with the new sources
    test_citations = [
        "219 L.Ed. 2d 420",  # Should be found in multiple sources
        "144 S.Ct. 1785",    # Supreme Court case
        "515 P.3d 1029",     # State court case
    ]
    
    print("\n" + "=" * 80)
    print("NEW SOURCES TESTING")
    print("=" * 80)
    
    for citation in test_citations:
        print(f"\nTesting new sources with: {citation}")
        print("-" * 50)
        
        # Test each new source individually
        new_sources = [
            ("OpenLegal", verifier._try_openlegal),
            ("Supreme Court", verifier._try_supreme_court),
            ("Federal Courts", verifier._try_federal_courts),
            ("State Courts", verifier._try_state_courts),
        ]
        
        for source_name, source_method in new_sources:
            try:
                result = source_method(citation)
                status = "✅ VERIFIED" if result.get("verified", False) else "❌ NOT FOUND"
                print(f"{source_name}: {status}")
                if result.get("error"):
                    print(f"  Error: {result['error']}")
            except Exception as e:
                print(f"{source_name}: ❌ ERROR - {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_enhanced_citation_formats()
    test_new_sources() 