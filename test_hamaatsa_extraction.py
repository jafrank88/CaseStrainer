#!/usr/bin/env python3
"""Test extraction for both Hamaatsa citations"""
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

# Test both Hamaatsa citations
test_cases = [
    ("388 P.3d 977", 22227),
    ("2017-NM-007", 22214),
]

for citation, start_idx in test_cases:
    print(f"\n{'='*80}")
    print(f"Testing: {citation} at position {start_idx}")
    print(f"{'='*80}\n")
    
    # Show context
    context = text[start_idx-50:start_idx+150]
    print(f"Context: {context}\n")
    
    # Try extraction
    result = extract_case_name_and_date_unified_master(
        text=text,
        citation=citation,
        start_index=start_idx,
        end_index=start_idx + len(citation),
        debug=False
    )
    
    if result:
        case_name = result.get('case_name', 'N/A')
        year = result.get('year', 'N/A')
        print(f"✅ EXTRACTED:")
        print(f"   Case name: {case_name}")
        print(f"   Year: {year}")
    else:
        print(f"❌ EXTRACTION FAILED")
    
    print(f"\n{'-'*80}\n")
