#!/usr/bin/env python3
"""List all citations to find 47 Conn. Supp. 113."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/9c3139e5-e1f7-4639-87e6-1c7e7aa8122e', timeout=30)
d = r.json()

# Check raw citations list
citations = d.get('citations', [])
print(f"Total raw citations: {len(citations)}")
for c in citations:
    if '47' in str(c.get('citation', '')):
        print(f"  Raw: {c.get('citation')}")

# Check clusters
clusters = d.get('clusters', [])
print(f"\nTotal clusters: {len(clusters)}")
total_cluster_cits = 0
for c in clusters:
    total_cluster_cits += len(c.get('citations', []))
print(f"Total citations in clusters: {total_cluster_cits}")

# Find any citation with "47" and "113"
print("\nCitations with '47' and '113':")
for c in clusters:
    for cit in c.get('citations', []):
        cit_str = cit.get('citation', '')
        if '47' in cit_str and '113' in cit_str:
            print(f"  {cit_str} - cluster: {c.get('cluster_case_name')}")
