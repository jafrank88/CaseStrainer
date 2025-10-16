import requests
import json
import time

# Test the BATCH citation-lookup API
citations = ["200 L. Ed. 2d 931", "138 S. Ct. 1649", "584 U.S. 554"]
url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
api_key = "***REDACTED_COURTLISTENER_KEY***"

payload = {"text": " ".join(citations)}
headers = {
    "Authorization": f"Token {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

print(f"Testing BATCH Citation Lookup API")
print(f"URL: {url}")
print(f"Citations: {citations}")
print(f"Payload: {payload}\n")

# Make the request
response = requests.post(url, json=payload, headers=headers)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    
    # Save response
    with open('batch_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("✅ Response saved to batch_response.json\n")
    
    # Check structure
    print(f"📋 Response type: {type(data)}")
    
    if isinstance(data, list):
        print(f"📋 Number of items: {len(data)}")
        if len(data) > 0:
            first_item = data[0]
            print(f"📋 First item keys: {list(first_item.keys())}\n")
            print(f"📄 First item sample:")
            print(json.dumps(first_item, indent=2)[:800])
            
            # Check if it has actual cluster data or just job ID
            if 'clusters' in first_item and first_item['clusters']:
                print(f"\n✅ Has clusters! First cluster has case_name:")
                first_cluster = first_item['clusters'][0]
                print(f"   case_name: {first_cluster.get('case_name')}")
            elif 'job_id' in first_item or 'status' in first_item:
                print(f"\n⚠️  Might be async - has job_id or status field")
            else:
                print(f"\n❓ Unknown structure")
    elif isinstance(data, dict):
        print(f"📋 Dict keys: {list(data.keys())}")
        print(f"📄 Sample:")
        print(json.dumps(data, indent=2)[:800])
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text[:500])
