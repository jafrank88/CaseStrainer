#!/usr/bin/env python3
"""
Test script to verify cluster grouping logic in UnifiedCitationProcessor.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

sample_text = (
    "John Doe v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), "
    "modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished). "
    "Also see Smith v. Jones, 171 Wn.2d 486 (2011)."
)

print("="*80)
print("TEST: Cluster Grouping Logic")
print("="*80)
print(f"Sample text:\n{sample_text}\n")

ucp = UnifiedCitationProcessor()
result = ucp.process_text(sample_text, extract_case_names=True, verify_citations=False)

print("RESULTS:")
print("="*80)
for i, citation in enumerate(result.get('results', []), 1):
    print(f"Result {i}:")
    print(f"  Citation: {citation.get('citation')}")
    print(f"  Is Cluster: {citation.get('is_cluster', False)}")
    if citation.get('is_cluster'):
        print(f"  Cluster Members: {citation.get('cluster_members', [])}")
    print(f"  Pinpoint Pages: {citation.get('pinpoint_pages', [])}")
    print(f"  Docket Numbers: {citation.get('docket_numbers', [])}")
    print(f"  Case History: {citation.get('case_history', [])}")
    print(f"  Publication Status: {citation.get('publication_status', '')}")
    print("-" * 40)

print(f"\nTotal Results: {len(result.get('results', []))}")
print("="*80) 