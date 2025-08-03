#!/usr/bin/env python3
"""
Test the improved CaseStrainer pipeline with integrated fallback verification
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_improved_pipeline():
    """Test the improved pipeline with the problematic citations we identified."""
    
    # Create processor with verification enabled
    config = ProcessingConfig(
        enable_verification=True,
        debug_mode=True
    )
    processor = UnifiedCitationProcessorV2(config)
    
    # Test text containing the problematic citations
    test_text = """
    In Davis v. Alaska, 385 U.S. 493 (1967), the Supreme Court held that...
    See also Garrity v. New Jersey, 17 L. Ed. 2d 562 (1967).
    This case was also reported at 87 S. Ct. 616.
    """
    
    print("Testing improved CaseStrainer pipeline...")
    print("=" * 60)
    print(f"Test text: {test_text.strip()}")
    print("=" * 60)
    
    # Process the text
    results = processor.process_text(test_text)
    
    print(f"\nResults:")
    print(f"Found {len(results['citations'])} citations")
    print(f"Created {len(results['clusters'])} clusters")
    print()
    
    # Examine each citation
    for i, citation in enumerate(results['citations'], 1):
        print(f"Citation #{i}: {citation.citation}")
        print(f"  Extracted case name: {citation.extracted_case_name}")
        print(f"  Extracted date: {citation.extracted_date}")
        print(f"  Verified: {citation.verified}")
        print(f"  Canonical name: {citation.canonical_name}")
        print(f"  Canonical date: {citation.canonical_date}")
        print(f"  Source: {citation.source}")
        print(f"  URL: {citation.url}")
        if hasattr(citation, 'metadata') and citation.metadata:
            print(f"  Metadata: {citation.metadata}")
        print()
    
    # Check if the problematic citations are now verified
    problematic_citations = ['385 U.S. 493', '17 L. Ed. 2d 562', '87 S. Ct. 616']
    verified_count = 0
    
    for citation in results['citations']:
        if any(prob in citation.citation for prob in problematic_citations):
            if citation.verified:
                verified_count += 1
                print(f"✅ SUCCESS: {citation.citation} is now verified!")
                print(f"   Canonical name: {citation.canonical_name}")
                print(f"   Source: {citation.source}")
            else:
                print(f"❌ STILL UNVERIFIED: {citation.citation}")
    
    print(f"\nSummary: {verified_count}/{len(problematic_citations)} problematic citations are now verified")
    
    return results

if __name__ == "__main__":
    test_improved_pipeline()
