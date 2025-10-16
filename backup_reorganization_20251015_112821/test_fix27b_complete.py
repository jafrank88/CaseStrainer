#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Fix #27B with force_mode="sync"
Tests the complete extraction fix on full 1033940.pdf
"""

import PyPDF2
import json
import requests
import time

print("=" * 80)
print("COMPREHENSIVE TEST: Fix #27B Extraction Bug Fix")
print("Testing with full 1033940.pdf using force_mode='sync'")
print("=" * 80)

# Extract full PDF text
print("\n📄 Step 1: Extracting text from 1033940.pdf...")
reader = PyPDF2.PdfReader('1033940.pdf')
text = ''.join([page.extract_text() for page in reader.pages])
print(f"   ✓ Extracted {len(text):,} characters from {len(reader.pages)} pages")

# Send to API with force_mode="sync"
print("\n🚀 Step 2: Sending to API with force_mode='sync'...")
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
payload = {
    "text": text,
    "type": "text",
    "force_mode": "sync"  # ← NEW FEATURE to force sync on large document!
}

start_time = time.time()
try:
    response = requests.post(url, json=payload, timeout=120)
    elapsed = time.time() - start_time
    
    print(f"   ✓ API Response: {response.status_code} ({elapsed:.1f}s)")
    
    if response.status_code != 200:
        print(f"\n❌ ERROR: {response.text}")
        exit(1)
    
    result = response.json()
    
    # Save results
    with open('test_results_fix27b_complete.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("   ✓ Results saved to test_results_fix27b_complete.json")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    exit(1)

# Analyze results
print("\n" + "=" * 80)
print("📊 ANALYSIS: Fix #27B Complete Results")
print("=" * 80)

citations = result.get('citations', [])
clusters = result.get('clusters', [])
processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
force_mode = result.get('metadata', {}).get('force_mode', 'not set')

print(f"\n✅ PROCESSING:")
print(f"   Mode: {processing_mode}")
print(f"   Force Mode: {force_mode}")
print(f"   Citations: {len(citations)}")
print(f"   Clusters: {len(clusters)}")

# Check the 3 critical citations that were failing before Fix #27B
critical_citations = [
    {
        'citation': '183 Wn.2d 649',
        'expected_extracted': 'Lopez Demetrio',
        'wrong_before_fix': 'Spokane County',
        'expected_canonical': 'Lopez Demetrio v. Sakuma Bros. Farms'
    },
    {
        'citation': '192 Wn.2d 453',
        'expected_extracted': 'Spokane',
        'wrong_before_fix': 'Lopez Demetrio',
        'expected_canonical': 'Spokane Cnty. v. Wash. Dep\'t of Fish & Wildlife'
    },
    {
        'citation': '182 Wn.2d 342',
        'expected_extracted': 'Ass\'n of Wash. Spirits',
        'wrong_before_fix': 'State v. Velasquez',
        'expected_canonical': 'Association of Washington Spirits'
    }
]

print("\n" + "=" * 80)
print("🔍 CRITICAL FIXES VERIFICATION (Fix #27B)")
print("=" * 80)

fixes_working = 0
fixes_failed = 0

for crit in critical_citations:
    cit_text = crit['citation']
    expected = crit['expected_extracted']
    wrong = crit['wrong_before_fix']
    expected_canon = crit['expected_canonical']
    
    # Find this citation in results
    found = None
    for c in citations:
        if c.get('citation') == cit_text:
            found = c
            break
    
    if found:
        extracted = found.get('extracted_case_name', 'N/A')
        canonical = found.get('canonical_name', 'N/A')
        verified = found.get('verified', False)
        
        # Check if extraction is correct now
        if expected.lower() in extracted.lower():
            status = "✅ FIXED!"
            fixes_working += 1
        elif wrong.lower() in extracted.lower():
            status = "❌ STILL WRONG"
            fixes_failed += 1
        elif extracted == 'N/A':
            status = "⚠️  N/A"
            fixes_failed += 1
        else:
            status = "⚠️  DIFFERENT"
            fixes_failed += 1
        
        print(f"\n{cit_text}: {status}")
        print(f"   Extracted: {extracted[:70]}")
        print(f"   Canonical: {canonical[:70]}")
        print(f"   Verified:  {verified}")
    else:
        print(f"\n{cit_text}: ❌ NOT FOUND")
        fixes_failed += 1

# Overall statistics
print("\n" + "=" * 80)
print("📈 OVERALL STATISTICS")
print("=" * 80)

# Split clusters
split_clusters = [c for c in clusters if '_split_' in c.get('cluster_id', '')]
print(f"\n🔀 CLUSTERING:")
print(f"   Total clusters: {len(clusters)}")
print(f"   Split clusters: {len(split_clusters)} (was 26 before Fix #27B)")
print(f"   Normal clusters: {len(clusters) - len(split_clusters)}")

# N/A extractions
na_extractions = [c for c in citations if c.get('extracted_case_name') == 'N/A']
print(f"\n📋 EXTRACTION QUALITY:")
print(f"   N/A extractions: {len(na_extractions)} / {len(citations)} ({100*len(na_extractions)/len(citations):.1f}%)")

# Verification
verified_citations = [c for c in citations if c.get('verified')]
print(f"\n✓ VERIFICATION:")
print(f"   Verified: {len(verified_citations)} / {len(citations)} ({100*len(verified_citations)/len(citations):.1f}%)")

# Canonical/Extracted mismatches
mismatches = []
for c in citations:
    extracted = c.get('extracted_case_name', '')
    canonical = c.get('canonical_name', '')
    if extracted and extracted != 'N/A' and canonical:
        extracted_words = set(extracted.lower().split())
        canonical_words = set(canonical.lower().split())
        if extracted_words and canonical_words:
            intersection = len(extracted_words & canonical_words)
            union = len(extracted_words | canonical_words)
            similarity = intersection / union if union > 0 else 0
            if similarity < 0.5:
                mismatches.append({
                    'citation': c.get('citation'),
                    'extracted': extracted,
                    'canonical': canonical,
                    'similarity': similarity
                })

print(f"\n⚠️  SUSPICIOUS VERIFICATIONS:")
print(f"   Low similarity matches: {len(mismatches)} citations")

if mismatches:
    print(f"\n   Top 5 mismatches:")
    for m in mismatches[:5]:
        print(f"   • {m['citation']}")
        print(f"     Extracted: {m['extracted'][:50]}")
        print(f"     Canonical: {m['canonical'][:50]}")
        print(f"     Similarity: {m['similarity']:.2f}")

# Final verdict
print("\n" + "=" * 80)
print("🎯 FIX #27B VERDICT")
print("=" * 80)

print(f"\n✅ Critical fixes working: {fixes_working} / 3")
print(f"❌ Critical fixes failed:  {fixes_failed} / 3")

if fixes_working == 3:
    print("\n🎉 SUCCESS! Fix #27B is working perfectly!")
    print("   All 3 critical citations are now extracting correctly.")
elif fixes_working >= 2:
    print("\n✅ MOSTLY WORKING! Fix #27B improved extraction significantly.")
    print(f"   {fixes_working}/3 critical citations fixed.")
else:
    print("\n⚠️  NEEDS MORE WORK. Fix #27B didn't fully resolve the issues.")
    print(f"   Only {fixes_working}/3 critical citations fixed.")

print("\n" + "=" * 80)


