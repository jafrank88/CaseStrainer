import sys
import os
sys.path.append('src')

def test_sync_processor_direct():
    """Test UnifiedSyncProcessor directly with PDF content."""
    
    print("🔍 TESTING UNIFIED SYNC PROCESSOR DIRECTLY")
    print("=" * 60)
    
    # Step 1: Get PDF content
    print("Step 1: Extracting PDF content...")
    try:
        from src.progress_manager import fetch_url_content
        
        test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
        content = fetch_url_content(test_url)
        
        if content and len(content.strip()) > 0:
            print(f"  ✅ PDF content: {len(content)} characters")
            
            # Step 2: Test UnifiedSyncProcessor directly
            print("\nStep 2: Testing UnifiedSyncProcessor with PDF content...")
            
            from src.unified_sync_processor import UnifiedSyncProcessor
            
            sync_processor = UnifiedSyncProcessor()
            
            print(f"  Processing {len(content)} characters through UnifiedSyncProcessor...")
            
            # Test the sync processor
            result = sync_processor.process_text_unified(content, {})
            
            print(f"  UnifiedSyncProcessor result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            
            if isinstance(result, dict):
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                processing_strategy = result.get('processing_strategy', 'N/A')
                success = result.get('success', False)
                
                print(f"  Success: {success}")
                print(f"  Citations found: {len(citations)}")
                print(f"  Clusters found: {len(clusters)}")
                print(f"  Processing strategy: {processing_strategy}")
                
                if len(citations) > 0:
                    print("  ✅ UnifiedSyncProcessor is working!")
                    
                    # Show some examples
                    for i, citation in enumerate(citations[:5], 1):
                        if isinstance(citation, dict):
                            citation_text = citation.get('citation', 'N/A')
                            case_name = citation.get('extracted_case_name', 'N/A')
                        else:
                            citation_text = str(citation)
                            case_name = 'N/A'
                        print(f"    Citation {i}: {citation_text} - {case_name}")
                    
                    if len(clusters) > 0:
                        print(f"  ✅ Clustering is working! {len(clusters)} clusters found")
                        
                        # Show some cluster examples
                        for i, cluster in enumerate(clusters[:3], 1):
                            if isinstance(cluster, dict):
                                cluster_id = cluster.get('cluster_id', 'N/A')
                                cluster_citations = cluster.get('citations', [])
                            else:
                                cluster_id = str(cluster)
                                cluster_citations = []
                            print(f"    Cluster {i}: {cluster_id} - {cluster_citations}")
                    else:
                        print("  ❌ No clusters found - clustering issue")
                else:
                    print("  ❌ UnifiedSyncProcessor found no citations")
                    print("  This is the root cause of the problem")
                    
                    # Check if there's an error message
                    error = result.get('error')
                    if error:
                        print(f"  Error: {error}")
                    
                    # Check processing strategy to see which path was taken
                    print(f"  Strategy used: {processing_strategy}")
                    
            else:
                print(f"  ❌ UnifiedSyncProcessor returned unexpected type: {type(result)}")
                print(f"  Result: {result}")
                
        else:
            print("  ❌ No PDF content extracted")
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_sync_processor_direct()
