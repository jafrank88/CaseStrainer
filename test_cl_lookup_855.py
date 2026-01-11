"""Test CourtListener citation-lookup API for 855 F.2d 569"""
import requests
import os
import json

# Get API key
api_key = os.environ.get("COURTLISTENER_API_KEY")
if not api_key:
    # Try reading from .env file
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('COURTLISTENER_API_KEY'):
                api_key = line.split('=')[1].strip()
                break

if not api_key:
    print("No API key found")
    exit(1)

headers = {"Authorization": f"Token {api_key}"}

# Test citation-lookup API
url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
payload = {"text": "855 F.2d 569"}

print("Testing CourtListener citation-lookup API for '855 F.2d 569':\n")

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        
        # API returns a list of results, one per citation in the text
        if isinstance(data, list):
            print(f"✅ Status: {response.status_code}")
            print(f"✅ API returned {len(data)} result(s)\n")
            
            for result_idx, result in enumerate(data):
                citation_text = result.get('citation', 'N/A')
                clusters = result.get('clusters', [])
                
                print(f"=== Result {result_idx+1}: Citation '{citation_text}' ===")
                print(f"Found {len(clusters)} cluster(s)\n")
                
                for i, cluster in enumerate(clusters):
                    print(f"--- Cluster {i+1} ---")
                    print(f"  Case Name: {cluster.get('case_name', 'N/A')}")
                    print(f"  Date Filed: {cluster.get('date_filed', 'N/A')}")
                    abs_url = cluster.get('absolute_url', 'N/A')
                    print(f"  Absolute URL: https://www.courtlistener.com{abs_url}")
                    
                    # Extract opinion ID from URL
                    if '/opinion/' in abs_url:
                        opinion_id = abs_url.split('/opinion/')[1].split('/')[0]
                        print(f"  Opinion ID: {opinion_id}")
                    
                    print(f"  Citations in cluster:")
                    
                    citations = cluster.get('citations', [])
                    for cit in citations:
                        if isinstance(cit, dict):
                            volume = cit.get('volume', '')
                            reporter = cit.get('reporter', '')
                            page = cit.get('page', '')
                            print(f"    - {volume} {reporter} {page}")
                        else:
                            print(f"    - {cit}")
                    print()
        else:
            clusters = data.get("clusters", [])
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Found {len(clusters)} cluster(s)\n")
        
        # Save full response
        with open('cl_lookup_855_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("✅ Full response saved to cl_lookup_855_response.json")
        
    else:
        print(f"❌ Status: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"⚠️  Exception: {e}")
