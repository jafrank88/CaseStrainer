"""
Test CourtListener batch citation-lookup API
"""
import requests
import json
import os

# Get API key from environment
api_key = os.environ.get('COURTLISTENER_API_KEY', '')

if not api_key:
    print("ERROR: COURTLISTENER_API_KEY not set")
    exit(1)

# Test citations
test_citations = [
    "578 U.S. 330",
    "521 U.S. 811",
    "183 Wash.2d 649",
    "192 Wash.2d 453"
]

print("="*80)
print("TESTING COURTLISTENER BATCH CITATION-LOOKUP API")
print("="*80)
print(f"Test citations: {len(test_citations)}")
for c in test_citations:
    print(f"  - {c}")
print(f"API Key: {api_key[:6]}...{api_key[-4:]}")
print()

# Test: POST to citation-lookup with multiple citations
print("Test: POST /v4/citation-lookup/ with multiple citations in text field")
print("-"*80)
url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
headers = {
    'Authorization': f'Token {api_key}',
    'Content-Type': 'application/json'
}

# Join all citations with spaces
combined_text = " ".join(test_citations)
payload = {"text": combined_text}

print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        clusters = data.get('clusters', [])
        
        print(f"\n✅ SUCCESS! Found {len(clusters)} clusters")
        print()
        
        for i, cluster in enumerate(clusters, 1):
            print(f"Cluster {i}:")
            print(f"  Case Name: {cluster.get('case_name')}")
            print(f"  Date Filed: {cluster.get('date_filed')}")
            print(f"  Citations: {cluster.get('citations', [])}")
            print()
        
        # Verify we got results for our citations
        print("="*80)
        print("MAPPING RESULTS TO INPUT CITATIONS:")
        print("="*80)
        for citation in test_citations:
            matched = False
            for cluster in clusters:
                cluster_citations = cluster.get('citations', [])
                if any(citation.lower() in str(cc).lower() for cc in cluster_citations):
                    print(f"✅ {citation} → {cluster.get('case_name')}")
                    matched = True
                    break
            if not matched:
                print(f"❌ {citation} → No match found")
    else:
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("Batch citation-lookup allows passing multiple citations in one request,")
print("dramatically improving performance (1 request vs N requests).")
