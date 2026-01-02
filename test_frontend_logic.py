#!/usr/bin/env python3
"""
Test frontend case name display logic based on known data structure
"""

def is_generic_case_name(name):
    """Helper function to detect generic case names"""
    generic_patterns = [
        'Washington State Case',
        'Pacific Reporter Case', 
        'Federal Appeals Case',
        'Federal District Case',
        'U.S. Supreme Court Case',
        'Case ('
    ]
    return any(pattern in name for pattern in generic_patterns)

def get_cluster_submitted_name_old(cluster):
    """Old frontend logic (shows generic names)"""
    if cluster.get('submitted_display_name') and cluster.get('submitted_display_name') != 'N/A':
        return cluster['submitted_display_name']
    return 'N/A'

def get_cluster_submitted_name_new(cluster):
    """New frontend logic (avoids generic names)"""
    # For verified clusters, use canonical names instead of generic extracted names
    has_verified_citation = any(cit.get('verified', False) for cit in cluster.get('citations', []))
    
    if has_verified_citation:
        # Use canonical name for verified clusters to avoid generic placeholders
        rep_citation = cluster.get('citations', [{}])[0]
        if rep_citation.get('canonical_name') and rep_citation['canonical_name'] != 'N/A':
            return rep_citation['canonical_name']
    
    # Try cluster level first (for unverified clusters)
    if (cluster.get('submitted_display_name') and 
        cluster['submitted_display_name'] != 'N/A' and
        not is_generic_case_name(cluster['submitted_display_name'])):
        return cluster['submitted_display_name']
    
    # Fallback to canonical name if available
    rep_citation = cluster.get('citations', [{}])[0]
    if rep_citation.get('canonical_name') and rep_citation['canonical_name'] != 'N/A':
        return rep_citation['canonical_name']
    
    return 'N/A'

# Simulate the cluster data structure from your API response
test_clusters = [
    {
        'cluster_id': 'cluster_1',
        'submitted_display_name': 'Washington State Case',  # Generic name
        'verifying_display_name': 'Ellensburg Cement Products, Inc. v. Kittitas County',
        'citations': [
            {
                'citation': '179 Wn.2d 737',
                'canonical_name': 'Ellensburg Cement Products, Inc. v. Kittitas County',
                'extracted_case_name': 'Washington State Case',  # Generic
                'verified': True
            },
            {
                'citation': '317 P.3d 1037',
                'canonical_name': 'Ellensburg Cement Products, Inc. v. Kittitas County',
                'extracted_case_name': 'Pacific Reporter Case',  # Generic
                'verified': True
            }
        ]
    },
    {
        'cluster_id': 'cluster_2',
        'submitted_display_name': 'Pacific Reporter Case',  # Generic name
        'verifying_display_name': 'Department of Ecology v. Campbell & Gwinn, LLC',
        'citations': [
            {
                'citation': '171 Wn.2d 820',
                'canonical_name': 'PHOENIX DEVELOPMENT, INC. v. City of Woodinville',
                'extracted_case_name': 'Washington State Case',  # Generic
                'verified': True
            },
            {
                'citation': '256 P.3d 1150',
                'canonical_name': 'PHOENIX DEVELOPMENT, INC. v. City of Woodinville',
                'extracted_case_name': 'Pacific Reporter Case',  # Generic
                'verified': True
            }
        ]
    }
]

print('🔍 TESTING CASE NAME DISPLAY FIX')
print('=' * 50)

for i, cluster in enumerate(test_clusters):
    print(f'\n=== CLUSTER {i+1} ===')
    
    old_name = get_cluster_submitted_name_old(cluster)
    new_name = get_cluster_submitted_name_new(cluster)
    
    print(f'Cluster ID: {cluster["cluster_id"]}')
    print(f'Old Logic (shows generic): "{old_name}"')
    print(f'New Logic (shows specific): "{new_name}"')
    
    is_generic_old = is_generic_case_name(old_name)
    is_generic_new = is_generic_case_name(new_name)
    
    print(f'Old shows generic: {is_generic_old}')
    print(f'New shows generic: {is_generic_new}')
    
    if is_generic_old and not is_generic_new:
        print('✅ SUCCESS: Fix eliminates generic case name!')
    elif not is_generic_old:
        print('✅ Already showing specific name')
    else:
        print('❌ Still showing generic name')

print('\n🎯 SUMMARY:')
print('The frontend fix ensures that for verified clusters,')
print('users will see the actual case names from the legal database')
print('instead of generic placeholders like "Washington State Case".')
