import requests
import json
import time

def test_url_detailed_debug():
    """Detailed debug of URL processing to see exactly what's happening."""
    
    print("🔍 DETAILED URL PROCESSING DEBUG")
    print("=" * 60)
    
    # Test with a shorter URL first to see if immediate processing works
    test_urls = [
        "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    ]
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\nTest {i}: {test_url}")
        
        url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CaseStrainer-Detailed-Debug/1.0'
        }
        data = {
            'type': 'url',
            'url': test_url
        }
        
        try:
            print("📤 Sending request...")
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            if response.status_code == 200:
                response_data = response.json()
                
                print(f"✅ Response received")
                print(f"   Status: {response_data.get('status', 'unknown')}")
                print(f"   Success: {response_data.get('success', False)}")
                
                # Check if it's immediate or async processing
                if 'result' in response_data:
                    print("   Processing: IMMEDIATE")
                    result = response_data['result']
                    
                    citations = result.get('citations', [])
                    clusters = result.get('clusters', [])
                    processing_strategy = result.get('processing_strategy', 'N/A')
                    
                    print(f"   Citations: {len(citations)}")
                    print(f"   Clusters: {len(clusters)}")
                    print(f"   Strategy: {processing_strategy}")
                    
                    if len(citations) > 0:
                        print("   ✅ IMMEDIATE PROCESSING WORKING!")
                        
                        # Show some examples
                        for j, citation in enumerate(citations[:3], 1):
                            citation_text = citation.get('citation', 'N/A')
                            case_name = citation.get('extracted_case_name', 'N/A')
                            print(f"     Citation {j}: {citation_text} - {case_name}")
                        
                        if len(clusters) > 0:
                            print(f"   ✅ CLUSTERING WORKING! {len(clusters)} clusters")
                            for j, cluster in enumerate(clusters[:2], 1):
                                cluster_id = cluster.get('cluster_id', 'N/A')
                                cluster_citations = cluster.get('citations', [])
                                print(f"     Cluster {j}: {cluster_id} - {cluster_citations}")
                        else:
                            print("   ❌ No clusters found")
                    else:
                        print("   ❌ No citations found in immediate processing")
                        
                else:
                    print("   Processing: ASYNC")
                    task_id = response_data.get('request_id') or response_data.get('task_id')
                    
                    if task_id:
                        print(f"   Task ID: {task_id}")
                        print("   ⏳ Waiting for async completion...")
                        
                        time.sleep(3)
                        
                        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
                        status_response = requests.get(status_url, timeout=30)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            citations = status_data.get('citations', [])
                            clusters = status_data.get('clusters', [])
                            
                            print(f"   Async Citations: {len(citations)}")
                            print(f"   Async Clusters: {len(clusters)}")
                            
                            if len(citations) > 0:
                                print("   ✅ ASYNC PROCESSING WORKING!")
                            else:
                                print("   ❌ Async processing also failed")
                        else:
                            print(f"   ❌ Status check failed: {status_response.status_code}")
                    else:
                        print("   ❌ No task ID for async processing")
                
                # Save response for analysis
                filename = f'url_debug_test_{i}_response.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                print(f"   📄 Response saved to {filename}")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_url_detailed_debug()
