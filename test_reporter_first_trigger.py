#!/usr/bin/env python3
"""
Test to trigger reporter-first verification with a citation that might fail primary lookup
"""

import requests
import json
import time

def test_reporter_first_trigger():
    """Test with citations that might fail primary lookup to trigger reporter-first"""
    
    # Test with older or less common citations that might not be in CourtListener
    test_citations = [
        "685 P.2d 715",  # From the PDF - this might fail primary lookup
        "990 P.2d 1",    # From the PDF - this might fail primary lookup
        "390 U.S. 747",  # From the PDF - this might fail primary lookup
    ]
    
    for citation_text in test_citations:
        test_text = f"In the case of {citation_text}, the court held that..."
        
        request_data = {
            "type": "text",
            "text": test_text,
            "client_request_id": f"test_trigger_{citation_text.replace('.', '').replace(' ', '_')}_{int(time.time())}"
        }
        
        print(f"\nTesting citation: {citation_text}")
        print(f"Request ID: {request_data['client_request_id']}")
        
        try:
            response = requests.post(
                'https://wolf.law.uw.edu/casestrainer/api/analyze?debug=1',
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('result', {}).get('citations', [])
                
                if citations:
                    citation = citations[0]
                    extracted_name = citation.get('extracted_case_name', 'N/A')
                    canonical_name = citation.get('canonical_name', None)
                    canonical_date = citation.get('canonical_date', None)
                    verified = citation.get('verified', False)
                    source = citation.get('verification_source', None)
                    
                    print(f"  Extracted name: '{extracted_name}'")
                    print(f"  Canonical name: {canonical_name}")
                    print(f"  Canonical date: {canonical_date}")
                    print(f"  Verified: {verified}")
                    print(f"  Source: {source}")
                    
                    if extracted_name == "N/A" or not extracted_name or len(extracted_name.strip()) < 3:
                        if canonical_name and canonical_date and verified:
                            if source and "reporter-first" in source.lower():
                                print("  ✅ SUCCESS: Reporter-first verification worked!")
                            else:
                                print(f"  ⚠️  Verified by source: {source}")
                        else:
                            print("  ❌ FAILED: No verification obtained")
                    else:
                        print("  ℹ️  Extracted case name was present")
                        
                    # Also check cluster verification source
                    clusters = result.get('result', {}).get('clusters', [])
                    if clusters:
                        cluster_source = clusters[0].get('verification_source', '')
                        print(f"  Cluster verification source: {cluster_source}")
                        if "reporter-first" in cluster_source.lower():
                            print("  ✅ SUCCESS: Reporter-first verification in cluster!")
            else:
                print(f"❌ API request failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    test_reporter_first_trigger()
