"""
Search for Grace v. Perkins Restaurant on CourtListener
"""

import requests
from src.config import COURTLISTENER_API_KEY

print("="*80)
print("SEARCHING FOR GRACE V. PERKINS RESTAURANT")
print("="*80)

headers = {
    'Authorization': f'Token {COURTLISTENER_API_KEY}',
    'Accept': 'application/json'
}

# Search for the case
search_url = "https://www.courtlistener.com/api/rest/v4/search/"
params = {
    'q': 'Grace v. Perkins Restaurant',
    'type': 'o',  # opinions
}

print(f"\nSearching CourtListener API...")
print(f"  Query: {params['q']}")

response = requests.get(search_url, headers=headers, params=params, timeout=30)
print(f"  Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    results = data.get('results', [])
    print(f"  Found {len(results)} results")
    
    for i, result in enumerate(results[:5], 1):
        case_name = result.get('caseName', 'N/A')
        citation = result.get('citation', [])
        court = result.get('court', 'N/A')
        date_filed = result.get('dateFiled', 'N/A')
        cluster_id = result.get('cluster_id', 'N/A')
        
        print(f"\n{i}. {case_name}")
        print(f"   Citations: {citation}")
        print(f"   Court: {court}")
        print(f"   Date: {date_filed}")
        print(f"   Cluster ID: {cluster_id}")
        
        # Check if this is Ohio case
        if 'Ohio' in str(citation):
            print(f"   ⭐ OHIO CASE - checking citation format...")
            if citation:
                for cit in citation:
                    print(f"     {cit}")
                    if '-' in cit:
                        print(f"       → Has dashes!")
else:
    print(f"  Error: {response.status_code}")
    print(f"  {response.text[:500]}")

print("\n" + "="*80)
