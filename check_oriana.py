#!/usr/bin/env python3
import requests
r = requests.get('http://localhost:5000/casestrainer/api/task_status/2802db24-082a-4034-b50c-a669c2a7d460', timeout=30)
d = r.json()

print("Citations with Ohio/Neb/N.E/N.W:")
for c in d.get('citations', []):
    cit = c.get('citation', '')
    if 'Ohio' in cit or 'Neb' in cit or 'N.E' in cit or 'N.W' in cit:
        print(f"  {cit}: extracted='{c.get('extracted_case_name')}'")

print("\nOriana House cluster details:")
for cluster in d.get('clusters', []):
    name = cluster.get('cluster_case_name', '') or ''
    if 'oriana' in name.lower():
        print(f"Cluster: {name}")
        for cit in cluster.get('citations', []):
            print(f"  - {cit.get('citation')}: extracted='{cit.get('extracted_case_name')}'")
