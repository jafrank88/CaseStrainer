#!/usr/bin/env python3
"""
Test script to verify cluster grouping logic in UnifiedCitationProcessor.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2

sample_text = (
    "John Doe v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), "
    "modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished). "
    "Also see Smith v. Jones, 171 Wn.2d 486 (2011)."
)

print("="*80)
print("TEST: Cluster Grouping Logic")
print("="*80)
print(f"Sample text:\n{sample_text}\n")

ucp = UnifiedCitationProcessorV2()
result = ucp.process_text(sample_text)

print("RESULTS:")
print("="*80)
for i, citation in enumerate(result, 1):
    print(f"Result {i}:")
    print(f"  Citation: {citation.citation}")
    print(f"  Case Name: {citation.canonical_name}")
    print(f"  Canonical Date: {citation.canonical_date}")
    print(f"  Verified: {citation.verified}")
    print(f"  URL: {citation.url}")
    print(f"  Source: {citation.source}")
    print()

print(f"\nTotal Results: {len(result)}")
print("="*80) 