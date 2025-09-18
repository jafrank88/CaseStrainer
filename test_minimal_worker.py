"""
Test Minimal Async Worker
Tests if the ultra-minimal async worker can complete successfully.
"""

import requests
import time

def test_minimal_async_worker():
    """Test the minimal async worker that bypasses all complex processing."""
    
    print("🧪 TESTING MINIMAL ASYNC WORKER")
    print("=" * 35)
    
    # Create text with clear citations that the minimal worker should find
    test_text = """
    Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003).
    Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007).
    Five Corners Fam. Farmers v. State, 173 Wn.2d 296, 306, 268 P.3d 892 (2011).
    """ * 100  # Make it large enough for async (~7KB)
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': test_text}
    
    print(f"📝 Text length: {len(test_text)} characters")
    print(f"🔧 Worker type: MINIMAL (regex only, no complex imports)")
    print(f"🎯 Expected: Should complete in <10 seconds if container allows")
    
    try:
        print(f"\n📤 Submitting minimal async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"✅ Task created: {task_id}")
                
                # Monitor with detailed status tracking
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                start_time = time.time()
                last_status = None
                
                for attempt in range(20):  # 60 seconds max
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                elapsed = time.time() - start_time
                                
                                # Print status changes
                                if status != last_status:
                                    print(f"   [{elapsed:5.1f}s] Status: {status}")
                                    last_status = status
                                    
                                    if status == 'started':
                                        print(f"      ✅ Worker picked up task")
                                    elif status == 'running':
                                        print(f"      🔄 Minimal processing started")
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    
                                    print(f"\n🎉 MINIMAL WORKER SUCCESS!")
                                    print(f"   ⏱️  Time: {elapsed:.1f}s")
                                    print(f"   📋 Citations: {len(citations)}")
                                    
                                    # Analyze results
                                    citation_texts = [c.get('citation', '') for c in citations]
                                    methods = [c.get('method', '') for c in citations]
                                    
                                    print(f"   🔍 Citation texts: {citation_texts}")
                                    print(f"   🔧 Methods: {set(methods)}")
                                    
                                    # Check deduplication
                                    unique_citations = set(citation_texts)
                                    duplicates = len(citation_texts) - len(unique_citations)
                                    
                                    print(f"   🔄 Deduplication: {len(citation_texts)} → {len(unique_citations)} ({duplicates} duplicates)")
                                    
                                    if 'minimal_async' in methods:
                                        print(f"   ✅ Confirmed: Using minimal async worker")
                                    
                                    print(f"\n🎯 CONTAINER ISSUE RESOLUTION:")
                                    if elapsed < 15:
                                        print(f"   ✅ RESOLVED: Minimal worker completes quickly")
                                        print(f"   🔍 Issue was in complex processing imports/logic")
                                        print(f"   💡 Solution: Gradually add back features to find exact cause")
                                    else:
                                        print(f"   ⚠️  SLOW: Even minimal worker took {elapsed:.1f}s")
                                        print(f"   🔍 Container has performance constraints")
                                    
                                    return True
                                    
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown error')
                                    print(f"\n❌ MINIMAL WORKER FAILED!")
                                    print(f"   ⏱️  Time: {elapsed:.1f}s")
                                    print(f"   💥 Error: {error}")
                                    
                                    if "minimal" in error.lower():
                                        print(f"   🔍 Issue in minimal processing logic")
                                    else:
                                        print(f"   🔍 Container environment issue")
                                    
                                    return False
                            
                            elif 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                elapsed = time.time() - start_time
                                print(f"\n🎉 MINIMAL WORKER SUCCESS (direct result)!")
                                print(f"   ⏱️  Time: {elapsed:.1f}s")
                                print(f"   📋 Citations: {len(citations)}")
                                return True
                        
                        elif status_response.status_code == 404:
                            if attempt < 3:
                                elapsed = time.time() - start_time
                                print(f"   [{elapsed:5.1f}s] Task not ready (404)")
                        
                    except Exception as e:
                        if attempt % 5 == 0:
                            elapsed = time.time() - start_time
                            print(f"   [{elapsed:5.1f}s] Connection error: {e}")
                    
                    time.sleep(3)
                
                elapsed = time.time() - start_time
                print(f"\n⏰ MINIMAL WORKER TEST TIMEOUT")
                print(f"   ⏱️  Monitored for: {elapsed:.1f}s")
                print(f"   📊 Last status: {last_status}")
                
                if last_status == 'started':
                    print(f"   🔍 DIAGNOSIS: Hangs during worker initialization")
                    print(f"   💡 Issue is in worker startup, not processing logic")
                elif last_status == 'running':
                    print(f"   🔍 DIAGNOSIS: Hangs during minimal processing")
                    print(f"   💡 Even basic regex processing hangs in container")
                else:
                    print(f"   🔍 DIAGNOSIS: Hangs before worker starts")
                    print(f"   💡 Issue in task queuing or Redis communication")
                
                return False
                
            else:
                # Processed as sync
                citations = result.get('result', {}).get('citations', [])
                processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                print(f"⚠️  PROCESSED AS SYNC!")
                print(f"   Mode: {processing_mode}")
                print(f"   Citations: {len(citations)}")
                return "sync"
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Test the minimal async worker."""
    
    print("🎯 MINIMAL ASYNC WORKER TEST")
    print("=" * 30)
    
    print("🔧 MINIMAL WORKER FEATURES:")
    print("   - Only uses built-in modules (re, time)")
    print("   - Basic regex citation extraction")
    print("   - Simple deduplication")
    print("   - No complex imports or processing")
    print("   - Should complete in seconds")
    
    result = test_minimal_async_worker()
    
    print(f"\n📊 MINIMAL WORKER RESULTS")
    print("=" * 25)
    
    if result == True:
        print(f"✅ SUCCESS: Minimal worker completes!")
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Container environment can handle basic async processing")
        print(f"   2. Issue is in complex processing logic or imports")
        print(f"   3. Gradually add back features to isolate exact cause")
        print(f"   4. Consider using minimal worker as fallback for async")
        
    elif result == "sync":
        print(f"⚠️  THRESHOLD: Text processed as sync")
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Lower async threshold or use larger test text")
        print(f"   2. Test with definitely async-triggering text size")
        
    else:
        print(f"❌ FAILURE: Even minimal worker hangs")
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Fundamental container environment issue")
        print(f"   2. Consider container resource limits")
        print(f"   3. Investigate Redis/RQ infrastructure")
        print(f"   4. May need alternative async architecture")

if __name__ == "__main__":
    main()
