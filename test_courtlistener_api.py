"""
Test CourtListener citation-lookup API to verify correct usage
"""
import requests
import json
import os

# Get API key from environment
api_key = os.environ.get('COURTLISTENER_API_KEY', '')

if not api_key:
    print("ERROR: COURTLISTENER_API_KEY not set")
    exit(1)

# Test citation
test_citation = "578 U.S. 330"

print("="*80)
print("TESTING COURTLISTENER CITATION-LOOKUP API")
print("="*80)
print(f"Test citation: {test_citation}")
print(f"API Key: {api_key[:6]}...{api_key[-4:]}")
print()

# Test 1: POST to citation-lookup endpoint (CORRECT per memory)
print("Test 1: POST /v4/citation-lookup/ with JSON body")
print("-"*80)
url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
headers = {
    'Authorization': f'Token {api_key}',
    'Content-Type': 'application/json'
}
payload = {"text": test_citation}  # API requires "text" field

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        if 'clusters' in data and len(data['clusters']) > 0:
            cluster = data['clusters'][0]
            print(f"\n✅ SUCCESS!")
            print(f"Case Name: {cluster.get('case_name')}")
            print(f"Date Filed: {cluster.get('date_filed')}")
            print(f"Court: {cluster.get('court')}")
        else:
            print(f"\n⚠️ No clusters found in response")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "="*80)

# Test 2: GET to citations endpoint (OLD/WRONG way)
print("Test 2: GET /v4/citations/?cite= (OLD METHOD)")
print("-"*80)
url2 = "https://www.courtlistener.com/api/rest/v4/citations/"
headers2 = {
    'Authorization': f'Token {api_key}'
}
params = {'cite': test_citation}

try:
    response2 = requests.get(url2, headers=headers2, params=params, timeout=10)
    print(f"Status: {response2.status_code}")
    print(f"Response: {json.dumps(response2.json(), indent=2)[:500]}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        if 'results' in data2 and len(data2['results']) > 0:
            result = data2['results'][0]
            print(f"\n✅ This method also works")
            print(f"Cluster: {result.get('cluster', {})}")
        else:
            print(f"\n⚠️ No results found")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("Both methods may work, but citation-lookup is the recommended endpoint")
print("per CourtListener documentation and our memories.")
