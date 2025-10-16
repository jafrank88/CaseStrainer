import requests
import json

# Test what the CourtListener v4 API actually returns
citation = "200 L. Ed. 2d 931"
url = "https://www.courtlistener.com/api/rest/v4/search/"
params = {
    "citation": citation,
    "type": "o"
}

print(f"Testing CourtListener v4 API for: {citation}")
print(f"URL: {url}")
print(f"Params: {params}\n")

response = requests.get(url, params=params)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    
    # Save full response
    with open('api_response_sample.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("✅ Response saved to api_response_sample.json\n")
    
    # Show structure
    if data.get('results'):
        first_result = data['results'][0]
        print(f"📋 First result keys: {list(first_result.keys())}\n")
        
        # Check for case name in various locations
        print("🔍 Looking for case name...")
        print(f"  case_name: {first_result.get('case_name')}")
        print(f"  caseName: {first_result.get('caseName')}")
        print(f"  cluster_name: {first_result.get('cluster_name')}")
        
        if 'docket' in first_result:
            docket = first_result['docket']
            if isinstance(docket, dict):
                print(f"\n📁 Docket is a dict with keys: {list(docket.keys())}")
                print(f"  docket.case_name: {docket.get('case_name')}")
                print(f"  docket.caseName: {docket.get('caseName')}")
            elif isinstance(docket, str):
                print(f"\n📁 Docket is a string: {docket}")
            else:
                print(f"\n📁 Docket type: {type(docket)}")
        
        # Show first 200 chars of full result
        print(f"\n📄 Sample of first result:")
        print(json.dumps(first_result, indent=2)[:500])
else:
    print(f"❌ Error: {response.text}")
