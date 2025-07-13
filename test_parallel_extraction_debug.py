#!/usr/bin/env python3
"""
Debug script to understand why parallel citations are not being grouped together.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_parallel_extraction_debug():
    """Debug the parallel citation extraction process."""
    
    # Test text with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""
    
    print("🧪 Debugging parallel citation extraction...")
    print(f"Text: {test_text}")
    print(f"Text length: {len(test_text)}")
    
    # Initialize processor
    config = ProcessingConfig(
        use_eyecite=False,  # Disable eyecite to focus on regex
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=False,  # Disable verification for debugging
        debug_mode=True
    )
    
    processor = UnifiedCitationProcessorV2(config)
    
    # Step 1: Extract citations with regex
    print("\n📝 Step 1: Extracting citations with regex...")
    regex_citations = processor._extract_with_regex(test_text)
    print(f"Found {len(regex_citations)} citations with regex:")
    for i, citation in enumerate(regex_citations, 1):
        print(f"  {i}. '{citation.citation}' (start: {citation.start_index}, end: {citation.end_index})")
        if citation.start_index is not None and citation.end_index is not None:
            context = test_text[max(0, citation.start_index-20):citation.end_index+20]
            print(f"     Context: ...{context}...")
    
    # Step 2: Detect parallel citations
    print("\n🔗 Step 2: Detecting parallel citations...")
    parallel_citations = processor._detect_parallel_citations(regex_citations, test_text)
    print(f"After parallel detection: {len(parallel_citations)} citations")
    
    # Show which citations have parallel_citations set
    parallel_count = 0
    for i, citation in enumerate(parallel_citations, 1):
        print(f"  {i}. '{citation.citation}'")
        if citation.parallel_citations:
            print(f"     Parallel citations: {citation.parallel_citations}")
            parallel_count += 1
        else:
            print(f"     No parallel citations")
    
    print(f"\n📊 Summary:")
    print(f"  Total citations: {len(parallel_citations)}")
    print(f"  Citations with parallels: {parallel_count}")
    
    # Step 3: Check specific citations we expect to be parallel
    print("\n🎯 Step 3: Checking specific expected parallels...")
    expected_parallels = [
        ("200 Wn.2d 72", "514 P.3d 643"),
        ("171 Wn.2d 486", "256 P.3d 321"),
        ("146 Wn.2d 1", "43 P.3d 4")
    ]
    
    for expected1, expected2 in expected_parallels:
        found1 = None
        found2 = None
        
        for citation in parallel_citations:
            if citation.citation == expected1:
                found1 = citation
            elif citation.citation == expected2:
                found2 = citation
        
        print(f"\n  Checking: {expected1} <-> {expected2}")
        if found1 and found2:
            print(f"    Found both citations")
            print(f"    {expected1} parallels: {found1.parallel_citations}")
            print(f"    {expected2} parallels: {found2.parallel_citations}")
            
            # Check if they reference each other
            if expected2 in found1.parallel_citations:
                print(f"    ✅ {expected1} lists {expected2} as parallel")
            else:
                print(f"    ❌ {expected1} does NOT list {expected2} as parallel")
                
            if expected1 in found2.parallel_citations:
                print(f"    ✅ {expected2} lists {expected1} as parallel")
            else:
                print(f"    ❌ {expected2} does NOT list {expected1} as parallel")
        else:
            print(f"    ❌ Missing citations: found1={found1 is not None}, found2={found2 is not None}")

if __name__ == "__main__":
    test_parallel_extraction_debug() 