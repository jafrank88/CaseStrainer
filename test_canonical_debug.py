#!/usr/bin/env python3
"""
Debug script to test why canonical data is not being populated from CourtListener API.
"""

import json
import requests
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_canonical_extraction():
    """Test canonical data extraction from CourtListener API."""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test citations from the user's output
    test_cases = [
        {
            'citation': '171 Wn.2d 486',
            'case_name': 'Carlson v. Glob. Client Sols., LLC',
            'date': '2011'
        },
        {
            'citation': '146 Wn.2d 1',
            'case_name': 'Campbell & Gwinn, LLC',
            'date': '2003'
        }
    ]
    
    print("Testing canonical data extraction:")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['citation']}")
        print(f"   Case name: {test_case['case_name']}")
        print(f"   Date: {test_case['date']}")
        
        try:
            # Test the verification method directly
            result = processor._verify_with_courtlistener_search(
                test_case['citation'],
                test_case['case_name'],
                test_case['date']
            )
            
            print(f"   Verification Result:")
            print(f"     verified: {result.get('verified')}")
            print(f"     canonical_name: {result.get('canonical_name')}")
            print(f"     canonical_date: {result.get('canonical_date')}")
            print(f"     url: {result.get('url')}")
            print(f"     source: {result.get('source')}")
            
            if result.get('raw'):
                raw_data = result['raw']
                print(f"     Raw data keys: {list(raw_data.keys())}")
                print(f"     caseName: {raw_data.get('caseName')}")
                print(f"     dateFiled: {raw_data.get('dateFiled')}")
                print(f"     absolute_url: {raw_data.get('absolute_url')}")
                print(f"     court: {raw_data.get('court')}")
                print(f"     citation: {raw_data.get('citation')}")
                
                # Check if the fields are being extracted correctly
                if raw_data.get('caseName'):
                    print(f"     ✅ caseName found: {raw_data['caseName']}")
                else:
                    print(f"     ❌ caseName missing")
                
                if raw_data.get('dateFiled'):
                    print(f"     ✅ dateFiled found: {raw_data['dateFiled']}")
                else:
                    print(f"     ❌ dateFiled missing")
                
                if raw_data.get('absolute_url'):
                    print(f"     ✅ absolute_url found: {raw_data['absolute_url']}")
                else:
                    print(f"     ❌ absolute_url missing")
            else:
                print(f"     ❌ No raw data available")
            
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Testing direct CourtListener API call:")
    
    # Test direct API call to see the actual response structure
    if processor.courtlistener_api_key:
        headers = {"Authorization": f"Token {processor.courtlistener_api_key}"}
        test_citation = "171 Wn.2d 486"
        base_citation = processor._get_base_citation(test_citation)
        search_url = f"https://www.courtlistener.com/api/rest/v4/search/?q={base_citation}&format=json"
        
        try:
            resp = requests.get(search_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                search_data = resp.json()
                results = search_data.get("results", [])
                
                print(f"Direct API call for '{test_citation}' (base: '{base_citation}'):")
                print(f"Status: {resp.status_code}")
                print(f"Results count: {len(results)}")
                
                if results:
                    first_result = results[0]
                    print(f"First result keys: {list(first_result.keys())}")
                    print(f"First result:")
                    print(json.dumps(first_result, indent=2))
                    
                    # Check specific fields
                    print(f"\nField analysis:")
                    print(f"  caseName: {first_result.get('caseName')}")
                    print(f"  dateFiled: {first_result.get('dateFiled')}")
                    print(f"  absolute_url: {first_result.get('absolute_url')}")
                    print(f"  court: {first_result.get('court')}")
                    print(f"  citation: {first_result.get('citation')}")
                else:
                    print("No results found")
            else:
                print(f"API call failed with status {resp.status_code}")
                print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Direct API call error: {e}")
    else:
        print("No CourtListener API key available")

if __name__ == "__main__":
    test_canonical_extraction() 