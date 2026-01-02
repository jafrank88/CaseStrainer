#!/usr/bin/env python3
"""
Test clustering fix with live API
"""

import requests
import json

test_text = 'Ellensburg Cement Products, Inc. v. Kittitas County, 179 Wn.2d 737, 317 P.3d 1037 (2014).'

response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
    json={'type': 'text', 'text': test_text, 'enable_verification': True}, 
    timeout=30)

print('Status:', response.status_code)
if response.status_code == 200:
    result = response.json()
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    print(f'Citations: {len(citations)}')
    print(f'Clusters: {len(clusters)}')
    
    for cit in citations:
        print(f'Citation: {cit.get("citation")}')
        print(f'  Extracted: {cit.get("extracted_case_name")}')
        print(f'  Canonical: {cit.get("canonical_name")}')
        print(f'  In cluster: {cit.get("is_in_cluster")}')
        print(f'  Parallel: {cit.get("is_parallel")}')
        print(f'  Cluster members: {cit.get("cluster_members")}')
        print('---')
        
    for i, cluster in enumerate(clusters):
        print(f'Cluster {i+1}: {cluster.get("cluster_id")}, size: {cluster.get("size")}')
        print(f'  Case name: {cluster.get("case_name")}')
        cit_list = cluster.get('citations', [])
        print(f'  Citations: {[c.get("citation") for c in cit_list]}')
else:
    print('Error:', response.text)
