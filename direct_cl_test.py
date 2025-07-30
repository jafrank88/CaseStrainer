#!/usr/bin/env python3
"""
Direct test of CourtListener API to verify citations
"""

import os
import requests
import json

def test_cl_api():
    """Test CourtListener API directly"""
    
    # Get API key
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'COURTLISTENER_API_KEY=' in line:
                    api_key = line.split('=')[1].strip().strip('"\'')
                    break
            else:
                api_key = os.getenv('COURTLISTENER_API_KEY')
    except:
        api_key = os.getenv('COURTLISTENER_API_KEY')
    
    if not api_key:
        print("No API key found")
        return
    
    print(f"Testing with API key: {api_key[:10]}...")
    
    # Test citations from production results
    test_cases = [
        {
            'citation': '654 F. Supp. 2d 321',
            'expected_case': 'Benckini v. Hawk',
            'opinion_id': '1689955'
        },
        {
            'citation': '147 Wn. App. 891', 
            'expected_case': 'State v. Alphonse',
            'opinion_id': '4945618'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['citation']} ---")
        print(f"Expected: {test_case['expected_case']}")
        
        url = f"https://www.courtlistener.com/api/rest/v4/opinions/{test_case['opinion_id']}/"
        
        headers = {
            'Authorization': f'Token {api_key}',
            'User-Agent': 'CaseStrainer-Verification/1.0'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract case name safely
                cluster = data.get('cluster', {})
                if cluster:
                    case_name = cluster.get('case_name', 'No case name')
                    date_filed = cluster.get('date_filed', 'No date')
                    
                    print(f"Actual case: {case_name}")
                    print(f"Date filed: {date_filed}")
                    
                    # Check match
                    if case_name and test_case['expected_case']:
                        if case_name.lower() == test_case['expected_case'].lower():
                            print("RESULT: EXACT MATCH - LEGITIMATE")
                        elif test_case['expected_case'].lower() in case_name.lower():
                            print("RESULT: PARTIAL MATCH - LEGITIMATE")
                        else:
                            print("RESULT: NO MATCH - FALSE POSITIVE")
                            print(f"  Expected: '{test_case['expected_case']}'")
                            print(f"  Got:      '{case_name}'")
                    else:
                        print("RESULT: MISSING DATA")
                else:
                    print("RESULT: NO CLUSTER DATA - POSSIBLE FALSE POSITIVE")
                    
            elif response.status_code == 404:
                print("RESULT: OPINION NOT FOUND - FALSE POSITIVE")
            elif response.status_code == 401:
                print("RESULT: AUTHENTICATION FAILED")
                print("Check API key")
                break
            else:
                print(f"RESULT: API ERROR {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_cl_api()
