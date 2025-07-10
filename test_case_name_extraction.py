#!/usr/bin/env python3
"""
Test script to verify case name extraction in UnifiedCitationProcessorV2
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_case_name_extraction():
    """Test case name extraction with sample text"""
    
    # Test text with multiple citations and case names
    test_text = """A federal court may ask this court to answer a question of Washington law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9 (2003)"""
    
    print("Testing case name extraction with sample text:")
    print("=" * 60)
    print(test_text)
    print("=" * 60)
    
    # Initialize processor with debug mode
    config = ProcessingConfig(debug_mode=True)
    processor = UnifiedCitationProcessorV2(config)
    
    # Process the text
    results = processor.process_text(test_text)
    
    print(f"\nFound {len(results)} citations:")
    print("-" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\nCitation {i}:")
        print(f"  Citation: {result.citation}")
        print(f"  Extracted Case Name: {result.extracted_case_name}")
        print(f"  Extracted Date: {result.extracted_date}")
        print(f"  Context: {result.context[:100]}...")
        print(f"  Confidence: {result.confidence}")
        
        if result.is_cluster:
            print(f"  Type: CLUSTER (size: {len(result.cluster_members)})")
        else:
            print(f"  Type: SINGLE")
    
    # Summary
    case_names_found = [r.extracted_case_name for r in results if r.extracted_case_name and r.extracted_case_name != "N/A"]
    dates_found = [r.extracted_date for r in results if r.extracted_date and r.extracted_date != "N/A"]
    
    print(f"\nSummary:")
    print(f"  Total citations: {len(results)}")
    print(f"  Case names found: {len(case_names_found)}")
    print(f"  Dates found: {len(dates_found)}")
    
    if case_names_found:
        print(f"  Case names: {case_names_found}")
    if dates_found:
        print(f"  Dates: {dates_found}")

if __name__ == "__main__":
    test_case_name_extraction() 