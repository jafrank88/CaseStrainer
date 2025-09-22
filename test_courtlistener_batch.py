#!/usr/bin/env python3
"""
Test CourtListener API batch mode with the provided citations
"""

import requests
import json
import time
from typing import List, Dict, Any
import os
import sys

# Try to get API key from environment or config.env file
COURTLISTENER_API_KEY = os.getenv('COURTLISTENER_API_KEY', '')

# If not in environment, try to load from config.env file
if not COURTLISTENER_API_KEY:
    try:
        config_env_path = os.path.join(os.path.dirname(__file__), 'config.env')
        if os.path.exists(config_env_path):
            with open(config_env_path, 'r') as f:
                for line in f:
                    if line.startswith('COURTLISTENER_API_KEY='):
                        COURTLISTENER_API_KEY = line.split('=', 1)[1].strip()
                        break
    except Exception as e:
        print(f"⚠️ Could not load config.env: {e}")
        COURTLISTENER_API_KEY = ""

def test_courtlistener_batch():
    """Test CourtListener API with batch citation lookup"""
    
    # Citations from the user's request
    citations = [
        "199 Wash.2d 528",
        "509 P.3d 818", 
        "559 P.3d 545",
        "4 Wash.3d 1021",
        "509 P.3d 325",
        "159 Wash.2d 700",
        "153 P.3d 846",
        "495 P.3d 866",
        "148 Wash.2d 224",
        "59 P.3d 655",
        "2024 WL 2133370",
        "2024 WL 3199858", 
        "2024 WL 4678268",
        "2 Wash.3d 310",
        "535 P.3d 856",
        "197 Wash.2d 841",
        "487 P.3d 499",
        "567 P.3d 1128",
        "182 Wash.2d 398",
        "341 P.3d 953",
        "118 Wash.2d 46",
        "821 P.2d 18",
        "198 Wash.2d 418",
        "495 P.3d 808",
        "147 Wash.2d 602",
        "56 P.3d 981",
        "432 P.3d 841"
    ]
    
    print("🔍 Testing CourtListener API Batch Mode")
    print("=" * 60)
    print(f"📋 Total citations to test: {len(citations)}")
    print(f"🔑 API Key configured: {'✅ Yes' if COURTLISTENER_API_KEY else '❌ No'}")
    print()
    
    if not COURTLISTENER_API_KEY:
        print("❌ No CourtListener API key configured!")
        return
    
    # Test individual citations first (since batch might not be available)
    print("🔍 Testing Individual Citation Lookups:")
    print("-" * 40)
    
    verified_count = 0
    failed_count = 0
    results = []
    
    for i, citation in enumerate(citations[:3], 1):  # Test only first 3 for debugging
        print(f"📄 {i:2d}. Testing: {citation}")
        
        try:
            # Try the opinions endpoint first (using v4 API)
            url = "https://www.courtlistener.com/api/rest/v4/opinions/"
            params = {
                'citation': citation,
                'format': 'json'
            }
            headers = {
                'Authorization': f'Token {COURTLISTENER_API_KEY}',
                'User-Agent': 'CaseStrainer/1.0 (Legal Citation Verification)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Debug: Print first response structure
                if i == 1:
                    print(f"   🔍 DEBUG - First response structure:")
                    print(f"      Type: {type(data)}")
                    print(f"      Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    if isinstance(data, dict) and 'results' in data:
                        print(f"      Results count: {len(data['results'])}")
                        if data['results']:
                            print(f"      First result keys: {list(data['results'][0].keys())}")
                            print(f"      First result sample: {data['results'][0]}")
                
                if isinstance(data, dict) and data.get('results') and len(data['results']) > 0:
                    result = data['results'][0]
                    
                    # Get cluster URL and fetch detailed information
                    cluster_url = result.get('cluster')
                    case_name = 'Unknown'
                    date_filed = 'Unknown'
                    court = 'Unknown'
                    
                    if cluster_url and isinstance(cluster_url, str):
                        try:
                            # Fetch cluster details
                            cluster_response = requests.get(cluster_url, headers=headers, timeout=10)
                            if cluster_response.status_code == 200:
                                cluster_data = cluster_response.json()
                                case_name = cluster_data.get('case_name', 'Unknown')
                                date_filed = cluster_data.get('date_filed', 'Unknown')
                                court_info = cluster_data.get('court', 'Unknown')
                                if isinstance(court_info, str):
                                    court = court_info
                                elif isinstance(court_info, dict):
                                    court = court_info.get('name', court_info.get('short_name', 'Unknown'))
                        except Exception as e:
                            print(f"      ⚠️ Could not fetch cluster details: {e}")
                    
                    print(f"   ✅ FOUND: {case_name} ({date_filed})")
                    print(f"      Court: {court}")
                    
                    results.append({
                        'citation': citation,
                        'status': 'verified',
                        'case_name': case_name,
                        'date_filed': date_filed,
                        'court': court
                    })
                    verified_count += 1
                else:
                    print(f"   ❌ NOT FOUND: No results")
                    results.append({
                        'citation': citation,
                        'status': 'not_found',
                        'error': 'No results returned'
                    })
                    failed_count += 1
            else:
                print(f"   ❌ API ERROR: {response.status_code}")
                results.append({
                    'citation': citation,
                    'status': 'api_error',
                    'error': f'HTTP {response.status_code}'
                })
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            results.append({
                'citation': citation,
                'status': 'exception',
                'error': str(e)
            })
            failed_count += 1
        
        # Rate limiting - be nice to the API
        time.sleep(0.5)
        print()
    
    # Summary
    print("=" * 60)
    print("📊 BATCH TEST RESULTS:")
    print("-" * 30)
    print(f"✅ Verified: {verified_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📈 Success Rate: {(verified_count / len(citations)) * 100:.1f}%")
    print()
    
    # Show verified citations
    if verified_count > 0:
        print("✅ VERIFIED CITATIONS:")
        print("-" * 30)
        for result in results:
            if result['status'] == 'verified':
                print(f"📄 {result['citation']}")
                print(f"   Case: {result['case_name']}")
                print(f"   Date: {result['date_filed']}")
                print(f"   Court: {result['court']}")
                print()
    
    # Show failed citations
    if failed_count > 0:
        print("❌ FAILED CITATIONS:")
        print("-" * 30)
        for result in results:
            if result['status'] != 'verified':
                print(f"📄 {result['citation']}: {result['error']}")
        print()
    
    # Test batch endpoint if available
    print("🔍 Testing Batch Endpoint:")
    print("-" * 30)
    
    try:
        # Try the batch citation endpoint (using v4 API)
        batch_url = "https://www.courtlistener.com/api/rest/v4/citations/"
        batch_params = {
            'citation': ','.join(citations[:5]),  # Test first 5 citations
            'format': 'json'
        }
        
        batch_response = requests.get(batch_url, params=batch_params, headers=headers, timeout=30)
        
        if batch_response.status_code == 200:
            batch_data = batch_response.json()
            print(f"✅ Batch endpoint works! Found {len(batch_data.get('results', []))} results")
        else:
            print(f"❌ Batch endpoint failed: HTTP {batch_response.status_code}")
            
    except Exception as e:
        print(f"❌ Batch endpoint exception: {str(e)}")
    
    return results

def main():
    """Main execution function"""
    results = test_courtlistener_batch()
    
    # Save results to file
    with open('courtlistener_batch_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("💾 Results saved to: courtlistener_batch_test_results.json")

if __name__ == "__main__":
    main()
