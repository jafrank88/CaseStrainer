"""Check WL citation clustering issue"""
import requests
import json

# Upload motion.pdf
with open('motion.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/upload',
        files={'file': f},
        data={'enable_verification': 'true'},
        timeout=300
    )

data = response.json()

# Find the two WL citations
wl_citations = []
for citation in data.get('citations', []):
    cit_text = citation.get('citation_text', '')
    if '2024 WL 4149252' in cit_text or '2024 WL 4003343' in cit_text:
        wl_citations.append({
            'citation': cit_text,
            'extracted_name': citation.get('extracted_case_name', 'N/A'),
            'extracted_date': citation.get('extracted_date', 'N/A'),
            'cluster_id': citation.get('cluster_id', 'N/A'),
        })

print("\n=== WL Citations Found ===\n")
for cit in wl_citations:
    print(f"Citation: {cit['citation']}")
    print(f"  Extracted Name: {cit['extracted_name']}")
    print(f"  Extracted Date: {cit['extracted_date']}")
    print(f"  Cluster ID: {cit['cluster_id']}")
    print()

# Check clusters
print("\n=== Clusters ===\n")
for cluster in data.get('clusters', []):
    cluster_cits = [c.get('citation_text', '') for c in cluster.get('citations', [])]
    has_wl = any('2024 WL 4149252' in c or '2024 WL 4003343' in c for c in cluster_cits)
    if has_wl:
        print(f"Cluster: {cluster.get('extracted_case_name', 'N/A')}")
        print(f"  Date: {cluster.get('extracted_date', 'N/A')}")
        print(f"  Citations in cluster:")
        for c in cluster_cits:
            print(f"    - {c}")
        print()
