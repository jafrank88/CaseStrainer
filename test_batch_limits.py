import requests
import json

# Test different batch sizes to find the limit
api_key = "***REDACTED_COURTLISTENER_KEY***"
url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"

headers = {
    "Authorization": f"Token {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Generate test citations
test_citations = [
    "200 L. Ed. 2d 931", "138 S. Ct. 1649", "584 U.S. 554",
    "572 U.S. 782", "188 L. Ed. 2d 1071", "134 S. Ct. 2024",
    "436 U.S. 49", "98 S. Ct. 1670", "56 L. Ed. 2d 106",
    "309 U.S. 506", "60 S. Ct. 653", "84 L. Ed. 894",
    "476 U.S. 877", "106 S. Ct. 2305", "90 L. Ed. 2d 881",
    "532 U.S. 411", "149 L. Ed. 2d 623", "121 S. Ct. 1589",
    "523 U.S. 751", "140 L. Ed. 2d 981", "118 S. Ct. 1700"
]

# Test different batch sizes
batch_sizes = [5, 10, 20, 30, 50]

for size in batch_sizes:
    batch = test_citations[:size]
    payload = {"text": " ".join(batch)}
    
    print(f"\n{'='*60}")
    print(f"Testing batch size: {size}")
    print(f"Citations: {len(batch)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Received {len(data)} results")
            
            # Check if all have clusters
            with_clusters = sum(1 for item in data if item.get('clusters'))
            print(f"   {with_clusters}/{len(data)} have clusters")
        elif response.status_code == 400:
            print(f"❌ BAD REQUEST - Batch size {size} might be too large")
            print(f"   Error: {response.text[:200]}")
        else:
            print(f"⚠️  Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")

print(f"\n{'='*60}")
print("Testing complete!")
