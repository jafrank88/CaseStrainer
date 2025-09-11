#!/usr/bin/env python3
"""
Test why P.3d citations aren't getting case names extracted.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from standalone_citation_parser import CitationParser

def test_p3d_case_extraction():
    """Test case name extraction for P.3d citations."""
    print("🧪 Testing P.3d case name extraction")
    
    parser = CitationParser()
    
    # Test text with our standard parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print(f"Test text: {test_text[:100]}...")
    print()
    
    # Test each P.3d citation
    p3d_citations = [
        '514 P.3d 643',  # Should extract: Convoyant, LLC v. DeepThink, LLC
        '256 P.3d 321',  # Should extract: Carlson v. Glob. Client Sols., LLC
        '43 P.3d 4'      # Should extract: Dep't of Ecology v. Campbell & Gwinn, LLC
    ]
    
    for citation in p3d_citations:
        print(f"--- Testing: {citation} ---")
        result = parser.extract_from_text(test_text, citation)
        
        print(f"Case name: {result.get('case_name')}")
        print(f"Year: {result.get('year')}")
        print(f"Full result: {result}")
        print()
    
    print("✅ Test completed!")

if __name__ == "__main__":
    test_p3d_case_extraction()
