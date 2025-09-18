"""
Debug Worker Isolation
Creates a minimal async worker to isolate exactly where the hanging occurs.
"""

import requests
import time

def test_minimal_worker_steps():
    """Test each step of the worker process to isolate the hanging point."""
    
    print("🔍 MINIMAL WORKER STEP ISOLATION")
    print("=" * 40)
    
    # Create the absolute minimal async task
    minimal_text = "150 Wn.2d 674" * 500  # ~6.5KB, definitely async
    
    print(f"📝 Minimal text: {len(minimal_text)} characters")
    print(f"🎯 Goal: Isolate exactly where the worker hangs")
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': minimal_text}
    
    try:
        print(f"\n📤 Step 1: Task submission...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"   ✅ Task created: {task_id}")
                
                print(f"\n📤 Step 2: Task status monitoring...")
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                # Monitor with detailed status tracking
                statuses_seen = []
                
                for attempt in range(15):  # 45 seconds
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                elapsed = (attempt + 1) * 3
                                
                                if status not in statuses_seen:
                                    statuses_seen.append(status)
                                    print(f"   📊 [{elapsed:2d}s] NEW STATUS: {status}")
                                    
                                    # Analyze status transitions
                                    if status == 'queued':
                                        print(f"      ✅ Task queued successfully")
                                    elif status == 'started':
                                        print(f"      ✅ Worker picked up task")
                                    elif status == 'running':
                                        print(f"      ⚠️  Worker started processing - THIS IS WHERE IT HANGS")
                                        print(f"      🔍 Hanging occurs INSIDE the worker process")
                                    elif status == 'completed':
                                        print(f"      🎉 Processing completed!")
                                        return True
                                    elif status == 'failed':
                                        print(f"      ❌ Processing failed")
                                        return False
                                
                                # If we've been running for more than 30 seconds, it's hanging
                                if status == 'running' and elapsed > 30:
                                    print(f"   ⏰ CONFIRMED: Hanging in 'running' status for {elapsed}s")
                                    print(f"   🎯 ISOLATION COMPLETE: Issue is inside worker process")
                                    return "hanging_in_worker"
                            
                        elif status_response.status_code == 404:
                            if attempt < 3:
                                print(f"   📊 [{(attempt + 1) * 3:2d}s] Task not ready (404)")
                        
                    except Exception as e:
                        if attempt % 5 == 0:
                            print(f"   📊 [{(attempt + 1) * 3:2d}s] Connection error: {e}")
                    
                    time.sleep(3)
                
                print(f"\n⏰ MONITORING COMPLETE")
                print(f"   Statuses seen: {' → '.join(statuses_seen)}")
                
                if 'running' in statuses_seen:
                    return "hanging_in_worker"
                else:
                    return "hanging_before_worker"
                
            else:
                print(f"   ⚠️  Processed as sync")
                return "sync"
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def create_ultra_minimal_worker():
    """Create a test that bypasses most of the processing logic."""
    
    print(f"\n🧪 ULTRA-MINIMAL WORKER TEST")
    print("-" * 30)
    
    print(f"💡 PROPOSED SOLUTIONS:")
    print(f"1. Replace UnifiedSyncProcessor with basic citation extraction")
    print(f"2. Add extensive logging to worker to see exactly where it hangs")
    print(f"3. Use process isolation instead of threading")
    print(f"4. Implement container resource monitoring")
    print(f"5. Consider alternative async architecture")
    
    # Let's create a minimal test that just does basic citation extraction
    print(f"\n🔧 CREATING MINIMAL WORKER REPLACEMENT...")
    
    minimal_worker_code = '''
# Minimal async worker replacement
def minimal_process_text(text, task_id):
    """Ultra-minimal text processing that should not hang."""
    import re
    
    # Basic citation regex (no complex processing)
    citation_pattern = r'\\d+\\s+Wn\\.2d\\s+\\d+'
    citations = re.findall(citation_pattern, text)
    
    return {
        'success': True,
        'citations': [{'citation': cit, 'extracted_case_name': 'Minimal', 'verified': False} for cit in citations],
        'clusters': [],
        'processing_strategy': 'minimal_async'
    }
'''
    
    print(f"📝 Minimal worker code created")
    print(f"🎯 This would bypass all complex processing and just extract citations")
    
    return minimal_worker_code

def analyze_container_environment():
    """Analyze what might be different in the container environment."""
    
    print(f"\n🔍 CONTAINER ENVIRONMENT ANALYSIS")
    print("-" * 35)
    
    issues_and_solutions = [
        {
            "issue": "Memory Constraints",
            "symptoms": "Worker starts but hangs during processing",
            "solution": "Increase container memory limits",
            "test": "Monitor container memory usage during processing"
        },
        {
            "issue": "CPU Throttling",
            "symptoms": "Processing starts but never completes",
            "solution": "Increase CPU limits or reduce processing complexity",
            "test": "Monitor CPU usage in container"
        },
        {
            "issue": "Blocking I/O Operations",
            "symptoms": "Hangs at specific processing steps",
            "solution": "Identify and make I/O operations async or timeout",
            "test": "Add detailed logging to each I/O operation"
        },
        {
            "issue": "Import/Module Loading",
            "symptoms": "Hangs when loading heavy dependencies",
            "solution": "Pre-load modules or use lighter alternatives",
            "test": "Add logging around all import statements"
        },
        {
            "issue": "Database/Redis Deadlocks",
            "symptoms": "Hangs when accessing shared resources",
            "solution": "Add connection timeouts and retry logic",
            "test": "Monitor Redis connections and queries"
        }
    ]
    
    print(f"🎯 TOP SUSPECTED ISSUES:")
    for i, item in enumerate(issues_and_solutions, 1):
        print(f"\n{i}. {item['issue']}")
        print(f"   Symptoms: {item['symptoms']}")
        print(f"   Solution: {item['solution']}")
        print(f"   Test: {item['test']}")

def main():
    """Run comprehensive worker isolation analysis."""
    
    print("🎯 ASYNC WORKER ISOLATION & ANALYSIS")
    print("=" * 40)
    
    # Test 1: Isolate hanging point
    result = test_minimal_worker_steps()
    
    print(f"\n📊 ISOLATION RESULTS")
    print("=" * 20)
    
    if result == "hanging_in_worker":
        print(f"✅ ISOLATION SUCCESSFUL!")
        print(f"   🎯 Issue: Worker process hangs INSIDE the processing logic")
        print(f"   🔍 Location: After 'running' status, during UnifiedSyncProcessor execution")
        print(f"   💡 Solution: Replace/simplify the processing logic")
        
        # Create minimal worker
        minimal_code = create_ultra_minimal_worker()
        
        print(f"\n🛠️  RECOMMENDED IMMEDIATE ACTION:")
        print(f"   1. Replace UnifiedSyncProcessor with minimal citation extraction")
        print(f"   2. Test if minimal worker completes successfully")
        print(f"   3. Gradually add back features to find exact hanging point")
        
    elif result == "hanging_before_worker":
        print(f"⚠️  ISOLATION PARTIAL")
        print(f"   🎯 Issue: Hangs before worker starts processing")
        print(f"   🔍 Location: In task queuing or worker startup")
        print(f"   💡 Solution: Investigate Redis/RQ infrastructure")
        
    elif result == "sync":
        print(f"⚠️  THRESHOLD ISSUE")
        print(f"   🎯 Issue: Text not large enough to trigger async")
        print(f"   💡 Solution: Lower async threshold or use larger test text")
        
    else:
        print(f"❌ ISOLATION FAILED")
        print(f"   🎯 Issue: Couldn't determine hanging point")
        print(f"   💡 Solution: Add more detailed logging")
    
    # Analyze container environment
    analyze_container_environment()

if __name__ == "__main__":
    main()
