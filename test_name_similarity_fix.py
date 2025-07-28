#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify that name similarity matching is working with individual verification.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_name_similarity_fix():
    """Test that name similarity matching works with individual verification."""
    
    print("Testing Name Similarity Matching Fix")
    print("=" * 50)
    
    # Test text with Luis v. United States citations
    test_text = "Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)."
    
    # Initialize processor
    processor = UnifiedCitationProcessorV2()
    
    print("Processing Luis v. United States citations...")
    print(f"Text: {test_text}")
    print()
    
    # Process citations
    result = processor.process_text(test_text)
    
    # Extract citations from result
    if isinstance(result, dict) and 'citations' in result:
        citations = result['citations']
    else:
        citations = result
    
    print(f"Found {len(citations)} citations")
    print()
    
    # Analyze each citation
    for i, citation in enumerate(citations):
        print(f"Citation {i+1}: {citation.citation}")
        print(f"  Extracted case name: {citation.extracted_case_name}")
        print(f"  Canonical name: {citation.canonical_name}")
        print(f"  Canonical date: {citation.canonical_date}")
        print(f"  Source: {citation.source}")
        print(f"  Verified: {citation.verified}")
        print()
    
    # Check for the specific Luis v. United States issue
    s_ct_citation = next((c for c in citations if '136 s. ct.' in c.citation.lower()), None)
    if s_ct_citation:
        print("=" * 50)
        print("LUIS V. UNITED STATES ISSUE CHECK")
        print("=" * 50)
        
        print(f"136 S. Ct. 1083 citation:")
        print(f"  Extracted case name: {s_ct_citation.extracted_case_name}")
        print(f"  Canonical name: {s_ct_citation.canonical_name}")
        
        if s_ct_citation.canonical_name == "Luis v. United States":
            print("✅ SUCCESS: Name similarity matching is working!")
            print("   136 S. Ct. 1083 correctly shows 'Luis v. United States'")
        elif s_ct_citation.canonical_name == "Friedrichs v. Cal. Teachers Ass'n":
            print("❌ ISSUE: Name similarity matching is NOT working")
            print("   136 S. Ct. 1083 still shows 'Friedrichs v. Cal. Teachers Ass'n'")
            print("   Expected: 'Luis v. United States'")
        else:
            print(f"? UNKNOWN: Unexpected canonical name: '{s_ct_citation.canonical_name}'")
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_name_similarity_fix()
