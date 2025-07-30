#!/usr/bin/env python3
"""
Fixed CourtListener API verification to check for false positives
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

def get_cl_api_key():
    """Get CourtListener API key from environment"""
    
    # Try to load from .env file first
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('COURTLISTENER_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    
    # Try environment variable
    api_key = os.getenv('COURTLISTENER_API_KEY')
    if api_key:
        return api_key
    
    print("ERROR: CourtListener API key not found")
    return None

def verify_opinion_by_id(opinion_id, api_key, expected_case, citation):
    """Verify a specific opinion by ID"""
    
    print(f"\nChecking Opinion ID: {opinion_id}")
    print(f"Citation: {citation}")
    print(f"Expected Case: {expected_case}")
    
    url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {str(e)}")
                print(f"Response content type: {response.headers.get('content-type', 'unknown')}")
                print(f"Response text (first 200 chars): {response.text[:200]}")
                return {
                    'found': False,
                    'legitimate': False,
                    'error': 'Invalid JSON response'
                }
            
            # Extract case information safely
            cluster = data.get('cluster')
            if not cluster:
                print("No cluster data found")
                return {
                    'found': False,
                    'legitimate': False,
                    'error': 'No cluster data'
                }
            
            case_name = cluster.get('case_name', 'N/A')
            date_filed = cluster.get('date_filed', 'N/A')
            
            docket = cluster.get('docket', {})
            court_info = str(docket.get('court', 'N/A'))
            
            absolute_url = data.get('absolute_url', 'N/A')
            
            print(f"FOUND - Case: {case_name}")
            print(f"Date: {date_filed}")
            print(f"Court: {court_info}")
            print(f"URL: {absolute_url}")
            
            # Check if case names match
            legitimate = False
            if case_name and expected_case and case_name != 'N/A':
                case_lower = case_name.lower()
                expected_lower = expected_case.lower()
                
                if case_lower == expected_lower:
                    print("RESULT: EXACT MATCH - LEGITIMATE")
                    legitimate = True
                elif expected_lower in case_lower or case_lower in expected_lower:
                    print("RESULT: PARTIAL MATCH - LIKELY LEGITIMATE")
                    legitimate = True
                else:
                    print("RESULT: NO MATCH - FALSE POSITIVE")
                    print(f"  Expected: '{expected_case}'")
                    print(f"  Actual:   '{case_name}'")
                    legitimate = False
            else:
                print("RESULT: CANNOT VERIFY - MISSING DATA")
                legitimate = False
            
            return {
                'found': True,
                'legitimate': legitimate,
                'actual_case': case_name,
                'date_filed': date_filed,
                'court': court_info,
                'url': absolute_url
            }
        
        elif response.status_code == 404:
            print("RESULT: OPINION NOT FOUND - FALSE POSITIVE")
            return {
                'found': False,
                'legitimate': False,
                'error': 'Opinion not found'
            }
        
        elif response.status_code == 401:
            print("RESULT: AUTHENTICATION FAILED")
            return {
                'found': False,
                'legitimate': False,
                'error': 'Authentication failed - check API key'
            }
        
        else:
            print(f"API ERROR: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return {
                'found': False,
                'legitimate': False,
                'error': f'HTTP {response.status_code}'
            }
    
    except Exception as e:
        print(f"REQUEST ERROR: {str(e)}")
        return {
            'found': False,
            'legitimate': False,
            'error': str(e)
        }

def main():
    """Main verification function"""
    
    api_key = get_cl_api_key()
    if not api_key:
        print("Cannot proceed without API key")
        return
    
    print("VERIFYING PRODUCTION CITATIONS WITH COURTLISTENER API")
    print("=" * 60)
    
    # Citations to verify
    citations = [
        {
            'citation': '654 F. Supp. 2d 321',
            'expected_case': 'Benckini v. Hawk',
            'opinion_id': '1689955'
        },
        {
            'citation': '147 Wn. App. 891',
            'expected_case': 'State v. Alphonse',
            'opinion_id': '4945618'
        },
        {
            'citation': '456 F.3d 789',
            'expected_case': 'David L. Hartjes v. Jeffrey P. Endicott',
            'opinion_id': '795205'
        },
        {
            'citation': '123 Wn.2d 456',
            'expected_case': 'State v. Board of Yakima County Commissioners',
            'opinion_id': '1229830'
        }
    ]
    
    results = []
    legitimate_count = 0
    
    for citation_info in citations:
        result = verify_opinion_by_id(
            citation_info['opinion_id'],
            api_key,
            citation_info['expected_case'],
            citation_info['citation']
        )
        
        result['citation'] = citation_info['citation']
        result['expected_case'] = citation_info['expected_case']
        results.append(result)
        
        if result['legitimate']:
            legitimate_count += 1
        
        time.sleep(1)  # Be respectful to API
    
    # Summary
    print(f"\nVERIFICATION SUMMARY")
    print("=" * 30)
    print(f"Total citations checked: {len(results)}")
    print(f"Legitimate verifications: {legitimate_count}")
    print(f"False positives: {len(results) - legitimate_count}")
    
    print(f"\nDETAILED RESULTS:")
    print("-" * 40)
    
    for result in results:
        status = "LEGITIMATE" if result['legitimate'] else "FALSE POSITIVE"
        print(f"{result['citation']}: {status}")
        
        if not result['legitimate'] and result.get('error'):
            print(f"  Error: {result['error']}")
    
    print(f"\nCONCLUSION:")
    print("=" * 15)
    
    if legitimate_count == len(results):
        print("ALL verifications are LEGITIMATE")
        print("Production pipeline is working correctly")
        print("The lack of clickable links is likely a UI display issue")
    elif legitimate_count > 0:
        print("MIXED results - some legitimate, some false positives")
        print("Production pipeline needs investigation")
    else:
        print("ALL verifications appear to be FALSE POSITIVES")
        print("Production pipeline has serious verification issues")
    
    return results

if __name__ == "__main__":
    main()
