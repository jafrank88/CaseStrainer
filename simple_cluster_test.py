#!/usr/bin/env python3
"""
Simple test to verify Gideon v. Wainwright clustering fix.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import CitationResult
from src.citation_clustering import group_citations_into_clusters

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

# Run clustering
clustered = group_citations_into_clusters(citations)

# Check results
clusters = {}
for citation in clustered:
    if hasattr(citation, 'metadata') and citation.metadata.get('is_in_cluster'):
        cluster_id = citation.metadata.get('cluster_id')
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(citation.citation)

print(f"Result: {len(clusters)} clusters")
for cluster_id, members in clusters.items():
    print(f"  {cluster_id}: {members}")

if len(clusters) == 1:
    print("✅ SUCCESS: All Gideon citations clustered together!")
else:
    print("❌ FAILURE: Citations not properly clustered")
