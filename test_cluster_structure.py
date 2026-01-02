#!/usr/bin/env python3
"""
Test cluster response structure
"""

import requests

# Test with a smaller subset to see cluster behavior
test_text = '''Department of Ecology v. Campbell & Gwinn, LLC, 171 Wn.2d 820, 256 P.3d 1150 (2011).
Ellensburg Cement Products, Inc. v. Kittitas County, 179 Wn.2d 737, 317 P.3d 1037 (2014).'''

response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
    json={'type': 'text', 'text': test_text, 'enable_verification': True}, 
    timeout=30)

print('Status:', response.status_code)
if response.status_code == 200:
    result = response.json()
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    print(f'Total citations: {len(citations)}')
    print(f'Total clusters: {len(clusters)}')
    
    print('\nCitations:')
    for i, cit in enumerate(citations):
        cluster_id = cit.get('cluster_id')
        is_parallel = cit.get('is_parallel')
        print(f'  {i+1}. {cit.get("citation")} -> cluster: {cluster_id}, parallel: {is_parallel}')
    
    print('\nClusters:')
    for i, cluster in enumerate(clusters):
        cluster_id = cluster.get('cluster_id')
        cluster_size = cluster.get('cluster_size')
        case_name = cluster.get('submitted_display_name', 'N/A')
        print(f'  {i+1}. {cluster_id} - size: {cluster_size}, case: {case_name}')
        cit_list = cluster.get('citations', [])
        citation_texts = [c.get('citation') for c in cit_list]
        print(f'      Citations: {citation_texts}')
else:
    print('Error:', response.text)
