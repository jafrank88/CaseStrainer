#!/usr/bin/env python3
"""Search for specific citation in PDF"""

import PyPDF2
import re

reader = PyPDF2.PdfReader('1033940.pdf')
text = ''.join([page.extract_text() for page in reader.pages])

# Search for "9 P.3d 655"
patterns = [
    r'9\s*P\.3d\s*655',
    r'9\s*P\.\s*3d\s*655',
    r'9\s+P\.3d\s+655',
]

print("=" * 80)
print("SEARCHING FOR: 9 P.3d 655")
print("=" * 80)

found = False
for pattern in patterns:
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    if matches:
        found = True
        print(f"\n✅ Found {len(matches)} match(es) with pattern: {pattern}")
        for i, match in enumerate(matches, 1):
            pos = match.start()
            context_before = text[max(0, pos-100):pos]
            context_after = text[pos:min(len(text), pos+100)]
            
            print(f"\n  Match {i} at position {pos}:")
            print(f"    Before: ...{context_before[-60:]}")
            print(f"    MATCH:  >>>{match.group(0)}<<<")
            print(f"    After:  {context_after[:60]}...")

if not found:
    print("\n❌ Citation '9 P.3d 655' NOT FOUND in document!")
    print("\nSearching for similar patterns:")
    
    # Try to find any "P.3d" citations
    p3d_pattern = r'\d+\s+P\.3d\s+\d+'
    p3d_matches = re.findall(p3d_pattern, text)
    if p3d_matches:
        print(f"\n  Found {len(p3d_matches)} P.3d citations:")
        unique = list(set(p3d_matches))
        for cite in sorted(unique)[:10]:  # Show first 10
            print(f"    - {cite}")
    
    # Check for "655" specifically
    pattern_655 = r'\d+\s+[A-Za-z\.\s]+\s*655'
    matches_655 = re.findall(pattern_655, text)
    if matches_655:
        print(f"\n  Citations ending in 655:")
        unique_655 = list(set(matches_655))
        for cite in sorted(unique_655)[:10]:
            print(f"    - {cite}")

print("\n" + "=" * 80)

