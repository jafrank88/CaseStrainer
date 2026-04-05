import json
d = json.load(open('batch_results/25_Verizon-v-Trinko_2004.pdf.json', encoding='utf-8'))
all_clusters = d.get('clusters', [])
print('Searching for MCI citations across all clusters...')
for c in all_clusters:
    for cit in c.get('citations', []):
        if 'MCI' in (cit.get('canonical_name') or '') or 'MCI' in (cit.get('citation') or ''):
            print(f'Found in cluster {c.get("cluster_id")}:')
            print(f'  Citation: {cit.get("citation", "")[:70]}')
            print(f'  Canonical name: {(cit.get("canonical_name") or "")[:50]}')
            print(f'  Verified: {cit.get("verified", False)}')
            print()
