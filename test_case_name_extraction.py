#!/usr/bin/env python3
"""
Test script to debug case name extraction with the standard test paragraph.
"""

import sys
import os
sys.path.append('src')

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.case_name_extraction_core import extract_case_name_triple_comprehensive

def test_case_name_extraction():
    """Test case name extraction with the standard test paragraph."""
    
    # Standard test paragraph
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("=== TESTING CASE NAME EXTRACTION ===")
    print(f"Test text: {test_text}")
    print()
    
    # Test 1: Direct core function test
    print("1. TESTING CORE FUNCTION DIRECTLY")
    print("-" * 50)
    
    test_citations = [
        "200 Wn.2d 72",
        "514 P.3d 643", 
        "171 Wn.2d 486",
        "256 P.3d 321",
        "146 Wn.2d 1",
        "43 P.3d 4"
    ]
    
    for citation in test_citations:
        print(f"\nTesting citation: {citation}")
        try:
            case_name, date, canonical = extract_case_name_triple_comprehensive(test_text, citation)
            print(f"  Case name: '{case_name}'")
            print(f"  Date: '{date}'")
            print(f"  Canonical: '{canonical}'")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Test 2: UCPv2 processor test
    print("\n\n2. TESTING UCPv2 PROCESSOR")
    print("-" * 50)
    
    config = ProcessingConfig(
        debug_mode=True,
        extract_case_names=True,
        extract_dates=True,
        enable_verification=False  # Skip verification for this test
    )
    
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text(test_text)
    
    print(f"\nFound {len(results)} citations:")
    for i, citation in enumerate(results, 1):
        print(f"\n{i}. Citation: {citation.citation}")
        print(f"   Extracted case name: '{citation.extracted_case_name}'")
        print(f"   Extracted date: '{citation.extracted_date}'")
        print(f"   Start index: {citation.start_index}")
        print(f"   End index: {citation.end_index}")
        print(f"   Context: '{citation.context[:100]}...'")
    
    # Test 3: Test the _extract_case_name_from_context method directly
    print("\n\n3. TESTING _extract_case_name_from_context METHOD")
    print("-" * 50)
    
    for citation in results:
        if citation.start_index is not None:
            print(f"\nTesting citation: {citation.citation}")
            case_name = processor._extract_case_name_from_context(test_text, citation)
            print(f"  Extracted case name: '{case_name}'")
            
            # Show the context being used
            context_start = max(0, citation.start_index - 150)
            context_end = min(len(test_text), citation.end_index + 150)
            context = test_text[context_start:context_end]
            print(f"  Context window: '{context}'")

if __name__ == "__main__":
    test_case_name_extraction() 