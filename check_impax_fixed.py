import json

# Check if Impax citation now has ECN
d = json.load(open('batch_results/06_Impax-v-FTC_2019.pdf.json', encoding='utf-8'))
cl = next((c for c in d['clusters'] if c.get('cluster_id') == 'cluster_30'), None)

if cl:
    print('=== Impax cluster_30 after Trade Cas. fix ===')
    print(f'submitted_display_name: {cl.get("submitted_display_name")}')
    print(f'cluster_case_name: {cl.get("cluster_case_name")}')
    print()
    print('Citations:')
    for i, c in enumerate(cl.get('citations', [])):
        print(f'  {i+1}. ECN: {c.get("extracted_case_name")} | {c.get("citation", "")[:80]}')
else:
    print('Cluster not found')
