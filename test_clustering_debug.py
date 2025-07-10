#!/usr/bin/env python3
"""
Debug script to test clustering logic step by step
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_clustering_debug():
    """Debug the clustering logic step by step"""
    
    # Test text with multiple citations
    test_text = """A federal court may ask this court to answer a question of Washington law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # Create processor with debug mode
    config = ProcessingConfig(debug_mode=True, enable_clustering=True)
    processor = UnifiedCitationProcessorV2(config)
    
    print("=== STEP 1: Extract citations with regex ===")
    regex_citations = processor._extract_with_regex(test_text)
    print(f"Found {len(regex_citations)} citations:")
    for i, citation in enumerate(regex_citations):
        print(f"  {i+1}. '{citation.citation}' at pos {citation.start_index}-{citation.end_index}")
        print(f"     Case name: '{citation.extracted_case_name}'")
        print(f"     Date: '{citation.extracted_date}'")
    
    print("\n=== STEP 2: Test clustering logic ===")
    # Sort by position
    sorted_citations = sorted(regex_citations, key=lambda x: x.start_index or 0)
    print(f"Sorted {len(sorted_citations)} citations by position")
    
    # Test the clustering logic manually
    groups = []
    current_group = []
    
    for i, citation in enumerate(sorted_citations):
        print(f"\nProcessing citation {i+1}: '{citation.citation}'")
        print(f"  Position: {citation.start_index}-{citation.end_index}")
        print(f"  Case name: '{citation.extracted_case_name}'")
        print(f"  Date: '{citation.extracted_date}'")
        
        if not current_group:
            current_group = [citation]
            print(f"  Starting new group")
        else:
            prev_citation = current_group[-1]
            # Check proximity
            close = (citation.start_index and prev_citation.end_index and
                     citation.start_index - prev_citation.end_index <= 50)
            # Check same case name and year
            same_case = (citation.extracted_case_name == current_group[0].extracted_case_name)
            same_year = (citation.extracted_date == current_group[0].extracted_date)
            
            print(f"  Close to previous: {close} (distance: {citation.start_index - prev_citation.end_index if citation.start_index and prev_citation.end_index else 'N/A'})")
            print(f"  Same case name: {same_case}")
            print(f"  Same year: {same_year}")
            
            if close and same_case and same_year:
                # Check for comma separation
                text_between = test_text[prev_citation.end_index:citation.start_index]
                comma_separated = ',' in text_between and len(text_between.strip()) < 30
                print(f"  Comma separated: {comma_separated} (text between: '{text_between}')")
                
                if comma_separated:
                    current_group.append(citation)
                    print(f"  Added to current group (size: {len(current_group)})")
                else:
                    if len(current_group) > 1:
                        groups.append(current_group)
                        print(f"  Finalized group with {len(current_group)} citations")
                    current_group = [citation]
                    print(f"  Started new group")
            else:
                if len(current_group) > 1:
                    groups.append(current_group)
                    print(f"  Finalized group with {len(current_group)} citations")
                current_group = [citation]
                print(f"  Started new group")
    
    # Add the last group if it has multiple citations
    if len(current_group) > 1:
        groups.append(current_group)
        print(f"\nFinalized final group with {len(current_group)} citations")
    
    print(f"\n=== STEP 3: Clustering Results ===")
    print(f"Found {len(groups)} groups:")
    for i, group in enumerate(groups):
        print(f"  Group {i+1} ({len(group)} citations):")
        for j, citation in enumerate(group):
            print(f"    {j+1}. '{citation.citation}'")
    
    # Test the actual clustering method
    print(f"\n=== STEP 4: Test _detect_parallel_citations method ===")
    clustered_citations = processor._detect_parallel_citations(regex_citations, test_text)
    print(f"Clustering method returned {len(clustered_citations)} citations:")
    
    clusters = 0
    singles = 0
    for citation in clustered_citations:
        if citation.is_cluster:
            clusters += 1
            print(f"  CLUSTER: '{citation.citation}' ({len(citation.cluster_members)} members)")
            for member in citation.cluster_members:
                print(f"    - {member}")
        else:
            singles += 1
            print(f"  SINGLE: '{citation.citation}'")
    
    print(f"\nSummary: {clusters} clusters, {singles} singles")

if __name__ == "__main__":
    test_clustering_debug() 