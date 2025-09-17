import requests
import json
import time

def test_async_processing():
    """Test if async processing is working properly."""
    
    print("🔍 TESTING ASYNC PROCESSING")
    print("=" * 60)
    
    # Test with a large text that should trigger async processing
    # Use a very long text to force async processing
    large_text = """
    This is a test of async processing with multiple legal citations to ensure proper clustering.
    
    Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015). This case deals with agricultural worker rights.
    
    Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430 P.3d 655 (2018). This case involves environmental regulations.
    
    State v. Blake, 197 Wn.2d 170, 481 P.3d 521 (2021). This is a significant criminal law case.
    
    Bostain v. Food Express, Inc., 159 Wn.2d 700, 153 P.3d 846 (2007). This case involves employment law.
    
    """ * 50  # Repeat 50 times to make it very large
    
    print(f"📝 Testing with large text: {len(large_text)} characters")
    print("   This should trigger async processing due to size")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer-Async-Test/1.0'
    }
    data = {
        'type': 'text',
        'text': large_text
    }
    
    try:
        print("📤 Sending large text for async processing...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"✅ Response received")
            print(f"   Status: {response_data.get('status', 'unknown')}")
            print(f"   Success: {response_data.get('success', False)}")
            
            # Check if it's async processing
            if 'result' in response_data:
                print("   Processing: IMMEDIATE (unexpected for large text)")
                result = response_data['result']
                
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"   Citations: {len(citations)}")
                print(f"   Clusters: {len(clusters)}")
                
                if len(citations) > 0:
                    print("   ✅ Immediate processing working for large text")
                else:
                    print("   ❌ No citations found in immediate processing")
                    
            else:
                print("   Processing: ASYNC (expected for large text)")
                task_id = response_data.get('request_id') or response_data.get('task_id')
                
                if task_id:
                    print(f"   Task ID: {task_id}")
                    print("   ⏳ Polling for async completion...")
                    
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
                            status = status_data.get('status', 'unknown')
                            
                            print(f"   Poll {poll_count}: Status = {status}")
                            
                            if status == 'completed':
                                citations = status_data.get('citations', [])
                                clusters = status_data.get('clusters', [])
                                
                                print(f"   ✅ ASYNC PROCESSING COMPLETED!")
                                print(f"   Citations found: {len(citations)}")
                                print(f"   Clusters found: {len(clusters)}")
                                
                                if len(citations) > 0:
                                    print("   ✅ Async citation extraction working!")
                                    
                                    # Show some examples
                                    for i, citation in enumerate(citations[:5], 1):
                                        citation_text = citation.get('citation', 'N/A')
                                        case_name = citation.get('extracted_case_name', 'N/A')
                                        print(f"     Citation {i}: {citation_text} - {case_name}")
                                    
                                    if len(clusters) > 0:
                                        print(f"   ✅ Async clustering working! {len(clusters)} clusters")
                                        
                                        # Show some cluster examples
                                        for i, cluster in enumerate(clusters[:3], 1):
                                            cluster_id = cluster.get('cluster_id', 'N/A')
                                            cluster_citations = cluster.get('citations', [])
                                            print(f"     Cluster {i}: {cluster_id} - {cluster_citations}")
                                            
                                            # Check for parallel citations
                                            if len(cluster_citations) >= 2:
                                                print(f"       ✅ PARALLEL CITATIONS DETECTED!")
                                    else:
                                        print("   ❌ No clusters found in async processing")
                                else:
                                    print("   ❌ No citations found in async processing")
                                
                                # Save response for analysis
                                with open('async_processing_response.json', 'w', encoding='utf-8') as f:
                                    json.dump(status_data, f, indent=2, ensure_ascii=False)
                                print("   📄 Response saved to async_processing_response.json")
                                
                                return len(citations) > 0 and len(clusters) > 0
                                
                            elif status == 'failed':
                                error = status_data.get('error', 'Unknown error')
                                print(f"   ❌ Async processing failed: {error}")
                                return False
                            else:
                                print(f"   ⏳ Still processing... ({status})")
                        else:
                            print(f"   ❌ Status check failed: {status_response.status_code}")
                            return False
                    
                    if poll_count >= max_polls:
                        print("   ❌ Timeout waiting for async completion")
                        return False
                else:
                    print("   ❌ No task ID for async processing")
                    return False
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)

def test_file_async_processing():
    """Test async processing with file upload."""
    
    print("\n🔍 TESTING FILE ASYNC PROCESSING")
    print("=" * 60)
    
    # Test with a URL that should trigger async processing
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    print(f"📄 Testing with URL: {test_url}")
    print("   This should trigger async processing")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer-File-Async-Test/1.0'
    }
    data = {
        'type': 'url',
        'url': test_url
    }
    
    try:
        print("📤 Sending URL for processing...")
        response = requests.post(url, headers=headers, json=data, timeout=120)
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"✅ Response received")
            
            # Check processing mode
            if 'result' in response_data:
                result = response_data['result']
                processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
                
                print(f"   Processing mode: {processing_mode}")
                
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"   Citations: {len(citations)}")
                print(f"   Clusters: {len(clusters)}")
                
                if len(citations) > 0 and len(clusters) > 0:
                    print("   ✅ URL processing working with clustering!")
                    return True
                else:
                    print("   ❌ URL processing not finding citations/clusters")
                    return False
            else:
                print("   ❌ No result in response")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ File async test failed: {e}")
        return False
    
    print("=" * 60)

if __name__ == "__main__":
    print("🎯 COMPREHENSIVE ASYNC PROCESSING TEST")
    print("=" * 80)
    
    # Test 1: Large text async processing
    text_async_working = test_async_processing()
    
    # Test 2: File/URL async processing  
    file_async_working = test_file_async_processing()
    
    print("\n🎯 FINAL ASYNC PROCESSING STATUS:")
    print("=" * 50)
    
    if text_async_working:
        print("✅ TEXT ASYNC PROCESSING: WORKING")
    else:
        print("❌ TEXT ASYNC PROCESSING: NOT WORKING")
    
    if file_async_working:
        print("✅ URL ASYNC PROCESSING: WORKING")
    else:
        print("❌ URL ASYNC PROCESSING: NOT WORKING")
    
    if text_async_working and file_async_working:
        print("\n🎉 ALL ASYNC PROCESSING IS WORKING!")
    else:
        print("\n⚠️  Some async processing issues detected")
    
    print("=" * 50)
