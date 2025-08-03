"""
Test script to verify a citation with CourtListener API
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
COURTLISTENER_API_KEY = os.getenv('COURTLISTENER_API_KEY')

if not COURTLISTENER_API_KEY:
    print("Error: COURTLISTENER_API_KEY not found in environment")
    sys.exit(1)

def test_citation(citation):
    """Test a citation with CourtListener API"""
    print(f"\nTesting citation: {citation}")
    
    # Test 1: Search API
    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
    headers = {
        'Authorization': f'Token {COURTLISTENER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Test 1.1: Search by citation
    print("\n1. Testing Search API with citation query...")
    params = {
        'q': f'citation:"{citation}"',
        'type': 'o',  # opinions
        'order_by': 'score desc',
        'format': 'json'
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data.get('count', 0)} results")
            
            if data.get('results'):
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"\nResult {i}:")
                    print(f"Case Name: {result.get('caseName')}")
                    print(f"Citation: {result.get('citation', [])}")
                    print(f"Date Filed: {result.get('dateFiled')}")
                    print(f"URL: https://www.courtlistener.com{result.get('absolute_url', '')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error with search API: {e}")
    
    # Test 1.2: Search by text (broader search)
    print("\n2. Testing Search API with text query...")
    params = {
        'q': f'"{citation}"',
        'type': 'o',
        'order_by': 'score desc',
        'format': 'json'
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data.get('count', 0)} results")
            
            if data.get('results'):
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"\nResult {i}:")
                    print(f"Case Name: {result.get('caseName')}")
                    print(f"Citation: {result.get('citation', [])}")
                    print(f"Date Filed: {result.get('dateFiled')}")
                    print(f"URL: https://www.courtlistener.com{result.get('absolute_url', '')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error with search API: {e}")
    
    # Test 2: Citation Lookup API
    print("\n3. Testing Citation Lookup API...")
    lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    try:
        response = requests.post(
            lookup_url,
            headers=headers,
            json={"text": citation},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} results")
            
            for i, result in enumerate(results[:3], 1):
                if result.get('status') == 200 and result.get('clusters'):
                    cluster = result['clusters'][0]  # Take first cluster
                    print(f"\nResult {i}:")
                    print(f"Case Name: {cluster.get('caseName')}")
                    print(f"Citation: {cluster.get('citation', [])}")
                    print(f"Date Filed: {cluster.get('dateFiled')}")
                    print(f"URL: https://www.courtlistener.com{cluster.get('absolute_url', '')}")
                else:
                    print(f"\nResult {i}: {result.get('status', 'error')} - {result.get('message', 'No details')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error with citation lookup API: {e}")

if __name__ == "__main__":
    # Test with the known good citation and the parallel citation
    test_citation("180 Wn.2d 632")  # Known good citation
    test_citation("327 P.3d 644")   # Parallel citation that should match
