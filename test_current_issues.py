#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to reproduce and debug the current canonical name/date issues.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
from models import CitationResult

def test_current_issues():
    """Test the current issues with canonical names and dates."""
    
    print("Testing Current Canonical Name/Date Issues")
    print("=" * 60)
    
    # Test text containing the problematic citations
    test_text = """
    Luis v. United States, 578 U.S. 5, 11, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016).
    Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020).
    """
    
    # Initialize processor
    processor = UnifiedCitationProcessorV2()
    
    # Process citations
    print("Processing test text...")
    result = processor.process_text(test_text)
    
    # Extract citations from result
    if isinstance(result, dict) and 'citations' in result:
        citations = result['citations']
    else:
        citations = result
    
    print(f"\nFound {len(citations)} citations")
    
    # Analyze the Luis v. United States cluster
    print("\n" + "="*50)
    print("LUIS V. UNITED STATES CLUSTER ANALYSIS")
    print("="*50)
    
    luis_citations = [c for c in citations if 'luis' in c.citation.lower() or 'united states' in c.citation.lower() or '578 u.s.' in c.citation.lower() or '136 s. ct.' in c.citation.lower() or '194 l. ed.' in c.citation.lower()]
    
    for citation in luis_citations:
        print(f"\nCitation: {citation.citation}")
        print(f"  Extracted case name: {citation.extracted_case_name}")
        print(f"  Canonical name: {citation.canonical_name}")
        print(f"  Canonical date: {citation.canonical_date}")
        print(f"  Source: {citation.source}")
        print(f"  Verified: {citation.verified}")
        if hasattr(citation, 'metadata') and citation.metadata:
            print(f"  Metadata: {citation.metadata}")
    
    # Analyze the Davison v. State cluster
    print("\n" + "="*50)
    print("DAVISON V. STATE CLUSTER ANALYSIS")
    print("="*50)
    
    davison_citations = [c for c in citations if 'davison' in c.citation.lower() or '196 wn.2d' in c.citation.lower() or '466 p.3d 231' in c.citation.lower()]
    
    for citation in davison_citations:
        print(f"\nCitation: {citation.citation}")
        print(f"  Extracted case name: {citation.extracted_case_name}")
        print(f"  Canonical name: {citation.canonical_name}")
        print(f"  Canonical date: {citation.canonical_date}")
        print(f"  Source: {citation.source}")
        print(f"  Verified: {citation.verified}")
        if hasattr(citation, 'metadata') and citation.metadata:
            print(f"  Metadata: {citation.metadata}")
    
    # Check for specific issues
    print("\n" + "="*50)
    print("ISSUE ANALYSIS")
    print("="*50)
    
    # Issue 1: Luis v. United States name similarity matching
    s_ct_citation = next((c for c in luis_citations if '136 s. ct.' in c.citation.lower()), None)
    if s_ct_citation:
        if s_ct_citation.canonical_name == "Friedrichs v. Cal. Teachers Ass'n":
            print("❌ ISSUE 1: Name similarity matching not working")
            print(f"   136 S. Ct. 1083 shows canonical_name: '{s_ct_citation.canonical_name}'")
            print(f"   Should be: 'Luis v. United States'")
        elif s_ct_citation.canonical_name == "Luis v. United States":
            print("✅ ISSUE 1: Name similarity matching working correctly")
        else:
            print(f"? ISSUE 1: Unexpected canonical_name: '{s_ct_citation.canonical_name}'")
    
    # Issue 2: Null canonical data in fallback clusters
    null_canonical_citations = [c for c in citations if c.canonical_name is None or c.canonical_date is None]
    if null_canonical_citations:
        print(f"\n❌ ISSUE 2: Found {len(null_canonical_citations)} citations with null canonical data:")
        for citation in null_canonical_citations:
            print(f"   {citation.citation}: canonical_name={citation.canonical_name}, canonical_date={citation.canonical_date}")
    else:
        print("\n✅ ISSUE 2: No citations with null canonical data found")
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_current_issues()
