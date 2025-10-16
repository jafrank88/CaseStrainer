#!/usr/bin/env python3
"""
Test that sync/async routing works correctly after re-enabling async
"""
import requests
import time
import json

base_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

print("="*60)
print("TESTING SYNC/ASYNC ROUTING")
print("="*60)

# Test 1: Small text - should use SYNC
print("\n" + "="*60)
print("TEST 1: SMALL TEXT (should use SYNC processing)")
print("="*60)

small_text = "This case cites 123 Wn.2d 456 and 789 P.3d 101."
print(f"Text length: {len(small_text)} chars")

response = requests.post(base_url, json={
    "type": "text",
    "text": small_text
}, timeout=30)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
    print(f"✓ Processing mode: {processing_mode}")
    print(f"  Citations: {len(result.get('citations', []))}")
    print(f"  Task ID present: {'task_id' in result}")
    
    if processing_mode == 'immediate':
        print("  ✅ CORRECT: Used sync processing for small text")
    else:
        print(f"  ⚠️  UNEXPECTED: Used {processing_mode} instead of sync")
else:
    print(f"✗ Error: {response.status_code}")

# Test 2: URL (PDF) - should use ASYNC
print("\n" + "="*60)
print("TEST 2: URL/PDF (should use ASYNC processing)")
print("="*60)

pdf_url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"
print(f"URL: {pdf_url}")

response = requests.post(base_url, json={
    "type": "url",
    "url": pdf_url
}, timeout=30)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    processing_mode = result.get('metadata', {}).get('processing_mode', 'unknown')
    task_id = result.get('task_id')
    
    print(f"✓ Processing mode: {processing_mode}")
    print(f"  Task ID: {task_id}")
    print(f"  Has task_id: {task_id is not None}")
    
    if processing_mode == 'queued':
        print("  ✅ CORRECT: Using async processing for PDF")
        
        # Poll for completion
        print("\n  Polling for completion (30 seconds max)...")
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        
        for i in range(30):
            time.sleep(1)
            status_response = requests.get(status_url, timeout=10)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status', 'unknown')
                
                if i % 5 == 0:
                    print(f"    [{i+1}s] Status: {status}")
                
                if status == 'completed':
                    citations_count = len(status_data.get('citations', []))
                    print(f"\n  ✅ ASYNC COMPLETED!")
                    print(f"     Citations: {citations_count}")
                    break
                elif status == 'failed':
                    print(f"\n  ✗ Failed: {status_data.get('error')}")
                    break
        else:
            print(f"\n  ⏱️ Still processing after 30s")
            
    elif processing_mode == 'immediate' or processing_mode == 'sync_fallback':
        print(f"  ⚠️  Used {processing_mode} instead of async")
        print(f"     (This is OK if Redis is unavailable)")
    else:
        print(f"  ⚠️  UNEXPECTED: {processing_mode}")
else:
    print(f"✗ Error: {response.status_code}")

print("\n" + "="*60)
print("TESTS COMPLETE")
print("="*60)
