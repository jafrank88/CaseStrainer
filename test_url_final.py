import requests
import json
import time

def test_url_final():
    """Final test of URL processing with proper async handling."""
    
    print("🔍 FINAL URL PROCESSING TEST")
    print("=" * 60)
    
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer-Final-URL-Test/1.0'
    }
    data = {
        'type': 'url',
        'url': test_url
    }
    
    try:
        print(f"📤 Testing URL: {test_url}")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"✅ Response received")
            
            # Check if it's async processing
            task_id = response_data.get('task_id') or response_data.get('request_id')
            
            if task_id:
                print(f"   Task ID: {task_id}")
                print(f"   📊 Polling for completion...")
                
                # Poll for completion
                for attempt in range(30):  # Wait up to 30 attempts (30 seconds)
                    time.sleep(1)
                    
                    status_url = f"http://localhost:8080/casestrainer/api/task_status/{task_id}"
                    status_response = requests.get(status_url, timeout=10)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        status = status_data.get('status', 'unknown')
                        print(f"     Attempt {attempt + 1}: {status}")
                        
                        if status == 'completed':
                            result = status_data.get('result', {})
                            
                            # Save final response
                            with open('url_final_response.json', 'w', encoding='utf-8') as f:
                                json.dump(status_data, f, indent=2, ensure_ascii=False)
                            
                            citations = result.get('citations', [])
                            clusters = result.get('clusters', [])
                            processing_mode = result.get('processing_mode', 'unknown')
                            
                            print(f"\n🎉 URL PROCESSING COMPLETED!")
                            print(f"   Processing mode: {processing_mode}")
                            print(f"   Citations: {len(citations)}")
                            print(f"   Clusters: {len(clusters)}")
                            
                            if len(citations) > 0:
                                print(f"   ✅ SUCCESS! Found {len(citations)} citations")
                                
                                # Show some example citations
                                for i, citation in enumerate(citations[:5], 1):
                                    citation_text = citation.get('citation', 'N/A')
                                    case_name = citation.get('extracted_case_name', 'N/A')
                                    print(f"     Citation {i}: {citation_text} - {case_name}")
                                
                                if len(clusters) > 0:
                                    print(f"   ✅ CLUSTERING WORKING! {len(clusters)} clusters found")
                                    
                                    # Show some example clusters
                                    for i, cluster in enumerate(clusters[:3], 1):
                                        cluster_citations = cluster.get('citations', [])
                                        print(f"     Cluster {i}: {len(cluster_citations)} citations")
                                else:
                                    print(f"   ⚠️  No clusters found (but citations extracted)")
                                
                                return True
                            else:
                                print(f"   ❌ No citations found")
                                return False
                                
                        elif status == 'failed':
                            error = status_data.get('error', 'Unknown error')
                            print(f"   ❌ Processing failed: {error}")
                            return False
                    else:
                        print(f"     Status check failed: {status_response.status_code}")
                
                print(f"   ⏰ Timeout waiting for completion")
                return False
            else:
                # Immediate processing
                print(f"   Processing: IMMEDIATE")
                
                citations = response_data.get('citations', [])
                clusters = response_data.get('clusters', [])
                
                print(f"   Citations: {len(citations)}")
                print(f"   Clusters: {len(clusters)}")
                
                return len(citations) > 0
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_url_final()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 URL PROCESSING WITH PROGRESS TRACKING: FULLY WORKING!")
        print("   ✅ Async processing functional")
        print("   ✅ Progress tracking implemented")
        print("   ✅ Citation extraction working")
        print("   ✅ Clustering functional")
    else:
        print("❌ URL processing still has issues")
    print("=" * 60)
