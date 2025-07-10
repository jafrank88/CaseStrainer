#!/usr/bin/env python3
import re

text = "Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1"

patterns = [
    r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]{1,80}?\s+v\.\s+[A-Za-z\s,\.\'-]{1,80}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
    r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)',
    r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
]

print(f"Testing text: {text}")
print()

for i, pattern in enumerate(patterns):
    print(f"Pattern {i+1}: {pattern}")
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        print(f"✅ Matched: '{match.group(1)}'")
    else:
        print("❌ No match")
    print() 