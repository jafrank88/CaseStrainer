#!/usr/bin/env python3
"""
Test script to verify that citation grouping optimizes verification.
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig, extract_citations_unified

def test_grouping_verification():
    """Test that citation grouping optimizes verification."""
    
    # Create a test document with multiple citation variants
    test_text = """
    The court in State v. Smith, 146 Wash.2d 1, 43 P.3d 4 (2001) held that...
    This was further clarified in State v. Smith, 146 Wn.2d 1, 43 P.3d 4 (2001)...
    The Washington Supreme Court in State v. Smith, 146 Wash.2d 1 (2001)...
    Additionally, in State v. Smith, 43 P.3d 4 (2001)...
    """
    
    config = ProcessingConfig(
        enable_verification=True,
        debug_mode=True
    )
    
    print("Testing citation grouping verification optimization:")
    print("=" * 60)
    print(f"Input text: {test_text.strip()}")
    print("=" * 60)
    
    # Process the document
    result = extract_citations_unified(test_text, config)
    
    print(f"\nExtracted {len(result)} citations:")
    for i, citation in enumerate(result, 1):
        print(f"\n{i}. Citation: {citation.citation}")
        print(f"   Case Name: {citation.extracted_case_name}")
        print(f"   Date: {citation.extracted_date}")
        print(f"   Verified: {citation.verified}")
        if citation.verified:
            print(f"   Canonical Name: {citation.canonical_name}")
            print(f"   Canonical Date: {citation.canonical_date}")
            print(f"   URL: {citation.url}")
    
    # Check if citations were grouped properly
    print(f"\n" + "=" * 60)
    print("Verification Analysis:")
    
    # Count unique base citations
    processor = UnifiedCitationProcessorV2(config)
    base_citations = set()
    for citation in result:
        base = processor._get_base_citation(citation.citation)
        base_citations.add(base)
    
    print(f"Unique base citations: {len(base_citations)}")
    print(f"Total citations: {len(result)}")
    print(f"Optimization ratio: {len(result)}/{len(base_citations)} = {len(result)/len(base_citations):.1f}x")
    
    if len(base_citations) < len(result):
        print("✓ Citations were grouped for efficient verification!")
    else:
        print("✗ No grouping optimization detected.")

if __name__ == "__main__":
    test_grouping_verification() 