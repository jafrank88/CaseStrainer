import sys
import os
sys.path.append('src')

def test_citation_service_direct():
    """Test the CitationService directly with extracted PDF content."""
    
    print("🔍 TESTING CITATION SERVICE DIRECTLY")
    print("=" * 60)
    
    # Step 1: Get PDF content
    print("Step 1: Extracting PDF content...")
    try:
        from src.progress_manager import fetch_url_content
        
        test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
        content = fetch_url_content(test_url)
        
        if content and len(content.strip()) > 0:
            print(f"  ✅ PDF content: {len(content)} characters")
            
            # Step 2: Test CitationService directly
            print("\nStep 2: Testing CitationService with PDF content...")
            
            from src.api.services.citation_service import CitationService
            
            citation_service = CitationService()
            
            # Prepare input data like the URL processor would
            input_data = {
                'text': content,
                'type': 'text',
                'source': 'url_test'
            }
            
            print(f"  Processing {len(content)} characters through CitationService...")
            
            # Test the citation processing using the immediate processing method
            result = citation_service.process_immediately(input_data)
            
            print(f"  CitationService result: {result.get('status', 'unknown')}")
            
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"  Citations found: {len(citations)}")
            print(f"  Clusters found: {len(clusters)}")
            
            if len(citations) > 0:
                print("  ✅ CitationService is working!")
                
                # Show some examples
                for i, citation in enumerate(citations[:5], 1):
                    citation_text = citation.get('citation', 'N/A')
                    case_name = citation.get('extracted_case_name', 'N/A')
                    print(f"    Citation {i}: {citation_text} - {case_name}")
                
                if len(clusters) > 0:
                    print(f"  ✅ Clustering is working! {len(clusters)} clusters found")
                    
                    # Show some cluster examples
                    for i, cluster in enumerate(clusters[:3], 1):
                        cluster_id = cluster.get('cluster_id', 'N/A')
                        cluster_citations = cluster.get('citations', [])
                        print(f"    Cluster {i}: {cluster_id} - {cluster_citations}")
                else:
                    print("  ❌ No clusters found - clustering issue")
            else:
                print("  ❌ CitationService found no citations")
                print("  This is the root cause of the problem")
                
        else:
            print("  ❌ No PDF content extracted")
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_citation_service_direct()
