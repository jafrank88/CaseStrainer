#!/usr/bin/env python3

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def test_comprehensive_routing():
    """Comprehensive test for routing consistency across different scenarios."""
    
    print("🔄 COMPREHENSIVE ROUTING CONSISTENCY TEST")
    print("=" * 70)
    
    url_endpoint = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Small Text (Direct)',
            'data': {'text': 'State v. Johnson, 192 Wash.2d 453 (2022).', 'type': 'text'},
            'expected': 'sync',
            'size': 43
        },
        {
            'name': 'Large Text (Direct)', 
            'data': {'text': ('State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022). ' * 100), 'type': 'text'},
            'expected': 'async',
            'size': 5700
        },
        {
            'name': 'Small Text (JSON)',
            'json': {'text': 'State v. Johnson, 192 Wash.2d 453 (2022).', 'type': 'text'},
            'expected': 'sync',
            'size': 43
        },
        {
            'name': 'Large Text (JSON)',
            'json': {'text': ('State v. Johnson, 192 Wash.2d 453, 509 P.3d 818 (2022). ' * 100), 'type': 'text'},
            'expected': 'async', 
            'size': 5700
        }
    ]
    
    results = {}
    
    # Test each scenario
    for scenario in scenarios:
        name = scenario['name']
        expected = scenario['expected']
        size = scenario['size']
        
        print(f"\n🧪 TESTING: {name}")
        print("-" * 50)
        print(f"   Content size: {size:,} bytes")
        print(f"   Expected: {expected.upper()}")
        
        try:
            start_time = time.time()
            
            if 'json' in scenario:
                response = requests.post(url_endpoint, json=scenario['json'], 
                                       headers={'Content-Type': 'application/json'}, timeout=30)
            else:
                response = requests.post(url_endpoint, data=scenario['data'], timeout=30)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
                task_id = result.get('task_id')
                
                if task_id:
                    actual_mode = 'async'
                    print(f"   📊 Result: QUEUED (async) - Task ID: {task_id}")
                else:
                    actual_mode = 'sync'
                    print(f"   📊 Result: {processing_mode.upper()} (sync)")
                    print(f"   📋 Citations: {len(result.get('citations', []))}")
                
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                
                # Check if result matches expectation
                if actual_mode == expected:
                    print(f"   ✅ CORRECT: Expected {expected}, got {actual_mode}")
                else:
                    print(f"   ❌ INCORRECT: Expected {expected}, got {actual_mode}")
                
                results[name] = {
                    'expected': expected,
                    'actual': actual_mode,
                    'correct': actual_mode == expected,
                    'response_time': response_time,
                    'task_id': task_id,
                    'citations': len(result.get('citations', [])),
                    'size': size
                }
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                results[name] = {'error': response.status_code, 'expected': expected}
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results[name] = {'error': str(e), 'expected': expected}
    
    print(f"\n{'='*70}")
    print("🔍 ROUTING CONSISTENCY ANALYSIS")
    print(f"{'='*70}")
    
    # Analyze results
    correct_count = 0
    total_count = 0
    sync_results = []
    async_results = []
    
    for name, result in results.items():
        if 'actual' in result:
            total_count += 1
            expected = result['expected']
            actual = result['actual']
            correct = result['correct']
            size = result['size']
            
            if correct:
                correct_count += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"   {name:20}: {expected:5} → {actual:5} {status} ({size:,} bytes)")
            
            if expected == 'sync':
                sync_results.append(actual)
            else:
                async_results.append(actual)
        else:
            print(f"   {name:20}: ERROR - {result.get('error', 'unknown')}")
    
    print()
    
    # Summary
    if total_count > 0:
        accuracy = (correct_count / total_count) * 100
        print(f"📊 ROUTING ACCURACY: {correct_count}/{total_count} ({accuracy:.1f}%)")
        
        if accuracy == 100:
            print("🎉 PERFECT: All routing decisions are correct!")
        elif accuracy >= 80:
            print("✅ GOOD: Most routing decisions are correct")
        else:
            print("❌ POOR: Many routing decisions are incorrect")
        
        # Check consistency within categories
        sync_consistent = len(set(sync_results)) <= 1 if sync_results else True
        async_consistent = len(set(async_results)) <= 1 if async_results else True
        
        print(f"🔄 SYNC CONSISTENCY: {'✅' if sync_consistent else '❌'} ({set(sync_results) if sync_results else 'N/A'})")
        print(f"🔄 ASYNC CONSISTENCY: {'✅' if async_consistent else '❌'} ({set(async_results) if async_results else 'N/A'})")
        
        if sync_consistent and async_consistent:
            print("✅ CONSISTENCY: Routing is consistent within each category")
        else:
            print("❌ INCONSISTENCY: Routing varies within categories")
    
    print()
    
    # Test concurrent requests for race conditions
    print("🏃 TESTING CONCURRENT REQUESTS (Race Condition Check)")
    print("-" * 50)
    
    def make_request(i):
        data = {'text': 'State v. Johnson, 192 Wash.2d 453 (2022).', 'type': 'text'}
        try:
            response = requests.post(url_endpoint, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                mode = 'async' if task_id else 'sync'
                return f"Request {i}: {mode}"
            else:
                return f"Request {i}: ERROR {response.status_code}"
        except Exception as e:
            return f"Request {i}: EXCEPTION {e}"
    
    # Run 5 concurrent requests
    with ThreadPoolExecutor(max_workers=5) as executor:
        concurrent_results = list(executor.map(make_request, range(1, 6)))
    
    for result in concurrent_results:
        print(f"   {result}")
    
    # Check if all concurrent results are the same
    concurrent_modes = [r.split(': ')[1] for r in concurrent_results if ': ' in r and 'ERROR' not in r and 'EXCEPTION' not in r]
    concurrent_consistent = len(set(concurrent_modes)) <= 1
    
    print(f"   🔄 CONCURRENT CONSISTENCY: {'✅' if concurrent_consistent else '❌'}")
    if not concurrent_consistent:
        print(f"   🚨 RACE CONDITION DETECTED: {set(concurrent_modes)}")
    
    print()
    
    # Final diagnosis
    print("🎯 FINAL DIAGNOSIS")
    print("=" * 70)
    
    issues = []
    
    if accuracy < 100:
        issues.append(f"Routing accuracy is {accuracy:.1f}% (should be 100%)")
    
    if not sync_consistent:
        issues.append("Sync routing is inconsistent")
    
    if not async_consistent:
        issues.append("Async routing is inconsistent")
    
    if not concurrent_consistent:
        issues.append("Race conditions detected in concurrent requests")
    
    if not issues:
        print("🎉 SUCCESS: Routing is working perfectly!")
        print("   ✅ All routing decisions are correct")
        print("   ✅ Routing is consistent within categories")
        print("   ✅ No race conditions detected")
    else:
        print("⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(f"   ❌ {issue}")
        
        print("\n🔧 RECOMMENDED ACTIONS:")
        if accuracy < 100:
            print("   - Review threshold logic in CitationService.determine_processing_mode()")
        if not sync_consistent or not async_consistent:
            print("   - Check for state/caching issues in routing logic")
        if not concurrent_consistent:
            print("   - Investigate thread safety in routing decision code")

if __name__ == "__main__":
    test_comprehensive_routing()
