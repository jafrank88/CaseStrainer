#!/usr/bin/env python3
"""Check positions of citations"""
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

# Find these citations
citations = [
    ("562 U.S. 42", r'562 U\.S\. 42'),
    ("388 P.3d 977", r'388 P\.3d 977'),
    ("2017-NM-007", r'2017-NM-007')
]

for name, pattern in citations:
    matches = [(m.start(), m.group()) for m in re.finditer(pattern, text)]
    print(f"\n{'='*80}")
    print(f"Citation: {name}")
    print(f"Found {len(matches)} instance(s)")
    print(f"{'='*80}")
    
    for pos, match in matches:
        context_start = max(0, pos - 150)
        context_end = min(len(text), pos + 150)
        context = text[context_start:context_end]
        
        print(f"\nPosition {pos}:")
        print(f"Context: ...{context}...")
