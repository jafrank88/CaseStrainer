#!/usr/bin/env python3
"""
Test cluster display with verification enabled
"""

import requests

# Test with actual parallel citations that should verify and cluster
test_text = '''Ellensburg Cement Products, Inc. v. Kittitas County, 179 Wn.2d 737, 317 P.3d 1037 (2014).
Department of Ecology v. Campbell & Gwinn, LLC, 171 Wn.2d 820, 256 P.3d 1150 (2011).'''

response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
    json={'type': 'text', 'text': test_text, 'enable_verification': True}, 
    timeout=45)

print('Status:', response.status_code)
if response.status_code == 200:
    result = response.json()
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    print(f'Total citations: {len(citations)}')
    print(f'Total clusters: {len(clusters)}')
    
    print('\n=== CITATION ANALYSIS ===')
    verified_count = 0
    for i, cit in enumerate(citations):
        verified = cit.get('verified', False)
        if verified:
            verified_count += 1
        print(f'  {i+1}. {cit.get("citation")} -> verified: {verified}, cluster: {cit.get("cluster_id")}, parallel: {cit.get("is_parallel")}')
    
    print(f'\nVerified citations: {verified_count}/{len(citations)}')
    
    print('\n=== CLUSTER ANALYSIS ===')
    for i, cluster in enumerate(clusters):
        cluster_id = cluster.get('cluster_id')
        cluster_size = cluster.get('cluster_size')
        case_name = cluster.get('submitted_display_name', 'N/A')
        verification_status = cluster.get('verification_status', 'unknown')
        
        print(f'  Cluster {i+1}: {cluster_id}')
        print(f'    Size: {cluster_size}')
        print(f'    Case: {case_name}')
        print(f'    Verification: {verification_status}')
        
        cit_list = cluster.get('citations', [])
        print(f'    Citations:')
        for cit in cit_list:
            cit_text = cit.get('citation', 'Unknown')
            cit_verified = cit.get('verified', False)
            print(f'      - {cit_text} (verified: {cit_verified})')
        print()
        
    print('=== FRONTEND DISPLAY EXPECTATION ===')
    print('Based on the data above, the frontend should show:')
    print(f'- {len(clusters)} clusters in the "Cases Found" section')
    print(f'- {verified_count} verified citations')
    print('- Each cluster should display the case name and list the parallel citations')
    
else:
    print('Error:', response.text)
