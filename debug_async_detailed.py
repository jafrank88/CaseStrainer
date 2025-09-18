"""
Debug Async Processing in Detail
Investigates why async tasks start but don't complete.
"""

import requests
import json
import time

def test_small_async_task():
    """Test with a smaller text that should complete quickly."""
    
    print("🔍 TESTING SMALL ASYNC TASK")
    print("=" * 30)
    
    # Smaller text but still large enough to trigger async
    base_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)"""
    
    # Repeat just enough to trigger async but not too much
    medium_text = base_text * 5  # 5x instead of 15x
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': medium_text}
    
    print(f"📝 Text length: {len(medium_text)} characters")
    
    try:
        # Submit the task
        print(f"\n📤 Submitting smaller async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Submission failed: HTTP {response.status_code}")
            return False
        
        result = response.json()
        
        if 'task_id' in result.get('result', {}):
            task_id = result['result']['task_id']
            print(f"✅ Async task created: {task_id}")
            
            # Monitor with shorter intervals and more patience
            status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
            
            print(f"\n⏳ Monitoring smaller task...")
            
            max_attempts = 60  # 3 minutes total
            for attempt in range(max_attempts):
                try:
                    status_response = requests.get(status_url, timeout=10)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if 'status' in status_data:
                            status = status_data['status']
                            
                            if attempt % 10 == 0 or status != 'running':  # Print every 30s or on status change
                                print(f"Attempt {attempt + 1}: Status = {status}")
                            
                            if status == 'completed':
                                citations = status_data.get('citations', [])
                                
                                print(f"\n✅ SMALL ASYNC TASK COMPLETED!")
                                print(f"   Citations found: {len(citations)}")
                                
                                # Check deduplication
                                citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                                unique_citations = set(citation_texts)
                                duplicates = len(citation_texts) - len(unique_citations)
                                
                                print(f"   Duplicates: {duplicates}")
                                
                                if duplicates == 0:
                                    print(f"   ✅ ASYNC DEDUPLICATION WORKING!")
                                else:
                                    print(f"   ❌ ASYNC DEDUPLICATION FAILED!")
                                
                                return True
                                
                            elif status == 'failed':
                                error = status_data.get('error', 'Unknown error')
                                print(f"\n❌ TASK FAILED: {error}")
                                return False
                                
                        else:
                            # Direct result
                            if 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                print(f"\n✅ TASK COMPLETED (direct result)!")
                                print(f"   Citations found: {len(citations)}")
                                return True
                    
                    elif status_response.status_code == 404:
                        if attempt < 5:  # Only show 404s for first few attempts
                            print(f"Attempt {attempt + 1}: 404 - task not ready yet")
                    else:
                        print(f"Attempt {attempt + 1}: HTTP {status_response.status_code}")
                        
                except Exception as e:
                    if attempt % 20 == 0:  # Only show errors occasionally
                        print(f"Attempt {attempt + 1}: Error - {e}")
                
                time.sleep(3)
            
            print(f"\n⏰ Small task also timed out after {max_attempts * 3} seconds")
            return False
            
        else:
            # Processed as sync
            processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
            citations = result.get('result', {}).get('citations', [])
            
            print(f"⚠️  Processed as sync: {processing_mode}")
            print(f"   Citations: {len(citations)}")
            print(f"   Text might not be large enough for async")
            return True
            
    except Exception as e:
        print(f"❌ Error in small async test: {e}")
        return False

def check_worker_logs():
    """Check if we can get any information about worker status."""
    
    print(f"\n🔍 CHECKING WORKER STATUS")
    print("-" * 25)
    
    # Try to check if there are any worker status endpoints
    base_url = "http://localhost:8080/casestrainer/api"
    
    endpoints_to_check = [
        f"{base_url}/workers",
        f"{base_url}/worker/status", 
        f"{base_url}/queue/status",
        f"{base_url}/redis/status",
        f"{base_url}/health"
    ]
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"   {endpoint}: HTTP {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"      Data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
                except:
                    print(f"      Response: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")

def test_redis_direct_check():
    """Test Redis connection directly to see task status."""
    
    print(f"\n🔍 CHECKING REDIS TASK STATUS")
    print("-" * 30)
    
    try:
        import redis
        import os
        
        redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@casestrainer-redis-prod:6379/0')
        r = redis.from_url(redis_url)
        
        # Test connection
        r.ping()
        print(f"✅ Redis connection successful")
        
        # Check recent jobs
        job_keys = r.keys('rq:job:*')
        print(f"📋 Total jobs in Redis: {len(job_keys)}")
        
        if job_keys:
            # Get the most recent jobs
            recent_jobs = sorted(job_keys)[-5:]
            
            print(f"Recent jobs:")
            for job_key in recent_jobs:
                job_key_str = job_key.decode('utf-8') if isinstance(job_key, bytes) else str(job_key)
                job_id = job_key_str.split(':')[-1]
                
                try:
                    job_data = r.hgetall(job_key)
                    if job_data:
                        status = job_data.get(b'status', job_data.get('status', b'unknown'))
                        status_str = status.decode('utf-8') if isinstance(status, bytes) else str(status)
                        
                        created_at = job_data.get(b'created_at', job_data.get('created_at'))
                        if created_at:
                            created_str = created_at.decode('utf-8') if isinstance(created_at, bytes) else str(created_at)
                        else:
                            created_str = 'unknown'
                        
                        print(f"   {job_id}: {status_str} (created: {created_str})")
                        
                        # Check if there's an error
                        if status_str == 'failed':
                            exc_info = job_data.get(b'exc_info', job_data.get('exc_info'))
                            if exc_info:
                                error_str = exc_info.decode('utf-8') if isinstance(exc_info, bytes) else str(exc_info)
                                print(f"      Error: {error_str[:200]}...")
                        
                except Exception as e:
                    print(f"   {job_id}: Error reading job data - {e}")
        
        # Check queue status
        queue_keys = r.keys('rq:queue:*')
        print(f"\n📋 Queues:")
        for queue_key in queue_keys:
            queue_name = queue_key.decode('utf-8') if isinstance(queue_key, bytes) else str(queue_key)
            queue_length = r.llen(queue_key)
            print(f"   {queue_name}: {queue_length} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis check failed: {e}")
        return False

def main():
    """Run comprehensive async debugging."""
    
    print("🎯 COMPREHENSIVE ASYNC PROCESSING DEBUG")
    print("=" * 50)
    
    # Test 1: Small async task
    small_success = test_small_async_task()
    
    # Test 2: Check worker status
    check_worker_logs()
    
    # Test 3: Check Redis directly
    redis_success = test_redis_direct_check()
    
    print(f"\n📊 ASYNC DEBUG SUMMARY")
    print("=" * 25)
    print(f"✅ Small async task: {'SUCCESS' if small_success else 'FAILED'}")
    print(f"✅ Redis connection: {'SUCCESS' if redis_success else 'FAILED'}")
    
    if not small_success:
        print(f"\n🔍 RECOMMENDATIONS:")
        print(f"   1. Check worker logs for errors")
        print(f"   2. Verify async processing pipeline")
        print(f"   3. Check if tasks are getting stuck in processing")

if __name__ == "__main__":
    main()
