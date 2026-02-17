"""
Test script to debug CourtListener batch lookup API behavior
"""
import requests
import json
import os

API_KEY = os.environ.get("COURTLISTENER_API_KEY", "443a87912e4f444fb818fca454364d71e4aa9f91")

# Test citations from user's document
test_citations = [
    "521 U.S. 811",
    "504 U.S. 555",
    "578 U.S. 330",
    "426 U.S. 26",
    "467 U.S. 1027",
    "481 U. S. 465",  # Note: with spaces
    "159 Wn.2d 700",  # Washington state
]

print("=" * 80)
print("COURTLISTENER BATCH LOOKUP API TEST")
print("=" * 80)

# Normalize citations
def normalize_citation(cit):
    # Remove extra spaces
    cit = ' '.join(cit.split())
    return cit

normalized = [normalize_citation(c) for c in test_citations]
combined_text = " ".join(normalized)

print(f"\nSending {len(test_citations)} citations to CourtListener batch API...")
print(f"Combined text: {combined_text[:100]}...")

url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
payload = {"text": combined_text}
headers = {
    "Authorization": f"Token {API_KEY}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response type: {type(data)}")
        
        if isinstance(data, list):
            print(f"\nGot {len(data)} results:")
            
            verified_count = 0
            for i, item in enumerate(data):
                cit = item.get("citation", "N/A")
                status = item.get("status", "unknown")
                error = item.get("error_message", "")
                clusters = item.get("clusters", [])
                
                print(f"\n{i+1}. Citation: {cit}")
                print(f"   Status: {status}")
                if error:
                    print(f"   Error: {error}")
                
                if clusters:
                    print(f"   Clusters: {len(clusters)}")
                    for j, cluster in enumerate(clusters[:1]):  # Show first cluster
                        case_name = cluster.get("caseName") or cluster.get("case_name", "N/A")
                        date_filed = cluster.get("dateFiled") or cluster.get("date_filed", "N/A")
                        absolute_url = cluster.get("absolute_url") or cluster.get("absoluteUrl", "N/A")
                        
                        print(f"   - Case: {case_name}")
                        print(f"   - Date Filed: {date_filed}")
                        print(f"   - URL: {absolute_url}")
                        
                        if case_name != "N/A" and absolute_url:
                            verified_count += 1
                else:
                    print(f"   No clusters found")
            
            print(f"\n{'='*80}")
            print(f"SUMMARY: {verified_count}/{len(data)} citations have cluster data with URL")
            print(f"{'='*80}")
        else:
            print(f"Unexpected response format: {type(data)}")
            print(json.dumps(data, indent=2)[:500])
    else:
        print(f"API Error: {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
