#!/usr/bin/env python3
"""
Test script to verify the reporter-first verification is working
"""

import requests
import json
import time

def test_reporter_first():
    """Test reporter-first verification with a citation that has missing case name"""
    
    # Test citation with missing case name
    test_text = """
    In the case of 105 F.4th 802, the court held that...
    """
    
    # Prepare the request
    request_data = {
        "type": "text",
        "text": test_text,
        "client_request_id": f"test_reporter_first_{int(time.time())}"
    }
    
    print("Testing reporter-first verification...")
    print(f"Request ID: {request_data['client_request_id']}")
    
    try:
        # Send request to the API
        response = requests.post(
            'https://wolf.law.uw.edu/casestrainer/api/analyze?debug=1',
            json=request_data,
            headers={'Content-Type': 'application/json'},
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            
            print(f"\nFound {len(citations)} citations:")
            
            for citation in citations:
                citation_text = citation.get('citation', 'Unknown')
                extracted_name = citation.get('extracted_case_name', 'N/A')
                canonical_name = citation.get('canonical_name', None)
                canonical_date = citation.get('canonical_date', None)
                verified = citation.get('verified', False)
                source = citation.get('verification_source', None)
                
                print(f"\nCitation: {citation_text}")
                print(f"  Extracted name: {extracted_name}")
                print(f"  Canonical name: {canonical_name}")
                print(f"  Canonical date: {canonical_date}")
                print(f"  Verified: {verified}")
                print(f"  Source: {source}")
                
                if extracted_name == "N/A" or not extracted_name or len(extracted_name.strip()) < 3:
                    if canonical_name and canonical_date and verified:
                        print("  ✅ SUCCESS: Reporter-first verification worked!")
                    else:
                        print("  ❌ FAILED: Reporter-first verification did not work")
                else:
                    print("  ⚠️  Extracted case name was present, reporter-first may not have been needed")
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    test_reporter_first()
