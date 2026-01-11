import json

with open('motion_test_results_v4.json', 'r') as f:
    data = json.load(f)

print("Checking clusters containing WL citations...")
print("=" * 60)

# Check clusters
for cluster in data.get('clusters', []):
    citations = cluster.get('citations', [])
    citation_texts = [c.get('citation', '') for c in citations]
    
    # Check if this cluster contains our problem citations
    has_4003343 = any('4003343' in cit for cit in citation_texts)
    has_4149252 = any('4149252' in cit for cit in citation_texts)
    has_3622166 = any('3622166' in cit for cit in citation_texts)
    has_1410708 = any('1410708' in cit for cit in citation_texts)
    
    if has_4003343 or has_4149252:
        print(f"\nCluster: {cluster.get('cluster_case_name')}")
        print(f"Size: {cluster.get('cluster_size')}")
        print(f"Citations:")
        for cit in citation_texts:
            print(f"  - {cit}")
        if has_4003343 and has_4149252:
            print("  ❌ PROBLEM: Both Mastriano and Doe in same cluster!")
        
    if has_3622166 or has_1410708:
        print(f"\nCluster: {cluster.get('cluster_case_name')}")
        print(f"Size: {cluster.get('cluster_size')}")
        print(f"Citations:")
        for cit in citation_texts:
            print(f"  - {cit}")
        if has_3622166 and has_1410708:
            print("  ❌ PROBLEM: Both 2021 and 2025 Alexander in same cluster!")

print("\n" + "=" * 60)
print("Summary:")
print(f"Total clusters: {len(data.get('clusters', []))}")
print(f"Total citations: {len(data.get('citations', []))}")
