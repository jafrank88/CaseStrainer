"""Check what the API is actually returning"""
import requests
import json

response = requests.post(
    'http://localhost:5000/api/upload',
    files={'file': open('motion.pdf', 'rb')},
    timeout=300
)

print(f"Status Code: {response.status_code}")
print(f"Response Length: {len(response.text)} chars")

try:
    data = response.json()
    print(f"\nJSON Keys: {list(data.keys())}")
    
    if 'error' in data:
        print(f"\n❌ ERROR: {data['error']}")
    
    if 'clusters' in data:
        print(f"\nClusters: {len(data['clusters'])}")
        if data['clusters']:
            # Show first cluster
            print(f"\nFirst cluster keys: {list(data['clusters'][0].keys())}")
            print(f"First cluster citations: {len(data['clusters'][0].get('citations', []))}")
    
    if 'citations' in data:
        print(f"\nCitations: {len(data['citations'])}")
        if data['citations']:
            print(f"\nFirst citation keys: {list(data['citations'][0].keys())}")
            print(f"First citation: {data['citations'][0].get('citation_text', 'N/A')}")
    
    # Save full response for inspection
    with open('api_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ Full response saved to api_response.json")
    
except Exception as e:
    print(f"\n❌ Failed to parse JSON: {e}")
    print(f"\nFirst 500 chars of response:")
    print(response.text[:500])
