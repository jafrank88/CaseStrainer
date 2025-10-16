#!/usr/bin/env python
"""Find New Mexico citations in the result"""
import requests
import json

task_id = "test-propagation"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

response = requests.get(url, timeout=10)
data = response.json()

citations = data.get('citations', [])
clusters = data.get('clusters', [])

print("=" * 80)
print("SEARCHING FOR NEW MEXICO CITATIONS")
print("=" * 80)

# Search for New Mexico patterns
nm_patterns = [
    'N.M.',
    'NMCA',
    'NMSC', 
    'New Mexico',
    'P.3d'  # New Mexico sometimes uses Pacific reporter
]

nm_citations = []

for cit in citations:
    cit_text = cit.get('citation', '')
    extracted = cit.get('extracted_case_name', '')
    
    # Check if it matches NM patterns
    if any(pattern.lower() in cit_text.lower() or pattern.lower() in extracted.lower() 
           for pattern in nm_patterns):
        # Check if it's actually a New Mexico citation
        if 'N.M.' in cit_text or 'NMCA' in cit_text or 'NMSC' in cit_text:
            nm_citations.append(cit)
            print(f"\n✅ FOUND: {cit_text}")
            print(f"   Extracted: {extracted}")
            print(f"   Verified: {'✅' if cit.get('verified') else '❌'}")

if not nm_citations:
    print("\n❌ NO NEW MEXICO CITATIONS FOUND")
    print("\nSearching for vendor-neutral citations (year-number format)...")
    
    # Look for vendor-neutral format: YYYY-NMCA-#### or similar
    for cit in citations:
        cit_text = cit.get('citation', '')
        if '-NMCA-' in cit_text or '-NMSC-' in cit_text or '2025-NMCA-' in cit_text or '2024-NMCA-' in cit_text:
            print(f"\n✅ VENDOR-NEUTRAL: {cit_text}")
            print(f"   Extracted: {cit.get('extracted_case_name', 'N/A')}")
            nm_citations.append(cit)

print(f"\n" + "=" * 80)
print(f"TOTAL NEW MEXICO CITATIONS: {len(nm_citations)}")
print("=" * 80)

if not nm_citations:
    print("\n🔍 Checking if the PDF contains New Mexico citations...")
    print("   The PDF is a Washington State Supreme Court case")
    print("   May not cite any New Mexico cases")
    print("\n💡 To test NM citation extraction, try a PDF that cites NM cases")
