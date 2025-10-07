import requests
import json

# Test with known parallel citations
url = "http://localhost:5000/casestrainer/api/analyze"
payload = {
    "type": "text", 
    "text": "See Lopez Demetrio v. Sakuma Bros. Farms, 183 Wash.2d 649, 355 P.3d 258 (2015)."
}

print("Testing with known parallel citations...")
response = requests.post(url, json=payload, timeout=10)
data = response.json()

print(f"\nSuccess: {data.get('success')}")
print(f"Citations found: {len(data.get('citations', []))}")
print(f"Clusters found: {len(data.get('clusters', []))}")

print("\n=== CITATION DETAILS ===")
for i, cit in enumerate(data.get('citations', []), 1):
    print(f"\nCitation {i}:")
    print(f"  Text: {cit.get('citation')}")
    print(f"  cluster_id: {cit.get('cluster_id')}")
    print(f"  is_cluster: {cit.get('is_cluster')}")
    print(f"  cluster_case_name: {cit.get('cluster_case_name')}")
    print(f"  parallel_citations: {cit.get('parallel_citations', [])}")

print("\n=== CLUSTER DETAILS ===")
for i, cluster in enumerate(data.get('clusters', []), 1):
    print(f"\nCluster {i}:")
    print(f"  cluster_id: {cluster.get('cluster_id')}")
    print(f"  case_name: {cluster.get('case_name') or cluster.get('cluster_case_name')}")
    print(f"  citations: {[c.get('citation') for c in cluster.get('citations', [])]}")
