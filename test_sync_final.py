"""Test sync mode with longer timeout"""
import requests
import time

API_BASE_URL = "http://localhost:5000/casestrainer/api"
TEST_URL = "https://www.courts.wa.gov/opinions/pdf/1031351.pdf"

print("Testing SYNC mode with 10-minute timeout...")
start = time.time()

response = requests.post(
    f"{API_BASE_URL}/analyze",
    json={
        "url": TEST_URL,
        "verify_citations": True,
        "processing_mode": "sync"
    },
    timeout=600  # 10 minutes
)

elapsed = time.time() - start
print(f"\n✓ Response received in {elapsed:.2f} seconds")
print(f"   Status: {response.status_code}")

data = response.json()
citations = data.get('citations', [])
clusters = data.get('clusters', [])

print(f"\n📊 Results:")
print(f"   Citations: {len(citations)}")
print(f"   Clusters: {len(clusters)}")
print(f"   Processing mode: {data.get('processing_mode', data.get('metadata', {}).get('processing_mode', 'unknown'))}")
print(f"   Status: {data.get('status')}")

if citations:
    verified = sum(1 for c in citations if c.get('verified', False))
    print(f"\n✅ SUCCESS: Found {len(citations)} citations, {len(clusters)} clusters")
    print(f"   Verified: {verified}/{len(citations)}")
    print(f"\n   Sample citations:")
    for i, cit in enumerate(citations[:3], 1):
        print(f"   {i}. {cit.get('citation', 'N/A')}")
        print(f"      - Extracted: {cit.get('extracted_case_name', 'N/A')}")
        print(f"      - Canonical: {cit.get('canonical_name', 'N/A')}")
        print(f"      - Verified: {cit.get('verified', False)}")
else:
    print(f"\n❌ FAILED: No citations found")

