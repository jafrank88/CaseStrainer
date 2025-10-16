#!/usr/bin/env python
"""Diagnose URL processing issue"""

import requests

# Test with the wolf endpoint
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

# Try a small test first
test_url = "https://www.courtlistener.com/opinion/10460933/robert-cassell-v-state-of-alaska/"

print("="*70)
print("DIAGNOSING URL PROCESSING ISSUE")
print("="*70)

print("\nTest 1: Checking if endpoint is responsive...")
try:
    response = requests.post(
        url,
        json={'text': 'Test: 410 U.S. 113', 'type': 'text'},
        verify=False,
        timeout=5
    )
    print(f"✅ Endpoint is responsive: {response.status_code}")
except Exception as e:
    print(f"❌ Endpoint not responding: {e}")

print("\nTest 2: Submitting URL (this might hang)...")
print(f"URL: {test_url}")
print("Timeout: 30 seconds")

try:
    response = requests.post(
        url,
        json={'url': test_url, 'type': 'url'},
        verify=False,
        timeout=30
    )
    print(f"✅ Response received: {response.status_code}")
    data = response.json()
    
    if 'task_id' in data:
        print(f"   Processing Mode: ASYNC")
        print(f"   Task ID: {data['task_id']}")
    elif data.get('metadata', {}).get('sync_complete'):
        print(f"   Processing Mode: SYNC (completed immediately)")
        print(f"   Citations found: {len(data.get('citations', []))}")
    else:
        print(f"   Unknown mode")
        
except requests.exceptions.Timeout:
    print("❌ REQUEST TIMED OUT after 30 seconds")
    print("\nLIKELY CAUSE:")
    print("  - URL content is large, triggering async processing")
    print("  - Async has verification enabled")
    print("  - CourtListener is rate limiting or slow")
    print("  - Worker is hanging on verification")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

print("""
IMMEDIATE FIX:
─────────────
Option 1: Temporarily disable verification in async path
   File: src/progress_manager.py, line 1617
   Change: enable_verification=True → enable_verification=False

Option 2: Check CourtListener rate limits
   The rate limits may have been hit again
   Wait 1 hour for reset

Option 3: Check worker logs
   docker logs casestrainer-rqworker1-prod
   Look for hanging verification calls

LONG-TERM FIX:
─────────────
Add a timeout wrapper around verification in async processing
so it doesn't hang indefinitely.
""")
