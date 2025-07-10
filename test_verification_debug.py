#!/usr/bin/env python3
"""
Test script to debug verification process for specific citations.
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
import json
import requests

def test_citation_lookup_directly():
    """Test the citation-lookup API directly to see what it returns."""
    from src.config import get_config_value
    
    api_key = get_config_value("COURTLISTENER_API_KEY")
    if not api_key:
        print("No CourtListener API key found")
        return
    
    headers = {"Authorization": f"Token {api_key}"}
    
    test_citations = [
        "200 Wn.2d 72",
        "171 Wn.2d 486", 
        "146 Wn.2d 1"
    ]
    
    print("Testing citation-lookup API directly:")
    print("=" * 60)
    
    for citation in test_citations:
        print(f"\nTesting: {citation}")
        try:
            lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            resp = requests.post(lookup_url, headers=headers, data={"text": citation}, timeout=10)
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                clusters = data.get("clusters", [])
                print(f"Clusters found: {len(clusters)}")
                
                if clusters:
                    print("✅ Citation found in CourtListener")
                else:
                    print("❌ No clusters found")
            else:
                print(f"Error: {resp.text}")
                
        except Exception as e:
            print(f"Error: {e}")

def test_verification():
    processor = UnifiedCitationProcessorV2()
    
    # Test citations from the user's output
    test_cases = [
        {
            'citation': '200 Wn.2d 72, 73, 514 P.3d 643',
            'case_name': 'Convoyant, LLC v. DeepThink, LLC',
            'date': '2022'
        },
        {
            'citation': '171 Wn.2d 486, 493, 256 P.3d 321',
            'case_name': 'Carlson v. Glob. Client Sols., LLC',
            'date': '2011'
        },
        {
            'citation': '146 Wn.2d 1, 9, 43 P.3d 4',
            'case_name': 'Campbell & Gwinn, LLC',
            'date': '2003'
        }
    ]
    
    print("Testing verification for each citation:")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['citation']}")
        print(f"   Case name: {test_case['case_name']}")
        print(f"   Date: {test_case['date']}")
        
        try:
            result = processor._verify_with_courtlistener(
                test_case['citation'],
                test_case['case_name'],
                test_case['date']
            )
            
            print(f"   Result:")
            print(f"     verified: {result.get('verified')}")
            print(f"     canonical_name: {result.get('canonical_name')}")
            print(f"     canonical_date: {result.get('canonical_date')}")
            print(f"     url: {result.get('url')}")
            print(f"     source: {result.get('source')}")
            
            if result.get('raw'):
                print(f"     raw data keys: {list(result['raw'].keys()) if isinstance(result['raw'], dict) else 'Not a dict'}")
                print(f"     raw data: {json.dumps(result['raw'], indent=2)}")
            
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Testing full processor workflow:")
    
    # Test the full workflow
    test_text = """
    when a resolution of that question is necessary to resolve a case before the 
    federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
    72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
    de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
    (2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
    Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)
    """
    
    try:
        results = processor.process_text(test_text)
        print(f"Found {len(results)} citations")
        
        for i, citation in enumerate(results, 1):
            print(f"\n{i}. Citation: {citation.citation}")
            print(f"   Extracted case name: {citation.extracted_case_name}")
            print(f"   Extracted date: {citation.extracted_date}")
            print(f"   Canonical name: {citation.canonical_name}")
            print(f"   Canonical date: {citation.canonical_date}")
            print(f"   Verified: {citation.verified}")
            print(f"   URL: {citation.url}")
            print(f"   Source: {citation.source}")
            
            # Show metadata if available
            if citation.metadata and 'courtlistener_raw' in citation.metadata:
                raw_data = citation.metadata['courtlistener_raw']
                print(f"   Raw CourtListener data: {json.dumps(raw_data, indent=2)}")
            
    except Exception as e:
        print(f"Error in full workflow: {e}")

if __name__ == "__main__":
    test_citation_lookup_directly()
    print("\n" + "=" * 80)
    test_verification() 