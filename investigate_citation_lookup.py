#!/usr/bin/env python3
"""
Investigate how CourtListener citation lookup found "State v. Flynn" for "17 L. Ed. 2d 562"
"""

import requests
import json
import os
from dotenv import load_dotenv

def investigate_citation_lookup():
    """Investigate the citation lookup behavior"""
    
    load_dotenv()
    api_key = os.getenv('COURTLISTENER_API_KEY')
    
    if not api_key:
        print("❌ No CourtListener API key found!")
        return
    
    citation = "17 L. Ed. 2d 562"
    print(f"INVESTIGATING CITATION LOOKUP FOR: {citation}")
    print("=" * 60)
    
    # Test 1: Direct citation-lookup API
    print("\n1. TESTING CITATION-LOOKUP API")
    print("-" * 40)
    
    citation_lookup_url = "https://www.courtlistener.com/api/rest/v4/citations/"
    headers = {"Authorization": f"Token {api_key}"}
    
    try:
        response = requests.get(
            citation_lookup_url,
            params={"cite": citation},
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Found {len(results)} results:")
            
            for i, result in enumerate(results[:5]):  # Show first 5
                cluster_id = result.get('cluster_id')
                volume = result.get('volume')
                reporter = result.get('reporter')
                page = result.get('page')
                
                print(f"\n  Result {i+1}:")
                print(f"    Citation: {volume} {reporter} {page}")
                print(f"    Cluster ID: {cluster_id}")
                
                # Get cluster details
                if cluster_id:
                    cluster_url = f"https://www.courtlistener.com/api/rest/v4/clusters/{cluster_id}/"
                    cluster_response = requests.get(cluster_url, headers=headers, timeout=10)
                    
                    if cluster_response.status_code == 200:
                        cluster_data = cluster_response.json()
                        case_name = cluster_data.get('case_name', 'N/A')
                        date_filed = cluster_data.get('date_filed', 'N/A')
                        canonical_url = f"https://www.courtlistener.com{cluster_data.get('absolute_url', '')}"
                        
                        print(f"    Case Name: {case_name}")
                        print(f"    Date Filed: {date_filed}")
                        print(f"    URL: {canonical_url}")
                        
                        # Check if this matches our problematic result
                        if "State v. Flynn" in case_name:
                            print(f"    🎯 THIS IS THE PROBLEMATIC MATCH!")
                    else:
                        print(f"    ❌ Cluster lookup failed: {cluster_response.status_code}")
        else:
            print(f"❌ Citation lookup failed: {response.status_code}")
            print(response.text[:200])
            
    except Exception as e:
        print(f"❌ Exception in citation lookup: {e}")
    
    # Test 2: Search API
    print(f"\n\n2. TESTING SEARCH API")
    print("-" * 40)
    
    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
    
    try:
        response = requests.get(
            search_url,
            params={
                "type": "o",  # opinions
                "q": f'"{citation}"',
                "order_by": "score desc"
            },
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Found {len(results)} results:")
            
            for i, result in enumerate(results[:5]):  # Show first 5
                case_name = result.get('caseName', 'N/A')
                date_filed = result.get('dateFiled', 'N/A')
                absolute_url = result.get('absolute_url', 'N/A')
                cluster_id = result.get('cluster_id')
                
                print(f"\n  Result {i+1}:")
                print(f"    Case Name: {case_name}")
                print(f"    Date Filed: {date_filed}")
                print(f"    Cluster ID: {cluster_id}")
                print(f"    URL: https://www.courtlistener.com{absolute_url}")
                
                # Check if this matches our problematic result
                if "State v. Flynn" in case_name:
                    print(f"    🎯 THIS IS THE PROBLEMATIC MATCH!")
                elif "Garrity" in case_name:
                    print(f"    ✅ THIS IS THE EXPECTED MATCH!")
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text[:200])
            
    except Exception as e:
        print(f"❌ Exception in search: {e}")
    
    # Test 3: Manual verification of what "17 L. Ed. 2d 562" should be
    print(f"\n\n3. MANUAL VERIFICATION")
    print("-" * 40)
    print("According to legal databases:")
    print("17 L. Ed. 2d 562 should be:")
    print("  Case: Garrity v. New Jersey")
    print("  Date: 1967")
    print("  Parallel citations: 385 U.S. 493, 87 S. Ct. 616")
    print()
    print("The fact that CourtListener is returning 'State v. Flynn' (2024)")
    print("suggests one of these issues:")
    print("1. CourtListener has incorrect/incomplete citation data")
    print("2. There's a citation collision (same citation used twice)")
    print("3. The citation lookup algorithm has bugs")
    print("4. Our search query is being interpreted incorrectly")

if __name__ == "__main__":
    investigate_citation_lookup()
