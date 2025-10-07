"""Test CourtListener API for 521 U.S. 811"""
import requests
import json

API_KEY = "***REDACTED_COURTLISTENER_KEY***"
BASE_URL = "https://www.courtlistener.com/api/rest/v4"

citation = "521 U.S. 811"

print("=" * 80)
print(f"Testing CourtListener API for: {citation}")
print("=" * 80)

# Try citation lookup
url = f"{BASE_URL}/search/"
params = {
    "type": "o",  # opinions
    "citation": citation,
}
headers = {
    "Authorization": f"Token {API_KEY}"
}

print(f"\nRequest URL: {url}")
print(f"Params: {params}")

response = requests.get(url, params=params, headers=headers)
print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResults count: {data.get('count', 0)}")
    
    if data.get('results'):
        print(f"\n{'='*80}")
        print("RESULTS:")
        print(f"{'='*80}")
        for i, result in enumerate(data['results'][:5], 1):
            print(f"\n{i}. {result.get('caseName', 'N/A')}")
            print(f"   Date: {result.get('dateFiled', 'N/A')}")
            print(f"   Court: {result.get('court', 'N/A')}")
            print(f"   Citation: {result.get('citation', [])}")
            print(f"   URL: {result.get('absolute_url', 'N/A')}")
            print(f"   Cluster ID: {result.get('cluster_id', 'N/A')}")
    else:
        print("\n❌ No results found")
        print(f"Full response: {json.dumps(data, indent=2)}")
else:
    print(f"\n❌ Error: {response.status_code}")
    print(f"Response: {response.text}")

# Also try direct cluster lookup if we know the cluster ID
print(f"\n\n{'='*80}")
print("Trying alternative: Search by reporter")
print(f"{'='*80}")

# Parse citation
parts = citation.split()
if len(parts) >= 3:
    volume = parts[0]
    reporter = parts[1]
    page = parts[2]
    
    url = f"{BASE_URL}/clusters/"
    params = {
        "citation": f"{volume} {reporter} {page}",
    }
    
    print(f"\nRequest URL: {url}")
    print(f"Params: {params}")
    
    response = requests.get(url, params=params, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Results count: {data.get('count', 0)}")
        
        if data.get('results'):
            print(f"\n{'='*80}")
            print("CLUSTER RESULTS:")
            print(f"{'='*80}")
            for i, result in enumerate(data['results'][:5], 1):
                print(f"\n{i}. {result.get('case_name', 'N/A')}")
                print(f"   Date: {result.get('date_filed', 'N/A')}")
                docket = result.get('docket', 'N/A')
                if isinstance(docket, dict):
                    print(f"   Court: {docket.get('court', 'N/A')}")
                else:
                    print(f"   Court: {docket}")
                print(f"   Citations: {result.get('citations', [])}")
                print(f"   URL: {result.get('absolute_url', 'N/A')}")
        else:
            print("\n❌ No cluster results found")
    else:
        print(f"❌ Error: {response.status_code}")
