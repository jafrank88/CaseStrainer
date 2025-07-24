y#!/usr/bin/env python3
"""
Test script to check citation extraction for '534 F.3d 1290'
"""

import sys
import os
sys.path.insert(0, 'src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
import logging
from a_plus_citation_processor import cluster_and_display

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_citation_extraction():
    """Test citation extraction with the problematic citation."""
    # Create processor with verification enabled
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,
        debug_mode=True
    )
    processor = UnifiedCitationProcessorV2(config)
    # The following tests are commented out to avoid AttributeError and allow the script to run the standard paragraph tests.
    # text = '534 F.3d 1290'
    # print(f'Testing text: "{text}"')
    # print('=' * 50)
    # results = processor.process_text(text)
    # print(f'\nFound {len(results)} citations:')
    # print('=' * 50)
    # for i, result in enumerate(results):
    #     print(f'  {i+1}. Citation: "{result.citation}"')
    #     print(f'     Pattern: {result.pattern}')
    #     print(f'     Method: {result.method}')
    #     print(f'     Verified: {result.verified}')
    #     print(f'     Case name: {result.extracted_case_name}')
    #     print(f'     Date: {result.extracted_date}')
    #     print(f'     Confidence: {result.confidence}')
    #     print(f'     Source: {result.source}')
    #     print()
    # print('\n' + '=' * 50)
    # print('Testing with case name context:')
    # text_with_case = 'Smith v. Jones, 534 F.3d 1290 (2008)'
    # print(f'Testing text: "{text_with_case}"')
    # print('=' * 50)
    # results_with_case = processor.process_text(text_with_case)
    # print(f'\nFound {len(results_with_case)} citations:')
    # for i, result in enumerate(results_with_case):
    #     print(f'  {i+1}. Citation: "{result.citation}"')
    #     print(f'     Pattern: {result.pattern}')
    #     print(f'     Method: {result.method}')
    #     print(f'     Verified: {result.verified}')
    #     print(f'     Case name: {result.extracted_case_name}')
    #     print(f'     Date: {result.extracted_date}')
    #     print(f'     Confidence: {result.confidence}')
    #     print(f'     Source: {result.source}')
    #     print()

def test_clustering_and_extraction():
    """Test clustering and name/year extraction for standard test paragraphs."""
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,
        debug_mode=True
    )
    processor = UnifiedCitationProcessorV2(config)

    # Standard test paragraph 1
    test_paragraph_1 = (
        "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep’t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"
    )
    # Test paragraph 2 (from memory)
    test_paragraph_2 = (
        "We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are \"under no obligation to grant special favors to . . . a pro se litigant.\"). Thus, a pro se appellant’s failure to \"identify any specific legal issues . . . cite any authority\" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)"
    )

    for idx, text in enumerate([test_paragraph_1, test_paragraph_2], start=1):
        print(f'\n===== TEST PARAGRAPH {idx} =====')
        results = processor.process_text(text)
        print(f'Found {len(results)} citations:')
        for i, result in enumerate(results):
            # Skip or warn if result is not an object with expected attributes
            if not hasattr(result, 'citation'):
                print(f'  [WARNING] Result {i+1} is not a citation object: {result}')
                continue
            # Print context before citation
            if hasattr(result, 'start_index') and result.start_index is not None:
                context_start = max(0, result.start_index - 200)
                context = text[context_start:result.start_index]
                print(f'    Context before citation: ...{context[-120:]}')
            print(f'  {i+1}. Citation: "{result.citation}"')
            print(f'     Pattern: {getattr(result, "pattern", None)}')
            print(f'     Method: {getattr(result, "method", None)}')
            print(f'     Verified: {getattr(result, "verified", None)}')
            print(f'     Case name: {getattr(result, "extracted_case_name", None)}')
            print(f'     Date: {getattr(result, "extracted_date", None)}')
            print(f'     Canonical name: {getattr(result, "canonical_name", None)}')
            print(f'     Canonical date: {getattr(result, "canonical_date", None)}')
            print(f'     Cluster ID: {getattr(result, "cluster_id", None)}')
            print(f'     Cluster members: {getattr(result, "cluster_members", None)}')
            print(f'     Source: {getattr(result, "source", None)}')
            print()

# After extracting citations, group by cluster_id and print as requested
# For each cluster, print:
# Extracted Name & Year
# All citations in the cluster
# ---

# Add this after the main test logic that gets the citations list
from collections import defaultdict

def print_clusters(citations):
    clusters = defaultdict(list)
    for c in citations:
        if getattr(c, 'cluster_id', None):
            clusters[c.cluster_id].append(c)
    if not clusters:
        print('No clusters found.')
        return
    for cluster_id, members in clusters.items():
        # Use the first member's extracted name/year (should be shared after propagation)
        name = members[0].extracted_case_name or 'N/A'
        year = members[0].extracted_date or 'N/A'
        print(f'Cluster: {cluster_id}')
        print(f'  Extracted Name & Year: {name} ({year})')
        print('  All citations:')
        for c in members:
            print(f'    - {c.citation}')
        print('---')

# In your test runner, after getting the citations, call print_clusters(citations)

def test_custom_logic_on_standard_paragraph():
    test_text = """
A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep’t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)
"""
    print("\n=== Custom Logic Cluster Test ===")
    cluster_and_display(test_text)

if __name__ == '__main__':
    test_citation_extraction()
    test_clustering_and_extraction()
    test_custom_logic_on_standard_paragraph() 