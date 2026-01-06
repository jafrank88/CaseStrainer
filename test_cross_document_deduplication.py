#!/usr/bin/env python3
"""
Test cross-document deduplication
"""

from src.cross_document_deduplication import deduplicate_clusters_cross_document

def test_cross_document_deduplication():
    """Test that duplicate clusters across documents are properly deduplicated"""
    
    print("Testing cross-document deduplication:")
    print("=" * 80)
    print()
    
    # Create test clusters that represent the same case from different documents
    clusters = [
        {
            'cluster_id': 'cluster_1',
            'canonical_name': 'Elliott v. Donegan',
            'canonical_date': '2020',
            'extracted_case_name': 'Elliott v. Donegan',
            'extracted_date': '2020',
            'submitted_case_name': 'Elliott v. Donegan',
            'submitted_date': '2020',
            'citations': [
                {'citation': '469 F. Supp. 3d 40', 'text': '469 F. Supp. 3d 40'}
            ],
            'verification_status': 'unverified'
        },
        {
            'cluster_id': 'cluster_2',
            'canonical_name': 'Elliott v. Donegan',
            'canonical_date': '2020',
            'extracted_case_name': 'Elliott v. Donegan',
            'extracted_date': '2020',
            'submitted_case_name': 'Elliott v. Donegan',
            'submitted_date': '2020',
            'citations': [
                {'citation': '469 F. Supp. 3d 40', 'text': '469 F. Supp. 3d 40'}
            ],
            'verification_status': 'unverified'
        },
        {
            'cluster_id': 'cluster_3',
            'canonical_name': 'Carroll v. Trump',
            'canonical_date': '2023',
            'extracted_case_name': 'Carroll v. Trump',
            'extracted_date': '2023',
            'submitted_case_name': 'Carroll v. Trump',
            'submitted_date': '2023',
            'citations': [
                {'citation': '685 F. Supp. 3d 267', 'text': '685 F. Supp. 3d 267'}
            ],
            'verification_status': 'unverified'
        }
    ]
    
    print(f"Input clusters: {len(clusters)}")
    for i, cluster in enumerate(clusters):
        print(f"  {i+1}. {cluster['extracted_case_name']}, {cluster['extracted_date']}")
        print(f"     Citations: {[c['citation'] for c in cluster['citations']]}")
    print()
    
    # Apply deduplication
    deduplicated = deduplicate_clusters_cross_document(clusters)
    
    print(f"After deduplication: {len(deduplicated)}")
    print()
    
    for i, cluster in enumerate(deduplicated):
        print(f"  {i+1}. {cluster['extracted_case_name']}, {cluster['extracted_date']}")
        print(f"     Citations: {[c['citation'] for c in cluster['citations']]}")
        
        if cluster.get('cross_document_merge'):
            print(f"     *** Merged from {cluster.get('merge_source_count')} documents ***")
            print(f"     Source: {cluster.get('submitted_case_name')}")
        print()
    
    # Verify results
    assert len(deduplicated) == 2, f"Expected 2 clusters, got {len(deduplicated)}"
    
    # Check Elliott v. Donegan was merged
    elliott_clusters = [c for c in deduplicated if 'Elliott' in c.get('extracted_case_name', '')]
    assert len(elliott_clusters) == 1, "Elliott v. Donegan should be merged into one cluster"
    assert elliott_clusters[0].get('cross_document_merge'), "Should be marked as merged"
    
    # Check Carroll v. Trump is unchanged
    carroll_clusters = [c for c in deduplicated if 'Carroll' in c.get('extracted_case_name', '')]
    assert len(carroll_clusters) == 1, "Carroll v. Trump should remain as one cluster"
    assert not carroll_clusters[0].get('cross_document_merge'), "Should not be marked as merged"
    
    print("✅ All tests passed!")
    print()
    print("Cross-document deduplication successfully:")
    print("- Merges duplicate clusters from different documents")
    print("- Preserves unique clusters")
    print("- Tracks source document information")

if __name__ == "__main__":
    test_cross_document_deduplication()
