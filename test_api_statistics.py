#!/usr/bin/env python3
"""
Test script for API endpoint with comprehensive citation statistics.
"""

import requests
import json

def test_api_statistics():
    """Test the API endpoint with comprehensive citation statistics."""
    
    # Test the paragraph with complex citations
    test_text = """Zink filed her first appeal after the trial court granted summary judgment to 
the Does. While the appeal was pending, this court decided John Doe A v. 
Washington State Patrol, which rejected a PRA exemption claim for sex offender 
registration records that was materially identical to one of the Does' claims in this 
case. 185 Wn.2d 363, 374 P.3d 63 (2016). Thus, following John Doe A, the Court 
of Appeals here reversed in part and held "that the registration records must be 
released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 
(2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. 
App. Oct. 2, 2018) (Doe II) (unpublished),"""
    
    print("Testing API endpoint with comprehensive citation statistics...")
    print("=" * 70)
    print(f"Test text: {test_text[:100]}...")
    print()
    
    try:
        # Make request to the API endpoint
        url = "http://127.0.0.1:5000/casestrainer/api/analyze"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        data = {
            'text': test_text,
            'type': 'text'
        }
        
        print("Making request to API endpoint...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ API request successful!")
            print()
            
            # Check if statistics are present
            if 'statistics' in result:
                print("COMPREHENSIVE STATISTICS FOUND:")
                print("-" * 40)
                stats = result['statistics']
                print(f"Total citations: {stats.get('total_citations', 0)}")
                print(f"Parallel citations: {stats.get('parallel_citations', 0)}")
                print(f"Verified citations: {stats.get('verified_citations', 0)}")
                print(f"Unverified citations: {stats.get('unverified_citations', 0)}")
                print(f"Unique cases: {stats.get('unique_cases', 0)}")
                print()
            else:
                print("❌ No statistics found in response")
                print("Response keys:", list(result.keys()))
                print()
            
            # Check citations
            if 'citations' in result:
                citations = result['citations']
                print(f"CITATIONS FOUND: {len(citations)}")
                print("-" * 40)
                for i, citation in enumerate(citations, 1):
                    print(f"{i}. Citation: {citation.get('citation', 'N/A')}")
                    print(f"   Verified: {citation.get('verified', 'N/A')}")
                    print(f"   Case Name: {citation.get('case_name', 'N/A')}")
                    print(f"   Is Complex: {citation.get('is_complex_citation', False)}")
                    print(f"   Is Parallel: {citation.get('is_parallel_citation', False)}")
                    if citation.get('display_text'):
                        print(f"   Display: {citation.get('display_text')}")
                    print()
            else:
                print("❌ No citations found in response")
            
            # Print full response for debugging
            print("FULL RESPONSE:")
            print("-" * 40)
            print(json.dumps(result, indent=2))
            
        else:
            print(f"❌ API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API endpoint. Make sure the server is running.")
    except Exception as e:
        print(f"❌ Error during API test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_statistics() 