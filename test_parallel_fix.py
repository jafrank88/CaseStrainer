#!/usr/bin/env python3
"""
Test script to verify parallel citation extraction fix.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from complex_citation_integration import ComplexCitationIntegrator

def test_parallel_citations():
    """Test parallel citation extraction."""
    print("Testing parallel citation extraction...")
    
    # Test text with parallel citations
    test_text = """A trial court's decision granting or denying a motion to seal court records is 
reviewed for abuse of discretion. State v. Richardson, 177 Wn.2d 351, 357, 302 
P.3d 156 (2013)."""
    
    integrator = ComplexCitationIntegrator()
    results = integrator.process_text_with_complex_citations_original(test_text)
    
    print(f"Found {len(results)} citations")
    
    for i, result in enumerate(results, 1):
        print(f"\nCitation {i}:")
        print(f"  Citation: {result.get('citation', 'N/A')}")
        print(f"  Case name: {result.get('case_name', 'N/A')}")
        print(f"  Verified: {result.get('verified', 'N/A')}")
        print(f"  Is complex: {result.get('is_complex_citation', False)}")
        print(f"  Is parallel: {result.get('is_parallel_citation', False)}")
        print(f"  Parallel citations: {result.get('parallel_citations', [])}")
        print(f"  Parallels field: {result.get('parallels', [])}")
        
        # Check if this citation has parallel citations
        if result.get('parallel_citations'):
            print(f"  ✅ Has parallel citations: {result['parallel_citations']}")
        elif result.get('parallels'):
            print(f"  ✅ Has parallels field: {len(result['parallels'])} items")
        else:
            print(f"  ❌ No parallel citations found")

if __name__ == "__main__":
    test_parallel_citations() 