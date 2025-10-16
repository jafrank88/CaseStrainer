#!/usr/bin/env python3
"""Trace the data flow from extraction → clustering → verification → output."""

import sys
import PyPDF2
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from services.citation_extractor import CitationExtractor
from unified_clustering_master import cluster_citations_unified_master

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

print("="*80)
print("DATA FLOW TRACE")
print("="*80)

pdf_path = Path("1033940.pdf")
text = extract_text_from_pdf(pdf_path)

# STEP 1: Extract
print("\n📝 STEP 1: EXTRACTION")
print("-"*60)
extractor = CitationExtractor()
citations = extractor.extract_citations(text)

# Find "199 Wn.2d 528"
target = None
for cit in citations:
    cit_text = cit.citation if hasattr(cit, 'citation') else str(cit)
    if "199" in cit_text and "528" in cit_text:
        target = cit
        break

if target:
    print(f"Found: {target.citation if hasattr(target, 'citation') else target}")
    print(f"  extracted_case_name: '{target.extracted_case_name if hasattr(target, 'extracted_case_name') else 'N/A'}'")
    print(f"  canonical_name: '{target.canonical_name if hasattr(target, 'canonical_name') else 'N/A'}'")
else:
    print("❌ Target citation not found!")
    sys.exit(1)

# STEP 2: Cluster
print("\n🔗 STEP 2: CLUSTERING")
print("-"*60)
clusters = cluster_citations_unified_master(citations, text, debug_mode=False)

# Find the cluster containing "199 Wn.2d 528"
target_cluster = None
for cluster in clusters:
    if isinstance(cluster, dict):
        cluster_cits = cluster.get('citations', []) or cluster.get('cluster_members', [])
        for cit in cluster_cits:
            cit_text = cit.citation if hasattr(cit, 'citation') else (cit.get('citation') if isinstance(cit, dict) else str(cit))
            if "199" in cit_text and "528" in cit_text:
                target_cluster = cluster
                break
    if target_cluster:
        break

if target_cluster:
    print(f"Cluster ID: {target_cluster.get('cluster_id', 'N/A')}")
    print(f"  cluster_case_name: '{target_cluster.get('cluster_case_name', 'N/A')}'")
    print(f"  canonical_name: '{target_cluster.get('canonical_name', 'N/A')}'")
    print(f"  extracted_case_name (cluster level): '{target_cluster.get('extracted_case_name', 'N/A')}'")
    
    # Check the individual citation in the cluster
    cluster_cits = target_cluster.get('citations', []) or target_cluster.get('cluster_members', [])
    for cit in cluster_cits:
        cit_text = cit.citation if hasattr(cit, 'citation') else (cit.get('citation') if isinstance(cit, dict) else str(cit))
        if "199" in cit_text and "528" in cit_text:
            print(f"\n  Citation in cluster:")
            if isinstance(cit, dict):
                print(f"    extracted_case_name: '{cit.get('extracted_case_name', 'N/A')}'")
                print(f"    canonical_name: '{cit.get('canonical_name', 'N/A')}'")
            elif hasattr(cit, 'extracted_case_name'):
                print(f"    extracted_case_name: '{cit.extracted_case_name}'")
                print(f"    canonical_name: '{cit.canonical_name if hasattr(cit, 'canonical_name') else 'N/A'}'")
            break
else:
    print("❌ Target cluster not found!")

print("\n" + "="*80)
print("ISSUE IDENTIFIED")
print("="*80)
print("\n🔍 The data is correct at extraction, but gets contaminated later.")
print("   Most likely causes:")
print("   1. Clustering is overwriting extracted_case_name with canonical_name")
print("   2. Verification is returning wrong canonical data")
print("   3. Final output formatting is mixing the fields")

