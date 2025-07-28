#!/usr/bin/env python3
"""
Test script to verify the Luis v. United States canonical date propagation fix.
"""

import sys
import os
sys.path.insert(0, 'src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
import json

def test_luis_date_propagation():
    """Test that canonical date is properly propagated from last citation to first citation in cluster."""
    
    # Create processor with verification enabled
    config = ProcessingConfig(
        enable_verification=True,
        debug_mode=True
    )
    processor = UnifiedCitationProcessorV2(config)
    
    # Test text containing the Luis v. United States citation sequence
    test_text = """
    L. Ed. 2d 799 (1963); Luis v. United States, 578 U.S. 5, 11, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)
    """
    
    print("Testing Luis v. United States canonical date propagation...")
    print(f"Test text: {test_text.strip()}")
    print("\n" + "="*80)
    
    # Process the text
    results = processor.process_text(test_text)
    citations = results['citations']
    
    print(f"Found {len(citations)} citations:")
    
    # Find the Luis v. United States citations
    luis_citations = []
    for citation in citations:
        if 'Luis' in str(citation.extracted_case_name or '') or citation.citation in ['578 U.S. 5', '136 S. Ct. 1083', '194 L. Ed. 2d 256']:
            luis_citations.append(citation)
    
    print(f"\nLuis v. United States citations found: {len(luis_citations)}")
    
    for i, citation in enumerate(luis_citations, 1):
        print(f"\nCitation {i}: {citation.citation}")
        print(f"  Extracted case name: {citation.extracted_case_name}")
        print(f"  Canonical name: {citation.canonical_name}")
        print(f"  Canonical date: {citation.canonical_date}")
        print(f"  Verified: {citation.verified}")
        print(f"  Source: {citation.source}")
        print(f"  Cluster ID: {citation.metadata.get('cluster_id') if citation.metadata else 'None'}")
        
        # Check if canonical data was propagated
        if citation.metadata:
            if 'canonical_date_propagated_from' in citation.metadata:
                print(f"  ✅ Canonical date propagated from: {citation.metadata['canonical_date_propagated_from']}")
            if 'canonical_name_propagated_from' in citation.metadata:
                print(f"  ✅ Canonical name propagated from: {citation.metadata['canonical_name_propagated_from']}")
    
    # Test the specific issue: 578 U.S. 5 should have canonical_date = "2016"
    us_citation = None
    for citation in luis_citations:
        if citation.citation == '578 U.S. 5':
            us_citation = citation
            break
    
    print(f"\n" + "="*80)
    print("SPECIFIC TEST: 578 U.S. 5 canonical date propagation")
    
    if us_citation:
        print(f"Citation: {us_citation.citation}")
        print(f"Canonical date: {us_citation.canonical_date}")
        print(f"Expected: 2016")
        
        if us_citation.canonical_date == "2016":
            print("✅ SUCCESS: Canonical date correctly propagated!")
        elif us_citation.canonical_date:
            print(f"❌ PARTIAL: Canonical date is '{us_citation.canonical_date}' but expected '2016'")
        else:
            print("❌ FAILED: Canonical date is still null")
            
        # Check canonical name as well
        print(f"Canonical name: {us_citation.canonical_name}")
        if us_citation.canonical_name == "Luis v. United States":
            print("✅ SUCCESS: Canonical name correctly propagated!")
        elif us_citation.canonical_name:
            print(f"❌ PARTIAL: Canonical name is '{us_citation.canonical_name}' but expected 'Luis v. United States'")
        else:
            print("❌ FAILED: Canonical name is still null")
    else:
        print("❌ ERROR: Could not find 578 U.S. 5 citation in results")
    
    return luis_citations

if __name__ == '__main__':
    test_luis_date_propagation()
