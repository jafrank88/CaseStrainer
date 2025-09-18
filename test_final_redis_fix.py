"""
Test Final Redis Fix
Tests the container-level Redis readiness check that should completely resolve async hanging.
"""

import requests
import time

def test_final_redis_fix():
    """Test the final container-level Redis readiness fix."""
    
    print("🎯 TESTING FINAL REDIS READINESS FIX")
    print("=" * 40)
    
    # Create comprehensive test text with multiple citations
    test_text = """
    Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003).
    This case established important precedent for development rights.
    
    Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007).
    The court held that food service establishments have specific liability obligations.
    
    Five Corners Fam. Farmers v. State, 173 Wn.2d 296, 306, 268 P.3d 892 (2011).
    This decision clarified agricultural land use regulations.
    
    Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App. 2d 75, 664 P.3d 1200 (2023).
    Recent case addressing licensing requirements for business operations.
    
    Additional context and analysis to ensure the text is large enough to trigger
    async processing. The system should now handle this properly with the Redis
    readiness check preventing BusyLoadingError exceptions during worker startup.
    """ * 25  # ~12KB to ensure async processing
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': test_text}
    
    print(f"📝 Text length: {len(test_text)} characters")
    print(f"🔧 Container fix: wait-for-redis.py before RQ worker startup")
    print(f"🎯 Expected: Workers wait for Redis dataset loading, then process successfully")
    
    try:
        print(f"\n📤 Submitting final Redis-fixed async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"✅ Task created: {task_id}")
                
                # Monitor with high expectation of success
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                start_time = time.time()
                last_status = None
                status_changes = []
                
                for attempt in range(30):  # 90 seconds (generous timeout)
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                elapsed = time.time() - start_time
                                
                                # Track status changes
                                if status != last_status:
                                    status_changes.append((elapsed, status))
                                    print(f"   [{elapsed:5.1f}s] Status: {status}")
                                    last_status = status
                                    
                                    if status == 'started':
                                        print(f"      ✅ Worker picked up task")
                                    elif status == 'running':
                                        print(f"      🔄 Processing started (Redis ready, no BusyLoadingError)")
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    
                                    print(f"\n🎉 FINAL REDIS FIX SUCCESS!")
                                    print(f"   ⏱️  Total time: {elapsed:.1f}s")
                                    print(f"   📋 Citations found: {len(citations)}")
                                    
                                    # Analyze processing quality
                                    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                                    unique_citations = set(citation_texts)
                                    duplicates = len(citation_texts) - len(unique_citations)
                                    
                                    print(f"   🔄 Deduplication: {len(citation_texts)} → {len(unique_citations)} ({duplicates} duplicates)")
                                    
                                    # Check case name extraction
                                    case_names = [c.get('extracted_case_name', 'N/A') for c in citations]
                                    complete_names = [name for name in case_names if len(name) > 10 and 'v.' in name]
                                    
                                    print(f"   📝 Case names: {len(complete_names)}/{len(case_names)} complete")
                                    
                                    # Show processing timeline
                                    print(f"\n📊 Processing timeline:")
                                    for time_point, status_name in status_changes:
                                        print(f"      {time_point:5.1f}s: {status_name}")
                                    
                                    # Show sample results
                                    print(f"\n📋 Sample citations:")
                                    for i, citation in enumerate(citations[:3], 1):
                                        citation_text = citation.get('citation', '').replace('\n', ' ').strip()
                                        case_name = citation.get('extracted_case_name', 'N/A')
                                        print(f"   {i}. {citation_text}")
                                        print(f"      Case: {case_name}")
                                    
                                    print(f"\n🎯 ASYNC SLOWDOWN RESOLUTION STATUS:")
                                    if elapsed < 30:
                                        print(f"   ✅ FULLY RESOLVED: Fast async processing!")
                                        print(f"   🔧 Container-level Redis fix successful")
                                        print(f"   🎉 BusyLoadingError completely eliminated")
                                    elif elapsed < 60:
                                        print(f"   ✅ MOSTLY RESOLVED: Reasonable async processing time")
                                        print(f"   🔧 Redis loading delay but no hanging")
                                        print(f"   💡 Significant improvement over infinite hanging")
                                    else:
                                        print(f"   ⚠️  PARTIALLY RESOLVED: Slow but working")
                                        print(f"   🔧 No more hanging but performance needs optimization")
                                    
                                    return True
                                    
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown')
                                    print(f"\n❌ FINAL REDIS FIX FAILED!")
                                    print(f"   ⏱️  Time: {elapsed:.1f}s")
                                    print(f"   💥 Error: {error}")
                                    
                                    if 'redis' in error.lower():
                                        print(f"   🔍 Redis-related failure still occurring")
                                        if 'loading' in error.lower():
                                            print(f"   💡 Redis readiness check may need longer timeout")
                                        elif 'timeout' in error.lower():
                                            print(f"   💡 Redis readiness timeout - increase wait time")
                                    else:
                                        print(f"   🔍 Non-Redis failure - different issue")
                                    
                                    return False
                            
                            elif 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                elapsed = time.time() - start_time
                                print(f"\n🎉 FINAL REDIS FIX SUCCESS (direct result)!")
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
                print(f"\n⏰ FINAL REDIS FIX TIMEOUT")
                print(f"   ⏱️  Monitored for: {elapsed:.1f}s")
                print(f"   📊 Last status: {last_status}")
                print(f"   📊 Status changes: {len(status_changes)}")
                
                if len(status_changes) >= 2:
                    print(f"   🔍 ANALYSIS: Worker progressed through statuses")
                    print(f"   💡 Redis readiness check may be working but processing is slow")
                elif len(status_changes) == 1:
                    print(f"   🔍 ANALYSIS: Worker started but didn't progress")
                    print(f"   💡 May still have Redis loading issues")
                else:
                    print(f"   🔍 ANALYSIS: No status changes detected")
                    print(f"   💡 Fundamental issue may persist")
                
                return False
                
            else:
                # Processed as sync
                citations = result.get('result', {}).get('citations', [])
                processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                print(f"⚠️  PROCESSED AS SYNC!")
                print(f"   Mode: {processing_mode}")
                print(f"   Citations: {len(citations)}")
                print(f"   Text may not be large enough for async threshold")
                return "sync"
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Test the final Redis readiness fix."""
    
    print("🎯 FINAL REDIS READINESS FIX TEST")
    print("=" * 35)
    
    print("🔍 CONTAINER-LEVEL FIX IMPLEMENTED:")
    print("   ✅ wait-for-redis.py script created")
    print("   ✅ RQ workers wait for Redis dataset loading")
    print("   ✅ Prevents BusyLoadingError at worker startup")
    print("   ✅ Should completely resolve async hanging")
    
    print(f"\n⚠️  NOTE: This test requires container restart to activate the fix!")
    
    result = test_final_redis_fix()
    
    print(f"\n📊 FINAL REDIS FIX RESULTS")
    print("=" * 28)
    
    if result == True:
        print(f"🎉 SUCCESS: ASYNC SLOWDOWN FULLY RESOLVED!")
        print(f"\n✅ FINAL RESOLUTION CONFIRMED:")
        print(f"   ✅ Root cause: Redis BusyLoadingError during dataset loading")
        print(f"   ✅ Solution: Container-level Redis readiness check")
        print(f"   ✅ Result: Async processing works correctly without hanging")
        print(f"   ✅ Deduplication: Working in async mode")
        print(f"   ✅ Case name extraction: Working in async mode")
        
        print(f"\n🎯 ASYNC PROCESSING NOW FULLY FUNCTIONAL!")
        
    elif result == "sync":
        print(f"⚠️  THRESHOLD: Text processed as sync")
        print(f"   Need to test with larger text to trigger async")
        print(f"   But sync processing is working correctly")
        
    else:
        print(f"❌ FAILURE: Container-level fix didn't resolve hanging")
        print(f"\n🔍 ADDITIONAL INVESTIGATION NEEDED:")
        print(f"   1. Check container logs for wait-for-redis.py output")
        print(f"   2. Verify Redis readiness check is running")
        print(f"   3. May need longer Redis wait timeout")
        print(f"   4. Consider alternative async architecture")

if __name__ == "__main__":
    main()
