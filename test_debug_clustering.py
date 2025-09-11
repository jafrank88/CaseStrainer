#!/usr/bin/env python3
"""
Debug the specific clustering issue with DeSean v. Sanger and State v. Ervin.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_debug_clustering():
    """Debug the specific clustering issue."""
    
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010)."""
    
    print("=== Debugging Clustering Issue ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from src.enhanced_clustering import EnhancedCitationClusterer, ClusteringConfig
        
        # Test with different proximity thresholds
        for threshold in [30, 50, 100]:
            print(f"🔍 Testing with proximity threshold: {threshold}")
            config = ClusteringConfig(debug_mode=True, proximity_threshold=threshold)
            clusterer = EnhancedCitationClusterer(config)
            
            # Mock citations with proper case names and years
            mock_citations = [
                {'citation': '2 Wn. 3d 329', 'extracted_case_name': 'DeSean v. Sanger', 'extracted_date': '2023'},
                {'citation': '536 P.3d 191', 'extracted_case_name': 'DeSean v. Sanger', 'extracted_date': '2023'},
                {'citation': '169 Wn.2d 815', 'extracted_case_name': 'State v. Ervin', 'extracted_date': '2010'},
                {'citation': '239 P.3d 354', 'extracted_case_name': 'State v. Ervin', 'extracted_date': '2010'}
            ]
            
            print("  Mock citations:")
            for citation in mock_citations:
                print(f"    '{citation['citation']}' → '{citation['extracted_case_name']}' ({citation['extracted_date']})")
            
            # Debug: Check citation structure
            print("  Citation structure debug:")
            for i, citation in enumerate(mock_citations):
                print(f"    Citation {i+1}: {citation}")
                print(f"      Has extracted_case_name: {hasattr(citation, 'extracted_case_name')}")
                print(f"      Has extracted_date: {hasattr(citation, 'extracted_date')}")
                print(f"      extracted_case_name: {getattr(citation, 'extracted_case_name', 'NOT_FOUND')}")
                print(f"      extracted_date: {getattr(citation, 'extracted_date', 'NOT_FOUND')}")
            
            # Test case name/year grouping directly
            print("  Testing case name/year grouping directly:")
            case_year_groups = clusterer._group_by_case_name_and_year(mock_citations)
            print(f"    Case name/year groups: {len(case_year_groups)}")
            for i, group in enumerate(case_year_groups):
                print(f"      Group {i+1}: {[c['citation'] for c in group]}")
            
            # Test parallel detection
            parallel_groups = clusterer._detect_parallel_citations_enhanced(mock_citations, test_text)
            print(f"  Parallel groups found: {len(parallel_groups)}")
            for i, group in enumerate(parallel_groups):
                print(f"    Group {i+1}: {[c['citation'] for c in group]}")
            
            # Test full clustering
            clusters = clusterer.cluster_citations(mock_citations, test_text, f"test_{threshold}")
            print(f"  Final clusters: {len(clusters)}")
            for i, cluster in enumerate(clusters):
                print(f"    Cluster {i+1}: '{cluster.get('case_name')}' ({cluster.get('year')}) - {len(cluster.get('citations', []))} citations")
            
            print()
        
        print("🎯 EXPECTED RESULTS:")
        print("  - Should create 2 clusters: DeSean v. Sanger (2023) and State v. Ervin (2010)")
        print("  - Each cluster should have 2 citations")
        print("  - Proximity threshold should separate the two case blocks")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_clustering()
