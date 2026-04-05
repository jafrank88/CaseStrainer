import json
d = json.load(open('batch_results/25_Verizon-v-Trinko_2004.pdf.json', encoding='utf-8'))
clusters = d.get('clusters', [])
url_split_clusters = [c for c in clusters if 'urlsplit' in (c.get('cluster_id') or '')]
print(f'URL split clusters: {len(url_split_clusters)}')
for c in url_split_clusters:
    cid = c.get('cluster_id', '')
    name = c.get('canonical_name', '')[:50]
    url = c.get('canonical_url', '')[:60]
    print(f'  {cid}: {name} | {url}')
