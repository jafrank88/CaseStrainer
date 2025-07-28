#!/usr/bin/env python3
"""
Test multiple matches for citations and name similarity matching
"""

import sys
import os
import requests
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config_value
from src.courtlistener_verification import verify_with_courtlistener

def test_multiple_matches():
    print("=== TESTING MULTIPLE MATCHES FOR 136 S. Ct. 1083 ===")
    
    api_key = get_config_value("COURTLISTENER_API_KEY")
    
    # First, let's see what the raw API returns
    print("\n1. Raw CourtListener citation-lookup API response:")
    headers = {'Authorization': f'Token {api_key}', 'Content-Type': 'application/json'}
    url = 'https://www.courtlistener.com/api/rest/v4/citation-lookup/'
    data = {'text': '136 S. Ct. 1083'}
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results)} results:")
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  Status: {result.get('status')}")
            if result.get('clusters'):
                print(f"  Clusters: {len(result['clusters'])}")
                for j, cluster in enumerate(result['clusters']):
                    case_name = cluster.get('case_name', 'Unknown')
                    date_filed = cluster.get('date_filed', 'Unknown')
                    print(f"    Cluster {j+1}: {case_name} ({date_filed})")
            else:
                print(f"  Error: {result.get('error_message', 'No clusters')}")
    
    # Now test our verification function with different extracted case names
    test_cases = [
        ("Luis v. United States", "Should match Luis case"),
        ("Friedrichs v. Cal. Teachers Ass'n", "Should match Friedrichs case"),
        ("Unknown Case", "Should pick best match or first result")
    ]
    
    print("\n2. Testing our verification function with different extracted names:")
    
    for extracted_name, description in test_cases:
        print(f"\n--- Testing with extracted_case_name: '{extracted_name}' ---")
        print(f"Expected: {description}")
        
        result = verify_with_courtlistener(api_key, '136 S. Ct. 1083', extracted_name)
        
        print(f"Result:")
        print(f"  verified: {result['verified']}")
        print(f"  canonical_name: {result['canonical_name']}")
        print(f"  canonical_date: {result['canonical_date']}")
        print(f"  source: {result['source']}")

if __name__ == "__main__":
    test_multiple_matches()
