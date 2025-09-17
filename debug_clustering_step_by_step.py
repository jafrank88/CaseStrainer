import sys
import os
sys.path.append('src')

def debug_clustering_step_by_step():
    """Debug each step of the clustering process to find where it fails."""
    
    test_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    print("🔍 STEP-BY-STEP CLUSTERING DEBUG")
    print("=" * 60)
    
    # Step 1: Extract citations using UnifiedSyncProcessor
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        
        processor = UnifiedSyncProcessor()
        
        print("Step 1: Testing _apply_clustering_with_verification directly...")
        
        # First get citations
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        citation_processor = UnifiedCitationProcessorV2()
        citations = citation_processor._extract_with_regex(test_text)
        
        print(f"  Extracted {len(citations)} citations")
        
        # Test the clustering method directly
        clusters = processor._apply_clustering_with_verification(
            citations=citations,
            text=test_text,
            request_id="debug_test",
            options={},
            enable_verification=False
        )
        
        print(f"  Clustering returned: {type(clusters)}")
        print(f"  Number of clusters: {len(clusters) if clusters else 0}")
        
        if clusters:
            print("  ✅ Clustering method works!")
            for i, cluster in enumerate(clusters, 1):
                print(f"    Cluster {i}: {cluster}")
        else:
            print("  ❌ Clustering method returned empty")
        
        print()
        
        # Step 2: Test cluster conversion
        if clusters:
            print("Step 2: Testing _convert_clusters_to_dicts...")
            clusters_dict = processor._convert_clusters_to_dicts(clusters, citations)
            
            print(f"  Conversion returned: {type(clusters_dict)}")
            print(f"  Number of cluster dicts: {len(clusters_dict) if clusters_dict else 0}")
            
            if clusters_dict:
                print("  ✅ Cluster conversion works!")
                for i, cluster_dict in enumerate(clusters_dict, 1):
                    print(f"    Cluster dict {i}: {cluster_dict}")
            else:
                print("  ❌ Cluster conversion returned empty")
        
        print()
        
        # Step 3: Test full processing
        print("Step 3: Testing full process_text_unified...")
        result = processor.process_text_unified(test_text, {})
        
        print(f"  Full processing result keys: {list(result.keys())}")
        print(f"  Citations: {len(result.get('citations', []))}")
        print(f"  Clusters: {len(result.get('clusters', []))}")
        print(f"  Strategy: {result.get('processing_strategy', 'N/A')}")
        
        if result.get('clusters'):
            print("  ✅ Full processing includes clusters!")
        else:
            print("  ❌ Full processing missing clusters")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    debug_clustering_step_by_step()
