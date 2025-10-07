import requests
import json

# Test direct backend with PDF URL (sync mode)
url = "http://localhost:5000/casestrainer/api/analyze"
payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
}

print("Submitting PDF to backend (sync mode)...")
response = requests.post(url, json=payload, timeout=120)
data = response.json()

print(f"\nStatus: {response.status_code}")
print(f"Success: {data.get('success')}")
print(f"Citations: {len(data.get('citations', []))}")
print(f"Clusters: {len(data.get('clusters', []))}")

# Check clustering details
citations = data.get('citations', [])
with_cluster_id = [c for c in citations if c.get('cluster_id')]
print(f"\nCitations with cluster_id: {len(with_cluster_id)}")

clusters = data.get('clusters', [])
print(f"Cluster count: {len(clusters)}")

if len(clusters) > 0:
    print("\n✅ CLUSTERING IS WORKING!")
    print(f"\nFirst 3 clusters:")
    for i, cluster in enumerate(clusters[:3], 1):
        print(f"\n  Cluster {i}:")
        print(f"    ID: {cluster.get('cluster_id')}")
        print(f"    Case: {cluster.get('case_name') or cluster.get('cluster_case_name')}")
        print(f"    Size: {len(cluster.get('citations', []))}")
else:
    print("\n❌ No clusters found")

# Check case name quality
empty_names = [c for c in citations if not c.get('extracted_case_name')]
print(f"\nEmpty case names: {len(empty_names)}/{len(citations)}")
