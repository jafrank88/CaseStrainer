import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/29445aa8-df9a-4089-bc1d-fe8739687239', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'meri' in name.lower():
        print('Cluster:', name)
        print('has_date_mismatch:', c.get('has_date_mismatch'))
        for cit in c.get('citations', []):
            print(f"  {cit.get('citation')}: verified={cit.get('verified')}, canonical_date={cit.get('canonical_date')}, source={cit.get('source')}")
