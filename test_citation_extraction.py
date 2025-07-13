#!/usr/bin/env python3
"""
Test script to examine citation extraction issues.
"""

import sys
import os
sys.path.append('src')

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_citation_extraction():
    # Test paragraph
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    print("Testing citation extraction...")
    print(f"Input text: {test_text}")
    print("-" * 80)

    # Create processor with debug mode
    config = ProcessingConfig(debug_mode=True, extract_case_names=True, extract_dates=True)
    processor = UnifiedCitationProcessorV2(config)

    # Process the text
    results = processor.process_text(test_text)

    print(f'Found {len(results)} citations:')
    for i, citation in enumerate(results):
        print(f'{i+1}. Citation: {citation.citation}')
        print(f'   Case name: {citation.extracted_case_name}')
        print(f'   Date: {citation.extracted_date}')
        print(f'   Context: {citation.context[:100]}...')
        print(f'   Start/End: {citation.start_index}/{citation.end_index}')
        print()

    # Test clustering
    clusters = processor.group_citations_into_clusters(results)
    print(f'Found {len(clusters)} clusters:')
    for i, cluster in enumerate(clusters):
        print(f'Cluster {i+1}:')
        for citation in cluster['citations']:
            print(f'  - {citation["citation"]} (case: {citation["extracted_case_name"]})')
        print()

if __name__ == "__main__":
    test_citation_extraction() 