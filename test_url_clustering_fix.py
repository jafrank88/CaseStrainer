import requests
import json
import time

def test_url_clustering_fix():
    """Test if URL processing now uses the fixed clustering system."""
    
    print("🔧 TESTING URL CLUSTERING FIX")
    print("=" * 60)
    print("Testing with the same Washington court PDF that showed 0 clusters")
    print("Expected: Should now find clusters using the unified clustering system")
    print()
    
    # Use the same URL that was showing 0 clusters
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer-URL-Clustering-Fix-Test/1.0'
    }
    data = {
        'type': 'url',
        'url': test_url
    }
    
    try:
        print("📤 Sending URL analysis request...")
        response = requests.post(url, headers=headers, json=data, timeout=300)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Handle async processing
            if 'result' in response_data:
                result = response_data['result']
            else:
                # Async processing - poll for results
                task_id = response_data.get('request_id')
                if task_id:
                    print(f"📋 Async processing started, task ID: {task_id}")
                    print("⏳ Polling for results...")
                    
                    # Poll for completion
                    max_polls = 30
                    poll_count = 0
                    
                    while poll_count < max_polls:
                        time.sleep(2)
                        poll_count += 1
                        
                        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
                        status_response = requests.get(status_url, timeout=30)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if status_data.get('status') == 'completed':
                                result = status_data
                                break
                            elif status_data.get('status') == 'failed':
                                print(f"❌ Task failed: {status_data.get('message', 'Unknown error')}")
                                return False
                            else:
                                print(f"⏳ Still processing... ({poll_count}/{max_polls})")
                        else:
                            print(f"❌ Status check failed: {status_response.status_code}")
                            return False
                    
                    if poll_count >= max_polls:
                        print("❌ Timeout waiting for results")
                        return False
                else:
                    print("❌ No task ID received")
                    return False
            
            # Analyze results
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"✅ URL Processing completed")
            print(f"   Citations found: {len(citations)}")
            print(f"   Clusters found: {len(clusters)}")
            print()
            
            if clusters:
                print(f"🎯 CLUSTERS FOUND: {len(clusters)}")
                for i, cluster in enumerate(clusters, 1):
                    cluster_id = cluster.get('cluster_id', 'N/A')
                    cluster_citations = cluster.get('citations', [])
                    print(f"   Cluster {i}: {cluster_id}")
                    print(f"     Citations: {cluster_citations}")
                    
                    # Check for parallel citations (clusters with multiple citations)
                    if len(cluster_citations) >= 2:
                        print(f"     ✅ PARALLEL CITATIONS DETECTED!")
                print()
                
                print("🎉 SUCCESS: URL clustering is now working!")
                print("   ✅ The unified clustering system is being used")
                print("   ✅ Clusters are being created for URL processing")
                
            else:
                print("❌ NO CLUSTERS FOUND")
                print("   The fix may not have taken effect yet")
                print("   Or this particular document may not have parallel citations")
            
            # Save response for analysis
            with open('url_clustering_fix_response.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("📄 Response saved to url_clustering_fix_response.json")
            
            return len(clusters) > 0
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)

if __name__ == "__main__":
    clustering_working = test_url_clustering_fix()
    
    print("\n🎯 FINAL URL CLUSTERING STATUS:")
    if clustering_working:
        print("✅ URL CLUSTERING IS NOW WORKING!")
        print("   The unified clustering system is being used for URL processing")
    else:
        print("❌ URL CLUSTERING STILL NOT WORKING")
        print("   May need additional investigation")
