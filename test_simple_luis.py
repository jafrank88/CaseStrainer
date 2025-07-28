#!/usr/bin/env python3
"""
Simple test for Luis v. United States canonical date propagation fix.
"""

import sys
import os
sys.path.insert(0, 'src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_simple_luis():
    """Simple test for canonical date propagation."""
    
    # Create processor with verification disabled for faster testing
    config = ProcessingConfig(
        enable_verification=False,
        debug_mode=False
    )
    processor = UnifiedCitationProcessorV2(config)
    
    # Simple test text with just the Luis citations
    test_text = "Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)"
    
    print("Testing Luis v. United States canonical date propagation...")
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
        
        # Check metadata
        metadata = getattr(citation, 'metadata', {}) or {}
        if 'canonical_date_propagated_from' in metadata:
            print(f"  ✅ Date propagated from: {metadata['canonical_date_propagated_from']}")
        if 'canonical_name_propagated_from' in metadata:
            print(f"  ✅ Name propagated from: {metadata['canonical_name_propagated_from']}")
        print()
    
    # Check if 578 U.S. 5 has canonical_date
    us_citation = None
    for citation in citations:
        if citation.citation == '578 U.S. 5':
            us_citation = citation
            break
    
    print("="*50)
    if us_citation:
        canonical_date = getattr(us_citation, 'canonical_date', None)
        print(f"578 U.S. 5 canonical_date: {canonical_date}")
        if canonical_date:
            print("✅ SUCCESS: Canonical date found!")
        else:
            print("❌ FAILED: No canonical date")
    else:
        print("❌ ERROR: 578 U.S. 5 not found")

if __name__ == '__main__':
    test_simple_luis()
