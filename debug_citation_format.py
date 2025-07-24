#!/usr/bin/env python3
"""
Debug script to test different citation formats for the citation-lookup API.
"""

import os
import requests
import json
import sys

def test_citation_formats():
    """Test different citation formats to see what the API expects."""
    
    # Get API key
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("ERROR: No CourtListener API key found in environment")
        return
    
    headers = {"Authorization": f"Token {api_key}"}
    lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    # Prevent use of v3 CourtListener API endpoints
    if 'v3' in lookup_url:
        print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
        sys.exit(1)
    
    # Test different request formats based on the error message
    test_requests = [
        # Try with 'text' parameter
        {"text": "146 Wn.2d 1, 9, 43 P.3d 4"},
        {"text": "146 Wn.2d 1"},
        
        # Try with 'reporter' parameter
        {"reporter": "146 Wn.2d 1, 9, 43 P.3d 4"},
        {"reporter": "146 Wn.2d 1"},
        
        # Try with both
        {"text": "146 Wn.2d 1, 9, 43 P.3d 4", "reporter": "Wn.2d"},
        {"text": "146 Wn.2d 1", "reporter": "Wn.2d"},
        
        # Try with 'citations' array format
        {"citations": ["146 Wn.2d 1, 9, 43 P.3d 4"]},
        {"citations": ["146 Wn.2d 1"]},
        
        # Try with 'citation' parameter
        {"citation": "146 Wn.2d 1, 9, 43 P.3d 4"},
        {"citation": "146 Wn.2d 1"},
    ]
    
    print("TESTING CITATION-LOOKUP API REQUEST FORMATS")
    print("=" * 60)
    
    for i, request_data in enumerate(test_requests, 1):
        print(f"\n{i}. Testing request format: {request_data}")
        try:
            response = requests.post(lookup_url, headers=headers, json=request_data, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result and "results" in result:
                    for cluster in result["results"]:
                        if cluster.get("status") == "ok" and cluster.get("citations"):
                            first_citation = cluster["citations"][0]
                            case_name = first_citation.get("case_name", "No case name")
                            print(f"   ✅ SUCCESS: {case_name}")
                        else:
                            print(f"   ⚠ Status: {cluster.get('status')}")
                else:
                    print(f"   ❌ No results in response")
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_citation_formats() 