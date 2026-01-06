#!/usr/bin/env python3
"""
Test the improved cross-document deduplication with stricter criteria
"""

from src.cross_document_deduplication import deduplicate_clusters_cross_document

def test_strict_deduplication():
    """Test that different cases are not merged even with partial name similarity"""
    
    print("Testing stricter cross-document deduplication:")
    print("=" * 80)
    print()
    
    # Create test clusters that should NOT be merged
    clusters = [
        {
            'cluster_id': 'cluster_1',
            'canonical_name': 'Doe v. City of New York',
            'canonical_date': '2022',
            'extracted_case_name': 'Doe v. City of New York',
            'extracted_date': '2022',
            'submitted_case_name': 'Doe v. City of New York',
            'submitted_date': '2022',
            'citations': [
                {'citation': '2022 WL 15153410', 'text': '2022 WL 15153410'}
            ],
            'verification_status': 'unverified'
        },
        {
            'cluster_id': 'cluster_2',
            'canonical_name': 'In re Search Warrant (Gunn)',
            'canonical_date': '1988',
            'extracted_case_name': 'In re Search Warrant (Gunn)',
            'extracted_date': '1988',
            'submitted_case_name': 'Doe v. City of New York',  # Note: Different extracted name
            'submitted_date': '2022',
            'citations': [
                {'citation': '855 F.2d 569', 'text': '855 F.2d 569'}
            ],
            'verification_status': 'unverified'
        },
        {
            'cluster_id': 'cluster_3',
            'canonical_name': 'Doe v. City of New York',
            'canonical_date': '2022',
            'extracted_case_name': 'Doe v. City of New York',
            'extracted_date': '2022',
            'submitted_case_name': 'Doe v. City of New York',
            'submitted_date': '2022',
            'citations': [
                {'citation': '2022 WL 15153410', 'text': '2022 WL 15153410'}
            ],
            'verification_status': 'unverified'
        }
    ]
    
    print(f"Input clusters: {len(clusters)}")
    for i, cluster in enumerate(clusters):
        print(f"  {i+1}. {cluster['canonical_name']}, {cluster['canonical_date']}")
        print(f"     Citation: {cluster['citations'][0]['citation']}")
    print()
    
    # Apply deduplication
    deduplicated = deduplicate_clusters_cross_document(clusters)
    
    print(f"After deduplication: {len(deduplicated)}")
    print()
    
    for i, cluster in enumerate(deduplicated):
        print(f"  {i+1}. {cluster['canonical_name']}, {cluster['canonical_date']}")
        print(f"     Citation: {cluster['citations'][0]['citation']}")
        
        if cluster.get('cross_document_merge'):
            print(f"     *** Merged from {cluster.get('merge_source_count')} documents ***")
        print()
    
    # Verify results
    assert len(deduplicated) == 2, f"Expected 2 clusters, got {len(deduplicated)}"
    
    # Check that Doe v. City of New York (2022) was merged
    doe_clusters = [c for c in deduplicated if 'Doe v. City of New York' in c.get('canonical_name', '') and '2022' in c.get('canonical_date', '')]
    assert len(doe_clusters) == 1, "Doe v. City of New York (2022) should be merged"
    assert doe_clusters[0].get('cross_document_merge'), "Should be marked as merged"
    
    # Check that In re Search Warrant (Gunn) was NOT merged
    gunn_clusters = [c for c in deduplicated if 'Search Warrant' in c.get('canonical_name', '')]
    assert len(gunn_clusters) == 1, "In re Search Warrant (Gunn) should remain separate"
    assert not gunn_clusters[0].get('cross_document_merge'), "Should not be marked as merged"
    
    print("✅ All tests passed!")
    print()
    print("Stricter deduplication correctly:")
    print("- Prevents merging different cases with similar names")
    print("- Considers year differences (1988 vs 2022)")
    print("- Only merges truly identical cases")

if __name__ == "__main__":
    test_strict_deduplication()
