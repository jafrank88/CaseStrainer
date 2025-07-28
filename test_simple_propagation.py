#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for canonical data propagation function.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_simple_propagation():
    """Test the canonical data propagation function directly."""
    
    print("Testing Canonical Data Propagation")
    print("=" * 40)
    
    try:
        from citation_clustering import propagate_canonical_date_within_clusters
        from models import CitationResult
        
        # Create test citations with cluster metadata
        citations = [
            CitationResult(
                citation="196 Wn. 2d 285",
                extracted_case_name="Davison v. State",
                extracted_date="2020",
                canonical_name=None,
                canonical_date=None,
                verified=False,
                metadata={'cluster_id': 'test_cluster_1'}
            ),
            CitationResult(
                citation="466 P.3d 231", 
                extracted_case_name="Davison v. State",
                extracted_date="2020",
                canonical_name="Davison v. State",
                canonical_date="2020",
                verified=True,
                metadata={'cluster_id': 'test_cluster_1'}
            )
        ]
        
        print("Before propagation:")
        for i, citation in enumerate(citations):
            print(f"  Citation {i+1}: {citation.citation}")
            print(f"    canonical_name: {citation.canonical_name}")
            print(f"    canonical_date: {citation.canonical_date}")
        
        # Test the propagation function
        print("\nRunning propagation...")
        propagate_canonical_date_within_clusters(citations)
        
        print("\nAfter propagation:")
        for i, citation in enumerate(citations):
            print(f"  Citation {i+1}: {citation.citation}")
            print(f"    canonical_name: {citation.canonical_name}")
            print(f"    canonical_date: {citation.canonical_date}")
        
        # Check results
        first_citation = citations[0]
        if first_citation.canonical_name == "Davison v. State" and first_citation.canonical_date == "2020":
            print("\n✅ Canonical data propagation is working correctly!")
            return True
        else:
            print(f"\n❌ Propagation failed. First citation has:")
            print(f"   canonical_name: {first_citation.canonical_name}")
            print(f"   canonical_date: {first_citation.canonical_date}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_simple_propagation()
    if success:
        print("\n🎉 Canonical data propagation is working!")
    else:
        print("\n❌ Canonical data propagation needs more work.")
