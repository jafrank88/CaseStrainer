import json

with open('motion_test_results_final.json', 'r') as f:
    data = json.load(f)

print("Checking WL citation clusters in detail...")
print("=" * 80)

# Find all WL citations
wl_citations = []
for cit in data.get('citations', []):
    citation_text = cit.get('citation', '')
    if 'WL' in citation_text:
        wl_citations.append({
            'citation': citation_text,
            'extracted_case_name': cit.get('extracted_case_name'),
            'cluster_id': cit.get('cluster_id'),
            'cluster_case_name': cit.get('cluster_case_name'),
            'is_in_cluster': cit.get('is_in_cluster'),
            'cluster_members': cit.get('cluster_members', [])
        })

print(f"Found {len(wl_citations)} WL citations:\n")

for cit in wl_citations:
    print(f"Citation: {cit['citation']}")
    print(f"  extracted_case_name: {cit['extracted_case_name']}")
    print(f"  cluster_id: {cit['cluster_id']}")
    print(f"  cluster_case_name: {cit['cluster_case_name']}")
    print(f"  is_in_cluster: {cit['is_in_cluster']}")
    print(f"  cluster_members count: {len(cit['cluster_members'])}")
    if len(cit['cluster_members']) > 1:
        print(f"  ❌ CLUSTERED WITH:")
        for member in cit['cluster_members']:
            if isinstance(member, dict):
                print(f"    - {member.get('citation')}: {member.get('extracted_case_name')}")
            else:
                print(f"    - {member}")
    print()

# Check clusters
print("\n" + "=" * 80)
print("Checking cluster structure:\n")

for cluster in data.get('clusters', []):
    citations = cluster.get('citations', [])
    citation_texts = [c.get('citation', '') for c in citations]
    
    # Check if this cluster contains WL citations
    has_wl = any('WL' in cit for cit in citation_texts)
    
    if has_wl:
        print(f"Cluster: {cluster.get('cluster_case_name')}")
        print(f"  cluster_id: {cluster.get('cluster_id')}")
        print(f"  cluster_size: {cluster.get('cluster_size')}")
        print(f"  Citations:")
        for cit in citations:
            print(f"    - {cit.get('citation')}: {cit.get('extracted_case_name')}")
        print()
