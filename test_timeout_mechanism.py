"""
Test Timeout Mechanism
Tests if the new timeout mechanism works and provides better error reporting.
"""

import requests
import time

def test_timeout_mechanism():
    """Test if the timeout mechanism prevents infinite hanging."""
    
    print("🔍 TESTING TIMEOUT MECHANISM")
    print("=" * 30)
    
    # Create text that should trigger async processing
    test_text = "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003). " * 50  # ~3KB
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': test_text}
    
    print(f"📝 Text length: {len(test_text)} characters")
    
    try:
        print(f"\n📤 Submitting async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"✅ Async task created: {task_id}")
                
                # Monitor for up to 90 seconds (should timeout at 60s)
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                start_time = time.time()
                
                for attempt in range(30):  # 90 seconds total
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                elapsed = time.time() - start_time
                                
                                # Print status every 10 seconds or on change
                                if attempt % 3 == 0:
                                    print(f"   [{elapsed:5.1f}s] Status: {status}")
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    print(f"\n🎉 TASK COMPLETED!")
                                    print(f"   Time: {elapsed:.1f}s")
                                    print(f"   Citations: {len(citations)}")
                                    
                                    # Check deduplication
                                    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                                    unique_citations = set(citation_texts)
                                    duplicates = len(citation_texts) - len(unique_citations)
                                    
                                    print(f"   Duplicates: {duplicates}")
                                    print(f"   ✅ Async processing: WORKING!")
                                    return True
                                    
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown error')
                                    print(f"\n⏰ TASK FAILED (TIMEOUT MECHANISM WORKING)!")
                                    print(f"   Time: {elapsed:.1f}s")
                                    print(f"   Error: {error}")
                                    
                                    if "timed out" in error.lower():
                                        print(f"   ✅ Timeout mechanism: WORKING!")
                                        return "timeout"
                                    else:
                                        print(f"   ❌ Different error: {error}")
                                        return False
                            
                            elif 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                elapsed = time.time() - start_time
                                print(f"\n🎉 TASK COMPLETED (direct result)!")
                                print(f"   Time: {elapsed:.1f}s")
                                print(f"   Citations: {len(citations)}")
                                return True
                        
                        elif status_response.status_code == 404:
                            if attempt < 3:
                                print(f"   [{time.time() - start_time:5.1f}s] Task not ready (404)")
                        
                    except Exception as e:
                        if attempt % 10 == 0:
                            elapsed = time.time() - start_time
                            print(f"   [{elapsed:5.1f}s] Connection error: {e}")
                    
                    time.sleep(3)
                
                elapsed = time.time() - start_time
                print(f"\n⏰ MONITORING TIMED OUT")
                print(f"   Monitored for: {elapsed:.1f}s")
                print(f"   Task may still be processing or timeout mechanism failed")
                return False
                
            else:
                # Processed as sync
                citations = result.get('result', {}).get('citations', [])
                processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                print(f"⚠️  Processed as sync: {processing_mode}")
                print(f"   Citations: {len(citations)}")
                return "sync"
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Test the timeout mechanism."""
    
    print("🎯 TIMEOUT MECHANISM TEST")
    print("=" * 25)
    
    result = test_timeout_mechanism()
    
    print(f"\n📊 TIMEOUT TEST RESULTS")
    print("=" * 25)
    
    if result == True:
        print(f"✅ ASYNC PROCESSING: FULLY WORKING!")
        print(f"   The container environment issue has been resolved!")
    elif result == "timeout":
        print(f"✅ TIMEOUT MECHANISM: WORKING!")
        print(f"   Tasks now fail gracefully instead of hanging forever")
        print(f"   This confirms the container environment issue exists")
    elif result == "sync":
        print(f"⚠️  TEXT PROCESSED AS SYNC")
        print(f"   Text may not be large enough to trigger async")
    else:
        print(f"❌ TIMEOUT MECHANISM: NOT WORKING")
        print(f"   Tasks are still hanging without timeout")

if __name__ == "__main__":
    main()
