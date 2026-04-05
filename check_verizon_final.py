import json
d = json.load(open('batch_results/25_Verizon-v-Trinko_2004.pdf.json', encoding='utf-8'))
clusters = d.get('clusters', [])
verizon_clusters = [c for c in clusters if 'AT T' in (c.get('submitted_display_name') or '') or 'MCI' in (c.get('submitted_display_name') or '') or 'Southern Pacific' in (c.get('submitted_display_name') or '')]
print(f'Verizon-related clusters: {len(verizon_clusters)}')
for vc in verizon_clusters:
    print(f'  {vc.get("cluster_id")}: {vc.get("submitted_display_name", "")[:60]}')
    for cit in vc.get('citations', []):
        print(f'    {cit.get("citation", "")[:50]} | {cit.get("canonical_name", "")[:40]}')
