#!/usr/bin/env python3
"""
Debug script to test the normalize_cluster_dict function directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.schemas.cluster import normalize_cluster_dict

def test_normalize_cluster_dict():
    """Test the normalize_cluster_dict function with sample data"""
    print("🔍 Testing normalize_cluster_dict function...")
    
    # Sample cluster from clustering master
    sample_cluster = {
        'cluster_id': 'cluster_1',
        'cluster_case_name': 'Smith v. Jones',
        'cluster_year': '2023',
        'cluster_size': 1,
        'citations': [{'citation': '123 F.3d 456', 'verified': False}],
        'confidence': 0.5,
        'verification_status': 'not_verified',
        'verification_source': None,
        'canonical_name': None,
        'canonical_date': None,
        'metadata': {'cluster_type': 'proximity_based'},
        'cluster_members': ['123 F.3d 456'],
        'has_name_mismatch': False,
        'has_date_mismatch': False,
        'mismatch_indices': []
    }
    
    print(f"\n📋 Input cluster:")
    print(f"   Keys: {list(sample_cluster.keys())}")
    print(f"   cluster_case_name: {sample_cluster.get('cluster_case_name')}")
    print(f"   cluster_year: {sample_cluster.get('cluster_year')}")
    print(f"   cluster_size: {sample_cluster.get('cluster_size')}")
    
    # Normalize the cluster
    normalized = normalize_cluster_dict(sample_cluster)
    
    print(f"\n📋 Normalized cluster:")
    print(f"   Keys: {list(normalized.keys())}")
    print(f"   cluster_case_name: {normalized.get('cluster_case_name')}")
    print(f"   cluster_year: {normalized.get('cluster_year')}")
    print(f"   cluster_size: {normalized.get('cluster_size')}")
    
    # Check if important fields are preserved
    expected_fields = ['cluster_id', 'cluster_case_name', 'cluster_year', 'cluster_size', 'citations']
    missing_fields = [field for field in expected_fields if field not in normalized.keys()]
    
    if missing_fields:
        print(f"\n❌ Missing fields: {missing_fields}")
    else:
        print(f"\n✅ All expected fields preserved")
    
    return normalized

if __name__ == "__main__":
    test_normalize_cluster_dict()
