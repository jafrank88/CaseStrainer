import json
d = json.load(open('batch_results/25_Verizon-v-Trinko_2004.pdf.json', encoding='utf-8'))
all_clusters = d.get('clusters', [])
mci_clusters = [c for c in all_clusters if 'MCI' in (c.get('submitted_display_name') or '') or 'MCI' in ''.join([cit.get('canonical_name') or '' for cit in c.get('citations', [])])]
print(f'MCI clusters: {len(mci_clusters)}')
for mc in mci_clusters:
    print(f'  {mc.get("cluster_id")}: {mc.get("submitted_display_name", "")[:60]}')
    for cit in mc.get('citations', []):
        print(f'    {cit.get("citation", "")[:50]} | {cit.get("canonical_name", "")[:40]}')
