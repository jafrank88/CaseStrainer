#!/usr/bin/env python3
"""
Test sync vs async processing with the same text to identify differences.
"""

import requests
import time

def test_sync_vs_async():
    """Compare sync and async processing results."""
    
    # Small text that should work in both modes
    test_text = """
    In State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007), the court established important precedent.
    The decision in City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) further clarified the law.
    See also Brown v. State, 180 Wn.2d 300, 320 P.3d 800 (2014).
    """
    
    print("🧪 Testing Sync vs Async Processing")
    print("=" * 50)
    
    # Test 1: Small document (should be sync)
    print(f"\n📝 Test 1: Small Document ({len(test_text)} chars)")
    sync_result = test_processing(test_text, "small")
    
    # Test 2: Large document (should be async)
    large_text = test_text + "\n\nPadding content. " * 2000
    print(f"\n📄 Test 2: Large Document ({len(large_text)} chars)")
    async_result = test_processing(large_text, "large")
    
    # Compare results
    print("\n" + "=" * 50)
    print("📊 COMPARISON")
    print("=" * 50)
    
    print(f"Small (sync):  {sync_result['citations']} citations, {sync_result['clusters']} clusters")
    print(f"Large (async): {async_result['citations']} citations, {async_result['clusters']} clusters")
    
    if sync_result['citations'] > 0 and async_result['citations'] == 0:
        print("⚠️ ISSUE: Async processing is not finding citations that sync processing finds")
    elif sync_result['citations'] > 0 and async_result['citations'] > 0:
        print("✅ Both sync and async processing are working")
    else:
        print("❌ Neither processing mode is finding citations")

def test_processing(text, label):
    """Test processing and return results."""
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": text},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"  ❌ {label} request failed: {response.status_code}")
            return {'citations': 0, 'clusters': 0, 'mode': 'failed'}
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        
        # If async, wait for completion
        if data.get('task_id'):
            print(f"  🔄 {label} queued as async task: {data['task_id']}")
            data = wait_for_task_completion(data['task_id'])
            processing_mode = 'async'
        else:
            print(f"  ⚡ {label} processed synchronously")
            processing_mode = 'sync'
        
        citations_count = len(data.get('citations', []))
        clusters_count = len(data.get('clusters', []))
        
        print(f"  📊 {label} results: {citations_count} citations, {clusters_count} clusters ({processing_mode})")
        
        # Show sample citations
        if citations_count > 0:
            citations = data.get('citations', [])
            print(f"  📋 Sample citations:")
            for i, citation in enumerate(citations[:3]):
                print(f"    {i+1}. {citation.get('citation', 'N/A')}")
        
        return {
            'citations': citations_count,
            'clusters': clusters_count,
            'mode': processing_mode
        }
        
    except Exception as e:
        print(f"  💥 {label} test failed: {e}")
        return {'citations': 0, 'clusters': 0, 'mode': 'error'}

def wait_for_task_completion(task_id, max_wait=30):
    """Wait for async task to complete and return results."""
    for attempt in range(max_wait):
        try:
            response = requests.get(
                f"http://localhost:8080/casestrainer/api/task_status/{task_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                if status == 'completed':
                    return data
                elif status == 'failed':
                    print(f"    ❌ Task failed: {data.get('error')}")
                    return {'citations': [], 'clusters': []}
                    
            time.sleep(1)
            
        except Exception as e:
            print(f"    ⚠️ Status check failed: {e}")
            time.sleep(1)
    
    print(f"    ⏰ Task timed out after {max_wait} seconds")
    return {'citations': [], 'clusters': []}

if __name__ == "__main__":
    test_sync_vs_async()
