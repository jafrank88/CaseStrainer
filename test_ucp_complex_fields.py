#!/usr/bin/env python3
"""
Test UnifiedCitationProcessor for pinpoint, docket, case history, and publication status extraction.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

sample_text = (
    "John Doe v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), "
    "modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished)."
)

print("="*80)
print("TEST: UnifiedCitationProcessor - Complex Fields Extraction")
print("="*80)
print(f"Sample text:\n{sample_text}\n")

ucp = UnifiedCitationProcessor()
result = ucp.process_text(sample_text)

for i, citation in enumerate(result, 1):
    print(f"Citation {i}:")
    print(f"  Citation: {citation.citation}")
    print(f"  Case Name: {citation.canonical_name}")
    print(f"  Date: {citation.canonical_date}")
    print(f"  Verified: {citation.verified}")
    print(f"  URL: {citation.url}")
    print(f"  Source: {citation.source}")
    print("-") 