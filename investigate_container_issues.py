"""
Investigate Container Issues
Identifies specific container environment problems causing async processing to hang.
"""

import requests
import time
import json

def test_container_resource_usage():
    """Test if container resource constraints are causing issues."""
    
    print("🔍 CONTAINER RESOURCE INVESTIGATION")
    print("=" * 40)
    
    # Test 1: Very minimal processing to see if basic functionality works
    print(f"Test 1: Minimal text processing...")
    minimal_text = "150 Wn.2d 674" * 200  # ~2.8KB, should trigger async
    
    success = test_async_processing(minimal_text, "minimal", timeout=30)
    
    if success == "sync":
        print(f"   ⚠️  Even 2.8KB text processed as sync - threshold issue")
    elif success:
        print(f"   ✅ Minimal async processing works!")
        return True
    else:
        print(f"   ❌ Even minimal async processing hangs")
    
    # Test 2: Check if it's related to verification
    print(f"\nTest 2: Testing without verification...")
    # We can't easily disable verification from here, but we can test with different text
    
    # Test 3: Check if it's related to clustering
    print(f"\nTest 3: Testing with single citation (no clustering)...")
    single_citation_text = "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003). " + "Additional text. " * 200
    
    success = test_async_processing(single_citation_text, "single_citation", timeout=30)
    
    if success:
        print(f"   ✅ Single citation async processing works!")
        return True
    else:
        print(f"   ❌ Single citation async processing also hangs")
    
    return False

def test_async_processing(text, label, timeout=30):
    """Test async processing with specific text."""
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': text}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"   📤 {label} task: {task_id}")
                
                # Quick monitoring
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                for attempt in range(timeout // 3):
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    print(f"   ✅ {label}: Completed in {(attempt + 1) * 3}s, {len(citations)} citations")
                                    return True
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown')
                                    print(f"   ❌ {label}: Failed - {error}")
                                    return False
                            
                            elif 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                print(f"   ✅ {label}: Direct result, {len(citations)} citations")
                                return True
                        
                    except:
                        pass
                    
                    time.sleep(3)
                
                print(f"   ⏰ {label}: Timed out after {timeout}s")
                return False
                
            else:
                # Processed as sync
                citations = result.get('result', {}).get('citations', [])
                print(f"   ⚠️  {label}: Processed as sync, {len(citations)} citations")
                return "sync"
        else:
            print(f"   ❌ {label}: Request failed {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ {label}: Error - {e}")
        return False

def investigate_specific_hang_causes():
    """Investigate specific causes that might make async processing hang."""
    
    print(f"\n🔍 SPECIFIC HANG CAUSE INVESTIGATION")
    print("-" * 40)
    
    potential_causes = [
        "Memory exhaustion in container",
        "CPU throttling/limits",
        "Blocking I/O operations",
        "Database/Redis connection issues", 
        "Import/dependency loading issues",
        "Verification API timeouts",
        "Infinite loops in processing logic",
        "Thread deadlocks",
        "File system access issues"
    ]
    
    print(f"Potential causes to investigate:")
    for i, cause in enumerate(potential_causes, 1):
        print(f"   {i}. {cause}")
    
    # Test some specific scenarios
    print(f"\n🧪 TESTING SPECIFIC SCENARIOS:")
    
    # Scenario 1: Test with text that should be ultra-fast
    print(f"\nScenario 1: Ultra-fast processing text...")
    ultra_fast_text = "150 Wn.2d 674" * 100  # Should be under ultra_fast_threshold
    
    # Force it to be async by making it larger
    async_ultra_fast = ultra_fast_text + " " + "padding " * 500  # ~3KB
    
    success = test_async_processing(async_ultra_fast, "ultra_fast_async", timeout=20)
    
    if success:
        print(f"   ✅ Ultra-fast async works - issue may be with complex processing")
    else:
        print(f"   ❌ Even ultra-fast async hangs - fundamental container issue")
    
    # Scenario 2: Test if it's related to text length
    print(f"\nScenario 2: Different text lengths...")
    
    lengths = [3000, 5000, 10000]  # 3KB, 5KB, 10KB
    
    for length in lengths:
        test_text = "A" * length + " Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003)"
        success = test_async_processing(test_text, f"{length//1000}KB", timeout=15)
        
        if success:
            print(f"   ✅ {length//1000}KB text works")
            break
        else:
            print(f"   ❌ {length//1000}KB text hangs")

def propose_solutions():
    """Propose potential solutions based on investigation."""
    
    print(f"\n💡 PROPOSED SOLUTIONS")
    print("=" * 20)
    
    solutions = [
        {
            "issue": "Container Memory Limits",
            "solution": "Increase container memory allocation",
            "implementation": "Modify docker-compose.yml to add memory limits"
        },
        {
            "issue": "Blocking Verification Calls", 
            "solution": "Disable verification in async processing",
            "implementation": "Set enable_verification=False in async worker"
        },
        {
            "issue": "Complex Processing Logic",
            "solution": "Simplify async processing pipeline",
            "implementation": "Use ultra-fast processing for async tasks"
        },
        {
            "issue": "Threading Issues",
            "solution": "Use process-based isolation instead of threading",
            "implementation": "Replace threading with multiprocessing"
        },
        {
            "issue": "Import/Dependency Loading",
            "solution": "Pre-load dependencies in worker initialization",
            "implementation": "Move imports to worker startup"
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"{i}. {solution['issue']}")
        print(f"   Solution: {solution['solution']}")
        print(f"   Implementation: {solution['implementation']}")
        print()

def main():
    """Run comprehensive container issue investigation."""
    
    print("🎯 CONTAINER ENVIRONMENT INVESTIGATION")
    print("=" * 40)
    
    # Test container resources
    resource_success = test_container_resource_usage()
    
    # Investigate specific causes
    investigate_specific_hang_causes()
    
    # Propose solutions
    propose_solutions()
    
    print(f"\n📊 INVESTIGATION SUMMARY")
    print("=" * 25)
    
    if resource_success:
        print(f"✅ Some async processing works - issue is specific")
    else:
        print(f"❌ All async processing hangs - fundamental container issue")
    
    print(f"\n🔧 RECOMMENDED NEXT STEPS:")
    print(f"1. Try disabling verification in async processing")
    print(f"2. Implement ultra-fast processing for async tasks")
    print(f"3. Add container resource monitoring")
    print(f"4. Consider process-based isolation instead of threading")

if __name__ == "__main__":
    main()
