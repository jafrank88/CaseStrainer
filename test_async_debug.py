import sys
import os
sys.path.append('src')

def test_async_debug():
    """Debug the async processing directly."""
    
    print("🔍 TESTING ASYNC PROCESSING DIRECTLY")
    print("=" * 60)
    
    try:
        from src.progress_manager import process_citation_task_direct
        
        # Test URL processing directly
        test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
        input_data = {'url': test_url}
        
        print(f"📤 Testing direct async processing with URL: {test_url}")
        
        result = process_citation_task_direct('test_task_123', 'url', input_data)
        
        print(f"✅ Direct async processing completed")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Status: {result.get('status', 'unknown')}")
        
        if result.get('success'):
            result_data = result.get('result', {})
            citations = result_data.get('citations', [])
            clusters = result_data.get('clusters', [])
            processing_mode = result_data.get('processing_mode', 'unknown')
            
            print(f"   Processing mode: {processing_mode}")
            print(f"   Citations: {len(citations)}")
            print(f"   Clusters: {len(clusters)}")
            
            if len(citations) > 0:
                print("   ✅ Direct async processing working!")
                
                # Show some examples
                for i, citation in enumerate(citations[:5], 1):
                    citation_text = citation.get('citation', 'N/A')
                    case_name = citation.get('extracted_case_name', 'N/A')
                    print(f"     Citation {i}: {citation_text} - {case_name}")
                
                if len(clusters) > 0:
                    print(f"   ✅ Clustering working! {len(clusters)} clusters")
                    for i, cluster in enumerate(clusters[:3], 1):
                        cluster_id = cluster.get('cluster_id', 'N/A')
                        cluster_citations = cluster.get('citations', [])
                        print(f"     Cluster {i}: {cluster_id} - {cluster_citations}")
                else:
                    print("   ❌ No clusters found")
            else:
                print("   ❌ No citations found in direct async processing")
        else:
            error = result.get('error', 'Unknown error')
            print(f"   ❌ Direct async processing failed: {error}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_async_debug()
