#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Luis v. United States canonical date propagation with verification enabled.
"""

import sys
import os
sys.path.insert(0, 'src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_luis_with_verification():
    """Test canonical date propagation with verification enabled."""
    
    # Create processor with verification enabled
    config = ProcessingConfig(
        enable_verification=True,
        debug_mode=False
    )
    processor = UnifiedCitationProcessorV2(config)
    
    # Test text with Luis citations
    test_text = "Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)"
    
    print("Testing Luis v. United States with verification enabled...")
    print(f"Test text: {test_text}")
    print()
    
    # Process the text
    results = processor.process_text(test_text)
    citations = results['citations']
    clusters = results.get('clusters', [])
    
    print(f"Found {len(citations)} citations")
    print(f"Found {len(clusters)} clusters")
    print()
    
    # Show all citations
    for i, citation in enumerate(citations, 1):
        print(f"Citation {i}: {citation.citation}")
        print(f"  Case name: {getattr(citation, 'extracted_case_name', 'None')}")
        print(f"  Date: {getattr(citation, 'extracted_date', 'None')}")
        print(f"  Canonical name: {getattr(citation, 'canonical_name', 'None')}")
        print(f"  Canonical date: {getattr(citation, 'canonical_date', 'None')}")
        print(f"  Verified: {getattr(citation, 'verified', False)}")
        print(f"  Source: {getattr(citation, 'source', 'None')}")
        
        # Check metadata for propagation tracking
        metadata = getattr(citation, 'metadata', {}) or {}
        if 'canonical_date_propagated_from' in metadata:
            print(f"  -> Date propagated from: {metadata['canonical_date_propagated_from']}")
        if 'canonical_name_propagated_from' in metadata:
            print(f"  -> Name propagated from: {metadata['canonical_name_propagated_from']}")
        print()
    
    # Focus on the 578 U.S. 5 citation
    us_citation = None
    led_citation = None
    
    for citation in citations:
        if citation.citation == '578 U.S. 5':
            us_citation = citation
        elif citation.citation == '194 L. Ed. 2d 256':
            led_citation = citation
    
    print("="*60)
    print("ANALYSIS:")
    
    if led_citation:
        print(f"194 L. Ed. 2d 256 canonical_date: {getattr(led_citation, 'canonical_date', 'None')}")
        print(f"194 L. Ed. 2d 256 canonical_name: {getattr(led_citation, 'canonical_name', 'None')}")
        print(f"194 L. Ed. 2d 256 verified: {getattr(led_citation, 'verified', False)}")
    
    if us_citation:
        print(f"578 U.S. 5 canonical_date: {getattr(us_citation, 'canonical_date', 'None')}")
        print(f"578 U.S. 5 canonical_name: {getattr(us_citation, 'canonical_name', 'None')}")
        print(f"578 U.S. 5 verified: {getattr(us_citation, 'verified', False)}")
        
        # Check if propagation worked
        canonical_date = getattr(us_citation, 'canonical_date', None)
        if canonical_date == "2016":
            print("SUCCESS: Canonical date correctly propagated to 578 U.S. 5!")
        elif canonical_date:
            print(f"PARTIAL: 578 U.S. 5 has canonical_date '{canonical_date}' but expected '2016'")
        else:
            print("FAILED: 578 U.S. 5 still has no canonical_date")
    else:
        print("ERROR: 578 U.S. 5 not found")

if __name__ == '__main__':
    test_luis_with_verification()
