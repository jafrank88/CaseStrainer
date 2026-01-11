#!/usr/bin/env python3
"""
Debug why United States v. Wong Kim Ark cluster has 6 unrelated citations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from spatial_clustering import SpatialClusterer

# Simulated text from Trump v. CASA PDF showing the problematic area
# This likely contains "United States v. Wong Kim Ark" followed by multiple citations
sample_text = """
See United States v. Wong Kim Ark, 169 U.S. 649 (1898)

Some other text here...

United States v. Wong, 2 Wheat. 227, 26 App. 95 (2025)
2025 WL 2061447, 2025 WL 553485, 764 F. Supp. 3d 1050 (2025)
2025 WL 1904338
"""

# Sample citations that are being clustered together
sample_citations = [
    {"citation": "2 Wheat. 227", "start_index": sample_text.find("2 Wheat. 227")},
    {"citation": "26 App. 95", "start_index": sample_text.find("26 App. 95")},
    {"citation": "2025 WL 2061447", "start_index": sample_text.find("2025 WL 2061447")},
    {"citation": "2025 WL 553485", "start_index": sample_text.find("2025 WL 553485")},
    {"citation": "764 F. Supp. 3d 1050", "start_index": sample_text.find("764 F. Supp. 3d 1050")},
    {"citation": "2025 WL 1904338", "start_index": sample_text.find("2025 WL 1904338")},
]

print("=" * 80)
print("WONG KIM ARK CLUSTER DEBUG")
print("=" * 80)
print()

# Initialize spatial clustering
clusterer = SpatialClusterer(config={"debug": True})

# Run clustering
print("Sample text:")
print(sample_text)
print()
print("=" * 80)
print()

clusters = clusterer.cluster_citations_spatial(sample_citations, sample_text)

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()
print(f"Total clusters created: {len(clusters)}")
print()

for i, cluster in enumerate(clusters, 1):
    print(f"Cluster {i}:")
    print(f"  Case Name: {cluster.get('cluster_case_name')}")
    print(f"  Year: {cluster.get('cluster_year')}")
    print(f"  Size: {cluster.get('cluster_size')}")
    
    members = cluster.get('cluster_members', [])
    print(f"  Members ({len(members)}):")
    for member in members:
        print(f"    - {member.get('citation')}")
    print()

print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()

# Check if all citations are in one cluster
if len(clusters) == 1 and clusters[0].get('cluster_size') == 6:
    print("❌ PROBLEM CONFIRMED: All 6 citations clustered together")
    print()
    print("Likely causes:")
    print("1. Only one case name + year pattern found in the text")
    print("2. All citations fall within the same spatial region")
    print("3. The case name pattern is matching incorrectly")
else:
    print(f"✅ Citations split into {len(clusters)} clusters")
    for i, cluster in enumerate(clusters, 1):
        print(f"   Cluster {i}: {cluster.get('cluster_size')} citations")
