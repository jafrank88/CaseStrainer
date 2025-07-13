#!/usr/bin/env python3
"""
Test script using real-world text from API response to verify case name extraction and parallel citation detection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_real_world_extraction():
    """Test with the actual text from the API response."""
    
    # Create processor with debug mode and min_confidence=0.0
    config = ProcessingConfig(
        debug_mode=True, 
        extract_case_names=True, 
        enable_clustering=True,
        min_confidence=0.0  # No confidence filtering
    )
    processor = UnifiedCitationProcessorV2(config)
    
    # The actual text from the API response
    text = """ton law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("Testing Real-World Text Extraction")
    print("=" * 60)
    print(f"Text: {text}")
    print()
    
    # Process the text
    results = processor.process_text(text)
    
    print(f"Found {len(results)} citations:")
    print("-" * 40)
    
    for i, citation in enumerate(results, 1):
        print(f"Citation {i}:")
        print(f"  Citation: {citation.citation}")
        print(f"  Extracted Case Name: {citation.extracted_case_name}")
        print(f"  Extracted Date: {citation.extracted_date}")
        print(f"  Canonical Name: {citation.canonical_name}")
        print(f"  Canonical Date: {citation.canonical_date}")
        print(f"  Verified: {citation.verified}")
        print(f"  Confidence: {citation.confidence}")
        print(f"  Method: {citation.method}")
        print(f"  Is Parallel: {citation.is_parallel}")
        print(f"  Parallel Citations: {citation.parallel_citations}")
        print(f"  Is Cluster: {citation.is_cluster}")
        print(f"  Cluster Members: {citation.cluster_members}")
        print(f"  Start Index: {citation.start_index}")
        print(f"  End Index: {citation.end_index}")
        print()

def test_case_name_extraction_specific():
    """Test case name extraction for specific citations in the text."""
    
    config = ProcessingConfig(debug_mode=True, extract_case_names=True)
    processor = UnifiedCitationProcessorV2(config)
    
    # Test cases with expected results
    test_cases = [
        {
            "text": "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)",
            "citation": "200 Wn.2d 72",
            "expected_case_name": "Convoyant, LLC v. DeepThink, LLC"
        },
        {
            "text": "Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)",
            "citation": "171 Wn.2d 486", 
            "expected_case_name": "Carlson v. Glob. Client Sols., LLC"
        },
        {
            "text": "Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)",
            "citation": "146 Wn.2d 1",
            "expected_case_name": "Dep't of Ecology v. Campbell & Gwinn, LLC"
        }
    ]
    
    print("Testing Specific Case Name Extraction")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        
        # Create a mock citation result
        from src.unified_citation_processor_v2 import CitationResult
        
        # Find citation position in text
        citation_pos = test_case['text'].find(test_case['citation'])
        if citation_pos == -1:
            print("ERROR: Citation not found in text")
            continue
            
        citation_result = CitationResult(
            citation=test_case['citation'],
            start_index=citation_pos,
            end_index=citation_pos + len(test_case['citation'])
        )
        
        # Test case name extraction
        extracted_name = processor._extract_case_name_from_context(test_case['text'], citation_result)
        print(f"Extracted Name: '{extracted_name}'")
        print(f"Expected Name: '{test_case['expected_case_name']}'")
        if extracted_name == test_case['expected_case_name']:
            print("PASS")
        else:
            print("FAIL")
        print("-" * 40)

if __name__ == "__main__":
    test_real_world_extraction()
    test_case_name_extraction_specific()
    print("\nTest completed!") 