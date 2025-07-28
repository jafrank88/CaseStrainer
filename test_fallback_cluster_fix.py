#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test canonical date propagation fix for fallback clusters (production scenario).
"""

import sys
import os
sys.path.insert(0, 'src')

from citation_clustering import group_citations_into_clusters

class MockCitation:
    def __init__(self, citation, canonical_name=None, canonical_date=None, start_index=0, verified=False):
        self.citation = citation
        self.canonical_name = canonical_name
        self.canonical_date = canonical_date
        self.start_index = start_index
        self.metadata = {}
        self.parallel_citations = []
        self.extracted_case_name = "Luis v. United States"
        self.extracted_date = "2016"
        self.verified = verified
        self.source = "CourtListener" if verified else "fallback"
        self.confidence = 1.0
        self.url = f"https://example.com/{citation}" if verified else None
        self.court = "" if verified else None
        self.context = f"Context for {citation}"

def test_fallback_cluster_propagation():
    """Test that canonical date propagation works for fallback clusters (like in production)."""
    
    print("Testing canonical date propagation for fallback clusters...")
    print("Simulating the exact production scenario for Luis v. United States")
    print()
    
    # Create mock citations exactly like the production data:
    # - 578 U.S. 5: No canonical data (API failed) - fallback source
    # - 136 S. Ct. 1083: Wrong canonical data (API returned wrong case) - verified but wrong
    # - 194 L. Ed. 2d 256: Correct canonical data - verified and correct
    citations = [
        MockCitation("578 U.S. 5", start_index=3907, verified=False),  # No canonical data
        MockCitation("136 S. Ct. 1083", 
                    canonical_name="Friedrichs v. Cal. Teachers Ass'n",  # Wrong case!
                    canonical_date="2016", 
                    start_index=3923, 
                    verified=True),  # Wrong canonical data
        MockCitation("194 L. Ed. 2d 256", 
                    canonical_name="Luis v. United States",  # Correct case
                    canonical_date="2016", 
                    start_index=3940, 
                    verified=True)  # Correct canonical data
    ]
    
    # Set up parallel citations to ensure they cluster together as fallback cluster
    for citation in citations:
        citation.parallel_citations = [c.citation for c in citations if c != citation]
    
    print("Before clustering (production scenario):")
    for i, citation in enumerate(citations, 1):
        print(f"  Citation {i}: {citation.citation}")
        print(f"    Canonical name: {citation.canonical_name}")
        print(f"    Canonical date: {citation.canonical_date}")
        print(f"    Verified: {citation.verified}")
        print(f"    Source: {citation.source}")
        print()
    
    # Run the clustering function with our fix
    print("Running clustering with canonical date propagation fix...")
    clusters = group_citations_into_clusters(citations)
    
    print("\nAfter clustering and propagation:")
    for i, citation in enumerate(citations, 1):
        print(f"  Citation {i}: {citation.citation}")
        print(f"    Canonical name: {citation.canonical_name}")
        print(f"    Canonical date: {citation.canonical_date}")
        print(f"    Verified: {citation.verified}")
        print(f"    Source: {citation.source}")
        
        # Check if data was propagated
        if hasattr(citation, 'metadata') and citation.metadata:
            if 'canonical_date_propagated_from' in citation.metadata:
                print(f"    -> Date propagated from: {citation.metadata['canonical_date_propagated_from']}")
            if 'canonical_name_propagated_from' in citation.metadata:
                print(f"    -> Name propagated from: {citation.metadata['canonical_name_propagated_from']}")
            if 'cluster_id' in citation.metadata:
                print(f"    -> Cluster ID: {citation.metadata['cluster_id']}")
        print()
    
    # Test the specific fix: 578 U.S. 5 should now have canonical_date = "2016"
    us_citation = citations[0]  # 578 U.S. 5
    
    print("="*70)
    print("PRODUCTION FIX VERIFICATION:")
    print(f"578 U.S. 5 canonical_date: {us_citation.canonical_date}")
    print(f"578 U.S. 5 canonical_name: {us_citation.canonical_name}")
    
    success = True
    
    if us_citation.canonical_date == "2016":
        print("✅ SUCCESS: Canonical date correctly propagated to 578 U.S. 5!")
    else:
        print("❌ FAILED: Canonical date was not propagated to 578 U.S. 5")
        success = False
    
    if us_citation.canonical_name == "Luis v. United States":
        print("✅ SUCCESS: Canonical name correctly propagated to 578 U.S. 5!")
    else:
        print("❌ FAILED: Canonical name was not propagated to 578 U.S. 5")
        success = False
    
    # Check that the wrong canonical data in 136 S. Ct. 1083 gets corrected
    sct_citation = citations[1]  # 136 S. Ct. 1083
    print(f"\n136 S. Ct. 1083 canonical_name: {sct_citation.canonical_name}")
    
    if sct_citation.canonical_name == "Luis v. United States":
        print("✅ SUCCESS: Wrong canonical name corrected for 136 S. Ct. 1083!")
    else:
        print("❌ PARTIAL: 136 S. Ct. 1083 still has wrong canonical name")
        # This might be expected behavior - we may not want to override verified data
    
    # Check propagation metadata
    if hasattr(us_citation, 'metadata') and us_citation.metadata:
        if 'canonical_date_propagated_from' in us_citation.metadata:
            print(f"✅ Propagation source tracked: {us_citation.metadata['canonical_date_propagated_from']}")
    
    return success

if __name__ == '__main__':
    success = test_fallback_cluster_propagation()
    if success:
        print("\n🎉 OVERALL: Fallback cluster canonical date propagation fix is working!")
    else:
        print("\n❌ OVERALL: Fallback cluster canonical date propagation fix needs more work")
