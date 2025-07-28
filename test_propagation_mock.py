#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test canonical date propagation with mock data to verify the fix works.
"""

import sys
import os
sys.path.insert(0, 'src')

from citation_clustering import group_citations_into_clusters

class MockCitation:
    def __init__(self, citation, canonical_name=None, canonical_date=None, start_index=0):
        self.citation = citation
        self.canonical_name = canonical_name
        self.canonical_date = canonical_date
        self.start_index = start_index
        self.metadata = {}
        self.parallel_citations = []
        self.extracted_case_name = "Luis v. United States"
        self.extracted_date = "2016"
        self.verified = canonical_name is not None

def test_canonical_date_propagation():
    """Test that canonical date propagation works correctly within clusters."""
    
    print("Testing canonical date propagation with mock data...")
    print()
    
    # Create mock citations simulating the Luis v. United States scenario
    # Only the last citation (194 L. Ed. 2d 256) has canonical data from API
    citations = [
        MockCitation("578 U.S. 5", start_index=100),  # No canonical data (API failed)
        MockCitation("136 S. Ct. 1083", start_index=120),  # No canonical data (wrong case)
        MockCitation("194 L. Ed. 2d 256", 
                    canonical_name="Luis v. United States", 
                    canonical_date="2016", 
                    start_index=140)  # Has canonical data (correct case)
    ]
    
    # Set up parallel citations to ensure they cluster together
    for citation in citations:
        citation.parallel_citations = [c.citation for c in citations if c != citation]
    
    print("Before clustering:")
    for i, citation in enumerate(citations, 1):
        print(f"  Citation {i}: {citation.citation}")
        print(f"    Canonical name: {citation.canonical_name}")
        print(f"    Canonical date: {citation.canonical_date}")
        print(f"    Verified: {citation.verified}")
        print()
    
    # Run the clustering function with our fix
    clusters = group_citations_into_clusters(citations)
    
    print("After clustering and propagation:")
    for i, citation in enumerate(citations, 1):
        print(f"  Citation {i}: {citation.citation}")
        print(f"    Canonical name: {citation.canonical_name}")
        print(f"    Canonical date: {citation.canonical_date}")
        print(f"    Verified: {citation.verified}")
        
        # Check if data was propagated
        if 'canonical_date_propagated_from' in citation.metadata:
            print(f"    -> Date propagated from: {citation.metadata['canonical_date_propagated_from']}")
        if 'canonical_name_propagated_from' in citation.metadata:
            print(f"    -> Name propagated from: {citation.metadata['canonical_name_propagated_from']}")
        print()
    
    # Test the specific fix: 578 U.S. 5 should now have canonical_date = "2016"
    us_citation = citations[0]  # 578 U.S. 5
    
    print("="*60)
    print("VERIFICATION:")
    print(f"578 U.S. 5 canonical_date: {us_citation.canonical_date}")
    print(f"578 U.S. 5 canonical_name: {us_citation.canonical_name}")
    
    if us_citation.canonical_date == "2016":
        print("✅ SUCCESS: Canonical date correctly propagated to 578 U.S. 5!")
        success = True
    else:
        print("❌ FAILED: Canonical date was not propagated")
        success = False
    
    if us_citation.canonical_name == "Luis v. United States":
        print("✅ SUCCESS: Canonical name correctly propagated to 578 U.S. 5!")
    else:
        print("❌ FAILED: Canonical name was not propagated")
        success = False
    
    # Check propagation metadata
    if 'canonical_date_propagated_from' in us_citation.metadata:
        print(f"✅ Propagation source tracked: {us_citation.metadata['canonical_date_propagated_from']}")
    
    return success

if __name__ == '__main__':
    success = test_canonical_date_propagation()
    if success:
        print("\n🎉 OVERALL: Canonical date propagation fix is working correctly!")
    else:
        print("\n❌ OVERALL: Canonical date propagation fix needs more work")
