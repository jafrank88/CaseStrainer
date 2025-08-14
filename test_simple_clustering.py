#!/usr/bin/env python3
"""Simple test for citation clustering"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    # Test text with parallel citations (same case, different reporters)
    text = "In Presidential Ests Apt. Assocs. v. Barrett, 129 Wn.2d 320, 917 P.2d 100 (1996), the court held..."
    
    processor = UnifiedCitationProcessorV2()
    
    # Test regex extraction first
    citations = processor._extract_with_regex_enhanced(text)
    print(f"Found {len(citations)} citations:")
    for i, cite in enumerate(citations, 1):
        print(f"  {i}. {cite.citation} (pos: {cite.start_index}-{cite.end_index})")
    
    print()
    
    # Test parallel detection
    if len(citations) >= 2:
        print("Testing parallel citation detection...")
        clustered = processor._detect_parallel_citations(citations, text)
        
        print(f"After clustering: {len(clustered)} citations")
        for i, cite in enumerate(clustered, 1):
            parallel_list = getattr(cite, 'parallel_citations', [])
            print(f"  {i}. {cite.citation}")
            print(f"     Parallels: {parallel_list}")
            print(f"     Is Parallel: {getattr(cite, 'is_parallel', False)}")
    else:
        print("Need at least 2 citations to test clustering")
        
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
