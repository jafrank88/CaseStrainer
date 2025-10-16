import requests
import json

# Test the ACTUAL citation-lookup endpoint we use
citation = "200 L. Ed. 2d 931"
url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
payload = {"text": citation}

print(f"Testing Citation Lookup API for: {citation}")
print(f"URL: {url}")
print(f"Payload: {payload}\n")

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    
    # Save full response
    with open('citation_lookup_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("✅ Response saved to citation_lookup_response.json\n")
    
    # Show structure
    if 'citations' in data and data['citations']:
        first_citation = data['citations'][0]
        print(f"📋 First citation keys: {list(first_citation.keys())}\n")
        
        if 'clusters' in first_citation and first_citation['clusters']:
            first_cluster = first_citation['clusters'][0]
            print(f"📦 First cluster keys: {list(first_cluster.keys())}\n")
            
            # Check for case name in various locations
            print("🔍 Looking for case name in cluster...")
            print(f"  case_name: {first_cluster.get('case_name')}")
            print(f"  caseName: {first_cluster.get('caseName')}")
            print(f"  cluster_name: {first_cluster.get('cluster_name')}")
            
            if 'docket' in first_cluster:
                docket = first_cluster['docket']
                print(f"\n📁 Docket type: {type(docket)}")
                if isinstance(docket, dict):
                    print(f"  Docket keys: {list(docket.keys())}")
                    print(f"  docket.case_name: {docket.get('case_name')}")
                    print(f"  docket.caseName: {docket.get('caseName')}")
                elif isinstance(docket, str):
                    print(f"  Docket is URL: {docket}")
            
            # Show sample
            print(f"\n📄 Sample of first cluster:")
            print(json.dumps(first_cluster, indent=2)[:800])
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
