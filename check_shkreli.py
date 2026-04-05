import json

# Check the Shkreli case specifically
d = json.load(open('batch_results/03_Deslandes-v-McDonalds_2022.pdf.json', encoding='utf-8'))
cl = next((c for c in d['clusters'] if c.get('cluster_id') == 'cluster_13'), None)

if cl:
    print('=== Shkreli cluster ===')
    print(f'submitted_display_name: {cl.get("submitted_display_name")}')
    print(f'canonical_name: {cl.get("canonical_name")}')
    print(f'verified: {cl.get("verified")}')
    print()
    print('Citations:')
    for c in cl.get('citations', []):
        print(f'  {c.get("citation", "")[:60]}')
        print(f'    submitted: {c.get("submitted_display_name", "")}')
        print(f'    canonical: {c.get("canonical_name", "")}')
        print(f'    verified: {c.get("verified", False)}')
else:
    print('Cluster not found')
