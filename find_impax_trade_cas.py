import json

# Find the Trade Cas. citation across all clusters in Impax doc
d = json.load(open('batch_results/06_Impax-v-FTC_2019.pdf.json', encoding='utf-8'))

print('Searching for Trade Cas. citation in Impax document...')
for cl in d.get('clusters', []):
    for cit in cl.get('citations', []):
        if 'Trade Cas.' in cit.get('citation', ''):
            print(f'Found in cluster {cl.get("cluster_id")}:')
            print(f'  Cluster name: {cl.get("submitted_display_name", "")[:60]}')
            print(f'  Citation: {cit.get("citation", "")[:80]}')
            print(f'  ECN: {cit.get("extracted_case_name")}')
            print()
