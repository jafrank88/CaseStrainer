#!/usr/bin/env python3

import requests
import json
import time

def test_large_content_routing():
    """Test routing consistency for large content that should be async."""
    
    print("🔄 LARGE CONTENT ROUTING TEST")
    print("=" * 60)
    
    # Create content larger than 5KB threshold
    base_text = '''State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022). The court also cited Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 355 P.3d 258 (2015). Another important case is Miranda v. Arizona, 384 U.S. 436 (1966). The Supreme Court in Mapp v. Ohio, 367 U.S. 643 (1961), established the exclusionary rule. Additionally, Terry v. Ohio, 392 U.S. 1 (1968), defined reasonable suspicion standards.'''
    
    # Repeat to make it larger than 5KB
    multiplier = 15  # This should make it > 5KB
    test_text = (base_text + '\n\n') * multiplier
    
    print(f"📏 Test content size: {len(test_text)} bytes")
    print(f"📏 Sync threshold: 5120 bytes (5KB)")
    print(f"📏 Expected routing: {'SYNC' if len(test_text) < 5120 else 'ASYNC'}")
    print()
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    results = {}
    
    # Test 1: Direct text input (form data)
    print("🧪 TEST 1: Form Data Input")
    print("-" * 40)
    
    data1 = {"text": test_text, "type": "text"}
    
    try:
        start_time = time.time()
        response1 = requests.post(url, data=data1, timeout=30)
        response_time = time.time() - start_time
        
        if response1.status_code == 200:
            result1 = response1.json()
            processing_mode1 = result1.get('metadata', {}).get('processing_mode', 'unknown')
            task_id1 = result1.get('task_id')
            
            if task_id1:
                processing_mode1 = 'queued'
                print(f"   📊 Result: QUEUED (async) - Task ID: {task_id1}")
                print(f"   ⏱️  Response time: {response_time:.2f}s (should be fast for queuing)")
            else:
                print(f"   📊 Result: {processing_mode1.upper()}")
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   📋 Citations found: {len(result1.get('citations', []))}")
            
            results['form_data'] = {
                'mode': processing_mode1,
                'citations': len(result1.get('citations', [])),
                'task_id': task_id1,
                'response_time': response_time
            }
        else:
            print(f"   ❌ Error: {response1.status_code}")
            print(f"   Response: {response1.text[:200]}...")
            results['form_data'] = {'error': response1.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['form_data'] = {'error': str(e)}
    
    print()
    
    # Test 2: JSON input
    print("🧪 TEST 2: JSON Input")
    print("-" * 40)
    
    json_data = {"text": test_text, "type": "text"}
    headers = {'Content-Type': 'application/json'}
    
    try:
        start_time = time.time()
        response2 = requests.post(url, json=json_data, headers=headers, timeout=30)
        response_time = time.time() - start_time
        
        if response2.status_code == 200:
            result2 = response2.json()
            processing_mode2 = result2.get('metadata', {}).get('processing_mode', 'unknown')
            task_id2 = result2.get('task_id')
            
            if task_id2:
                processing_mode2 = 'queued'
                print(f"   📊 Result: QUEUED (async) - Task ID: {task_id2}")
                print(f"   ⏱️  Response time: {response_time:.2f}s (should be fast for queuing)")
            else:
                print(f"   📊 Result: {processing_mode2.upper()}")
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   📋 Citations found: {len(result2.get('citations', []))}")
            
            results['json_input'] = {
                'mode': processing_mode2,
                'citations': len(result2.get('citations', [])),
                'task_id': task_id2,
                'response_time': response_time
            }
        else:
            print(f"   ❌ Error: {response2.status_code}")
            print(f"   Response: {response2.text[:200]}...")
            results['json_input'] = {'error': response2.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['json_input'] = {'error': str(e)}
    
    print()
    
    # Test 3: Third request to check for any caching/state issues
    print("🧪 TEST 3: Third Request (Form Data)")
    print("-" * 40)
    
    time.sleep(1)  # Small delay
    
    try:
        start_time = time.time()
        response3 = requests.post(url, data=data1, timeout=30)
        response_time = time.time() - start_time
        
        if response3.status_code == 200:
            result3 = response3.json()
            processing_mode3 = result3.get('metadata', {}).get('processing_mode', 'unknown')
            task_id3 = result3.get('task_id')
            
            if task_id3:
                processing_mode3 = 'queued'
                print(f"   📊 Result: QUEUED (async) - Task ID: {task_id3}")
                print(f"   ⏱️  Response time: {response_time:.2f}s")
            else:
                print(f"   📊 Result: {processing_mode3.upper()}")
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   📋 Citations found: {len(result3.get('citations', []))}")
            
            results['third_request'] = {
                'mode': processing_mode3,
                'citations': len(result3.get('citations', [])),
                'task_id': task_id3,
                'response_time': response_time
            }
        else:
            print(f"   ❌ Error: {response3.status_code}")
            results['third_request'] = {'error': response3.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['third_request'] = {'error': str(e)}
    
    print()
    
    # Analysis
    print("🔍 ROUTING CONSISTENCY ANALYSIS")
    print("=" * 60)
    
    modes = []
    response_times = []
    
    for test_name, result in results.items():
        if 'mode' in result:
            modes.append(result['mode'])
            response_times.append(result.get('response_time', 0))
            print(f"   {test_name:15}: {result['mode']:10} | Time: {result.get('response_time', 0):.2f}s")
        else:
            print(f"   {test_name:15}: ERROR - {result.get('error', 'unknown')}")
    
    print()
    
    # Check consistency
    unique_modes = set(modes)
    if len(unique_modes) == 1:
        mode = list(unique_modes)[0]
        print(f"✅ CONSISTENT: All requests used '{mode}' processing")
        
        if mode == 'queued' and len(test_text) >= 5120:
            print("✅ CORRECT: Large content properly routed to async processing")
        elif mode == 'immediate' and len(test_text) < 5120:
            print("✅ CORRECT: Small content properly routed to sync processing")
        else:
            print(f"⚠️  UNEXPECTED: Content size {len(test_text)} bytes with mode '{mode}'")
            
        # Check response times for async
        if mode == 'queued':
            avg_time = sum(response_times) / len(response_times) if response_times else 0
            print(f"   Average queue time: {avg_time:.2f}s (should be < 1s for queuing)")
            
    elif len(unique_modes) > 1:
        print("❌ INCONSISTENT: Different processing modes detected!")
        print(f"   Modes found: {list(unique_modes)}")
        print("   🚨 This is the routing inconsistency issue!")
    else:
        print("⚠️  NO VALID RESULTS: All requests failed")
    
    print()
    
    # Check for any async tasks
    async_tasks = [(name, result) for name, result in results.items() if result.get('task_id')]
    if async_tasks:
        print("⏳ CHECKING ASYNC TASK STATUS...")
        print("-" * 40)
        
        for test_name, result in async_tasks:
            task_id = result['task_id']
            print(f"   Task {task_id} ({test_name}):")
            
            try:
                status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
                status_response = requests.get(status_url, timeout=10)
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    status = status_result.get('status', 'unknown')
                    print(f"      Status: {status}")
                    
                    if status == 'completed':
                        citations_count = len(status_result.get('citations', []))
                        print(f"      Citations: {citations_count}")
                    elif status == 'failed':
                        print(f"      Error: {status_result.get('error', 'unknown')}")
                else:
                    print(f"      Status check failed: {status_response.status_code}")
                    
            except Exception as e:
                print(f"      Status check error: {e}")
        
        print()
    
    # Final summary
    print("🎯 ROUTING ANALYSIS SUMMARY")
    print("=" * 60)
    
    print(f"Content size: {len(test_text):,} bytes")
    print(f"Threshold: 5,120 bytes (5KB)")
    print(f"Expected: {'async' if len(test_text) >= 5120 else 'sync'}")
    print(f"Actual modes: {list(unique_modes)}")
    print()
    
    if len(unique_modes) == 1:
        expected_mode = 'queued' if len(test_text) >= 5120 else 'immediate'
        actual_mode = list(unique_modes)[0]
        
        if actual_mode == expected_mode:
            print("🎉 SUCCESS: Routing is working correctly and consistently")
        else:
            print(f"⚠️  ISSUE: Expected '{expected_mode}' but got '{actual_mode}'")
    else:
        print("🚨 CRITICAL: Routing inconsistency detected!")
        print("   The same content is being processed differently on different requests")
        print("   This needs immediate investigation")

if __name__ == "__main__":
    test_large_content_routing()
