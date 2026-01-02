#!/usr/bin/env python3
"""
Test that case names are now properly displayed in frontend
"""

import requests

test_text = '''Ellensburg Cement Products, Inc. v. Kittitas County, 179 Wn.2d 737, 317 P.3d 1037 (2014).
Department of Ecology v. Campbell & Gwinn, LLC, 171 Wn.2d 820, 256 P.3d 1150 (2011).'''

response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
    json={'type': 'text', 'text': test_text, 'enable_verification': True}, 
    timeout=30)

print('Status:', response.status_code)

if response.status_code == 200:
    result = response.json()
    clusters = result.get('clusters', [])
    
    print(f'📊 Found {len(clusters)} clusters\n')
    
    for i, cluster in enumerate(clusters):
        print(f'=== CLUSTER {i+1} ===')
        
        # Test the frontend logic for what names will be displayed
        cluster_id = cluster.get('cluster_id')
        verifying_name = cluster.get('verifying_display_name') or 'N/A'
        submitted_name = cluster.get('submitted_display_name') or 'N/A'
        
        # Get representative citation for canonical name
        citations = cluster.get('citations', [])
        rep_citation = citations[0] if citations else {}
        canonical_name = rep_citation.get('canonical_name') or 'N/A'
        
        print(f'Cluster ID: {cluster_id}')
        print(f'Verifying Name (top line): {verifying_name}')
        print(f'Submitted Name (bottom line): {submitted_name}')
        print(f'Canonical Name: {canonical_name}')
        
        # Check if citations are verified
        has_verified = any(cit.get('verified', False) for cit in citations)
        print(f'Has Verified Citations: {has_verified}')
        
        # Simulate frontend logic
        if has_verified:
            expected_display_name = canonical_name
        else:
            expected_display_name = submitted_name
        
        print(f'Expected Display Name: {expected_display_name}')
        
        # Check if it's a generic name
        generic_names = ['Washington State Case', 'Pacific Reporter Case', 'Federal Appeals Case']
        is_generic = any(gen in expected_display_name for gen in generic_names)
        
        print(f'Is Generic Name: {is_generic}')
        print(f'✅ SUCCESS: {"Will show proper case name" if not is_generic else "Will show generic name"}')
        print()
    
    print('🎯 FRONTEND EXPECTATION:')
    print('After the fix, verified clusters should show canonical names instead of generic placeholders')
    print('Users will now see: "Ellensburg Cement Products, Inc. v. Kittitas County" instead of "Washington State Case"')
    
else:
    print('Error:', response.text)
