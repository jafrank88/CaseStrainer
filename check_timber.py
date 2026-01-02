#!/usr/bin/env python3
import requests
r = requests.get('http://localhost:5000/casestrainer/api/task_status/6b03d32e-2cf0-4464-be55-80b7fafe9151', timeout=30)
d = r.json()

print("Mountain Timber clusters:")
for c in d.get('clusters', []):
    name = c.get('cluster_case_name') or ''
    if 'timber' in name.lower():
        print(f"  {name}")
        print(f"    has_date_mismatch: {c.get('has_date_mismatch')}")
        print(f"    verified: {c.get('verified')}")
        for cit in c.get('citations', []):
            print(f"      - {cit.get('citation')}: verified={cit.get('verified')}")
