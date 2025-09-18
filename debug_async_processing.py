"""
Debug Async Processing Issues
Investigates why async tasks return 404 and fixes the issues.
"""

import requests
import json
import time
import os

def debug_async_flow():
    """Debug the complete async processing flow."""
    
    print("🔍 DEBUGGING ASYNC PROCESSING FLOW")
    print("=" * 50)
    
    # Create large text to force async processing
    base_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)"""
    
    # Repeat to ensure async processing
    large_text = base_text * 20  # 20x repetition
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': large_text}
    
    print(f"📝 Text length: {len(large_text)} characters")
    print(f"🌐 Submitting to: {url}")
    
    try:
        # Step 1: Submit the task
        print(f"\n📤 STEP 1: Submitting async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Submission failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        result = response.json()
        print(f"✅ Submission successful")
        print(f"Response keys: {list(result.keys())}")
        
        # Check if we got a task_id (async) or immediate result (sync)
        if 'task_id' in result.get('result', {}):
            task_id = result['result']['task_id']
            print(f"📋 Async task created: {task_id}")
            
            # Step 2: Check different status endpoints
            print(f"\n🔍 STEP 2: Testing different status endpoints...")
            
            endpoints_to_test = [
                f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}",
                f"http://localhost:8080/casestrainer/api/analyze/status/{task_id}",
                f"http://localhost:8080/casestrainer/api/analyze/results/{task_id}",
                f"http://localhost:8080/casestrainer/api/task/{task_id}",
                f"http://localhost:8080/casestrainer/api/task/status/{task_id}"
            ]
            
            for endpoint in endpoints_to_test:
                try:
                    status_response = requests.get(endpoint, timeout=10)
                    print(f"   {endpoint}")
                    print(f"      Status: {status_response.status_code}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"      ✅ SUCCESS! Data keys: {list(status_data.keys())}")
                        
                        # If we found a working endpoint, monitor it
                        return monitor_task(endpoint, task_id)
                    elif status_response.status_code == 404:
                        print(f"      ❌ 404 Not Found")
                    else:
                        print(f"      ⚠️  HTTP {status_response.status_code}: {status_response.text[:100]}")
                        
                except Exception as e:
                    print(f"      ❌ Error: {e}")
            
            print(f"\n❌ No working status endpoint found!")
            
            # Step 3: Check if the task is in Redis directly
            print(f"\n🔍 STEP 3: Checking Redis task storage...")
            check_redis_task(task_id)
            
        else:
            # It was processed synchronously
            processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
            citations = result.get('result', {}).get('citations', [])
            
            print(f"⚠️  Processed synchronously despite large text")
            print(f"   Processing mode: {processing_mode}")
            print(f"   Citations: {len(citations)}")
            print(f"   This suggests async threshold is very high or async is disabled")
            
            return analyze_sync_result(result)
            
    except Exception as e:
        print(f"❌ Error in async flow debug: {e}")
        import traceback
        traceback.print_exc()

def monitor_task(endpoint, task_id):
    """Monitor a working task endpoint."""
    
    print(f"\n⏳ MONITORING TASK: {task_id}")
    print(f"Using endpoint: {endpoint}")
    
    max_attempts = 20
    for attempt in range(max_attempts):
        try:
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                print(f"Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    print(f"\n✅ TASK COMPLETED!")
                    
                    citations = data.get('citations', [])
                    print(f"Citations found: {len(citations)}")
                    
                    # Check deduplication
                    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                    unique_citations = set(citation_texts)
                    duplicates = len(citation_texts) - len(unique_citations)
                    
                    print(f"Duplicates: {duplicates}")
                    
                    if duplicates == 0:
                        print(f"✅ ASYNC DEDUPLICATION WORKING!")
                    else:
                        print(f"❌ ASYNC DEDUPLICATION FAILED!")
                        from collections import Counter
                        counts = Counter(citation_texts)
                        for citation, count in counts.items():
                            if count > 1:
                                print(f"   '{citation}' appears {count} times")
                    
                    return True
                    
                elif status == 'failed':
                    error = data.get('error', 'Unknown error')
                    print(f"\n❌ TASK FAILED: {error}")
                    return False
                    
                else:
                    time.sleep(3)
                    
            else:
                print(f"Attempt {attempt + 1}: HTTP {response.status_code}")
                time.sleep(3)
                
        except Exception as e:
            print(f"Attempt {attempt + 1}: Error - {e}")
            time.sleep(3)
    
    print(f"\n⏰ Task monitoring timed out")
    return False

def check_redis_task(task_id):
    """Check if the task exists in Redis."""
    
    try:
        import redis
        
        # Try to connect to Redis
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        
        print(f"Connecting to Redis: {redis_url}")
        r = redis.from_url(redis_url)
        
        # Check different Redis keys that might contain the task
        keys_to_check = [
            f'rq:job:{task_id}',
            f'rq:job:{task_id}:result',
            f'task:{task_id}',
            f'result:{task_id}'
        ]
        
        for key in keys_to_check:
            try:
                exists = r.exists(key)
                print(f"   Redis key '{key}': {'EXISTS' if exists else 'NOT FOUND'}")
                
                if exists:
                    data = r.get(key)
                    if data:
                        print(f"      Data preview: {str(data)[:100]}...")
                        
            except Exception as e:
                print(f"   Error checking key '{key}': {e}")
        
        # List all keys matching the task_id
        try:
            matching_keys = r.keys(f'*{task_id}*')
            print(f"   All matching keys: {matching_keys}")
            
        except Exception as e:
            print(f"   Error listing keys: {e}")
            
    except ImportError:
        print(f"   Redis module not available for direct checking")
    except Exception as e:
        print(f"   Error connecting to Redis: {e}")

def analyze_sync_result(result):
    """Analyze a sync result to understand why it wasn't async."""
    
    print(f"\n📊 SYNC RESULT ANALYSIS")
    print("-" * 30)
    
    citations = result.get('result', {}).get('citations', [])
    processing_strategy = result.get('result', {}).get('metadata', {}).get('processing_strategy', 'unknown')
    
    print(f"Processing strategy: {processing_strategy}")
    print(f"Citations found: {len(citations)}")
    
    # Check deduplication in sync mode
    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
    unique_citations = set(citation_texts)
    duplicates = len(citation_texts) - len(unique_citations)
    
    print(f"Duplicates: {duplicates}")
    
    if duplicates == 0:
        print(f"✅ SYNC DEDUPLICATION WORKING!")
    else:
        print(f"❌ SYNC DEDUPLICATION FAILED!")
        from collections import Counter
        counts = Counter(citation_texts)
        for citation, count in counts.items():
            if count > 1:
                print(f"   '{citation}' appears {count} times")
    
    return True

if __name__ == "__main__":
    debug_async_flow()
