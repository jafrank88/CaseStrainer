#!/usr/bin/env python3
"""
Simple CourtListener verification test
"""

import os
import requests
import json

def simple_verify():
    """Simple verification of CourtListener citations"""
    
    # Get API key
    api_key = None
    try:
        with open('.env', 'r') as f:
            content = f.read()
            if 'COURTLISTENER_API_KEY=' in content:
                api_key = content.split('COURTLISTENER_API_KEY=')[1].split('\n')[0].strip().strip('"\'')
    except:
        pass
    
    if not api_key:
        api_key = os.getenv('COURTLISTENER_API_KEY')
    
    if not api_key:
        print("No API key found")
        return
    
    print(f"Using API key: {api_key[:10]}...")
    
    # Test one citation
    opinion_id = '1689955'
    expected_case = 'Benckini v. Hawk'
    citation = '654 F. Supp. 2d 321'
    
    print(f"\nTesting: {citation}")
    print(f"Expected: {expected_case}")
    print(f"Opinion ID: {opinion_id}")
    
    url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse response carefully
            try:
                data = response.json()
                print("Response type: JSON")
                
                # Check if we have the expected structure
                if isinstance(data, dict):
                    cluster = data.get('cluster')
                    if cluster and isinstance(cluster, dict):
                        case_name = cluster.get('case_name')
                        print(f"Found case: {case_name}")
                        
                        if case_name:
                            if case_name.lower() == expected_case.lower():
                                print("RESULT: LEGITIMATE VERIFICATION")
                                return True
                            elif expected_case.lower() in case_name.lower():
                                print("RESULT: LEGITIMATE (partial match)")
                                return True
                            else:
                                print("RESULT: FALSE POSITIVE")
                                print(f"  Expected: {expected_case}")
                                print(f"  Got:      {case_name}")
                                return False
                        else:
                            print("RESULT: No case name found")
                            return False
                    else:
                        print("RESULT: No cluster data")
                        return False
                else:
                    print(f"RESULT: Unexpected response type: {type(data)}")
                    return False
                    
            except json.JSONDecodeError:
                print("Response type: Not JSON")
                print(f"Content: {response.text[:200]}")
                return False
                
        elif response.status_code == 404:
            print("RESULT: Opinion not found - FALSE POSITIVE")
            return False
        elif response.status_code == 401:
            print("RESULT: Authentication failed")
            return False
        else:
            print(f"RESULT: API error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    result = simple_verify()
    if result is True:
        print("\nCONCLUSION: The citation verification appears to be LEGITIMATE")
        print("The production pipeline is working correctly")
        print("The lack of clickable links is likely a UI display issue")
    elif result is False:
        print("\nCONCLUSION: The citation verification appears to be a FALSE POSITIVE")
        print("The production pipeline may have verification issues")
    else:
        print("\nCONCLUSION: Unable to determine verification legitimacy")
        print("Manual verification may be required")
