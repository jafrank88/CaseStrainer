import json

with open('motion_wl_preserve_final.json', 'r') as f:
    data = json.load(f)

# Find all WL citations
wl_cits = [c for c in data.get('citations', []) if '2024 WL 1232082' in c.get('citation', '') or '2006 WL 2788256' in c.get('citation', '')]

print("=" * 80)
print("WL CITATIONS CLUSTERING ANALYSIS")
print("=" * 80)

for cit in wl_cits:
    print(f"\nCitation: {cit.get('citation')}")
    print(f"  Cluster ID: {cit.get('cluster_id')}")
    print(f"  Case Name: {cit.get('extracted_case_name')}")
    print(f"  Year: {cit.get('extracted_date')}")
    print(f"  Position: {cit.get('start_index')}-{cit.get('end_index')}")

# Check clusters
print("\n" + "=" * 80)
print("CLUSTER ANALYSIS")
print("=" * 80)

clusters = data.get('clusters', [])
for cluster in clusters:
    cluster_cits = cluster.get('citations', [])
    has_wl = any('WL' in c.get('citation', '') for c in cluster_cits)
    
    if has_wl:
        print(f"\nCluster ID: {cluster.get('cluster_id')}")
        print(f"  Name: {cluster.get('case_name')}")
        print(f"  Year: {cluster.get('year')}")
        print(f"  Citations in cluster:")
        for c in cluster_cits:
            if 'WL' in c.get('citation', ''):
                print(f"    - {c.get('citation')} (year: {c.get('extracted_date')})")
