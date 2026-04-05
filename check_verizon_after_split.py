import json
d = json.load(open('batch_results/25_Verizon-v-Trinko_2004.pdf.json', encoding='utf-8'))
cl = next((c for c in d['clusters'] if c.get('cluster_id') == 'cluster_11_canonical_split_0'), None)
if cl:
    print('cluster_11_canonical_split_0 after split:')
    print(f'  Submitted name: {cl.get("submitted_display_name", "")[:60]}')
    print('  Citations:')
    for c in cl.get('citations', []):
        print(f'    {c.get("citation", "")[:50]} | {c.get("canonical_name", "")[:40]} | {c.get("canonical_url", "")[:50]}')
else:
    print('Cluster not found')
