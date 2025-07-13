#!/usr/bin/env python3
"""
Debug test to see exactly what's happening with case name extraction.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig, CitationResult

def debug_case_name_extraction():
    """Debug the case name extraction for the problematic citation."""
    
    config = ProcessingConfig(debug_mode=True, extract_case_names=True)
    processor = UnifiedCitationProcessorV2(config)
    
    # The actual text from the API response
    text = """ton law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("Debug Case Name Extraction - Isolated Context")
    print("=" * 60)
    print(f"Full text: {text}")
    print()
    
    # Test all three citations
    citations = [
        ("200 Wn.2d 72, 73, 514 P.3d 643", "Convoyant, LLC v. DeepThink, LLC"),
        ("171 Wn.2d 486", "Carlson v. Glob. Client Sols., LLC"),
        ("146 Wn.2d 1, 9, 43 P.3d 4", "Dep't of Ecology v. Campbell & Gwinn, LLC")
    ]
    
    for citation_text, expected_case_name in citations:
        citation_pos = text.find(citation_text)
        if citation_pos == -1:
            print(f"ERROR: Citation '{citation_text}' not found in text")
            continue
        
        citation_result = CitationResult(
            citation=citation_text,
            start_index=citation_pos,
            end_index=citation_pos + len(citation_text)
        )
        
        print(f"Citation: {citation_result.citation}")
        print(f"Start Index: {citation_result.start_index}")
        print(f"End Index: {citation_result.end_index}")
        
        # Get isolated context
        context_start, context_end = processor._get_isolated_context(text, citation_result)
        if context_start is not None and context_end is not None:
            isolated_context = text[context_start:context_end]
            print(f"Isolated Context: '{isolated_context}'")
            print(f"Context boundaries: {context_start} to {context_end}")
        else:
            print("ERROR: Could not determine context boundaries")
            continue
        
        # Extract case name
        extracted_name = processor._extract_case_name_from_context(text, citation_result)
        print(f"Extracted Case Name: '{extracted_name}'")
        print(f"Expected Case Name: '{expected_case_name}'")
        
        if extracted_name == expected_case_name:
            print("✅ PASS")
        else:
            print("❌ FAIL")
        print("-" * 40)

if __name__ == "__main__":
    debug_case_name_extraction() 