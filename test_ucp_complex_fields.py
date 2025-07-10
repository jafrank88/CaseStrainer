#!/usr/bin/env python3
"""
Test UnifiedCitationProcessor for pinpoint, docket, case history, and publication status extraction.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
result = ucp.process_text(sample_text, extract_case_names=True, verify_citations=False)

for i, citation in enumerate(result.get('results', []), 1):
    print(f"Citation {i}:")
    print(f"  Citation: {citation.get('citation')}")
    print(f"  Pinpoint pages: {citation.get('pinpoint_pages') or []}")
    print(f"  Docket numbers: {citation.get('docket_numbers') or []}")
    print(f"  Case history: {citation.get('case_history') or []}")
    print(f"  Publication status: {citation.get('publication_status') or ''}")
    print(f"  Extracted case name: {citation.get('extracted_case_name') or ''}")
    print(f"  Year: {citation.get('extracted_date') or ''}")
    print(f"  Context: {(citation.get('context') or '')[:80]}...")
    print("-") 