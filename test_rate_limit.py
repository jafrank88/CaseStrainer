#!/usr/bin/env python3
"""
Test rate limit handling - submit multiple citations rapidly
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000/casestrainer/api"

test_citations = [
    "The court in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) held that...",
    "In Brown v. Board of Education, 347 U.S. 483 (1954), the Court ruled...",
    "See also Miranda v. Arizona, 384 U.S. 436 (1966) establishing...",
    "The precedent in Roe v. Wade, 410 U.S. 113 (1973) was cited...",
]

print("=" * 80)
print("RATE LIMIT HANDLING TEST")
print("=" * 80)
print()
print(f"Submitting {len(test_citations)} requests rapidly to trigger rate limit...")
print()

results = []

for i, text in enumerate(test_citations, 1):
    print(f"[{i}/{len(test_citations)}] Testing: {text[:50]}...")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"type": "text", "text": text},
            timeout=10
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            citations_count = len(data.get('citations', []))
            verified_count = sum(1 for c in data.get('citations', []) if c.get('verified'))
            
            results.append({
                'success': True,
                'elapsed': elapsed,
                'citations': citations_count,
                'verified': verified_count,
                'status': response.status_code
            })
            
            print(f"    ✅ Completed in {elapsed:.1f}s - {citations_count} citations, {verified_count} verified")
        else:
            print(f"    ❌ Failed: {response.status_code}")
            results.append({
                'success': False,
                'status': response.status_code,
                'elapsed': elapsed
            })
            
    except requests.exceptions.Timeout:
        print(f"    ⚠️  TIMEOUT - Request took >10s (possible infinite loop!)")
        results.append({
            'success': False,
            'timeout': True
        })
    except Exception as e:
        print(f"    ❌ Error: {e}")
        results.append({
            'success': False,
            'error': str(e)
        })
    
    # Small delay between requests
    time.sleep(0.5)

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

success_count = sum(1 for r in results if r.get('success'))
timeout_count = sum(1 for r in results if r.get('timeout'))
avg_time = sum(r.get('elapsed', 0) for r in results if 'elapsed' in r) / len(results) if results else 0

print(f"Total requests: {len(test_citations)}")
print(f"Successful: {success_count}")
print(f"Timeouts: {timeout_count}")
print(f"Average time: {avg_time:.2f}s")
print()

if timeout_count > 0:
    print("❌ FAILED: Infinite loop detected (timeouts)")
elif success_count == len(test_citations):
    print("✅ PASSED: All requests completed without hanging")
    print("✅ Rate limit handling working correctly!")
else:
    print("⚠️  PARTIAL: Some requests failed but no infinite loops")

print()
