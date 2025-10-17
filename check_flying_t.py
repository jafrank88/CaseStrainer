#!/usr/bin/env python3
"""Check Flying T Ranch citation positions"""
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

# Find Flying T Ranch citations
citations = [
    ("31 Wn. App. 2d 343", r'31 Wn\. App\. 2d 343'),
    ("3 Wn.2d 1031", r'3 Wn\.2d 1031'),
    ("549 P.3d 727", r'549 P\.3d 727')
]

positions = []
for name, pattern in citations:
    matches = [(m.start(), name) for m in re.finditer(pattern, text)]
    if matches:
        pos, _ = matches[0]
        positions.append((pos, name))
        print(f"\n{name}: position {pos}")
        
        context_start = max(0, pos - 200)
        context_end = min(len(text), pos + 200)
        context = text[context_start:context_end]
        print(f"Context: ...{context}...")

# Check distances
if len(positions) >= 2:
    positions.sort()
    print(f"\n{'='*80}")
    print(f"DISTANCES:")
    for i in range(1, len(positions)):
        dist = positions[i][0] - positions[i-1][0]
        print(f"{positions[i-1][1]} → {positions[i][1]}: {dist} chars")
        
        # Check for semicolons
        text_between = text[positions[i-1][0]:positions[i][0]]
        has_semi = ';' in text_between
        print(f"  Semicolon: {has_semi}")
