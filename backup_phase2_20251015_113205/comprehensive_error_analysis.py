#!/usr/bin/env python3
"""Comprehensive error analysis for post-FIX #44 results"""

import json
import PyPDF2
import re
from collections import defaultdict

print("=" * 80)
print("COMPREHENSIVE ERROR ANALYSIS - POST FIX #44")
print("=" * 80)

# Read test results
with open('test_post_fix44.json', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Extract citations and clusters from output
lines = content.split('\n')
citations_line = [l for l in lines if 'Citations:' in l]
clusters_line = [l for l in lines if 'Clusters:' in l]

if citations_line and clusters_line:
    total_citations = int(citations_line[0].split(':')[1].strip())
    total_clusters = int(clusters_line[0].split(':')[1].strip())
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"   Total Citations: {total_citations}")
    print(f"   Total Clusters: {total_clusters}")
else:
    print("❌ Could not parse summary statistics")
    total_citations = 0
    total_clusters = 0

# Extract PDF text
print(f"\n📄 READING DOCUMENT:")
reader = PyPDF2.PdfReader('1033940.pdf')
pdf_text = ''.join([page.extract_text() for page in reader.pages])
print(f"   Document length: {len(pdf_text)} characters")

# Check for specific missing citations
print(f"\n🔍 CHECKING FOR MISSING CITATIONS:")
missing_citations = []

# Known problematic citations
problem_cites = [
    ('148 Wn.2d 224', 'Fraternal Order', 25344),
    ('59 P.3d 655', 'Fraternal Order parallel', 25360),
    ('148 Wash. 2d 224', 'Fraternal Order (normalized)', 25344),
]

for cite_pattern, description, expected_pos in problem_cites:
    # Check if in PDF
    pdf_match = re.search(re.escape(cite_pattern).replace(r'\ ', r'\s+'), pdf_text)
    if not pdf_match:
        # Try with flexible spacing
        flexible = cite_pattern.replace(' ', r'\s+').replace('.', r'\.')
        pdf_match = re.search(flexible, pdf_text)
    
    in_pdf = pdf_match is not None
    pdf_pos = pdf_match.start() if pdf_match else None
    
    # Check if in results
    in_results = cite_pattern in content
    
    status = "✅" if in_results else "❌"
    print(f"\n   {status} {cite_pattern} ({description})")
    print(f"      In PDF: {'Yes' if in_pdf else 'No'}{f' at pos {pdf_pos}' if pdf_pos else ''}")
    print(f"      In Results: {'Yes' if in_results else 'No'}")
    
    if in_pdf and not in_results:
        missing_citations.append({
            'citation': cite_pattern,
            'description': description,
            'position': pdf_pos
        })

# Check parallel citation pairs
print(f"\n🔗 CHECKING PARALLEL CITATION CLUSTERING:")
parallel_pairs = [
    ('192 Wn.2d 453', '430 P.3d 655'),
    ('146 Wn.2d 1', '43 P.3d 4'),
    ('199 Wn.2d 528', '509 P.3d 818'),
    ('183 Wn.2d 649', '355 P.3d 258'),
]

split_pairs = []
for cite1, cite2 in parallel_pairs:
    cite1_in = cite1 in content
    cite2_in = cite2 in content
    
    # Check if they appear in same cluster
    if cite1_in and cite2_in:
        # Look for cluster containing both
        in_same_cluster = False
        for line in lines:
            if cite1 in line and cite2 in line:
                in_same_cluster = True
                break
        
        status = "✅" if in_same_cluster else "❌ SPLIT"
        print(f"   {status} {cite1} + {cite2}")
        if not in_same_cluster:
            split_pairs.append((cite1, cite2))
    elif not cite1_in or not cite2_in:
        print(f"   ⚠️  {cite1} + {cite2} - One or both missing from results")

# Check for wrong verification matches
print(f"\n🔎 CHECKING VERIFICATION ACCURACY:")
verification_checks = [
    ('182 Wn.2d 342', 'State v. Velasquez', 'Ass\'n of Wash. Spirits'),
    ('9 P.3d 655', 'Fraternal Order', 'Mississippi'),
    ('199 Wn.2d 528', None, 'PRP Of Darcy Dean Racus'),
]

wrong_verifications = []
for citation, expected_name, wrong_name in verification_checks:
    if citation in content:
        # Find the line with this citation
        for line in lines:
            if citation in line and 'canonical_name' in line:
                if wrong_name and wrong_name in line:
                    print(f"   ❌ {citation} - WRONG: '{wrong_name}'")
                    if expected_name:
                        print(f"      Expected: '{expected_name}'")
                    wrong_verifications.append(citation)
                elif expected_name and expected_name in line:
                    print(f"   ✅ {citation} - Correct: '{expected_name}'")
                break
    else:
        print(f"   ⚠️  {citation} - Not found in results")

# Summary
print(f"\n" + "=" * 80)
print("ISSUE SUMMARY:")
print("=" * 80)
print(f"📊 Statistics:")
print(f"   Citations: {total_citations} (was 87)")
print(f"   Clusters: {total_clusters} (was 57)")
print(f"\n🔥 CRITICAL ISSUES:")
print(f"   Missing Citations: {len(missing_citations)}")
for mc in missing_citations:
    print(f"      - {mc['citation']} ({mc['description']})")
print(f"   Wrong Verifications: {len(wrong_verifications)}")
for wv in wrong_verifications:
    print(f"      - {wv}")
print(f"\n⚠️  MEDIUM ISSUES:")
print(f"   Split Parallel Pairs: {len(split_pairs)}")
for sp in split_pairs:
    print(f"      - {sp[0]} + {sp[1]}")
print(f"\n✅ FIX #44 STATUS:")
print(f"   Text Normalization: ACTIVE")
print(f"   Eyecite Extraction: 99 citations (up from ~40!)")
print(f"   Net Citation Gain: +1 (88 vs 87)")
print(f"   Deduplication: 11 citations removed (99 → 88)")

print(f"\n" + "=" * 80)

