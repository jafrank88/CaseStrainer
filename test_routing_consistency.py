#!/usr/bin/env python3

import requests
import json
import time

def test_routing_consistency():
    """Test routing consistency for the same content via different input methods."""
    
    print("🔄 ROUTING CONSISTENCY TEST")
    print("=" * 60)
    
    # Test content - should be under 5KB for sync processing
    test_text = '''State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022). The court also cited Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 355 P.3d 258 (2015). Another important case is Miranda v. Arizona, 384 U.S. 436 (1966).''' * 10  # Repeat to make it larger
    
    print(f"📏 Test content size: {len(test_text)} bytes")
    print(f"📏 Sync threshold: 5120 bytes (5KB)")
    print(f"📏 Expected routing: {'SYNC' if len(test_text) < 5120 else 'ASYNC'}")
    print()
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    results = {}
    
    # Test 1: Direct text input
    print("🧪 TEST 1: Direct Text Input")
    print("-" * 40)
    
    data1 = {"text": test_text, "type": "text"}
    
    try:
        response1 = requests.post(url, data=data1, timeout=30)
        
        if response1.status_code == 200:
            result1 = response1.json()
            processing_mode1 = result1.get('metadata', {}).get('processing_mode', 'unknown')
            task_id1 = result1.get('task_id')
            
            if task_id1:
                # This was queued (async)
                processing_mode1 = 'queued'
                print(f"   📊 Result: QUEUED (async) - Task ID: {task_id1}")
            else:
                print(f"   📊 Result: {processing_mode1.upper()}")
            
            results['direct_text'] = {
                'mode': processing_mode1,
                'citations': len(result1.get('citations', [])),
                'task_id': task_id1
            }
        else:
            print(f"   ❌ Error: {response1.status_code}")
            results['direct_text'] = {'error': response1.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['direct_text'] = {'error': str(e)}
    
    print()
    
    # Test 2: Same content, second request (to test consistency)
    print("🧪 TEST 2: Same Text Input (Second Request)")
    print("-" * 40)
    
    time.sleep(1)  # Small delay
    
    try:
        response2 = requests.post(url, data=data1, timeout=30)
        
        if response2.status_code == 200:
            result2 = response2.json()
            processing_mode2 = result2.get('metadata', {}).get('processing_mode', 'unknown')
            task_id2 = result2.get('task_id')
            
            if task_id2:
                processing_mode2 = 'queued'
                print(f"   📊 Result: QUEUED (async) - Task ID: {task_id2}")
            else:
                print(f"   📊 Result: {processing_mode2.upper()}")
            
            results['second_request'] = {
                'mode': processing_mode2,
                'citations': len(result2.get('citations', [])),
                'task_id': task_id2
            }
        else:
            print(f"   ❌ Error: {response2.status_code}")
            results['second_request'] = {'error': response2.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['second_request'] = {'error': str(e)}
    
    print()
    
    # Test 3: JSON input (same content)
    print("🧪 TEST 3: JSON Input (Same Content)")
    print("-" * 40)
    
    json_data = {"text": test_text, "type": "text"}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response3 = requests.post(url, json=json_data, headers=headers, timeout=30)
        
        if response3.status_code == 200:
            result3 = response3.json()
            processing_mode3 = result3.get('metadata', {}).get('processing_mode', 'unknown')
            task_id3 = result3.get('task_id')
            
            if task_id3:
                processing_mode3 = 'queued'
                print(f"   📊 Result: QUEUED (async) - Task ID: {task_id3}")
            else:
                print(f"   📊 Result: {processing_mode3.upper()}")
            
            results['json_input'] = {
                'mode': processing_mode3,
                'citations': len(result3.get('citations', [])),
                'task_id': task_id3
            }
        else:
            print(f"   ❌ Error: {response3.status_code}")
            results['json_input'] = {'error': response3.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['json_input'] = {'error': str(e)}
    
    print()
    
    # Analysis
    print("🔍 CONSISTENCY ANALYSIS")
    print("=" * 60)
    
    modes = []
    for test_name, result in results.items():
        if 'mode' in result:
            modes.append(result['mode'])
            print(f"   {test_name}: {result['mode']}")
        else:
            print(f"   {test_name}: ERROR - {result.get('error', 'unknown')}")
    
    print()
    
    # Check consistency
    unique_modes = set(modes)
    if len(unique_modes) == 1:
        print("✅ CONSISTENT: All requests used the same processing mode")
        print(f"   Mode: {list(unique_modes)[0]}")
    elif len(unique_modes) > 1:
        print("❌ INCONSISTENT: Different processing modes detected!")
        print(f"   Modes found: {list(unique_modes)}")
        print("   This indicates a routing inconsistency issue")
    else:
        print("⚠️  NO VALID RESULTS: All requests failed")
    
    print()
    
    # Wait for any async tasks to complete and check results
    async_tasks = [r for r in results.values() if r.get('task_id')]
    if async_tasks:
        print("⏳ WAITING FOR ASYNC TASKS TO COMPLETE...")
        print("-" * 40)
        
        for i, (test_name, result) in enumerate(results.items()):
            if result.get('task_id'):
                task_id = result['task_id']
                print(f"   Checking {test_name} (Task: {task_id})")
                
                # Poll for completion
                for attempt in range(10):
                    try:
                        status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
                        status_response = requests.get(status_url, timeout=10)
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status', 'unknown')
                            
                            if status == 'completed':
                                citations_count = len(status_result.get('citations', []))
                                print(f"      ✅ Completed: {citations_count} citations")
                                results[test_name]['final_citations'] = citations_count
                                break
                            elif status == 'failed':
                                print(f"      ❌ Failed: {status_result.get('error', 'unknown error')}")
                                break
                            else:
                                print(f"      ⏳ Status: {status} (attempt {attempt + 1})")
                                time.sleep(2)
                        else:
                            print(f"      ❌ Status check failed: {status_response.status_code}")
                            break
                            
                    except Exception as e:
                        print(f"      ❌ Status check error: {e}")
                        break
        
        print()
    
    # Final summary
    print("🎯 FINAL SUMMARY")
    print("=" * 60)
    
    print(f"Content size: {len(test_text)} bytes")
    print(f"Expected mode: {'sync' if len(test_text) < 5120 else 'async'}")
    print()
    
    for test_name, result in results.items():
        mode = result.get('mode', 'error')
        citations = result.get('citations', result.get('final_citations', 'N/A'))
        print(f"{test_name:20}: {mode:10} | Citations: {citations}")
    
    print()
    
    if len(unique_modes) == 1:
        print("🎉 SUCCESS: Routing is consistent across all input methods")
    else:
        print("⚠️  ISSUE: Routing inconsistency detected - needs investigation")

if __name__ == "__main__":
    test_routing_consistency()
