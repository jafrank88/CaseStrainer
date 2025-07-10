#!/usr/bin/env python3
"""
Debug script to test case name extraction
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_case_name_extraction():
    """Debug case name extraction"""
    
    # Test text with multiple citations
    test_text = """A federal court may ask this court to answer a question of Washington law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # Create processor with debug mode
    config = ProcessingConfig(debug_mode=True)
    processor = UnifiedCitationProcessorV2(config)
    
    print("=== TESTING CASE NAME EXTRACTION ===")
    
    # Test each citation individually
    citations_to_test = [
        ("200 Wn.2d\n72, 73, 514 P.3d 643", 216, 246),
        ("171 Wn.2d 486, 493, 256 P.3d 321", 351, 383),
        ("146 Wn.2d 1, 9, 43 P.3d 4", 485, 510)
    ]
    
    for citation_text, start, end in citations_to_test:
        print(f"\n--- Testing citation: '{citation_text}' ---")
        print(f"Position: {start}-{end}")
        
        # Create a mock citation result
        from unified_citation_processor_v2 import CitationResult
        citation = CitationResult(
            citation=citation_text,
            start_index=start,
            end_index=end
        )
        
        # Extract case name
        case_name = processor._extract_case_name_from_context(test_text, citation)
        print(f"Extracted case name: '{case_name}'")
        
        # Show the context window
        context_start = max(0, start - 300)
        context_end = min(len(test_text), end + 300)
        context = test_text[context_start:context_end]
        print(f"Context window: '{context}'")

if __name__ == "__main__":
    test_case_name_extraction() 