#!/usr/bin/env python3

import requests
import json
import time

def test_url_routing_consistency():
    """Test routing consistency for URL input vs extracted text."""
    
    print("🌐 URL ROUTING CONSISTENCY TEST")
    print("=" * 60)
    
    # Test with a URL that should have consistent routing
    test_url = "https://httpbin.org/json"  # Returns a small JSON response
    
    url_endpoint = "http://localhost:5000/casestrainer/api/analyze"
    
    results = {}
    
    # Test 1: URL input
    print("🧪 TEST 1: URL Input")
    print("-" * 40)
    print(f"   URL: {test_url}")
    
    data1 = {"url": test_url, "type": "url"}
    
    try:
        start_time = time.time()
        response1 = requests.post(url_endpoint, data=data1, timeout=30)
        response_time = time.time() - start_time
        
        if response1.status_code == 200:
            result1 = response1.json()
            processing_mode1 = result1.get('metadata', {}).get('processing_mode', 'unknown')
            task_id1 = result1.get('task_id')
            
            if task_id1:
                processing_mode1 = 'queued'
                print(f"   📊 Result: QUEUED (async) - Task ID: {task_id1}")
            else:
                print(f"   📊 Result: {processing_mode1.upper()}")
                print(f"   📋 Citations found: {len(result1.get('citations', []))}")
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            
            results['url_input'] = {
                'mode': processing_mode1,
                'citations': len(result1.get('citations', [])),
                'task_id': task_id1,
                'response_time': response_time
            }
        else:
            print(f"   ❌ Error: {response1.status_code}")
            print(f"   Response: {response1.text[:200]}...")
            results['url_input'] = {'error': response1.status_code, 'response': response1.text[:200]}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['url_input'] = {'error': str(e)}
    
    print()
    
    # Test 2: Extract the same content manually and send as text
    print("🧪 TEST 2: Manual Text Extraction")
    print("-" * 40)
    
    try:
        # Manually fetch the URL content
        print("   Fetching URL content manually...")
        url_response = requests.get(test_url, timeout=10)
        
        if url_response.status_code == 200:
            extracted_text = url_response.text
            print(f"   📏 Extracted content size: {len(extracted_text)} bytes")
            print(f"   📏 Expected routing: {'SYNC' if len(extracted_text) < 5120 else 'ASYNC'}")
            
            # Send as text input
            data2 = {"text": extracted_text, "type": "text"}
            
            start_time = time.time()
            response2 = requests.post(url_endpoint, data=data2, timeout=30)
            response_time = time.time() - start_time
            
            if response2.status_code == 200:
                result2 = response2.json()
                processing_mode2 = result2.get('metadata', {}).get('processing_mode', 'unknown')
                task_id2 = result2.get('task_id')
                
                if task_id2:
                    processing_mode2 = 'queued'
                    print(f"   📊 Result: QUEUED (async) - Task ID: {task_id2}")
                else:
                    print(f"   📊 Result: {processing_mode2.upper()}")
                    print(f"   📋 Citations found: {len(result2.get('citations', []))}")
                
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                
                results['manual_text'] = {
                    'mode': processing_mode2,
                    'citations': len(result2.get('citations', [])),
                    'task_id': task_id2,
                    'response_time': response_time,
                    'content_size': len(extracted_text)
                }
            else:
                print(f"   ❌ Error: {response2.status_code}")
                results['manual_text'] = {'error': response2.status_code}
        else:
            print(f"   ❌ URL fetch failed: {url_response.status_code}")
            results['manual_text'] = {'error': f'URL fetch failed: {url_response.status_code}'}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['manual_text'] = {'error': str(e)}
    
    print()
    
    # Test 3: Same URL again to check consistency
    print("🧪 TEST 3: Same URL (Second Request)")
    print("-" * 40)
    
    time.sleep(1)  # Small delay
    
    try:
        start_time = time.time()
        response3 = requests.post(url_endpoint, data=data1, timeout=30)
        response_time = time.time() - start_time
        
        if response3.status_code == 200:
            result3 = response3.json()
            processing_mode3 = result3.get('metadata', {}).get('processing_mode', 'unknown')
            task_id3 = result3.get('task_id')
            
            if task_id3:
                processing_mode3 = 'queued'
                print(f"   📊 Result: QUEUED (async) - Task ID: {task_id3}")
            else:
                print(f"   📊 Result: {processing_mode3.upper()}")
                print(f"   📋 Citations found: {len(result3.get('citations', []))}")
            
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            
            results['url_second'] = {
                'mode': processing_mode3,
                'citations': len(result3.get('citations', [])),
                'task_id': task_id3,
                'response_time': response_time
            }
        else:
            print(f"   ❌ Error: {response3.status_code}")
            results['url_second'] = {'error': response3.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results['url_second'] = {'error': str(e)}
    
    print()
    
    # Analysis
    print("🔍 URL vs TEXT ROUTING ANALYSIS")
    print("=" * 60)
    
    modes = []
    
    for test_name, result in results.items():
        if 'mode' in result:
            modes.append(result['mode'])
            content_size = result.get('content_size', 'N/A')
            print(f"   {test_name:15}: {result['mode']:10} | Time: {result.get('response_time', 0):.2f}s | Size: {content_size}")
        else:
            print(f"   {test_name:15}: ERROR - {result.get('error', 'unknown')}")
    
    print()
    
    # Check consistency
    unique_modes = set(modes)
    if len(unique_modes) == 1:
        print(f"✅ CONSISTENT: All requests used '{list(unique_modes)[0]}' processing")
    elif len(unique_modes) > 1:
        print("❌ INCONSISTENT: Different processing modes detected!")
        print(f"   Modes found: {list(unique_modes)}")
        print("   🚨 This indicates URL routing inconsistency!")
        
        # Check if it's URL vs text inconsistency
        url_modes = [results[k]['mode'] for k in ['url_input', 'url_second'] if k in results and 'mode' in results[k]]
        text_modes = [results[k]['mode'] for k in ['manual_text'] if k in results and 'mode' in results[k]]
        
        if url_modes and text_modes:
            url_mode = url_modes[0] if len(set(url_modes)) == 1 else 'inconsistent'
            text_mode = text_modes[0]
            
            if url_mode != text_mode:
                print(f"   🎯 ROOT CAUSE: URL input → {url_mode}, Text input → {text_mode}")
                print("   This suggests the routing decision happens at different stages")
                print("   for URL vs text input, causing inconsistency")
    else:
        print("⚠️  NO VALID RESULTS: All requests failed")
    
    print()
    
    # Check for any async tasks
    async_tasks = [(name, result) for name, result in results.items() if result.get('task_id')]
    if async_tasks:
        print("⏳ CHECKING ASYNC TASK STATUS...")
        print("-" * 40)
        
        for test_name, result in async_tasks[:2]:  # Check first 2 to avoid spam
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
    
    # Final diagnosis
    print("🎯 ROUTING CONSISTENCY DIAGNOSIS")
    print("=" * 60)
    
    if len(unique_modes) == 1:
        print("✅ ROUTING IS CONSISTENT")
        print("   All input methods (URL, text) use the same routing logic")
    else:
        print("🚨 ROUTING INCONSISTENCY DETECTED")
        print("   Possible causes:")
        print("   1. URL text extraction happens after routing decision")
        print("   2. Different code paths for URL vs text input")
        print("   3. Caching or state issues between requests")
        print("   4. Race conditions in async processing")
        print()
        print("   🔧 RECOMMENDED FIXES:")
        print("   - Ensure URL text extraction happens BEFORE routing decision")
        print("   - Use unified routing logic for all input types")
        print("   - Add logging to track routing decision points")

if __name__ == "__main__":
    test_url_routing_consistency()
