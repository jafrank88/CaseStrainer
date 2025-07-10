#!/usr/bin/env python3
"""
Debug script to test case name extraction for the specific citations in the user's output.
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, CitationResult
import re

def test_case_name_extraction():
    """Test case name extraction for the problematic citations."""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test the specific contexts from the user's output
    test_cases = [
        {
            'citation': '171 Wn.2d 486, 493, 256 P.3d 321',
            'context': 'eepThink, LLC, 200 Wn.2d\n72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review\nde novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 \n(2011). We also review the meaning of a statute de novo. Dep\'t of Ecology v.\nCampbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)',
            'expected_case_name': 'Carlson v. Glob. Client Sols., LLC'
        },
        {
            'citation': '146 Wn.2d 1, 9, 43 P.3d 4',
            'context': 'ent Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 \n(2011). We also review the meaning of a statute de novo. Dep\'t of Ecology v.\nCampbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)',
            'expected_case_name': 'Campbell & Gwinn, LLC'
        }
    ]
    
    print("Testing case name extraction for problematic citations:")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Citation: {test_case['citation']}\nContext: {test_case['context']}\nExpected: {test_case['expected_case_name']}")
        
        # Create a CitationResult object with proper indices
        citation_text = test_case['citation']
        context = test_case['context']
        
        # Find the citation in the context
        citation_start = context.find(citation_text)
        if citation_start == -1:
            print("ERROR: Citation not found in context!")
            continue
            
        citation_end = citation_start + len(citation_text)
        
        # Create CitationResult object
        citation_result = CitationResult(
            citation=citation_text,
            start_index=citation_start,
            end_index=citation_end,
            context=context
        )
        
        # Print the context window used for extraction (for the first test case)
        if i == 1:
            context_start = max(0, citation_start - 300)
            context_end = citation_end
            context_window = context[context_start:context_end]
            print(f"Context window used for extraction (first 200 chars):\n{context_window[:200]}")
            # Print all regex matches for case names in the context window
            print("Regex matches in context window:")
            for pattern_str in processor.case_name_patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                for match in pattern.finditer(context_window):
                    print(f"Pattern: {pattern_str}")
                    print(f"Match: {match.group(1)}")
        
        # Test case name extraction
        extracted_name = processor._extract_case_name_from_context(
            context, 
            citation_result
        )
        print(f"Extracted: {extracted_name}")
        print("-" * 40)

if __name__ == "__main__":
    test_case_name_extraction() 