#!/usr/bin/env python3
"""
Test live API with fresh request to verify clusters are working
"""

import requests
import json

test_text = '''Ellensburg Cement Products, Inc. v. Kittitas County, 179 Wn.2d 737, 317 P.3d 1037 (2014).
Department of Ecology v. Campbell & Gwinn, LLC, 171 Wn.2d 820, 256 P.3d 1150 (2011).'''

print('Testing live CaseStrainer API...')
response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
    json={'type': 'text', 'text': test_text, 'enable_verification': True}, 
    timeout=30)

print(f'Status: {response.status_code}')

if response.status_code == 200:
    result = response.json()
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f'\n📊 RESULTS SUMMARY:')
    print(f'  Citations found: {len(citations)}')
    print(f'  Clusters created: {len(clusters)}')
    
    # Check if clusters have verified citations (frontend logic)
    clusters_with_verified = 0
    for cluster in clusters:
        cluster_citations = cluster.get('citations', [])
        if any(cit.get('verified', False) for cit in cluster_citations):
            clusters_with_verified += 1
    
    print(f'  Clusters with verified citations: {clusters_with_verified}')
    
    print(f'\n🎯 FRONTEND EXPECTATION:')
    print(f'  Should display: "{clusters_with_verified} Cases Found"')
    print(f'  Should show {clusters_with_verified} cluster(s) under "✅ Verified" section')
    
    print(f'\n📋 CLUSTER DETAILS:')
    for i, cluster in enumerate(clusters):
        cluster_id = cluster.get('cluster_id')
        cluster_size = cluster.get('cluster_size')
        case_name = cluster.get('submitted_display_name', 'N/A')
        
        cluster_citations = cluster.get('citations', [])
        verified_in_cluster = sum(1 for cit in cluster_citations if cit.get('verified', False))
        
        print(f'  Cluster {i+1}: {cluster_id}')
        print(f'    Size: {cluster_size}')
        print(f'    Case: {case_name}')
        print(f'    Verified citations: {verified_in_cluster}/{len(cluster_citations)}')
        print(f'    Citations: {[cit.get("citation") for cit in cluster_citations]}')
        print()
    
    if clusters_with_verified > 0:
        print('✅ SUCCESS: Clusters should be visible in frontend!')
        print('If you still see no clusters, try:')
        print('1. Hard refresh the browser (Ctrl+F5)')
        print('2. Clear browser cache')
        print('3. Open browser dev tools and check Network tab for fresh API response')
    else:
        print('❌ ISSUE: No clusters with verified citations found')
        
else:
    print(f'❌ API Error: {response.text}')
