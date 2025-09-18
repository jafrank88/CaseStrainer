"""
Test Redis Readiness Fix
Tests if the Redis readiness check resolves the async hanging issue.
"""

import requests
import time

def test_redis_readiness_fix():
    """Test the Redis readiness fix for async processing."""
    
    print("🔧 TESTING REDIS READINESS FIX")
    print("=" * 35)
    
    # Create test text
    test_text = """
    Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003).
    Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007).
    Five Corners Fam. Farmers v. State, 173 Wn.2d 296, 306, 268 P.3d 892 (2011).
    Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App. 2d 75, 664 P.3d 1200 (2023).
    """ * 50  # ~10KB to ensure async processing
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': test_text}
    
    print(f"📝 Text length: {len(test_text)} characters")
    print(f"🔧 Fix: Redis readiness check with 30s timeout")
    print(f"🎯 Expected: Worker waits for Redis, then processes successfully")
    
    try:
        print(f"\n📤 Submitting Redis-fixed async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"✅ Task created: {task_id}")
                
                # Monitor with expectation of success
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                start_time = time.time()
                last_status = None
                redis_wait_detected = False
                
                for attempt in range(25):  # 75 seconds (allow time for Redis loading)
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
                                        print(f"      🔄 Processing started (Redis ready)")
                                        redis_wait_detected = True
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    
                                    print(f"\n🎉 REDIS FIX SUCCESS!")
                                    print(f"   ⏱️  Total time: {elapsed:.1f}s")
                                    print(f"   📋 Citations found: {len(citations)}")
                                    
                                    # Analyze results
                                    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                                    unique_citations = set(citation_texts)
                                    duplicates = len(citation_texts) - len(unique_citations)
                                    
                                    print(f"   🔄 Deduplication: {len(citation_texts)} → {len(unique_citations)} ({duplicates} duplicates)")
                                    
                                    # Check processing method
                                    methods = [c.get('method', '') for c in citations]
                                    processing_strategy = status_data.get('metadata', {}).get('processing_strategy', 'unknown')
                                    
                                    print(f"   🔧 Processing: {processing_strategy}")
                                    print(f"   🔧 Methods: {set(methods)}")
                                    
                                    # Show sample citations
                                    print(f"\n📋 Sample citations:")
                                    for i, citation in enumerate(citations[:3], 1):
                                        citation_text = citation.get('citation', '').replace('\n', ' ').strip()
                                        case_name = citation.get('extracted_case_name', 'N/A')
                                        print(f"   {i}. {citation_text}")
                                        print(f"      Case: {case_name}")
                                    
                                    print(f"\n🎯 ASYNC SLOWDOWN RESOLUTION:")
                                    if elapsed < 30:
                                        print(f"   ✅ FULLY RESOLVED: Async processing works quickly!")
                                        print(f"   🔧 Redis readiness check prevented hanging")
                                        print(f"   🎉 Container environment issue solved")
                                    else:
                                        print(f"   ⚠️  PARTIALLY RESOLVED: Works but slow ({elapsed:.1f}s)")
                                        print(f"   🔧 Redis loading causes delay but no hanging")
                                    
                                    return True
                                    
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown')
                                    print(f"\n❌ REDIS FIX FAILED!")
                                    print(f"   ⏱️  Time: {elapsed:.1f}s")
                                    print(f"   💥 Error: {error}")
                                    
                                    if 'redis' in error.lower():
                                        print(f"   🔍 Redis-related failure detected")
                                        if 'loading' in error.lower():
                                            print(f"   💡 Redis still loading after timeout")
                                        elif 'timeout' in error.lower():
                                            print(f"   💡 Redis readiness timeout")
                                    
                                    return False
                            
                            elif 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                elapsed = time.time() - start_time
                                print(f"\n🎉 REDIS FIX SUCCESS (direct result)!")
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
                print(f"\n⏰ REDIS FIX TEST TIMEOUT")
                print(f"   ⏱️  Monitored for: {elapsed:.1f}s")
                print(f"   📊 Last status: {last_status}")
                
                if last_status == 'running':
                    print(f"   🔍 ANALYSIS: Still hangs during processing")
                    print(f"   💡 Redis fix may not be complete or other issues exist")
                elif last_status == 'started':
                    print(f"   🔍 ANALYSIS: Hangs during worker startup")
                    print(f"   💡 Redis readiness check may be taking too long")
                else:
                    print(f"   🔍 ANALYSIS: Hangs before processing")
                    print(f"   💡 Issue may be in task queuing")
                
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
    """Test the Redis readiness fix."""
    
    print("🎯 REDIS READINESS FIX TEST")
    print("=" * 28)
    
    print("🔍 ROOT CAUSE IDENTIFIED:")
    print("   ❌ redis.exceptions.BusyLoadingError")
    print("   ❌ Redis loading dataset in memory (13-15 seconds)")
    print("   ❌ Workers hang waiting for Redis during loading")
    
    print(f"\n🔧 FIX IMPLEMENTED:")
    print("   ✅ Redis readiness check with 30s timeout")
    print("   ✅ Worker waits for Redis to finish loading")
    print("   ✅ Prevents BusyLoadingError exceptions")
    
    result = test_redis_readiness_fix()
    
    print(f"\n📊 REDIS FIX RESULTS")
    print("=" * 20)
    
    if result == True:
        print(f"✅ SUCCESS: Redis fix resolved async hanging!")
        print(f"\n🎉 ASYNC SLOWDOWN FULLY RESOLVED!")
        print(f"   ✅ Root cause: Redis loading dataset")
        print(f"   ✅ Solution: Redis readiness check")
        print(f"   ✅ Result: Async processing works correctly")
        
    elif result == "sync":
        print(f"⚠️  THRESHOLD: Text processed as sync")
        print(f"   Need larger text to test async processing")
        
    else:
        print(f"❌ FAILURE: Redis fix didn't resolve hanging")
        print(f"   May need additional fixes or longer timeout")
        print(f"   Check container logs for Redis readiness messages")

if __name__ == "__main__":
    main()
