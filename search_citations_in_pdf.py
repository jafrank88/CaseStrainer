#!/usr/bin/env python3
"""
Search for specific citations in the Trump v. Barbara PDF
"""

import pdfplumber

pdf_path = 'D:/dev/casestrainer/trumpvbarbaracertpet.pdf'

# Extract text
pdf = pdfplumber.open(pdf_path)
text = ''.join([page.extract_text() or '' for page in pdf.pages])
pdf.close()

print(f"Total document length: {len(text)} characters\n")

# Citations from the problematic cluster
citations = [
    '2 Wheat. 227',
    '26 App. 95',
    '2025 WL 2061447',
    '2025 WL 553485',
    '764 F. Supp. 3d 1050',
    '2025 WL 1904338',
    '169 U.S. 649'
]

print("Searching for citations:\n")
for cit in citations:
    pos = text.find(cit)
    if pos != -1:
        # Show context
        context_start = max(0, pos - 100)
        context_end = min(len(text), pos + 100)
        context = text[context_start:context_end]
        print(f"✓ FOUND: {cit} at position {pos}")
        print(f"  Context: ...{context}...")
        print()
    else:
        print(f"✗ NOT FOUND: {cit}")
        print()
