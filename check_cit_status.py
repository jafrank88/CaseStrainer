import json
d = json.load(open('batch_results/25_Verizon-v-Trinko_2004.pdf.json', encoding='utf-8'))
cl = next((c for c in d['clusters'] if c.get('cluster_id') == 'cluster_11_canonical_split_0'), None)

if cl:
    print('Citations in cluster_11_canonical_split_0:')
    for i, c in enumerate(cl.get('citations', [])):
        verified = c.get('verified', False)
        url = c.get('canonical_url', '')[:50]
        name = c.get('canonical_name', '')[:40]
        print(f'  {i+1}. verified={verified} | {name} | {url}')
else:
    print('Cluster not found')
