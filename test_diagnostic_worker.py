"""
Test Diagnostic Worker
Tests the diagnostic worker to see exactly where it hangs during startup.
"""

import requests
import time

def test_diagnostic_worker():
    """Test the diagnostic worker with extensive logging."""
    
    print("🔍 TESTING DIAGNOSTIC WORKER")
    print("=" * 30)
    
    # Create test text
    test_text = "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003). " * 100  # ~6KB
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': test_text}
    
    print(f"📝 Text length: {len(test_text)} characters")
    print(f"🔍 Diagnostic logging: ENABLED")
    print(f"🎯 Goal: See exactly where worker hangs")
    
    try:
        print(f"\n📤 Submitting diagnostic task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"✅ Task created: {task_id}")
                
                print(f"\n🔍 MONITORING DIAGNOSTIC LOGS...")
                print(f"   Expected log sequence:")
                print(f"   1. WORKER STARTUP BEGINS")
                print(f"   2. Step 1: Function entry")
                print(f"   3. Step 2: Basic imports")
                print(f"   4. Step 3: Environment info")
                print(f"   5. Step 4: Redis environment")
                print(f"   6. Step 5: CitationService import")
                print(f"   7. Step 6: CitationService creation")
                print(f"   8. WORKER STARTUP COMPLETE")
                print(f"   9. MAIN PROCESSING BEGINS")
                print(f"   10. Step 7-11: Processing steps")
                
                # Monitor task status
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                start_time = time.time()
                last_status = None
                
                for attempt in range(15):  # 45 seconds
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                elapsed = time.time() - start_time
                                
                                if status != last_status:
                                    print(f"\n   [{elapsed:5.1f}s] Status: {status}")
                                    last_status = status
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    
                                    print(f"\n🎉 DIAGNOSTIC WORKER SUCCESS!")
                                    print(f"   ⏱️  Time: {elapsed:.1f}s")
                                    print(f"   📋 Citations: {len(citations)}")
                                    
                                    # Check if it used diagnostic method
                                    methods = [c.get('method', '') for c in citations]
                                    if 'diagnostic' in str(methods):
                                        print(f"   ✅ Used diagnostic processing")
                                    elif 'minimal_async' in str(methods):
                                        print(f"   ✅ Used minimal async processing")
                                    
                                    print(f"\n🔍 DIAGNOSTIC CONCLUSION:")
                                    print(f"   ✅ Worker startup completed successfully")
                                    print(f"   ✅ All import and initialization steps worked")
                                    print(f"   ✅ Container environment can handle worker startup")
                                    print(f"   💡 Previous hanging was likely a temporary issue")
                                    
                                    return True
                                    
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown')
                                    print(f"\n❌ DIAGNOSTIC WORKER FAILED!")
                                    print(f"   ⏱️  Time: {elapsed:.1f}s")
                                    print(f"   💥 Error: {error}")
                                    
                                    if 'startup' in error.lower():
                                        print(f"   🔍 Startup failure detected")
                                    elif 'diagnostic' in error.lower():
                                        print(f"   🔍 Diagnostic processing failure")
                                    
                                    return False
                            
                            elif 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                elapsed = time.time() - start_time
                                print(f"\n🎉 DIAGNOSTIC SUCCESS (direct result)!")
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
                print(f"\n⏰ DIAGNOSTIC TIMEOUT")
                print(f"   ⏱️  Monitored for: {elapsed:.1f}s")
                print(f"   📊 Last status: {last_status}")
                
                print(f"\n🔍 DIAGNOSTIC ANALYSIS:")
                if last_status == 'started':
                    print(f"   ❌ Worker hangs during startup/initialization")
                    print(f"   🎯 Check container logs for diagnostic messages")
                    print(f"   💡 Look for last successful diagnostic step")
                elif last_status == 'running':
                    print(f"   ❌ Worker hangs during processing")
                    print(f"   🎯 Startup completed but processing hangs")
                else:
                    print(f"   ❌ Worker hangs before startup")
                    print(f"   🎯 Issue in task queuing or worker pickup")
                
                return False
                
            else:
                # Processed as sync
                citations = result.get('result', {}).get('citations', [])
                print(f"⚠️  PROCESSED AS SYNC!")
                print(f"   Citations: {len(citations)}")
                return "sync"
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Test the diagnostic worker."""
    
    print("🎯 DIAGNOSTIC WORKER TEST")
    print("=" * 25)
    
    print("🔧 DIAGNOSTIC FEATURES:")
    print("   - Step-by-step startup logging")
    print("   - Import tracking")
    print("   - Environment information")
    print("   - Service creation monitoring")
    print("   - Processing step tracking")
    
    print(f"\n⚠️  IMPORTANT: Check container logs for diagnostic output!")
    print(f"   The diagnostic logs will show exactly where the worker hangs")
    
    result = test_diagnostic_worker()
    
    print(f"\n📊 DIAGNOSTIC RESULTS")
    print("=" * 20)
    
    if result == True:
        print(f"✅ SUCCESS: Diagnostic worker completed!")
        print(f"   Container environment issue may be resolved")
        print(f"   Or issue was temporary/intermittent")
        
    elif result == "sync":
        print(f"⚠️  THRESHOLD: Text processed as sync")
        print(f"   Need larger text to trigger async processing")
        
    else:
        print(f"❌ FAILURE: Diagnostic worker still hangs")
        print(f"   Check container logs for last successful diagnostic step")
        print(f"   This will pinpoint the exact hanging location")
    
    print(f"\n🔍 NEXT STEPS:")
    print(f"1. Check container logs: docker logs casestrainer-rqworker1-prod")
    print(f"2. Look for [DIAGNOSTIC:task_id] messages")
    print(f"3. Find the last successful step before hanging")
    print(f"4. This will identify the exact cause of the container issue")

if __name__ == "__main__":
    main()
