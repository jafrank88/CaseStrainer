"""
Test if batch size or text length causes 401
"""

import requests
from src.config import COURTLISTENER_API_KEY

headers = {
    'Authorization': f'Token {COURTLISTENER_API_KEY}',
    'Accept': 'application/json'
}

url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"

# Test 1: Single citation (should work)
print("Test 1: Single citation")
payload1 = {"text": "347 U.S. 483"}
r1 = requests.post(url, json=payload1, headers=headers, timeout=30)
print(f"  Status: {r1.status_code}")

# Test 2: 5 citations
print("\nTest 2: 5 citations")
payload2 = {"text": "347 U.S. 483 410 U.S. 113 384 U.S. 436 123 F.3d 456 456 F.2d 789"}
r2 = requests.post(url, json=payload2, headers=headers, timeout=30)
print(f"  Status: {r2.status_code}")

# Test 3: 20 citations
print("\nTest 3: 20 citations")
citations = ["347 U.S. 483"] * 20  # Same citation repeated
payload3 = {"text": " ".join(citations)}
r3 = requests.post(url, json=payload3, headers=headers, timeout=30)
print(f"  Status: {r3.status_code}")
print(f"  Text length: {len(payload3['text'])}")

# Test 4: 50 citations (our failing case)
print("\nTest 4: 50 citations")
citations = ["347 U.S. 483"] * 50
payload4 = {"text": " ".join(citations)}
r4 = requests.post(url, json=payload4, headers=headers, timeout=30)
print(f"  Status: {r4.status_code}")
print(f"  Text length: {len(payload4['text'])}")

print("\nConclusion:")
if r1.status_code == 200 and r4.status_code != 200:
    print("  Batch size limit exists - need to chunk requests")
elif all(r.status_code == 200 for r in [r1, r2, r3, r4]):
    print("  All succeeded - issue is elsewhere")
else:
    print(f"  Unexpected pattern: {[r.status_code for r in [r1, r2, r3, r4]]}")
