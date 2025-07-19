#!/usr/bin/env python3
"""
Production Server Performance and Load Testing
Tests performance characteristics and load handling capabilities
"""

import requests
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test configuration
BASE_URL = "https://wolf.law.uw.edu"
API_ENDPOINT = f"{BASE_URL}/casestrainer/api/analyze"
HEALTH_ENDPOINT = f"{BASE_URL}/casestrainer/api/health"

def test_response_time_baseline():
    """Test baseline response times for different input sizes"""
    print("Testing Response Time Baseline...")
    
    test_cases = [
        {
            "name": "Short text (1 citation)",
            "text": "In Roe v. Wade, 410 U.S. 113 (1973), the court held that...",
            "expected_time": 2.0
        },
        {
            "name": "Medium text (3 citations)",
            "text": """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)""",
            "expected_time": 5.0
        },
        {
            "name": "Long text (10+ citations)",
            "text": "In Roe v. Wade, 410 U.S. 113 (1973), the court held that... " * 20 + "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that... " * 20,
            "expected_time": 10.0
        }
    ]
    
    results = []
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        data = {"text": case['text'], "source_type": "text"}
        
        try:
            start_time = time.time()
            response = requests.post(API_ENDPOINT, json=data, timeout=30)
            processing_time = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Processing time: {processing_time:.2f} seconds")
            print(f"Expected time: {case['expected_time']} seconds")
            
            if response.status_code in [200, 202]:
                performance_ok = processing_time <= case['expected_time']
                print(f"Performance: {'✅ Good' if performance_ok else '❌ Slow'}")
                
                results.append({
                    'name': case['name'],
                    'time': processing_time,
                    'expected': case['expected_time'],
                    'status': response.status_code,
                    'success': True
                })
            else:
                print(f"❌ Request failed: {response.status_code}")
                results.append({
                    'name': case['name'],
                    'time': 0,
                    'expected': case['expected_time'],
                    'status': response.status_code,
                    'success': False
                })
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'name': case['name'],
                'time': 0,
                'expected': case['expected_time'],
                'status': 'error',
                'success': False
            })
    
    return results

def test_concurrent_load(concurrent_users=10, requests_per_user=5):
    """Test system performance under concurrent load"""
    print(f"\nTesting Concurrent Load ({concurrent_users} users, {requests_per_user} requests each)...")
    
    def make_user_requests(user_id):
        """Make multiple requests for a single user"""
        user_results = []
        
        for req_id in range(requests_per_user):
            test_text = f"User {user_id}, Request {req_id+1}: In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995)"
            data = {"text": test_text, "source_type": "text"}
            
            try:
                start_time = time.time()
                response = requests.post(API_ENDPOINT, json=data, timeout=30)
                processing_time = time.time() - start_time
                
                user_results.append({
                    'user_id': user_id,
                    'request_id': req_id + 1,
                    'status': response.status_code,
                    'time': processing_time,
                    'success': response.status_code in [200, 202]
                })
                
            except Exception as e:
                user_results.append({
                    'user_id': user_id,
                    'request_id': req_id + 1,
                    'status': 'error',
                    'time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        return user_results
    
    # Execute concurrent requests
    all_results = []
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(make_user_requests, i+1) for i in range(concurrent_users)]
        
        for future in as_completed(futures):
            user_results = future.result()
            all_results.extend(user_results)
    
    # Analyze results
    successful_requests = [r for r in all_results if r['success']]
    failed_requests = [r for r in all_results if not r['success']]
    
    if successful_requests:
        response_times = [r['time'] for r in successful_requests]
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"\nLoad Test Results:")
        print(f"Total requests: {len(all_results)}")
        print(f"Successful: {len(successful_requests)}")
        print(f"Failed: {len(failed_requests)}")
        print(f"Success rate: {len(successful_requests)/len(all_results)*100:.1f}%")
        print(f"Average response time: {avg_time:.2f}s")
        print(f"Median response time: {median_time:.2f}s")
        print(f"Min response time: {min_time:.2f}s")
        print(f"Max response time: {max_time:.2f}s")
        
        # Performance assessment
        if avg_time <= 5.0 and len(successful_requests)/len(all_results) >= 0.9:
            print("✅ Load test passed - good performance under load")
        elif avg_time <= 10.0 and len(successful_requests)/len(all_results) >= 0.8:
            print("⚠️  Load test acceptable - moderate performance under load")
        else:
            print("❌ Load test failed - poor performance under load")
    else:
        print("❌ No successful requests in load test")
    
    return all_results

def test_memory_usage():
    """Test for memory leaks by making many requests"""
    print("\nTesting Memory Usage (Making 50 requests)...")
    
    response_times = []
    memory_indicators = []
    
    for i in range(50):
        test_text = f"Memory test {i+1}: In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995)"
        data = {"text": test_text, "source_type": "text"}
        
        try:
            start_time = time.time()
            response = requests.post(API_ENDPOINT, json=data, timeout=30)
            processing_time = time.time() - start_time
            
            if response.status_code in [200, 202]:
                response_times.append(processing_time)
                
                # Check if response time is increasing (potential memory leak indicator)
                if len(response_times) > 10:
                    recent_avg = statistics.mean(response_times[-10:])
                    early_avg = statistics.mean(response_times[:10])
                    memory_indicators.append(recent_avg - early_avg)
            
            if (i + 1) % 10 == 0:
                print(f"Completed {i+1}/50 requests...")
                
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    
    if response_times:
        print(f"\nMemory Test Results:")
        print(f"Total successful requests: {len(response_times)}")
        print(f"Average response time: {statistics.mean(response_times):.2f}s")
        print(f"First 10 requests avg: {statistics.mean(response_times[:10]):.2f}s")
        print(f"Last 10 requests avg: {statistics.mean(response_times[-10:]):.2f}s")
        
        if memory_indicators:
            avg_increase = statistics.mean(memory_indicators)
            if avg_increase < 1.0:
                print("✅ No significant memory leak detected")
            elif avg_increase < 3.0:
                print("⚠️  Moderate performance degradation detected")
            else:
                print("❌ Significant performance degradation - possible memory leak")
    
    return response_times

def test_async_vs_sync_processing():
    """Test the difference between async and sync processing"""
    print("\nTesting Async vs Sync Processing...")
    
    # Test cases that should trigger different processing modes
    test_cases = [
        {
            "name": "Short text (should be sync)",
            "text": "In Roe v. Wade, 410 U.S. 113 (1973), the court held that...",
            "expected_mode": "sync"
        },
        {
            "name": "Long text (should be async)",
            "text": "This is a long document. " * 500 + "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that...",
            "expected_mode": "async"
        }
    ]
    
    results = []
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        data = {"text": case['text'], "source_type": "text"}
        
        try:
            start_time = time.time()
            response = requests.post(API_ENDPOINT, json=data, timeout=30)
            processing_time = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Processing time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                mode = "sync"
                print("✅ Processed synchronously")
            elif response.status_code == 202:
                mode = "async"
                print("✅ Queued for async processing")
            else:
                mode = "unknown"
                print(f"❌ Unexpected status: {response.status_code}")
            
            expected_correct = mode == case['expected_mode']
            print(f"Mode: {mode} (Expected: {case['expected_mode']})")
            print(f"Mode correct: {'✅ Yes' if expected_correct else '❌ No'}")
            
            results.append({
                'name': case['name'],
                'actual_mode': mode,
                'expected_mode': case['expected_mode'],
                'correct': expected_correct,
                'time': processing_time
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'name': case['name'],
                'actual_mode': 'error',
                'expected_mode': case['expected_mode'],
                'correct': False,
                'time': 0
            })
    
    return results

def test_throughput():
    """Test maximum throughput (requests per second)"""
    print("\nTesting Maximum Throughput...")
    
    # Make requests as fast as possible
    start_time = time.time()
    successful_requests = 0
    total_requests = 20
    
    for i in range(total_requests):
        test_text = f"Throughput test {i+1}: In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995)"
        data = {"text": test_text, "source_type": "text"}
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=10)
            if response.status_code in [200, 202]:
                successful_requests += 1
        except:
            pass
    
    end_time = time.time()
    total_time = end_time - start_time
    throughput = successful_requests / total_time
    
    print(f"Throughput Results:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Successful requests: {successful_requests}/{total_requests}")
    print(f"Throughput: {throughput:.2f} requests/second")
    
    if throughput >= 2.0:
        print("✅ Good throughput")
    elif throughput >= 1.0:
        print("⚠️  Moderate throughput")
    else:
        print("❌ Low throughput")
    
    return throughput

def main():
    """Run all performance tests"""
    print("🚀 Production Server Performance Test Suite")
    print("=" * 60)
    
    # Run all performance tests
    baseline_results = test_response_time_baseline()
    load_results = test_concurrent_load()
    memory_results = test_memory_usage()
    async_results = test_async_vs_sync_processing()
    throughput = test_throughput()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Performance Test Summary")
    print(f"{'='*60}")
    
    # Baseline test summary
    baseline_success = sum(1 for r in baseline_results if r['success'])
    print(f"Baseline tests: {baseline_success}/{len(baseline_results)} passed")
    
    # Load test summary
    if load_results:
        load_success = sum(1 for r in load_results if r['success'])
        print(f"Load test: {load_success}/{len(load_results)} requests successful")
    
    # Memory test summary
    if memory_results:
        print(f"Memory test: {len(memory_results)} requests completed")
    
    # Async test summary
    async_correct = sum(1 for r in async_results if r['correct'])
    print(f"Async mode tests: {async_correct}/{len(async_results)} correct")
    
    # Throughput summary
    print(f"Throughput: {throughput:.2f} requests/second")
    
    # Overall assessment
    overall_score = 0
    if baseline_success == len(baseline_results):
        overall_score += 1
    if load_results and sum(1 for r in load_results if r['success'])/len(load_results) >= 0.8:
        overall_score += 1
    if memory_results and len(memory_results) >= 40:
        overall_score += 1
    if async_correct == len(async_results):
        overall_score += 1
    if throughput >= 1.0:
        overall_score += 1
    
    print(f"\nOverall Performance Score: {overall_score}/5")
    
    if overall_score >= 4:
        print("🎉 Excellent performance!")
    elif overall_score >= 3:
        print("✅ Good performance")
    else:
        print("⚠️  Performance needs improvement")

if __name__ == "__main__":
    main() 