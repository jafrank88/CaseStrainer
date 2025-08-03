#!/usr/bin/env python3
"""
Test proper citation search strategy using CourtListener Search API
"""

import requests
import json
import os
from dotenv import load_dotenv

def test_proper_citation_search():
    """Test different search strategies to find the case published at a citation"""
    
    load_dotenv()
    api_key = os.getenv('COURTLISTENER_API_KEY')
    
    if not api_key:
        print("❌ No CourtListener API key found!")
        return
    
    citation = "17 L. Ed. 2d 562"
    expected_case = "Garrity v. New Jersey"
    expected_year = "1967"
    
    print(f"TESTING PROPER CITATION SEARCH STRATEGIES")
    print(f"Target: {citation} -> {expected_case} ({expected_year})")
    print("=" * 70)
    
    headers = {"Authorization": f"Token {api_key}"}
    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
    
    # Strategy 1: Search by citation field specifically
    print("\n1. STRATEGY: Search by citation field")
    print("-" * 50)
    
    try:
        response = requests.get(
            search_url,
            params={
                "type": "o",
                "q": f'citation:"{citation}"',  # Search specifically in citation field
                "order_by": "score desc"
            },
            headers=headers,
            timeout=10
        )
        
        print(f"Query: citation:\"{citation}\"")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Found {len(results)} results:")
            
            for i, result in enumerate(results[:3]):
                case_name = result.get('caseName', 'N/A')
                date_filed = result.get('dateFiled', 'N/A')
                citations = result.get('citation', [])
                
                print(f"\n  Result {i+1}:")
                print(f"    Case Name: {case_name}")
                print(f"    Date Filed: {date_filed}")
                print(f"    Citations: {citations}")
                
                # Check if this citation is in the citations array
                if citation in citations:
                    print(f"    ✅ MATCH: Citation found in citations array!")
                    if expected_case.lower() in case_name.lower():
                        print(f"    🎯 PERFECT: This is the expected case!")
                    else:
                        print(f"    ⚠️  Case name doesn't match expected")
                else:
                    print(f"    ❌ Citation not found in citations array")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Strategy 2: Search with advanced citation operator
    print("\n\n2. STRATEGY: Advanced citation search")
    print("-" * 50)
    
    try:
        # Try different citation formats
        citation_queries = [
            f'citation:({citation})',
            f'citation:"{citation.replace(" ", "")}"',  # Remove spaces
            f'citation:"17L.Ed.2d562"',  # Compact format
            f'citation:"17 L Ed 2d 562"',  # Different spacing
        ]
        
        for query in citation_queries:
            print(f"\nTrying query: {query}")
            
            response = requests.get(
                search_url,
                params={
                    "type": "o",
                    "q": query,
                    "order_by": "score desc"
                },
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"  Found {len(results)} results")
                
                if results:
                    result = results[0]
                    case_name = result.get('caseName', 'N/A')
                    citations = result.get('citation', [])
                    
                    if citation in citations:
                        print(f"  ✅ SUCCESS: Found {case_name} with citation {citation}")
                        if expected_case.lower() in case_name.lower():
                            print(f"  🎯 PERFECT MATCH!")
                            break
            else:
                print(f"  ❌ Failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Strategy 3: Combine case name and citation
    print("\n\n3. STRATEGY: Combine case name and citation")
    print("-" * 50)
    
    try:
        response = requests.get(
            search_url,
            params={
                "type": "o",
                "q": f'caseName:"Garrity" AND citation:"{citation}"',
                "order_by": "score desc"
            },
            headers=headers,
            timeout=10
        )
        
        print(f"Query: caseName:\"Garrity\" AND citation:\"{citation}\"")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Found {len(results)} results:")
            
            if results:
                result = results[0]
                case_name = result.get('caseName', 'N/A')
                date_filed = result.get('dateFiled', 'N/A')
                citations = result.get('citation', [])
                
                print(f"\n  Case Name: {case_name}")
                print(f"  Date Filed: {date_filed}")
                print(f"  Citations: {citations}")
                
                if citation in citations and expected_case.lower() in case_name.lower():
                    print(f"  🎯 PERFECT: This is exactly what we want!")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print(f"\n\n4. CONCLUSION")
    print("-" * 50)
    print("The key is to search specifically in the 'citation' field, not in the full text.")
    print("This should return cases that ARE published at that citation, not cases that")
    print("mention the citation in their opinion text.")
    print()
    print("Recommended search strategy:")
    print(f'1. Primary: citation:"{citation}"')
    print(f'2. Fallback: caseName:"[expected_name]" AND citation:"{citation}"')
    print("3. Validate that the citation appears in the result's citation array")

if __name__ == "__main__":
    test_proper_citation_search()
