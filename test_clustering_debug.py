#!/usr/bin/env python3
"""
Test clustering master directly to see why no clusters are being created
"""

import sys
sys.path.append('/app')

from src.unified_clustering_master import cluster_citations_unified_master

# Test data from your actual results - these should cluster as parallel citations
test_citations = [
    {
        'citation': '179 Wn.2d 737',
        'case_name': 'Ellensburg Cement Products, Inc. v. Kittitas County',
        'extracted_case_name': 'Washington State Case',
        'extracted_date': '2014',
        'canonical_name': 'Ellensburg Cement Products, Inc. v. Kittitas County',
        'canonical_date': '2014-02-06',
        'parallel_citations': ['317 P.3d 1037'],
        'verified': True
    },
    {
        'citation': '317 P.3d 1037', 
        'case_name': 'Ellensburg Cement Products, Inc. v. Kittitas County',
        'extracted_case_name': 'Pacific Reporter Case',
        'extracted_date': '2014',
        'canonical_name': 'Ellensburg Cement Products, Inc. v. Kittitas County',
        'canonical_date': '2014-02-06',
        'parallel_citations': ['179 Wn.2d 737'],
        'verified': True
    },
    {
        'citation': '171 Wn.2d 820',
        'case_name': 'Department of Ecology v. Campbell & Gwinn, LLC',
        'extracted_case_name': 'Washington State Case', 
        'extracted_date': '2011',
        'canonical_name': 'Department of Ecology v. Campbell & Gwinn, LLC',
        'canonical_date': '2011-09-15',
        'parallel_citations': ['256 P.3d 1150'],
        'verified': True
    },
    {
        'citation': '256 P.3d 1150',
        'case_name': 'Department of Ecology v. Campbell & Gwinn, LLC', 
        'extracted_case_name': 'Pacific Reporter Case',
        'extracted_date': '2011',
        'canonical_name': 'Department of Ecology v. Campbell & Gwinn, LLC',
        'canonical_date': '2011-09-15',
        'parallel_citations': ['171 Wn.2d 820'],
        'verified': True
    }
]

print("Testing clustering master directly...")
print(f"Input: {len(test_citations)} citations with parallel relationships")

try:
    clusters = cluster_citations_unified_master(
        test_citations,
        original_text="Test text with citations",
        enable_verification=False
    )
    
    print(f"Output: {len(clusters)} clusters")
    for i, cluster in enumerate(clusters):
        print(f"Cluster {i+1}: {cluster}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
