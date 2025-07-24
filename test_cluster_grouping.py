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

# Test Paragraph 1 (existing)
sample_text_1 = (
    "John Doe v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), "
    "modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished). "
    "Also see Smith v. Jones, 171 Wn.2d 486 (2011)."
)

# Test Paragraph 2 (standard test)
sample_text_2 = (
    "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep’t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"
)

# Test Paragraph 3 (second standard test from memory)
sample_text_3 = (
    "We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are “under no obligation to grant special favors to . . . a pro se litigant.”). Thus, a pro se appellant’s failure to “identify any specific legal issues . . . cite any authority” or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)"
)

ucp = UnifiedCitationProcessorV2()

for idx, (label, sample_text) in enumerate([
    ("Paragraph 1 (Doe/Smith sample)", sample_text_1),
    ("Paragraph 2 (Standard test)", sample_text_2),
    ("Paragraph 3 (Second standard test)", sample_text_3)
], 1):
    print("="*80)
    print(f"TEST {idx}: Cluster Grouping Logic - {label}")
    print("="*80)
    print(f"Sample text:\n{sample_text}\n")
    result = ucp.process_text(sample_text)
    print("RESULTS:")
    print("="*80)
    for i, citation in enumerate(result['citations'], 1):
        # Print context window for Paragraph 3
        if idx == 3:
            # Print 100 chars before and after the citation in the text
            cite_text = citation.citation
            pos = sample_text.find(cite_text)
            if pos != -1:
                context_before = sample_text[max(0, pos-100):pos]
                context_after = sample_text[pos+len(cite_text):pos+len(cite_text)+100]
                print(f"  [Context window for '{cite_text}']:")
                print(f"    ...{context_before}>>>{cite_text}<<<{context_after}...")
            # Print extracted date for debugging
            print(f"  [Extracted date for '{cite_text}']: {citation.extracted_date}")
            # Print raw extracted case name for 136 Wn. App. 104
            if cite_text == '136 Wn. App. 104':
                print(f"  [RAW extracted_case_name for '136 Wn. App. 104']: {citation.extracted_case_name}")
                # Print the actual context window used for extraction
                if hasattr(citation, 'context') and citation.context:
                    print(f"  [ACTUAL extraction context for '136 Wn. App. 104']:")
                    print(f"    {citation.context}")
        print(f"Result {i}:")
        print(f"  Citation: {citation.citation}")
        print(f"  Canonical Name: {citation.canonical_name}")
        print(f"  Extracted Case Name: {citation.extracted_case_name}")
        print(f"  Canonical Date: {citation.canonical_date}")
        print(f"  Verified: {citation.verified}")
        print(f"  URL: {citation.url}")
        print(f"  Source: {citation.source}")
        print()
    print(f"\nTotal Results: {len(result['citations'])}")
    print("="*80) 