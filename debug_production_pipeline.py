import sys
import os
sys.path.append('src')

def debug_production_pipeline():
    """Debug the exact production pipeline to see where clusters are lost."""
    
    # Test text with Bostain parallel citations
    test_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    print("=" * 80)
    print("🔍 DEBUGGING PRODUCTION PIPELINE")
    print("=" * 80)
    
    print(f"Text length: {len(test_text)} characters")
    print("Expected: Should trigger full processing with clustering")
    print()
    
    # Step 1: Test UnifiedSyncProcessor directly
    print("Step 1: Testing UnifiedSyncProcessor directly...")
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        
        processor = UnifiedSyncProcessor()
        result = processor.process_text_unified(test_text, {})
        
        print(f"Sync processor result keys: {list(result.keys())}")
        print(f"Citations found: {len(result.get('citations', []))}")
        print(f"Clusters found: {len(result.get('clusters', []))}")
        print(f"Processing strategy: {result.get('processing_strategy', 'N/A')}")
        
        if result.get('clusters'):
            print("✅ Clusters found in sync processor!")
            for i, cluster in enumerate(result['clusters'], 1):
                print(f"  Cluster {i}: {cluster}")
        else:
            print("❌ No clusters in sync processor result")
            
        # Save sync processor result
        import json
        with open('sync_processor_debug.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"❌ Sync processor test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Step 2: Test UnifiedInputProcessor
    print("Step 2: Testing UnifiedInputProcessor...")
    try:
        from unified_input_processor import UnifiedInputProcessor
        
        input_processor = UnifiedInputProcessor()
        result = input_processor.process_any_input(test_text, 'text', 'debug_test')
        
        print(f"Input processor result keys: {list(result.keys())}")
        print(f"Success: {result.get('success', False)}")
        
        if 'citations' in result:
            print(f"Citations found: {len(result.get('citations', []))}")
            print(f"Clusters found: {len(result.get('clusters', []))}")
        
        # Save input processor result
        with open('input_processor_debug.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"❌ Input processor test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Step 3: Test clustering function directly
    print("Step 3: Testing clustering function directly...")
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from unified_citation_clustering import cluster_citations_unified
        
        # Extract citations first
        processor = UnifiedCitationProcessorV2()
        citations = processor._extract_with_regex(test_text)
        
        print(f"Extracted {len(citations)} citations")
        
        # Test clustering directly
        clusters = cluster_citations_unified(citations, test_text, enable_verification=False)
        
        print(f"Direct clustering returned: {type(clusters)}")
        print(f"Number of clusters: {len(clusters) if clusters else 0}")
        
        if clusters:
            print("✅ Direct clustering works!")
            for i, cluster in enumerate(clusters, 1):
                print(f"  Cluster {i}: {cluster}")
        else:
            print("❌ Direct clustering returned no results")
            
    except Exception as e:
        print(f"❌ Direct clustering test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)

if __name__ == "__main__":
    debug_production_pipeline()
