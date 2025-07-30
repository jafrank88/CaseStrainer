#!/usr/bin/env python3
"""
Use CourtListener API to directly verify the citations and check if they're legitimate
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def get_cl_api_key():
    """Get CourtListener API key from environment"""
    
    # Try to load from .env file first
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('COURTLISTENER_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    
    # Try environment variable
    api_key = os.getenv('COURTLISTENER_API_KEY')
    if api_key:
        return api_key
    
    print("❌ CourtListener API key not found in .env file or environment variables")
    return None

def search_citation_in_cl(citation_text, api_key):
    """Search for a citation in CourtListener using the API"""
    
    print(f"\n🔍 SEARCHING COURTLISTENER API: {citation_text}")
    
    # CourtListener API v4 search endpoint
    url = "https://www.courtlistener.com/api/rest/v4/search/"
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Search parameters
    params = {
        'q': citation_text,
        'type': 'o',  # opinions
        'format': 'json'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            results = data.get('results', [])
            count = data.get('count', 0)
            
            print(f"📈 Search Results Count: {count}")
            
            if results:
                print(f"📋 Found {len(results)} results:")
                
                for i, result in enumerate(results[:3], 1):  # Show first 3 results
                    case_name = result.get('caseName', 'N/A')
                    date_filed = result.get('dateFiled', 'N/A')
                    court = result.get('court', 'N/A')
                    absolute_url = result.get('absolute_url', 'N/A')
                    
                    print(f"  {i}. Case: {case_name}")
                    print(f"     Date: {date_filed}")
                    print(f"     Court: {court}")
                    print(f"     URL: {absolute_url}")
                    
                    # Check if this result contains our citation
                    citation_in_result = citation_text in str(result)
                    print(f"     Citation Match: {'Yes' if citation_in_result else 'No'}")
                
                return {
                    'found': True,
                    'count': count,
                    'results': results,
                    'api_accessible': True
                }
            else:
                print("❌ No results found")
                return {
                    'found': False,
                    'count': 0,
                    'results': [],
                    'api_accessible': True
                }
        
        elif response.status_code == 401:
            print("❌ API Authentication Failed (401)")
            return {
                'found': False,
                'count': 0,
                'results': [],
                'api_accessible': False,
                'error': 'Authentication failed'
            }
        
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error text: {response.text}")
            
            return {
                'found': False,
                'count': 0,
                'results': [],
                'api_accessible': False,
                'error': f'HTTP {response.status_code}'
            }
    
    except Exception as e:
        print(f"❌ Request Exception: {str(e)}")
        return {
            'found': False,
            'count': 0,
            'results': [],
            'api_accessible': False,
            'error': str(e)
        }

def lookup_opinion_by_id(opinion_id, api_key):
    """Look up a specific opinion by ID"""
    
    print(f"\n🔍 LOOKING UP OPINION ID: {opinion_id}")
    
    url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            case_name = data.get('cluster', {}).get('case_name', 'N/A')
            date_filed = data.get('cluster', {}).get('date_filed', 'N/A')
            court = data.get('cluster', {}).get('docket', {}).get('court', 'N/A')
            absolute_url = data.get('absolute_url', 'N/A')
            
            print(f"✅ Opinion Found:")
            print(f"   Case: {case_name}")
            print(f"   Date: {date_filed}")
            print(f"   Court: {court}")
            print(f"   URL: {absolute_url}")
            
            return {
                'found': True,
                'data': data,
                'case_name': case_name,
                'date_filed': date_filed,
                'court': court,
                'url': absolute_url
            }
        
        elif response.status_code == 404:
            print("❌ Opinion Not Found (404)")
            return {
                'found': False,
                'error': 'Opinion not found'
            }
        
        else:
            print(f"❌ API Error: {response.status_code}")
            return {
                'found': False,
                'error': f'HTTP {response.status_code}'
            }
    
    except Exception as e:
        print(f"❌ Request Exception: {str(e)}")
        return {
            'found': False,
            'error': str(e)
        }

def verify_production_citations():
    """Verify the citations from the production results using CourtListener API"""
    
    api_key = get_cl_api_key()
    if not api_key:
        return
    
    print("🔍 VERIFYING PRODUCTION CITATIONS WITH COURTLISTENER API")
    print("=" * 70)
    
    # Citations from production results with their claimed URLs
    citations_to_verify = [
        {
            'citation': '654 F. Supp. 2d 321',
            'claimed_case': 'Benckini v. Hawk',
            'claimed_url': 'https://www.courtlistener.com/opinion/1689955/benckini-v-hawk/',
            'opinion_id': '1689955'
        },
        {
            'citation': '147 Wn. App. 891',
            'claimed_case': 'State v. Alphonse',
            'claimed_url': 'https://www.courtlistener.com/opinion/4945618/state-v-alphonse/',
            'opinion_id': '4945618'
        },
        {
            'citation': '456 F.3d 789',
            'claimed_case': 'David L. Hartjes v. Jeffrey P. Endicott',
            'claimed_url': 'https://www.courtlistener.com/opinion/795205/david-l-hartjes-v-jeffrey-p-endicott/',
            'opinion_id': '795205'
        },
        {
            'citation': '123 Wn.2d 456',
            'claimed_case': 'State v. Board of Yakima County Commissioners',
            'claimed_url': 'https://www.courtlistener.com/opinion/1229830/state-v-board-of-yakima-county-commissioners/',
            'opinion_id': '1229830'
        }
    ]
    
    verification_results = []
    
    for citation_info in citations_to_verify:
        print(f"\n{'='*60}")
        print(f"VERIFYING: {citation_info['citation']}")
        print(f"CLAIMED CASE: {citation_info['claimed_case']}")
        print(f"CLAIMED URL: {citation_info['claimed_url']}")
        
        # Method 1: Search for the citation
        search_result = search_citation_in_cl(citation_info['citation'], api_key)
        
        # Method 2: Look up the specific opinion ID
        opinion_result = lookup_opinion_by_id(citation_info['opinion_id'], api_key)
        
        # Analyze results
        verification = {
            'citation': citation_info['citation'],
            'claimed_case': citation_info['claimed_case'],
            'claimed_url': citation_info['claimed_url'],
            'search_found': search_result['found'],
            'opinion_found': opinion_result['found'] if opinion_result else False,
            'legitimate': False,
            'issues': []
        }
        
        if opinion_result and opinion_result['found']:
            actual_case = opinion_result['case_name']
            claimed_case = citation_info['claimed_case']
            
            print(f"\n📊 VERIFICATION ANALYSIS:")
            print(f"   Claimed Case: {claimed_case}")
            print(f"   Actual Case:  {actual_case}")
            
            # Check if case names match
            if actual_case and claimed_case:
                if actual_case.lower() == claimed_case.lower():
                    print(f"   ✅ Case names match exactly")
                    verification['legitimate'] = True
                elif claimed_case.lower() in actual_case.lower() or actual_case.lower() in claimed_case.lower():
                    print(f"   ⚠️  Case names partially match")
                    verification['legitimate'] = True
                    verification['issues'].append('Partial case name match')
                else:
                    print(f"   ❌ Case names do not match")
                    verification['legitimate'] = False
                    verification['issues'].append('Case name mismatch')
            else:
                print(f"   ⚠️  Cannot compare case names (missing data)")
                verification['issues'].append('Missing case name data')
        else:
            print(f"   ❌ Opinion ID not found in CourtListener")
            verification['legitimate'] = False
            verification['issues'].append('Opinion not found by ID')
        
        verification_results.append(verification)
        
        # Be respectful to the API
        time.sleep(1)
    
    # Summary
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 30)
    
    legitimate_count = sum(1 for v in verification_results if v['legitimate'])
    total_count = len(verification_results)
    
    print(f"Total citations verified: {total_count}")
    print(f"Legitimate verifications: {legitimate_count}")
    print(f"False positives: {total_count - legitimate_count}")
    
    print(f"\n📋 DETAILED RESULTS:")
    print("-" * 50)
    
    for result in verification_results:
        status = "✅ LEGITIMATE" if result['legitimate'] else "❌ FALSE POSITIVE"
        print(f"{result['citation']}: {status}")
        
        if result['issues']:
            for issue in result['issues']:
                print(f"  ⚠️  Issue: {issue}")
    
    print(f"\n💡 CONCLUSION:")
    print("=" * 15)
    
    if legitimate_count == total_count:
        print("✅ All verifications are legitimate")
        print("✅ Production pipeline is working correctly")
    elif legitimate_count > 0:
        print("⚠️  Mixed results - some legitimate, some false positives")
        print("⚠️  Production pipeline needs investigation")
    else:
        print("❌ All verifications appear to be false positives")
        print("❌ Production pipeline has serious issues")
    
    return verification_results

if __name__ == "__main__":
    verify_production_citations()
