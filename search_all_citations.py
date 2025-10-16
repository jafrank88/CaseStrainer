#!/usr/bin/env python
"""Search ALL citations for New Mexico patterns"""
import requests
import json

task_id = "test-propagation"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

response = requests.get(url, timeout=10)
data = response.json()

citations = data.get('citations', [])

print("=" * 80)
print(f"SEARCHING ALL {len(citations)} CITATIONS FOR NEW MEXICO PATTERNS")
print("=" * 80)

# Search for NM patterns in ALL fields
nm_found = []

for i, cit in enumerate(citations, 1):
    cit_text = cit.get('citation', '')
    extracted = cit.get('extracted_case_name', '')
    canonical = cit.get('canonical_name', '')
    
    # Check for NM patterns
    full_text = f"{cit_text} {extracted} {canonical}".lower()
    
    if any(pattern in full_text for pattern in ['nm-', 'new mexico', 'n.m.', 'pueblo']):
        nm_found.append({
            'index': i,
            'citation': cit_text,
            'extracted': extracted,
            'canonical': canonical
        })

if nm_found:
    print(f"\n✅ FOUND {len(nm_found)} POTENTIAL NEW MEXICO CITATIONS:\n")
    for item in nm_found:
        print(f"  [{item['index']}] {item['citation']}")
        print(f"      Extracted: {item['extracted']}")
        print(f"      Canonical: {item['canonical']}")
        print()
else:
    print("\n❌ NO NEW MEXICO CITATIONS FOUND")
    print("\nSearching for vendor-neutral format (YYYY-XX-###)...")
    
    # Look for vendor-neutral pattern
    for i, cit in enumerate(citations, 1):
        cit_text = cit.get('citation', '')
        # Pattern like 2017-NM-007 or 2024-NMCA-001
        if '-' in cit_text and any(char.isdigit() for char in cit_text[:4]):
            print(f"\n  [{i}] {cit_text}")

print("\n" + "=" * 80)
print("LISTING ALL CITATIONS FOR MANUAL INSPECTION")
print("=" * 80)

for i, cit in enumerate(citations[:10], 1):  # First 10
    print(f"\n[{i}] {cit.get('citation', 'N/A')}")
    print(f"    Extracted: {cit.get('extracted_case_name', 'N/A')[:60]}...")
