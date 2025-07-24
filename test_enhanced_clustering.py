#!/usr/bin/env python3
"""
Comprehensive test for enhanced clustering functionality using Test Paragraph 2
"""

from src.document_processing_unified import process_document
import os

# Test Paragraph 2 from memory
TEST_PARAGRAPH_2 = (
    "We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. "
    "Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) "
    "(noting courts are “under no obligation to grant special favors to . . . a pro se litigant.”). Thus, a pro se appellant’s failure to “identify any specific legal issues . . . cite any authority” or comply with procedural rules may still preclude appellate review. "
    "State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)"
)

print("=== ENHANCED CLUSTERING TEST: TEST PARAGRAPH 2 ===")
print(f"Test text: {TEST_PARAGRAPH_2[:100]}...")

# Process the document
result = process_document(content=TEST_PARAGRAPH_2)

print(f"\nProcessing complete!")
print(f"Citations found: {len(result['citations'])}")

# Group citations by cluster
clusters = {}
for citation in result['citations']:
    cluster_id = citation.get('cluster_id', 'no_cluster')
    if cluster_id not in clusters:
        clusters[cluster_id] = []
    clusters[cluster_id].append(citation)

print(f"\nClusters found: {len(clusters)}")

# Display clusters
for cluster_id, cluster_citations in clusters.items():
    print(f"\n=== CLUSTER: {cluster_id} ===")
    print(f"Citations in cluster: {len(cluster_citations)}")
    
    # Cluster-level case name and year (should be the same for all citations in the cluster)
    cluster_case_name = cluster_citations[0].get('enhanced_case_name')
    cluster_year = cluster_citations[0].get('enhanced_year')
    print(f"Cluster case name: {cluster_case_name}")
    print(f"Cluster year: {cluster_year}")
    
    # Show all citations in this cluster
    for i, citation in enumerate(cluster_citations, 1):
        confidence_text = "[HIGH]" if citation.get('confidence') == 'high' else "[MED]"
        verified_text = "[VERIFIED]" if citation.get('verified') else "[NOT VERIFIED]"
        print(f"  {i}. {confidence_text} {citation['citation']} (Year: {citation.get('enhanced_year')})")
        print(f"     Method: {citation.get('method', 'unknown')} | {verified_text}")
        print(f"     Parallel Citations: {citation.get('parallel_citations', [])}")

print(f"\n=== CLUSTERING ANALYSIS ===")
print("Expected clusters:")
print("1. Holder v. City of Vancouver: 136 Wn. App. 104, 147 P.3d 641 (2006)")
print("2. In re Marriage of Olson: 69 Wn. App. 621, 850 P.2d 527 (1993)")
print("3. State v. Marintorres: 93 Wn. App. 442, 969 P.2d 501 (1999)")

expected_clusters = [
    ("Holder v. City of Vancouver", "2006"),
    ("In re Marriage of Olson", "1993"),
    ("State v. Marintorres", "1999"),
]

print("\n=== SUMMARY CHECK ===")
all_match = True
for idx, (expected_name, expected_year) in enumerate(expected_clusters):
    cluster = clusters.get(f"cluster_{idx}")
    if not cluster:
        print(f"Cluster {idx}: MISSING")
        all_match = False
        continue
    actual_name = cluster[0].get('enhanced_case_name')
    actual_year = cluster[0].get('enhanced_year')
    name_match = (actual_name == expected_name)
    year_match = (actual_year == expected_year)
    print(f"Cluster {idx}: name: {actual_name} (expected: {expected_name}) | year: {actual_year} (expected: {expected_year}) | name_match: {name_match} | year_match: {year_match}")
    if not (name_match and year_match):
        all_match = False
if all_match:
    print("\nAll clusters, names, and years match expected values!\n")
else:
    print("\nSome clusters, names, or years do not match expected values.\n")

# Save summary to logs directory
os.makedirs('logs', exist_ok=True)
with open('logs/clustering_summary_check.txt', 'w', encoding='utf-8') as f:
    f.write("=== ENHANCED CLUSTERING TEST: TEST PARAGRAPH 2 ===\n")
    f.write(f"Test text: {TEST_PARAGRAPH_2[:100]}...\n\n")
    f.write(f"Citations found: {len(result['citations'])}\n\n")
    f.write(f"Clusters found: {len(clusters)}\n\n")
    for idx, (expected_name, expected_year) in enumerate(expected_clusters):
        cluster = clusters.get(f"cluster_{idx}")
        if not cluster:
            f.write(f"Cluster {idx}: MISSING\n")
            continue
        actual_name = cluster[0].get('enhanced_case_name')
        actual_year = cluster[0].get('enhanced_year')
        name_match = (actual_name == expected_name)
        year_match = (actual_year == expected_year)
        f.write(f"Cluster {idx}: name: {actual_name} (expected: {expected_name}) | year: {actual_year} (expected: {expected_year}) | name_match: {name_match} | year_match: {year_match}\n")
    if all_match:
        f.write("\nAll clusters, names, and years match expected values!\n")
    else:
        f.write("\nSome clusters, names, or years do not match expected values.\n")
    f.write("\n=== END OF TEST ===\n")

print("=== END OF TEST ===")

print(f"\n=== ENHANCED CLUSTERING TEST COMPLETE ===")
print("✅ Enhanced clustering and extraction for Test Paragraph 2!") 