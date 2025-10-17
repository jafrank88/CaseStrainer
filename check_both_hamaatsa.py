#!/usr/bin/env python3
"""Check positions of both Hamaatsa citations"""
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

# Find both citations
citations = [
    ("388 P.3d 977", r'388 P\.3d 977'),
    ("2017-NM-007", r'2017-NM-007')
]

for name, pattern in citations:
    matches = [(m.start(), m.group()) for m in re.finditer(pattern, text)]
    print(f"\n{'='*80}")
    print(f"Found {len(matches)} instances of '{name}':")
    print(f"{'='*80}")
    
    for pos, match in matches:
        context_start = max(0, pos - 100)
        context_end = min(len(text), pos + 120)
        context = text[context_start:context_end]
        
        print(f"\nPosition {pos}:")
        print(f"  Context: ...{context}...")

# Check distance between them
pos_388 = text.find('388 P.3d 977')
pos_2017 = text.find('2017-NM-007')

if pos_388 >= 0 and pos_2017 >= 0:
    distance = abs(pos_388 - pos_2017)
    print(f"\n{'='*80}")
    print(f"DISTANCE BETWEEN CITATIONS: {distance} characters")
    print(f"{'='*80}")
    if distance < 200:
        print("✅ Within 200 chars - SHOULD cluster by proximity")
    else:
        print("❌ More than 200 chars apart - WON'T cluster by proximity alone")
        print("   They need name+year clustering to group together!")
