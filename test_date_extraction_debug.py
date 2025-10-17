#!/usr/bin/env python3
"""Debug date extraction for 388 P.3d 977"""
import sys
sys.path.insert(0, 'src')
import re

import requests
from robust_pdf_extractor import extract_pdf_text_robust

print("Downloading PDF...")
url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"
response = requests.get(url)
with open('temp_1034300.pdf', 'wb') as f:
    f.write(response.content)

print("Extracting text...")
text, _ = extract_pdf_text_robust("temp_1034300.pdf")

# Citation: 388 P.3d 977 at position 22227
citation = "388 P.3d 977"
start_index = 22227
end_index = start_index + len(citation)

print(f"\nCitation: '{citation}'")
print(f"Start: {start_index}, End: {end_index}")
print(f"\nContext:")
print(f"BEFORE: '{text[start_index-50:start_index]}'")
print(f"CITATION: '{text[start_index:end_index]}'")
print(f"AFTER: '{text[end_index:end_index+100]}'")

# Test the date extraction logic
after_context = text[end_index:end_index + 300]
before_context = text[max(0, start_index - 100):start_index]

print(f"\n\nDate Extraction Test:")
print(f"=" * 80)

# Strategy 1: Look for (YYYY) after
year_match = re.search(r'\((\d{4})\)', after_context[:100])
if year_match:
    print(f"✅ Strategy 1 (after): Found (YYYY) = {year_match.group(1)}")
    print(f"   Match at position: {year_match.start()}-{year_match.end()}")
    print(f"   Context: '{after_context[max(0,year_match.start()-20):year_match.end()+20]}'")
else:
    print(f"❌ Strategy 1 (after): No (YYYY) found in: '{after_context[:100]}'")

# Strategy 1b: Look for (YYYY) before
year_match_before = re.search(r'\((\d{4})\)', before_context[-50:])
if year_match_before:
    print(f"⚠️  Strategy 1 (before): Found (YYYY) = {year_match_before.group(1)}")
    print(f"   This would be the WRONG year from previous citation!")
else:
    print(f"✅ Strategy 1 (before): No (YYYY) found (good!)")
