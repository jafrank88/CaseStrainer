#!/usr/bin/env python3
"""
Verify CourtListener API connectivity and test citation lookup.
"""

import os
import requests
import json

def test_courtlistener_api():
    # API endpoint
    api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    # API key from config
    api_key = "***REDACTED_COURTLISTENER_KEY***"
    
    # Test citation
    test_citation = "195 Wn.2d 742"
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer/1.0 (https://github.com/yourusername/casestrainer)'
    }
    
    try:
        print(f"Testing CourtListener API with citation: {test_citation}")
        print(f"Using API key: {api_key[:4]}...{api_key[-4:]}")
        
        # Make the API request with just the text parameter
        response = requests.post(
            api_url,
            headers=headers,
            json={"text": test_citation},
            timeout=10
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        try:
            data = response.json()
            print("\nResponse JSON:")
            print(json.dumps(data, indent=2))
            
            if 'count' in data and data['count'] > 0:
                print("\nFound matching cases:")
                for i, result in enumerate(data['results'][:3], 1):
                    cluster = result.get('cluster', {})
                    print(f"\n{i}. {cluster.get('case_name', 'No case name')}")
                    print(f"   Citation: {cluster.get('citation', 'No citation')}")
                    print(f"   Court: {cluster.get('court', 'No court')}")
                    print(f"   Date: {cluster.get('date_filed', 'No date')}")
            else:
                print("\nNo matching cases found.")
                
        except json.JSONDecodeError:
            print("\nResponse is not valid JSON. Raw response:")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {str(e)}")

if __name__ == "__main__":
    test_courtlistener_api()
