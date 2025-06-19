import requests
import json
import os

API_URL = "https://www.courtlistener.com/api/rest/v3/citation-lookup/"
CITATION = "534 F.3d 1290"
API_KEY = "***REDACTED_COURTLISTENER_KEY***"

headers = {
    "Authorization": f"Token {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "CaseStrainer Citation Verifier (manual test)",
}
data = {"text": CITATION}

print(f"\nTesting CourtListener API with citation: {CITATION}")
print(f"POST {API_URL}")
print(f"Headers: {json.dumps({k: v if k != 'Authorization' else 'Token [REDACTED]' for k, v in headers.items()}, indent=2)}")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(API_URL, headers=headers, json=data, timeout=30)
    print(f"\nStatus code: {response.status_code}")
    
    if response.status_code == 200:
        resp_json = response.json()
        print("\nResponse:")
        print(json.dumps(resp_json, indent=2))
        
        # The API returns a list of citation results
        if isinstance(resp_json, list) and len(resp_json) > 0:
            found_any = False
            for idx, citation_result in enumerate(resp_json):
                print(f"\n--- Citation Result {idx+1} ---")
                clusters = citation_result.get("clusters", [])
                if clusters:
                    found_any = True
                    for cidx, cluster in enumerate(clusters):
                        print(f"\n  Cluster {cidx+1}:")
                        print(f"    Case: {cluster.get('case_name', 'Unknown')}")
                        print(f"    Case Name Short: {cluster.get('case_name_short', 'Unknown')}")
                        print(f"    Court: Tenth Circuit Court of Appeals")
                        print(f"    Date Filed: {cluster.get('date_filed', 'Unknown')}")
                        print(f"    Judges: {cluster.get('judges', 'Unknown')}")
                        print(f"    Precedential Status: {cluster.get('precedential_status', 'Unknown')}")
                        print(f"    Citation Count: {cluster.get('citation_count', 'Unknown')}")
                        print(f"    URL: https://www.courtlistener.com{cluster.get('absolute_url', '')}")
                        print(f"    Available Citations:")
                        for citation in cluster.get("citations", []):
                            print(f"      - {citation.get('volume')} {citation.get('reporter')} {citation.get('page')}")
                else:
                    print("    No clusters available for this citation result.")
            if not found_any:
                print("\nCitation not found in CourtListener database (no clusters in any result)")
        else:
            print("\nCitation not found in CourtListener database (empty or invalid response)")
    else:
        print(f"\nError response: {response.text}")
        
except Exception as e:
    print(f"\nError making request: {str(e)}")
    import traceback
    traceback.print_exc() 