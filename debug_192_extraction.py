#!/usr/bin/env python3
"""
Debug the extraction for 192 Wn.2d 453 specifically
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_extraction_architecture import UnifiedExtractionArchitecture

def debug_192_extraction():
    """Debug the extraction for 192 Wn.2d 453"""
    
    # The exact test paragraph from the user
    test_text = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
P.3d 655 (2018)."""
    
    # Find the position of 192 Wn.2d 453
    citation_text = "192 Wn.2d 453"
    start_pos = test_text.find(citation_text)
    if start_pos == -1:
        print(f"❌ Citation not found in text")
        return
        
    end_pos = start_pos + len(citation_text)
    print(f"Citation: {citation_text}")
    print(f"Position: {start_pos}-{end_pos}")
    print()
    
    # Show context around the citation
    context_start = max(0, start_pos - 100)
    context_end = min(len(test_text), end_pos + 100)
    context = test_text[context_start:context_end]
    print(f"Context: ...{context}...")
    print()
    
    # Test extraction with the unified architecture
    extractor = UnifiedExtractionArchitecture()
    result = extractor.extract_case_name_and_year(
        text=test_text,
        citation=citation_text,
        start_index=start_pos,
        end_index=end_pos,
        debug=True
    )
    
    print(f"Extracted case name: '{result.case_name}'")
    print(f"Extracted year: '{result.year}'")
    print(f"Confidence: {result.confidence}")
    print(f"Method: {result.method}")
    print()
    
    # Test the specific text around this citation
    print("=== Testing specific text around citation ===")
    specific_text = "Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018)"
    print(f"Text: {specific_text}")
    
    # Test different patterns on this specific text
    import re
    patterns = [
        r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*),\s*(\d+)\s+Wn\.',
        r'([A-Z][^,]+?)\s+v\.\s+([A-Z][^,]+?),\s*(\d+)\s+Wn\.',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        matches = list(re.finditer(pattern, specific_text, re.IGNORECASE))
        print(f"Matches: {len(matches)}")
        for match in matches:
            print(f"  '{match.group(0)}'")
            print(f"  Groups: {match.groups()}")

if __name__ == "__main__":
    debug_192_extraction()









