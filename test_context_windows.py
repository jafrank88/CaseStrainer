#!/usr/bin/env python3
"""
Test script to show the three context windows for the standard test paragraph.
"""

import sys
import os
sys.path.append('src')

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig, extract_case_clusters_by_name_and_year, cluster_citations_by_citation_and_year

def test_context_windows():
    """Test and show the context windows for each citation."""
    
    # Standard test paragraph
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("=== TESTING CONTEXT WINDOWS ===")
    print(f"Test text: {test_text}")
    print()
    
    # Initialize processor
    config = ProcessingConfig(
        debug_mode=True,
        extract_case_names=True,
        extract_dates=True,
        enable_verification=False
    )
    
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text(test_text)
    
    # Show context windows for each citation
    print("CONTEXT WINDOWS FOR EACH CITATION:")
    print("=" * 80)
    
    for i, citation in enumerate(results, 1):
        print(f"\n{i}. Citation: {citation.citation}")
        print(f"   Start index: {citation.start_index}")
        print(f"   End index: {citation.end_index}")
        print(f"   Extracted case name: '{citation.extracted_case_name}'")
        print(f"   Extracted date: '{citation.extracted_date}'")
        
        if citation.start_index is not None:
            # Show the context window being used
            context_start = max(0, citation.start_index - 150)
            context_end = min(len(test_text), citation.end_index + 150)
            context = test_text[context_start:context_end]
            
            print(f"   Context window (150 chars before, 150 after):")
            print(f"   '{context}'")
            
            # Show the case name in context
            if "v." in context:
                print(f"   'v.' found in context: YES")
                # Find the case name pattern
                import re
                case_pattern = r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+(.+?)(?=,\s*\d|\s*\(|$)'
                matches = list(re.finditer(case_pattern, context, re.IGNORECASE))
                if matches:
                    for j, match in enumerate(matches):
                        case_name = f"{match.group(1)} v. {match.group(2)}"
                        print(f"   Case name match {j+1}: '{case_name}'")
                else:
                    print(f"   No case name pattern found in context")
            else:
                print(f"   'v.' found in context: NO")
        
        print("-" * 80)
    
    # Now test with larger context window
    print("\n\nTESTING WITH LARGER CONTEXT WINDOW (500 chars):")
    print("=" * 80)
    
    for i, citation in enumerate(results, 1):
        if citation.start_index is not None:
            print(f"\n{i}. Citation: {citation.citation}")
            
            # Show larger context window
            context_start = max(0, citation.start_index - 500)
            context_end = min(len(test_text), citation.end_index + 100)
            context = test_text[context_start:context_end]
            
            print(f"   Larger context window (500 chars before, 100 after):")
            print(f"   '{context}'")
            
            # Test case name extraction with larger context
            case_name = processor._extract_case_name_from_context(test_text, citation)
            print(f"   Extracted case name with larger context: '{case_name}'")
            
            print("-" * 80)

def test_case_clusters():
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    clusters = extract_case_clusters_by_name_and_year(test_text)
    print("\n=== CLUSTERS BETWEEN CASE NAME AND YEAR ===")
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i}:")
        print(f"  Case name: {cluster['case_name']}")
        print(f"  Year: {cluster['year']}")
        print(f"  Citations: {cluster['citations']}")
        print(f"  Text: '{test_text[cluster['start']:cluster['end']]}'")

def test_citation_and_year_clusters():
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    clusters = cluster_citations_by_citation_and_year(test_text)
    print("\n=== CLUSTERS BY CITATION AND YEAR (NO PINCITES) ===")
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i}:")
        print(f"  Case name: {cluster['case_name']}")
        print(f"  Year: {cluster['year']}")
        print(f"  Citations: {cluster['citations']}")
        print(f"  Cleaned text: '{cluster['text']}'")

if __name__ == "__main__":
    test_context_windows()
    test_case_clusters()
    test_citation_and_year_clusters() 