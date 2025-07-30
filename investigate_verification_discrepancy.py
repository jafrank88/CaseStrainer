#!/usr/bin/env python3
"""
Investigate the verification discrepancy between our API test and the verification function
"""

import os
import sys
import requests
import json

def get_api_key():
    """Get CourtListener API key"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'COURTLISTENER_API_KEY=' in line:
                    return line.split('=')[1].strip().strip('"\'')
    except:
        pass
    return os.getenv('COURTLISTENER_API_KEY')

def test_citation_lookup_api(api_key, citation):
    """Test the citation-lookup API directly"""
    
    print(f"TESTING CITATION-LOOKUP API")
    print("=" * 35)
    
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {"Authorization": f"Token {api_key}"}
    data = {"text": citation}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Results count: {len(results)}")
            
            for i, result in enumerate(results):
                print(f"\nResult {i+1}:")
                print(f"  Status: {result.get('status')}")
                print(f"  Clusters: {len(result.get('clusters', []))}")
                
                if result.get('clusters'):
                    for j, cluster in enumerate(result.get('clusters', [])):
                        print(f"  Cluster {j+1}:")
                        print(f"    Case Name: '{cluster.get('case_name')}'")
                        print(f"    Date Filed: '{cluster.get('date_filed')}'")
                        print(f"    Absolute URL: '{cluster.get('absolute_url')}'")
                        
                        # Check if this cluster has valid data
                        case_name = cluster.get('case_name')
                        absolute_url = cluster.get('absolute_url')
                        
                        if case_name and case_name.strip() and absolute_url and absolute_url.strip():
                            print(f"    VALIDATION: PASS (has essential data)")
                        else:
                            print(f"    VALIDATION: FAIL (missing essential data)")
            
            return results
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def test_opinion_api(api_key, opinion_id):
    """Test the opinion API directly"""
    
    print(f"\nTESTING OPINION API")
    print("=" * 25)
    
    url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
    headers = {"Authorization": f"Token {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            cluster = data.get('cluster')
            if cluster:
                case_name = cluster.get('case_name')
                date_filed = cluster.get('date_filed')
                
                print(f"Cluster found:")
                print(f"  Case Name: '{case_name}'")
                print(f"  Date Filed: '{date_filed}'")
                
                if case_name and case_name.strip():
                    print(f"  VALIDATION: PASS (has case name)")
                else:
                    print(f"  VALIDATION: FAIL (no case name)")
            else:
                print(f"No cluster data found")
            
            return data
        else:
            print(f"Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def main():
    """Main investigation function"""
    
    api_key = get_api_key()
    if not api_key:
        print("No API key found")
        return
    
    citation = "654 F. Supp. 2d 321"
    opinion_id = "1689955"
    
    print(f"INVESTIGATING VERIFICATION DISCREPANCY")
    print("=" * 45)
    print(f"Citation: {citation}")
    print(f"Opinion ID: {opinion_id}")
    
    # Test 1: Citation-lookup API (what the verification function uses)
    lookup_results = test_citation_lookup_api(api_key, citation)
    
    # Test 2: Opinion API (what our earlier test used)
    opinion_result = test_opinion_api(api_key, opinion_id)
    
    # Analysis
    print(f"\nANALYSIS:")
    print("=" * 15)
    
    if lookup_results:
        # Check if citation-lookup found valid data
        found_valid_cluster = False
        for result in lookup_results:
            if result.get('status') != 404 and result.get('clusters'):
                for cluster in result.get('clusters', []):
                    case_name = cluster.get('case_name')
                    absolute_url = cluster.get('absolute_url')
                    if case_name and case_name.strip() and absolute_url and absolute_url.strip():
                        found_valid_cluster = True
                        break
        
        if found_valid_cluster:
            print("Citation-lookup API: FOUND VALID DATA")
            print("This explains why the verification function marks it as verified")
        else:
            print("Citation-lookup API: NO VALID DATA")
            print("The verification function should NOT mark this as verified")
    
    if opinion_result:
        cluster = opinion_result.get('cluster')
        if cluster and cluster.get('case_name') and cluster.get('case_name').strip():
            print("Opinion API: FOUND VALID DATA")
        else:
            print("Opinion API: NO VALID DATA")
            print("This matches our earlier test showing 'no cluster data'")
    
    print(f"\nCONCLUSION:")
    print("-" * 15)
    print("The discrepancy may be due to different API endpoints returning different data.")
    print("Citation-lookup API vs Opinion API may have different data completeness.")

if __name__ == "__main__":
    main()
