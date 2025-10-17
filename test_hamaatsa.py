#!/usr/bin/env python3
"""Check the Hamaatsa case extraction"""
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

# Find "388 P.3d 977"
idx = text.find('388 P.3d 977')
print(f"\nPosition: {idx}")
print(f"\n{'='*80}")
print("CONTEXT AROUND '388 P.3d 977':")
print(f"{'='*80}")
print(text[max(0, idx-300):idx+150])
print(f"{'='*80}\n")

# Also find "2017-NM-007"
idx2 = text.find('2017-NM-007')
if idx2 >= 0:
    print(f"\nPosition of '2017-NM-007': {idx2}")
    print(f"\n{'='*80}")
    print("CONTEXT AROUND '2017-NM-007':")
    print(f"{'='*80}")
    print(text[max(0, idx2-300):idx2+150])
    print(f"{'='*80}\n")
