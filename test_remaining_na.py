#!/usr/bin/env python3
"""Investigate the remaining 5 N/A citations"""
import sys
sys.path.insert(0, 'src')

import requests
from robust_pdf_extractor import extract_pdf_text_robust

print("Downloading PDF...")
url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"
response = requests.get(url)
with open('temp_1034300.pdf', 'wb') as f:
    f.write(response.content)

print("Extracting text...")
text, _ = extract_pdf_text_robust("temp_1034300.pdf")

# The 5 remaining N/A citations
citations_to_check = [
    "187 F.3d 645",
    "197 Wn.2d 868",
    "489 P.3d 631",
    "17 F.4th 901",
    "523 U.S. 751"
]

for citation in citations_to_check:
    idx = text.find(citation)
    if idx == -1:
        print(f"\n❌ '{citation}' NOT FOUND in document")
        continue
    
    print(f"\n{'='*80}")
    print(f"📍 CITATION: {citation} (Position: {idx})")
    print(f"{'='*80}")
    
    # Show context
    context_before = text[max(0, idx-250):idx]
    context_after = text[idx:min(len(text), idx+150)]
    
    print(f"\n🔍 CONTEXT BEFORE ({len(context_before)} chars):")
    print(f"---")
    print(context_before)
    print(f"---")
    
    print(f"\n📌 CITATION: >>> {citation} <<<")
    
    print(f"\n🔍 CONTEXT AFTER ({len(context_after)} chars):")
    print(f"---")
    print(context_after)
    print(f"---")
    
    # Check for comma
    pre_citation = text[max(0, idx-10):idx]
    has_comma = ',' in pre_citation
    print(f"\n💡 Has comma within 10 chars before? {has_comma}")
    if has_comma:
        print(f"   Pre-citation text: '{pre_citation}'")

print(f"\n{'='*80}")
print("INVESTIGATION COMPLETE")
print(f"{'='*80}")
