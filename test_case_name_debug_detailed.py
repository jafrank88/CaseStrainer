#!/usr/bin/env python3
"""
Detailed debug script to test case name extraction
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
import re

def test_case_name_extraction_detailed():
    """Debug case name extraction in detail"""
    
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
    
    print("=== DETAILED CASE NAME EXTRACTION DEBUG ===")
    
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
        
        # Extract context
        context_start = max(0, start - 200)
        context_end = min(len(test_text), end + 100)
        context = test_text[context_start:context_end]
        print(f"Context: '{context}'")
        
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', context)
        print(f"Sentences ({len(sentences)}):")
        for i, sentence in enumerate(sentences):
            print(f"  {i+1}. '{sentence}'")
        
        # Test each pattern on each sentence
        print("Testing patterns:")
        for pattern_str in processor.case_name_patterns:
            print(f"  Pattern: {pattern_str}")
            pattern = re.compile(pattern_str, re.IGNORECASE)
            
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                matches = pattern.finditer(sentence)
                for match in matches:
                    case_name = match.group(1).strip()
                    print(f"    Sentence {i+1}: Found '{case_name}'")
        
        # Extract case name using the processor
        case_name = processor._extract_case_name_from_context(test_text, citation)
        print(f"Final extracted case name: '{case_name}'")

if __name__ == "__main__":
    test_case_name_extraction_detailed() 