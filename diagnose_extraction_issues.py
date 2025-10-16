#!/usr/bin/env python
"""Diagnose extraction issues with the latest results"""
import requests
import json

# Get latest results
task_id = "test-vendor-neutral-fix"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

response = requests.get(url, timeout=10)
data = response.json()

citations = data.get('citations', [])
clusters = data.get('clusters', [])

print("=" * 80)
print("EXTRACTION QUALITY ANALYSIS")
print("=" * 80)

# Issue 1: Duplicate citations
print("\n🔍 ISSUE 1: DUPLICATE CITATIONS")
citation_texts = {}
for cit in citations:
    cit_text = cit.get('citation', '')
    if cit_text in citation_texts:
        citation_texts[cit_text].append(cit)
    else:
        citation_texts[cit_text] = [cit]

duplicates = {k: v for k, v in citation_texts.items() if len(v) > 1}
if duplicates:
    print(f"Found {len(duplicates)} duplicate citations:")
    for cit_text, cit_list in duplicates.items():
        print(f"\n  {cit_text} ({len(cit_list)} instances)")
        for i, cit in enumerate(cit_list, 1):
            print(f"    [{i}] Extracted: {cit.get('extracted_case_name', 'N/A')}")
            print(f"        Method: {cit.get('method', 'N/A')}")
else:
    print("  ✅ No duplicates found")

# Issue 2: Bad extracted names
print("\n🔍 ISSUE 2: SUSPICIOUS EXTRACTED NAMES")
bad_patterns = [
    ('N/A', 'Missing extraction'),
    ('dangerous', 'Fragment/not case name'),
    ('doctrine', 'Fragment/not case name'),
    ('immunity', 'Fragment/not case name'),
    ('child', 'Fragment/not case name'),
]

bad_extractions = []
for cit in citations:
    extracted = cit.get('extracted_case_name', '')
    for pattern, issue in bad_patterns:
        if pattern.lower() in extracted.lower():
            bad_extractions.append({
                'citation': cit.get('citation', ''),
                'extracted': extracted,
                'issue': issue,
                'method': cit.get('method', 'N/A')
            })
            break

if bad_extractions:
    print(f"Found {len(bad_extractions)} suspicious extractions:")
    for item in bad_extractions:
        print(f"\n  {item['citation']}")
        print(f"    Extracted: '{item['extracted']}'")
        print(f"    Issue: {item['issue']}")
        print(f"    Method: {item['method']}")
else:
    print("  ✅ No suspicious extractions")

# Issue 3: Verification rate
print("\n🔍 ISSUE 3: VERIFICATION STATUS")
verified_count = sum(1 for c in citations if c.get('verified', False))
print(f"  Verified: {verified_count}/{len(citations)} ({verified_count/len(citations)*100:.1f}%)")
if verified_count == 0:
    print("  ❌ ZERO citations verified - verification system may not be running")

# Issue 4: Truncated names
print("\n🔍 ISSUE 4: TRUNCATED NAMES")
truncated = []
for cit in citations:
    extracted = cit.get('extracted_case_name', '')
    # Check for truncation indicators
    if any(indicator in extracted for indicator in ['Inc. v.', ', 31 Wn. App.', '...', 'N/A']):
        truncated.append({
            'citation': cit.get('citation', ''),
            'extracted': extracted
        })

if truncated:
    print(f"Found {len(truncated)} potentially truncated names:")
    for item in truncated[:5]:  # First 5
        print(f"\n  {item['citation']}")
        print(f"    '{item['extracted']}'")
else:
    print("  ✅ No obvious truncation detected")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print("""
1. DUPLICATES: Deduplication should remove these
2. BAD NAMES: Case name extraction needs fixing for these patterns
3. VERIFICATION: Check why verification isn't running
4. TRUNCATION: Corporate name handling still needs work
""")
