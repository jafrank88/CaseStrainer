#!/usr/bin/env python3
"""Check if 388 P.3d 977 appears multiple times"""
import sys
sys.path.insert(0, 'src')
import re
import requests
from robust_pdf_extractor import extract_pdf_text_robust

print("Downloading PDF...")
resp = requests.get('https://www.courts.wa.gov/opinions/pdf/1034300.pdf')
with open('temp.pdf', 'wb') as f:
    f.write(resp.content)

print("Extracting text...")
text, _ = extract_pdf_text_robust('temp.pdf')

# Find all instances
matches = [(m.start(), m.group()) for m in re.finditer(r'388 P\.3d 977', text)]

print(f"\n{'='*80}")
print(f"Found {len(matches)} instances of '388 P.3d 977':")
print(f"{'='*80}\n")

for pos, match in matches:
    context_start = max(0, pos - 100)
    context_end = min(len(text), pos + 120)
    context = text[context_start:context_end]
    
    print(f"Position {pos}:")
    print(f"  Context: ...{context}...")
    print()
