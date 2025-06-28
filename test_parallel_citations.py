#!/usr/bin/env python3
"""
Test script to check if parallel citations are being extracted from CourtListener API.
"""

import sys
import os
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import json

def test_parallel_citations():
    """Test parallel citation extraction."""
    verifier = EnhancedMultiSourceVerifier()
    
    # Test with a well-known case that should have parallel citations
    test_citations = [
        "347 U.S. 483",  # Brown v. Board of Education
        "410 U.S. 113",  # Roe v. Wade
        "384 U.S. 436",  # Miranda v. Arizona
    ]
    
    for citation in test_citations:
        print(f"\n{'='*60}")
        print(f"Testing citation: {citation}")
        print(f"{'='*60}")
        
        try:
            # Use the lookup method that should extract parallel citations
            result = verifier._lookup_citation(citation)
            
            if result:
                print(f"✓ Found result for {citation}")
                print(f"Case name: {result.get('case_name', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
                print(f"Date filed: {result.get('date_filed', 'N/A')}")
                
                # Check for parallel citations
                parallel_citations = result.get('parallel_citations', [])
                print(f"Parallel citations found: {len(parallel_citations)}")
                
                if parallel_citations:
                    print("Parallel citations:")
                    for i, pc in enumerate(parallel_citations, 1):
                        if isinstance(pc, dict):
                            print(f"  {i}. Citation: {pc.get('citation', 'N/A')}")
                            print(f"     Reporter: {pc.get('reporter', 'N/A')}")
                            print(f"     Category: {pc.get('category', 'N/A')}")
                            print(f"     URL: {pc.get('url', 'N/A')}")
                        else:
                            print(f"  {i}. {pc}")
                else:
                    print("No parallel citations found")
                    
                # Also check if there are citations in the raw result
                print(f"\nRaw result keys: {list(result.keys())}")
                if 'citations' in result:
                    print(f"Citations field: {result['citations']}")
                    
            else:
                print(f"✗ No result found for {citation}")
                
        except Exception as e:
            print(f"✗ Error testing {citation}: {e}")

if __name__ == "__main__":
    test_parallel_citations() 