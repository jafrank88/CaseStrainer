#!/usr/bin/env python3
"""Check clustering for the 148 Wn.2d + 59 P.3d pair"""

import requests
import json
import sys

print("=" * 80)
print("CLUSTERING INVESTIGATION: 148 Wn.2d 224 + 59 P.3d 655")
print("=" * 80)

# Get results from API
response = requests.post(
    'https://wolf.law.uw.edu/casestrainer/api/analyze',
    json={
        'text': open('1033940.pdf', 'rb').read().decode('latin-1', errors='ignore'),
        'type': 'text',
        'force_mode': 'sync'
    },
    timeout=120,
    verify=False
)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    sys.exit(1)

data = response.json()
clusters = data.get('clusters', [])

# Find clusters containing these citations
wash_cluster = None
pac_cluster = None

for cluster in clusters:
    citations = cluster.get('citations', [])
    for cit in citations:
        cite_text = cit.get('citation', '')
        if '148 Wn.2d' in cite_text and '224' in cite_text:
            wash_cluster = cluster
        if '59 P.3d' in cite_text or '9 P.3d' in cite_text:
            if '655' in cite_text:
                pac_cluster = cluster

print(f"\n📊 RESULTS:")
print(f"   Total clusters: {len(clusters)}")

if wash_cluster:
    print(f"\n✅ Found cluster with '148 Wn.2d 224':")
    print(f"   Cluster ID: {wash_cluster.get('cluster_id')}")
    print(f"   Extracted name: {wash_cluster.get('extracted_case_name')}")
    print(f"   Canonical name: {wash_cluster.get('canonical_name')}")
    print(f"   Citations in cluster:")
    for cit in wash_cluster.get('citations', []):
        print(f"      - {cit.get('citation')} (pos: {cit.get('start_index')})")
else:
    print("\n❌ '148 Wn.2d 224' not found!")

if pac_cluster:
    print(f"\n✅ Found cluster with '59 P.3d 655' or '9 P.3d 655':")
    print(f"   Cluster ID: {pac_cluster.get('cluster_id')}")
    print(f"   Extracted name: {pac_cluster.get('extracted_case_name')}")
    print(f"   Canonical name: {pac_cluster.get('canonical_name')}")
    print(f"   Citations in cluster:")
    for cit in pac_cluster.get('citations', []):
        print(f"      - {cit.get('citation')} (pos: {cit.get('start_index')})")
else:
    print("\n❌ '59 P.3d 655' / '9 P.3d 655' not found!")

# Check if they're in the same cluster
if wash_cluster and pac_cluster:
    if wash_cluster.get('cluster_id') == pac_cluster.get('cluster_id'):
        print(f"\n✅ SUCCESS: Citations are in the SAME cluster!")
    else:
        print(f"\n❌ PROBLEM: Citations are in DIFFERENT clusters!")
        print(f"   This is a clustering bug - they should be together.")
        
        # Check distance
        wash_pos = wash_cluster.get('citations', [{}])[0].get('start_index', 0)
        pac_pos = pac_cluster.get('citations', [{}])[0].get('start_index', 0)
        distance = abs(wash_pos - pac_pos)
        print(f"\n   Distance between citations: {distance} characters")
        
        # Check extracted names
        wash_name = wash_cluster.get('extracted_case_name')
        pac_name = pac_cluster.get('extracted_case_name')
        print(f"\n   Extracted names:")
        print(f"      148 Wn.2d: {wash_name}")
        print(f"      9 P.3d:    {pac_name}")
        print(f"      Match: {wash_name == pac_name}")

print("\n" + "=" * 80)

