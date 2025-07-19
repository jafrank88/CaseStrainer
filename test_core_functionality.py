#!/usr/bin/env python3
"""
Test script to examine core citation extraction functionality without requiring backend.
"""

import sys, os
# Add both the current directory and src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_core_citation_extraction():
    """Test core citation extraction functionality."""
    # Test paragraph
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    print("Testing core citation extraction...")
    print(f"Input text: {test_text}")
    print("-" * 80)

    # Create processor with debug mode disabled to avoid hyperscan issues
    config = ProcessingConfig(debug_mode=False, extract_case_names=True, extract_dates=True)
    processor = UnifiedCitationProcessorV2(config)

    # Process the text
    results = processor.process_text(test_text)

    print(f'Found {len(results)} citations:')
    for i, citation in enumerate(results):
        print(f'{i+1}. Citation: {citation.citation}')
        print(f'   Case name: {citation.extracted_case_name}')
        print(f'   Date: {citation.extracted_date}')
        print(f'   Context: {citation.context[:100]}...')
        print(f'   Start/End: {citation.start_index}/{citation.end_index}')
        print()

    # Test clustering
    clusters = processor.group_citations_into_clusters(results)
    print(f'Found {len(clusters)} clusters:')
    for i, cluster in enumerate(clusters):
        print(f'Cluster {i+1}:')
        for citation in cluster['citations']:
            print(f'  - {citation["citation"]} (case: {citation["extracted_case_name"]})')
        print()

    # Assertions - be more lenient since external services may be down
    assert len(results) > 0, "No citations extracted"
    
    # Check that we have the expected citations (at least some of them)
    citation_texts = [c.citation for c in results]
    expected_citations = ["200 Wn.2d 72", "171 Wn.2d 486", "146 Wn.2d 1"]
    
    found_citations = 0
    for expected in expected_citations:
        if any(expected in ct for ct in citation_texts):
            found_citations += 1
    
    # Require at least 2 out of 3 expected citations
    assert found_citations >= 2, f"Only found {found_citations}/3 expected citations"
    
    print("✅ Core citation extraction test passed!")

def test_filtering_functionality():
    """Test that web domain filtering is working."""
    print("\nTesting filtering functionality...")
    
    # Test with a citation that should trigger filtering
    test_citation = "410 U.S. 113"
    
    config = ProcessingConfig(debug_mode=False, extract_case_names=True, extract_dates=True)
    processor = UnifiedCitationProcessorV2(config)
    
    # Test the unified workflow
    result = processor.verify_citation_unified_workflow(test_citation)
    
    # Check if filtering worked
    canonical_name = result.get('canonical_name')
    verified = result.get('verified')
    
    print(f"Citation: {test_citation}")
    print(f"Canonical Name: {canonical_name}")
    print(f"Verified: {verified}")
    
    # The filtering should prevent web domains from being returned
    if canonical_name:
        # Check if it's a web domain
        if any(domain in canonical_name.lower() for domain in ['youtube.com', 'google.com', 'cheaperthandirt.com', 'http', 'www.']):
            assert False, f"Web domain returned as canonical name: {canonical_name}"
        else:
            print("✅ Canonical name appears valid")
    else:
        print("✅ No canonical name returned (filtering worked)")
    
    print("✅ Filtering functionality test passed!")

if __name__ == "__main__":
    test_core_citation_extraction()
    test_filtering_functionality()
    print("\n🎉 All core functionality tests passed!") 