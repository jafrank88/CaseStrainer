#!/usr/bin/env python3
"""Check if 148 Wash citation appears in results"""

import json

# Read output file
with open('test_fix44_results.txt', 'r') as f:
    lines = f.readlines()

# Find JSON line (starts with '{')
json_line = None
for line in lines:
    if line.strip().startswith('{'):
        json_line = line
        break

if not json_line:
    print("No JSON found")
    exit(1)

data = json.loads(json_line)
citations = data.get('citations', [])

print(f"Total citations: {len(citations)}")
print("\nSearching for '148', 'Fraternal', '59 P':")

found = []
for i, cite in enumerate(citations):
    cite_text = cite.get('citation', '')
    extracted_name = cite.get('extracted_case_name', '')
    
    if '148' in cite_text or 'Fraternal' in str(extracted_name) or '59 P' in cite_text:
        found.append({
            'index': i,
            'citation': cite_text,
            'extracted_name': extracted_name,
            'method': cite.get('method', 'unknown')
        })

if found:
    print(f"\n✅ Found {len(found)} matching citations:")
    for item in found:
        print(f"\n  [{item['index']}] {item['citation']}")
        print(f"      Name: {item['extracted_name']}")
        print(f"      Method: {item['method']}")
else:
    print("\n❌ No matches found!")
    print("\nShowing all Wash./Wn. citations:")
    for i, cite in enumerate(citations):
        cite_text = cite.get('citation', '')
        if 'Wash' in cite_text or 'Wn.' in cite_text or 'P.3d' in cite_text or 'P. 3d' in cite_text:
            print(f"  [{i}] {cite_text}")

