#!/usr/bin/env python3
"""
Test CourtListener API for a specific citation and print the raw response.
"""
import os
import requests
import json

def test_courtlistener_citation(citation):
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("No CourtListener API key found in environment.")
        return
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    data = {"text": citation}
    print(f"Testing CourtListener API for citation: {citation}")
    response = requests.post(url, headers=headers, json=data, timeout=15)
    print(f"Status code: {response.status_code}")
    try:
        resp_json = response.json()
        print(json.dumps(resp_json, indent=2))
        # Try to extract canonical fields if present
        if isinstance(resp_json, list) and resp_json:
            clusters = resp_json[0].get('clusters', [])
            if clusters:
                cluster = clusters[0]
                print("\nCanonical fields:")
                print(f"  absolute_url: {cluster.get('absolute_url')}")
                print(f"  case_name: {cluster.get('case_name')}")
                print(f"  date_filed: {cluster.get('date_filed')}")
    except Exception as e:
        print(f"Error parsing response: {e}")

if __name__ == "__main__":
    test_courtlistener_citation("534 F.3d 1290") 