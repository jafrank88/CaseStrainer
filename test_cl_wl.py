"""Test if CourtListener can find WL/LEXIS citations"""
import requests
import os

# Get API key
api_key = os.environ.get("COURTLISTENER_API_KEY")
if not api_key:
    print("No API key found")
    exit(1)

# Test WL citations from motion.pdf
wl_citations = [
    "2024 WL 4149252",
    "2024 WL 4003343",
    "2024 WL 1232082",
    "2021 WL 3622166",
    "2025 WL 1410708",
    "2022 WL 15153410",
    "2006 WL 2788256",
]

headers = {"Authorization": f"Token {api_key}"}

print("Testing CourtListener citation-lookup API for WL citations:\n")

for citation in wl_citations:
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    payload = {"citation": citation}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            clusters = data.get("clusters", [])
            if clusters:
                print(f"✅ {citation}: FOUND {len(clusters)} cluster(s)")
                for cluster in clusters[:1]:  # Show first result
                    print(f"   - {cluster.get('case_name', 'N/A')}")
                    print(f"   - {cluster.get('absolute_url', 'N/A')}")
            else:
                print(f"❌ {citation}: Not found (200 but no clusters)")
        elif response.status_code == 404:
            print(f"❌ {citation}: Not found (404)")
        else:
            print(f"⚠️  {citation}: Error {response.status_code}")
    except Exception as e:
        print(f"⚠️  {citation}: Exception - {e}")
    print()
