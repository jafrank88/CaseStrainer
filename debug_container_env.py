"""
Debug Container Environment
Tests what might be different in the container environment vs local.
"""

import requests
import time

def test_container_vs_local():
    """Compare container behavior vs local behavior."""
    
    print("🔍 CONTAINER VS LOCAL ENVIRONMENT TEST")
    print("=" * 45)
    
    # Test with very simple text that should process quickly
    simple_text = "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003). " * 40  # ~2.5KB
    
    print(f"📝 Test text: {len(simple_text)} characters")
    
    # Test 1: Local processing simulation (we know this works)
    print(f"\n🏠 LOCAL PROCESSING TEST:")
    local_success = test_local_processing(simple_text)
    
    # Test 2: Container async processing
    print(f"\n🐳 CONTAINER ASYNC PROCESSING TEST:")
    container_success = test_container_async(simple_text)
    
    # Test 3: Try to get more info about the hanging task
    if not container_success:
        print(f"\n🔍 INVESTIGATING HANGING TASK:")
        investigate_hanging_task()
    
    return local_success, container_success

def test_local_processing(text):
    """Test local processing (we know this works)."""
    
    try:
        start = time.time()
        
        from src.unified_sync_processor import UnifiedSyncProcessor, ProcessingOptions
        
        options = ProcessingOptions(
            enable_verification=True,
            enable_clustering=True,
            enable_caching=True,
            force_ultra_fast=False
        )
        processor = UnifiedSyncProcessor(options)
        
        result = processor.process_text_unified(text, {'request_id': 'local_test'})
        
        processing_time = time.time() - start
        
        if result.get('success', False):
            citations = result.get('citations', [])
            print(f"   ✅ Local: {processing_time:.3f}s, {len(citations)} citations")
            return True
        else:
            print(f"   ❌ Local failed: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Local error: {e}")
        return False

def test_container_async(text):
    """Test container async processing."""
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': text}
    
    try:
        # Submit task
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"   ✅ Task created: {task_id}")
                
                # Monitor for just 30 seconds
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                for attempt in range(10):  # 30 seconds
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                elapsed = (attempt + 1) * 3
                                
                                if attempt == 0 or attempt % 3 == 0:  # Print every 9 seconds
                                    print(f"   [{elapsed:2d}s] Status: {status}")
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    print(f"   ✅ Container: {elapsed}s, {len(citations)} citations")
                                    return True
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown')
                                    print(f"   ❌ Container failed: {error}")
                                    return False
                            
                        elif status_response.status_code == 404:
                            if attempt == 0:
                                print(f"   [  3s] Task not ready (404)")
                        
                    except Exception as e:
                        if attempt == 0:
                            print(f"   [  3s] Connection error: {e}")
                    
                    time.sleep(3)
                
                print(f"   ⏰ Container: Timed out after 30s (still running)")
                return False
                
            else:
                # Processed as sync
                citations = result.get('result', {}).get('citations', [])
                print(f"   ⚠️  Container processed as sync: {len(citations)} citations")
                return False
        else:
            print(f"   ❌ Container request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Container error: {e}")
        return False

def investigate_hanging_task():
    """Try to get more information about why tasks hang."""
    
    print(f"🔍 HANGING TASK INVESTIGATION:")
    
    # Try to check if there are any patterns in hanging
    print(f"   1. Testing with minimal text...")
    minimal_text = "150 Wn.2d 674" * 100  # ~1.4KB, should be sync but let's see
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': minimal_text}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                print(f"      ⚠️  Even minimal text triggers async")
                
                # Check if this one completes faster
                task_id = result['result']['task_id']
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                for attempt in range(5):  # 15 seconds
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                
                                if status == 'completed':
                                    print(f"      ✅ Minimal text completed in {(attempt + 1) * 3}s")
                                    return
                                elif status == 'failed':
                                    print(f"      ❌ Minimal text failed")
                                    return
                        
                    except:
                        pass
                    
                    time.sleep(3)
                
                print(f"      ⏰ Even minimal text hangs")
                
            else:
                citations = result.get('result', {}).get('citations', [])
                print(f"      ✅ Minimal text processed as sync: {len(citations)} citations")
        
    except Exception as e:
        print(f"      ❌ Minimal text test error: {e}")
    
    print(f"   2. Possible container issues:")
    print(f"      - Memory constraints in container")
    print(f"      - CPU throttling")
    print(f"      - Network latency to Redis")
    print(f"      - Missing dependencies in container")
    print(f"      - Different Python version/environment")
    print(f"      - Blocking I/O operations")

def main():
    """Run container environment investigation."""
    
    print("🎯 ASYNC SLOWDOWN: CONTAINER INVESTIGATION")
    print("=" * 45)
    
    local_works, container_works = test_container_vs_local()
    
    print(f"\n📊 ENVIRONMENT COMPARISON")
    print("=" * 25)
    print(f"✅ Local environment: {'WORKING' if local_works else 'FAILED'} (~0.4s)")
    print(f"✅ Container environment: {'WORKING' if container_works else 'HANGING'} (>30s)")
    
    if local_works and not container_works:
        print(f"\n🔍 CONCLUSION: Container Environment Issue")
        print(f"   The async worker code is correct but something in the")
        print(f"   container environment is causing it to hang.")
        print(f"   ")
        print(f"   Possible solutions:")
        print(f"   1. Check container resource limits")
        print(f"   2. Verify all dependencies are installed")
        print(f"   3. Check Redis connection in container")
        print(f"   4. Add timeout mechanisms to prevent hanging")
        print(f"   5. Simplify the async worker to isolate the issue")
    elif local_works and container_works:
        print(f"\n🎉 RESOLVED: Both environments working!")
    else:
        print(f"\n❌ BOTH ENVIRONMENTS HAVE ISSUES")

if __name__ == "__main__":
    main()
