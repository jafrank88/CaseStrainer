#!/usr/bin/env python3
"""
Test script for CourtListener API integration
"""
import requests
import json
import sys

def test_courtlistener_api(api_key, citation):
    """Test the CourtListener API with a single citation."""
    print(f"Testing CourtListener API with citation: {citation}")
    
    # API endpoint
    api_url = 'https://www.courtlistener.com/api/rest/v4/citation-lookup/'
    
    # Prepare the request
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'text': citation
    }
    
    # Make the request
    print(f"Sending request to {api_url}")
    try:
        response = requests.post(api_url, headers=headers, json=data)
        
        # Check the response
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            print("API request successful")
            result = response.json()
            
            # Save the API response to a file for inspection
            with open('test_api_response.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print("API response saved to test_api_response.json")
            
            # Print a summary of the response
            print("\nResponse summary:")
            if isinstance(result, list):
                for item in result:
                    print(f"Citation: {item.get('citation', 'N/A')}")
                    clusters = item.get('clusters', [])
                    if clusters:
                        cluster = clusters[0]
                        print(f"Case name: {cluster.get('case_name', 'N/A')}")
                        print(f"Court: {cluster.get('court', 'N/A')}")
                        print(f"Date filed: {cluster.get('date_filed', 'N/A')}")
                        print(f"URL: {cluster.get('absolute_url', 'N/A')}")
                        print("Citations:")
                        for cite in cluster.get('citations', []):
                            print(f"  {cite.get('volume')} {cite.get('reporter')} {cite.get('page')}")
                    else:
                        print("No case details found")
                    print()
            elif 'citations' in result:
                for citation in result['citations']:
                    print(f"Citation: {citation.get('citation', 'N/A')}")
                    print(f"Found: {citation.get('found', False)}")
                    if citation.get('found'):
                        print(f"Case name: {citation.get('case_name', 'N/A')}")
                        print(f"Court: {citation.get('court', 'N/A')}")
                        print(f"Year: {citation.get('year', 'N/A')}")
                    print()
            else:
                print("No citations found in the response")
            
            return True
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load API key from config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get('courtlistener_api_key')
            if not api_key:
                print("No CourtListener API key found in config.json")
                sys.exit(1)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        sys.exit(1)
    
    # Test citation
    test_citation = "410 U.S. 113"  # Roe v. Wade
    if len(sys.argv) > 1:
        test_citation = sys.argv[1]
    
    test_courtlistener_api(api_key, test_citation)
