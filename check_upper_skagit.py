#!/usr/bin/env python3
"""Check Upper Skagit vs Bay Mills contamination"""
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

# Find Upper Skagit and Bay Mills
patterns = [
    ("Upper Skagit", r'Upper Skagit[^.]{0,200}'),
    ("Bay Mills", r'Bay Mills[^.]{0,200}'),
    ("584 U.S. 554", r'584 U\.S\. 554'),
    ("572 U.S. 782", r'572 U\.S\. 782')
]

for name, pattern in patterns:
    matches = list(re.finditer(pattern, text))
    print(f"\n{'='*80}")
    print(f"{name}: {len(matches)} occurrence(s)")
    print(f"{'='*80}")
    
    for i, match in enumerate(matches[:3], 1):  # Show first 3
        pos = match.start()
        context_start = max(0, pos - 150)
        context_end = min(len(text), pos + 300)
        context = text[context_start:context_end]
        print(f"\n{i}. Position {pos}:")
        print(f"{context}")
