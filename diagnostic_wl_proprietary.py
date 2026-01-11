"""
Diagnostic script for WL proprietary format marking issue
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("WL PROPRIETARY FORMAT MARKING DIAGNOSTIC")
print("=" * 60)

# Test with actual WL citations from the interface
test_citations = [
    "2024 WL 4149252",
    "2024 WL 4003343", 
    "2024 WL 1232082",
    "2022 WL 2819734",
    "2021 WL 3622166",
    "2025 WL 1410708"
]

print("\nTesting WL citation detection:")
print("-" * 50)

import re

for cit in test_citations:
    # Test the regex pattern
    is_wl = bool(re.search(r"\d{4}\s+WL\s+\d+", cit))
    print(f"{cit}: {'MATCH' if is_wl else 'NO MATCH'}")

print("\n\nTesting extraction pipeline:")
print("-" * 50)

# Test through the actual pipeline
from src.citation_extraction_endpoint import extract_citations_production

text = """Mastriano v. Gregory, 2024. 2024 WL 4149252, at *6 and 2024 WL 4003343, at *5."""

print(f"Processing text: {text}")
result = extract_citations_production(text)

print(f"\nResults:")
print(f"Method: {result.get('method', 'N/A')}")
print(f"Total citations: {result.get('total', 0)}")

citations = result.get('citations', [])
for cit in citations:
    cit_str = str(cit.get('citation', ''))
    if 'WL' in cit_str:
        print(f"\nWL Citation:")
        print(f"  Citation: {cit_str}")
        print(f"  Verified: {cit.get('verified', False)}")
        print(f"  Verification Status: {cit.get('verification_status', 'N/A')}")
        print(f"  Verification Error: {cit.get('verification_error', 'None')}")

print("\n\nChecking clean_extraction_pipeline.py:")
print("-" * 50)

# Test the deprecated pipeline
from src.clean_extraction_pipeline import extract_citations_clean

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    citations_clean = extract_citations_clean(text)
    
    print(f"Clean pipeline extracted {len(citations_clean)} citations")
    for cit in citations_clean:
        if 'WL' in str(cit.citation):
            print(f"\nWL from clean pipeline:")
            print(f"  Citation: {cit.citation}")
            print(f"  Verification Error: {getattr(cit, 'verification_error', 'None')}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
