import json

# Check Carterfone cluster_32
d = json.load(open('batch_results/25_Verizon-v-Trinko_2004.pdf.json', encoding='utf-8'))
cl = next((c for c in d['clusters'] if c.get('cluster_id') == 'cluster_32'), None)

if cl:
    print('=== Carterfone cluster_32 ===')
    print(f'submitted_display_name: {cl.get("submitted_display_name")}')
    print(f'submitted_case_name: {cl.get("submitted_case_name")}')
    print(f'cluster_case_name: {cl.get("cluster_case_name")}')
    print()
    print('Citations:')
    for i, c in enumerate(cl.get('citations', [])):
        print(f'  {i+1}. ECN: {c.get("extracted_case_name")} | {c.get("citation", "")[:80]}')
else:
    print('Cluster not found')
