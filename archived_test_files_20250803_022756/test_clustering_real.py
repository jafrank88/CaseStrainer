#!/usr/bin/env python3
"""
Real test to verify Gideon v. Wainwright clustering fix using actual function output.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import CitationResult
from src.services.citation_clusterer import CitationClusterer CitationClusterer

# Create test citations for Gideon v. Wainwright
citations = [
    CitationResult(
        citation="372 U.S. 335",
        canonical_name="Gideon v. Wainwright",
        canonical_date="1963",
        extracted_case_name="Gideon v. Wainwright",
        extracted_date="1963",
        verified=True,
        start_index=0
    ),
    CitationResult(
        citation="83 S. Ct. 792",
        canonical_name="Gideon v. Wainwright",
        canonical_date="1963",
        extracted_case_name="Gideon v. Wainwright",
        extracted_date="1963",
        verified=True,
        start_index=50
    ),
    CitationResult(
        citation="9 L. Ed. 2d 799",
        extracted_case_name="Gideon v. Wainwright",
        extracted_date="1963",
        verified=False,
        start_index=100
    )
]

print("Testing Gideon v. Wainwright clustering...")
print(f"Input: {len(citations)} citations")

# Run clustering - this returns a list of cluster dictionaries
cluster_results = CitationClusterer(citations)

print(f"Result: {len(cluster_results)} clusters")

# Analyze clusters
gideon_clusters = []
other_clusters = []

for cluster in cluster_results:
    cluster_name = cluster.get('canonical_name', cluster.get('extracted_case_name', 'Unknown'))
    cluster_size = cluster.get('size', 0)
    
    print(f"  Cluster: {cluster_name} ({cluster_size} citations)")
    print(f"    Citations: {[c['citation'] for c in cluster['citations']]}")
    
    if 'gideon' in cluster_name.lower():
        gideon_clusters.append(cluster)
    else:
        other_clusters.append(cluster)

# Check results
if len(gideon_clusters) == 1:
    gideon_cluster = gideon_clusters[0]
    gideon_size = gideon_cluster.get('size', 0)
    if gideon_size == 3:
        print("\n✅ SUCCESS: All 3 Gideon citations clustered together!")
    else:
        print(f"\n⚠️  PARTIAL: Gideon cluster has {gideon_size} citations (expected 3)")
elif len(gideon_clusters) > 1:
    print(f"\n❌ FAILURE: Gideon citations split into {len(gideon_clusters)} clusters!")
else:
    print(f"\n❌ FAILURE: No Gideon clusters found!")

# Check for singletons (should be minimal)
singleton_count = sum(1 for cluster in cluster_results if cluster.get('size', 0) == 1)
if singleton_count > 0:
    print(f"\nNote: {singleton_count} singleton clusters (citations not grouped)")

print(f"\nSummary:")
print(f"  Total clusters: {len(cluster_results)}")
print(f"  Gideon clusters: {len(gideon_clusters)}")
print(f"  Other clusters: {len(other_clusters)}")
print(f"  Singleton clusters: {singleton_count}")
