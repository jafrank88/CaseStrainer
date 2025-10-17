#!/usr/bin/env python3
"""Check what's around 549 P.3d 727"""
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

# Find "549 P.3d 727"
idx = text.find('549 P.3d 727')
print(f"\nPosition: {idx}")
print(f"\n{'='*80}")
print("CONTEXT AROUND '549 P.3d 727':")
print(f"{'='*80}")
print(text[max(0, idx-200):idx+150])
print(f"{'='*80}\n")

# Also check the second occurrence
idx2 = text.find('31 Wn. App. 2d 343')
print(f"\nPosition of '31 Wn. App. 2d 343': {idx2}")
print(f"\n{'='*80}")
print("CONTEXT AROUND '31 Wn. App. 2d 343':")
print(f"{'='*80}")
print(text[max(0, idx2-200):idx2+150])
print(f"{'='*80}\n")
