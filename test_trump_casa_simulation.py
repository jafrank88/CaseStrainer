#!/usr/bin/env python3
"""
Simulate Trump v. CASA PDF processing with the new spatial clustering code.
This tests the fix where regions should end at the year position, not extend beyond.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from spatial_clustering import SpatialClusterer

# Simulated text from Trump v. CASA table of authorities
# This represents the problematic "Wong Kim Ark" section
sample_text = """
TABLE OF AUTHORITIES

United States v. Wong Kim Ark, 169 U.S. 649 (1898)

See also United States v. Wong, 2 Wheat. 227 (1817); 
United States v. Wong, 26 App. 95 (2020);
United States v. Wong, 2025 WL 2061447 (D.C. 2025);
United States v. Wong, 2025 WL 553485 (D.C. 2025);
United States v. Wong, 764 F. Supp. 3d 1050 (D.D.C. 2025);
United States v. Wong, 2025 WL 1904338 (D.C. 2025).

Trump v. Hawaii, 138 S. Ct. 2392 (2018)

DHS v. Regents of the University of California, 591 U.S. 1 (2020)
"""

# Extract citation positions
citations = []
citation_texts = [
    "169 U.S. 649",
    "2 Wheat. 227",
    "26 App. 95",
    "2025 WL 2061447",
    "2025 WL 553485",
    "764 F. Supp. 3d 1050",
    "2025 WL 1904338",
    "138 S. Ct. 2392",
    "591 U.S. 1"
]

for cit_text in citation_texts:
    pos = sample_text.find(cit_text)
    if pos != -1:
        citations.append({
            "citation": cit_text,
            "start_index": pos,
            "end_index": pos + len(cit_text)
        })

print("=" * 80)
print("TRUMP V. CASA SPATIAL CLUSTERING TEST")
print("=" * 80)
print()
print(f"Document length: {len(sample_text)} characters")
print(f"Total citations: {len(citations)}")
print()

# Initialize spatial clustering with debug mode
clusterer = SpatialClusterer(config={"debug": True, "max_region_size": 200})

print("Running spatial clustering...")
print()

clusters = clusterer.cluster_citations_spatial(citations, sample_text)

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()
print(f"Total clusters created: {len(clusters)}")
print()

for i, cluster in enumerate(clusters, 1):
    case_name = cluster.get('cluster_case_name', 'N/A')
    year = cluster.get('cluster_year', 'N/A')
    size = cluster.get('cluster_size', 0)
    
    print(f"Cluster {i}: {case_name}, {year}")
    print(f"  Size: {size} citation(s)")
    
    members = cluster.get('cluster_members', [])
    for member in members:
        cit = member.get('citation', 'N/A')
        print(f"    - {cit}")
    print()

print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()

# Check for the Wong Kim Ark issue
wong_clusters = [c for c in clusters if 'Wong' in c.get('cluster_case_name', '')]
if wong_clusters:
    print(f"Found {len(wong_clusters)} 'Wong' cluster(s):")
    for wc in wong_clusters:
        size = wc.get('cluster_size', 0)
        year = wc.get('cluster_year', 'N/A')
        print(f"  - {wc.get('cluster_case_name')}, {year}: {size} citation(s)")
        
        if size > 1:
            print(f"    WARNING: Multiple citations in Wong cluster!")
            members = wc.get('cluster_members', [])
            for m in members:
                print(f"      - {m.get('citation')}")
else:
    print("No 'Wong' clusters found (citations may be unassigned)")

print()

# Check if citations are properly separated
if len(clusters) >= 3:
    print("SUCCESS: Citations are properly separated into multiple clusters")
    print(f"  Expected: 3 clusters (Wong Kim Ark 1898, Trump v. Hawaii 2018, DHS v. Regents 2020)")
    print(f"  Actual: {len(clusters)} clusters")
else:
    print(f"ISSUE: Only {len(clusters)} cluster(s) created")
    print("  The 2017-2025 Wong citations should NOT be in the 1898 Wong Kim Ark cluster")

print()

# Count unassigned citations
total_assigned = sum(c.get('cluster_size', 0) for c in clusters)
unassigned = len(citations) - total_assigned
if unassigned > 0:
    print(f"Note: {unassigned} citation(s) unassigned (expected for citations after year)")
