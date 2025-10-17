#!/usr/bin/env python3
"""Test extraction for the 5 specific N/A citations"""
import sys
sys.path.insert(0, 'src')

import requests
from robust_pdf_extractor import extract_pdf_text_robust
from unified_case_extraction_master import extract_case_name_and_date_unified_master

print("Downloading PDF...")
url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"
response = requests.get(url)
with open('temp_1034300.pdf', 'wb') as f:
    f.write(response.content)

print("Extracting text...")
text, _ = extract_pdf_text_robust("temp_1034300.pdf")

# The 5 remaining N/A citations with their positions
test_cases = [
    ("187 F.3d 645", 39009),
    ("197 Wn.2d 868", 45491),
    ("489 P.3d 631", 45514),
    ("17 F.4th 901", 58538),
    ("523 U.S. 751", 9914),
]

print(f"\n{'='*80}")
print("TESTING EXTRACTION FOR 5 N/A CITATIONS")
print(f"{'='*80}\n")

for citation, start_idx in test_cases:
    print(f"\n{'='*80}")
    print(f"Testing: {citation} at position {start_idx}")
    print(f"{'='*80}\n")
    
    # Try to extract
    result = extract_case_name_and_date_unified_master(
        text=text,
        citation=citation,
        start_index=start_idx,
        end_index=start_idx + len(citation),
        debug=True
    )
    
    if result and isinstance(result, dict):
        case_name = result.get('case_name', 'N/A')
        year = result.get('year', 'N/A')
        print(f"\n✅ RESULT: '{case_name}' ({year})")
    elif result:
        print(f"\n✅ RESULT: '{result.case_name}' ({result.year})")
    else:
        print(f"\n❌ EXTRACTION FAILED - No result returned")
    
    print(f"\n{'-'*80}\n")

print(f"\n{'='*80}")
print("TESTING COMPLETE")
print(f"{'='*80}")
