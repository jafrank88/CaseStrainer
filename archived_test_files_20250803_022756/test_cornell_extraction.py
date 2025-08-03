#!/usr/bin/env python3
"""
Quick test to see what Cornell Law's page actually contains for 385 U.S. 493
"""

import requests
import re

url = "https://www.law.cornell.edu/supremecourt/text/385/493"
response = requests.get(url)

print(f"Status: {response.status_code}")
print("=" * 50)

# Look for title
title_match = re.search(r'<title>([^<]+)</title>', response.text)
if title_match:
    print(f"Title: {title_match.group(1)}")

print("=" * 50)

# Look for h1 tags
h1_matches = re.findall(r'<h1[^>]*>([^<]+)</h1>', response.text)
for i, h1 in enumerate(h1_matches):
    print(f"H1 #{i+1}: {h1}")

print("=" * 50)

# Look for case names in content
case_patterns = [
    r'([A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+)',
    r'([A-Z][A-Z\s]+v\.?\s+[A-Z][A-Z\s]+)',
]

for pattern in case_patterns:
    matches = re.findall(pattern, response.text)
    if matches:
        print(f"Pattern {pattern} found:")
        for match in matches[:5]:  # Show first 5 matches
            print(f"  - {match}")
        print()
