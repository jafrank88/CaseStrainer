import requests
import json
import time

# Test if batch API returns immediately or needs polling
api_key = "***REDACTED_COURTLISTENER_KEY***"
url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"

headers = {
    "Authorization": f"Token {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Use obscure citations that might not be cached
citations = [
    "200 L. Ed. 2d 931",
    "138 S. Ct. 1649", 
    "584 U.S. 554"
]

payload = {"text": " ".join(citations)}

print("Testing batch API timing...")
print(f"Citations: {len(citations)}")

# Time the request
start = time.time()
response = requests.post(url, json=payload, headers=headers)
elapsed = time.time() - start

print(f"\nStatus: {response.status_code}")
print(f"Time: {elapsed:.2f} seconds")

if response.status_code == 200:
    data = response.json()
    print(f"✅ Got immediate results: {len(data)} items")
    
    # Check if results are complete or placeholders
    for i, item in enumerate(data):
        status = item.get('status', 'unknown')
        clusters = item.get('clusters', [])
        citation = item.get('citation', 'unknown')
        
        print(f"\n  [{i+1}] {citation}")
        print(f"      Status: {status}")
        print(f"      Clusters: {len(clusters)}")
        
        if clusters:
            first_cluster = clusters[0]
            case_name = first_cluster.get('case_name')
            print(f"      Case name: {case_name}")
        
        # Check for job_id or async indicator
        if 'job_id' in item:
            print(f"      ⚠️  Has job_id: {item['job_id']} - ASYNC!")
        if status == 202:
            print(f"      ⚠️  Status 202 - ASYNC/PROCESSING!")
            
elif response.status_code == 202:
    print("⚠️  Status 202 (Accepted) - This IS async!")
    print("Response:", response.text[:500])
    
    # Try to extract job ID or polling URL
    try:
        data = response.json()
        if 'job_id' in data:
            print(f"\nJob ID: {data['job_id']}")
            print("Would need to poll for results!")
    except:
        pass
else:
    print(f"Error: {response.text[:200]}")

print("\n" + "="*60)
print("Conclusion:")
if elapsed < 2:
    print("✅ FAST response (<2s) - likely synchronous")
else:
    print("⚠️  SLOW response (>2s) - might be async or just slow network")
