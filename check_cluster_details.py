#!/usr/bin/env python
"""Check cluster details for the Flying T Ranch citations"""
import requests
import json

# Get the task result
task_id = "debug-test-logging"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

response = requests.get(url, timeout=10)
data = response.json()

print("=" * 80)
print("SEARCHING FOR: 549 P.3d 727 and 3 Wn.2d 1031")
print("=" * 80)

# Find these citations
target_citations = ['549 P.3d 727', '3 Wn.2d 1031']
found_citations = {}

for cit in data.get('citations', []):
    cit_text = cit.get('citation', '')
    if any(target in cit_text for target in target_citations):
        found_citations[cit_text] = cit

print(f"\n📋 FOUND {len(found_citations)} MATCHING CITATIONS:")
for cit_text, cit in found_citations.items():
    print(f"\n  Citation: {cit_text}")
    print(f"  Extracted Name: {cit.get('extracted_case_name', 'N/A')}")
    print(f"  Canonical Name: {cit.get('canonical_name', 'N/A')}")
    print(f"  Cluster ID: {cit.get('cluster_id', 'N/A')}")
    print(f"  Is in Cluster: {cit.get('is_in_cluster', False)}")
    print(f"  Verified: {cit.get('verified', False)}")

# Now check clusters
print("\n" + "=" * 80)
print("CHECKING CLUSTERS")
print("=" * 80)

clusters = data.get('clusters', [])
relevant_clusters = []

for cluster in clusters:
    cluster_citations = cluster.get('citations', [])
    cluster_cit_texts = [c.get('citation', '') for c in cluster_citations]
    
    # Check if any of our target citations are in this cluster
    if any(any(target in cit_text for target in target_citations) for cit_text in cluster_cit_texts):
        relevant_clusters.append(cluster)
        
        print(f"\n🔗 CLUSTER FOUND:")
        print(f"   Cluster ID: {cluster.get('cluster_id', 'N/A')}")
        print(f"   Cluster Name: {cluster.get('cluster_case_name', 'N/A')}")
        print(f"   Canonical Name: {cluster.get('canonical_name', 'N/A')}")
        print(f"   Total Citations: {len(cluster_citations)}")
        
        print(f"\n   Citations in this cluster:")
        for i, cit in enumerate(cluster_citations, 1):
            cit_text = cit.get('citation', '')
            extracted = cit.get('extracted_case_name', 'N/A')
            canonical = cit.get('canonical_name', 'N/A')
            verified = cit.get('verified', False)
            
            marker = "🎯" if any(target in cit_text for target in target_citations) else "  "
            print(f"   {marker} [{i}] {cit_text}")
            print(f"        Extracted: {extracted}")
            print(f"        Canonical: {canonical}")
            print(f"        Verified: {'✅' if verified else '❌'}")

if not relevant_clusters:
    print("\n⚠️  No cluster found containing both citations!")
    print("   These citations may not be recognized as parallel citations.")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

if len(relevant_clusters) == 1:
    print("✅ Both citations are in the SAME cluster (correctly identified as parallel)")
    print("\n🔍 Case Name Extraction Analysis:")
    
    cluster = relevant_clusters[0]
    extracted_names = set()
    for cit in cluster.get('citations', []):
        if any(target in cit.get('citation', '') for target in target_citations):
            extracted_names.add(cit.get('extracted_case_name', 'N/A'))
    
    if len(extracted_names) > 1:
        print("   ❌ ISSUE: Different extracted case names within the same cluster!")
        print(f"   Found {len(extracted_names)} different extracted names:")
        for name in extracted_names:
            print(f"      - {name}")
        print("\n   💡 RECOMMENDATION: Propagate best extracted name within cluster")
    else:
        print("   ✅ Extracted case names are consistent within cluster")
        
elif len(relevant_clusters) > 1:
    print(f"⚠️  Citations are in DIFFERENT clusters ({len(relevant_clusters)} clusters)")
    print("   This suggests clustering algorithm didn't recognize them as parallel")
else:
    print("⚠️  Citations not found in any clusters")
