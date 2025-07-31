#!/usr/bin/env python3
"""
Investigate whether CourtListener Search API returns citing cases vs cited cases
"""

import requests
import json
import os
from dotenv import load_dotenv

def investigate_citing_vs_cited():
    """Investigate the difference between citing and cited cases"""
    
    load_dotenv()
    api_key = os.getenv('COURTLISTENER_API_KEY')
    
    if not api_key:
        print("❌ No CourtListener API key found!")
        return
    
    citation = "17 L. Ed. 2d 562"
    print(f"INVESTIGATING CITING VS CITED CASES FOR: {citation}")
    print("=" * 70)
    
    headers = {"Authorization": f"Token {api_key}"}
    
    # Test 1: Search API with citation in quotes (exact match)
    print("\n1. SEARCH API - EXACT CITATION MATCH")
    print("-" * 50)
    
    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
    
    try:
        response = requests.get(
            search_url,
            params={
                "type": "o",  # opinions
                "q": f'"{citation}"',  # Exact match in quotes
                "order_by": "score desc"
            },
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Found {len(results)} results for exact citation match:")
            
            for i, result in enumerate(results[:3]):  # Show first 3
                case_name = result.get('caseName', 'N/A')
                date_filed = result.get('dateFiled', 'N/A')
                cluster_id = result.get('cluster_id')
                
                print(f"\n  Result {i+1}:")
                print(f"    Case Name: {case_name}")
                print(f"    Date Filed: {date_filed}")
                print(f"    Cluster ID: {cluster_id}")
                
                # Check if this is likely the citing case vs cited case
                if "State v. Flynn" in case_name:
                    print(f"    🔍 HYPOTHESIS: This is a CITING case (cites {citation} in its text)")
                elif "Garrity" in case_name:
                    print(f"    ✅ HYPOTHESIS: This is the CITED case (published at {citation})")
                
                # Get the full opinion text to see if it contains the citation
                if cluster_id:
                    print(f"    📄 Checking if opinion text contains '{citation}'...")
                    
                    # Get opinion details
                    opinion_url = f"https://www.courtlistener.com/api/rest/v4/opinions/"
                    opinion_response = requests.get(
                        opinion_url,
                        params={"cluster": cluster_id},
                        headers=headers,
                        timeout=10
                    )
                    
                    if opinion_response.status_code == 200:
                        opinion_data = opinion_response.json()
                        opinions = opinion_data.get('results', [])
                        
                        if opinions:
                            opinion_text = opinions[0].get('plain_text', '') or opinions[0].get('html', '')
                            
                            if citation in opinion_text:
                                print(f"    ✅ CONFIRMED: Opinion text contains '{citation}' - this is a CITING case")
                            else:
                                print(f"    ❓ Opinion text does not contain '{citation}' - might be the CITED case")
                    else:
                        print(f"    ❌ Could not retrieve opinion text")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception in search: {e}")
    
    # Test 2: Try to find the actual case published at this citation
    print(f"\n\n2. TRYING TO FIND THE ACTUAL CASE AT {citation}")
    print("-" * 50)
    
    # Search for "Garrity v. New Jersey" specifically
    try:
        response = requests.get(
            search_url,
            params={
                "type": "o",
                "q": "Garrity New Jersey 1967",
                "order_by": "score desc"
            },
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Found {len(results)} results for 'Garrity New Jersey 1967':")
            
            for i, result in enumerate(results[:3]):
                case_name = result.get('caseName', 'N/A')
                date_filed = result.get('dateFiled', 'N/A')
                
                print(f"\n  Result {i+1}:")
                print(f"    Case Name: {case_name}")
                print(f"    Date Filed: {date_filed}")
                
                if "Garrity" in case_name and "1967" in date_filed:
                    print(f"    ✅ This looks like the correct case!")
                    
                    # Check what citations this case has
                    cluster_id = result.get('cluster_id')
                    if cluster_id:
                        cluster_url = f"https://www.courtlistener.com/api/rest/v4/clusters/{cluster_id}/"
                        cluster_response = requests.get(cluster_url, headers=headers, timeout=10)
                        
                        if cluster_response.status_code == 200:
                            cluster_data = cluster_response.json()
                            
                            # Get citations for this cluster
                            citations_url = f"https://www.courtlistener.com/api/rest/v4/citations/"
                            citations_response = requests.get(
                                citations_url,
                                params={"cluster": cluster_id},
                                headers=headers,
                                timeout=10
                            )
                            
                            if citations_response.status_code == 200:
                                citations_data = citations_response.json()
                                citations_list = citations_data.get('results', [])
                                
                                print(f"    📚 Citations for this case:")
                                for cite in citations_list:
                                    volume = cite.get('volume')
                                    reporter = cite.get('reporter')
                                    page = cite.get('page')
                                    citation_str = f"{volume} {reporter} {page}"
                                    print(f"      - {citation_str}")
                                    
                                    if citation_str == citation:
                                        print(f"        🎯 FOUND IT! This case IS published at {citation}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print(f"\n\n3. CONCLUSION")
    print("-" * 50)
    print("The issue is likely that CourtListener's Search API is designed to find")
    print("cases that MENTION a citation in their text, not cases that ARE published")
    print("at that citation.")
    print()
    print("This means:")
    print("- Search API finds CITING cases (cases that reference the citation)")
    print("- Citation-lookup API should find CITED cases (the actual case at that citation)")
    print()
    print("For proper verification, we need to:")
    print("1. Use citation-lookup API to find the actual case at the citation")
    print("2. Only use search API as a fallback when citation-lookup fails")
    print("3. Implement strict context validation to catch these mismatches")

if __name__ == "__main__":
    investigate_citing_vs_cited()
