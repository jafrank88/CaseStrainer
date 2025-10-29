#!/usr/bin/env python3
"""
Test with a fake citation to trigger reporter-first verification
"""

import requests
import json
import time

def test_fake_citation():
    """Test with a fake citation that should fail primary lookup"""
    
    # Use a fake citation that will fail primary lookup but has valid reporter format
    fake_citation = "999 F.3d 999"  # Fake citation with valid reporter format
    
    test_text = f"In the case of {fake_citation}, the court held that..."
    
    request_data = {
        "type": "text",
        "text": test_text,
        "client_request_id": f"test_fake_{int(time.time())}"
    }
    
    print(f"Testing fake citation: {fake_citation}")
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
            clusters = result.get('result', {}).get('clusters', [])
            
            print(f"\nFound {len(citations)} citations:")
            
            if citations:
                citation = citations[0]
                citation_text = citation.get('citation', 'Unknown')
                extracted_name = citation.get('extracted_case_name', 'N/A')
                canonical_name = citation.get('canonical_name', None)
                canonical_date = citation.get('canonical_date', None)
                verified = citation.get('verified', False)
                source = citation.get('verification_source', None)
                
                print(f"Citation: {citation_text}")
                print(f"  Extracted name: '{extracted_name}'")
                print(f"  Canonical name: {canonical_name}")
                print(f"  Canonical date: {canonical_date}")
                print(f"  Verified: {verified}")
                print(f"  Source: {source}")
                
                if clusters:
                    cluster = clusters[0]
                    cluster_source = cluster.get('verification_source', '')
                    print(f"  Cluster verification source: {cluster_source}")
                    
                    if cluster_source and "reporter-first" in cluster_source.lower():
                        print("  ✅ SUCCESS: Reporter-first verification worked!")
                    elif verified:
                        print(f"  ⚠️  Verified by another source: {cluster_source}")
                    else:
                        print("  ❌ FAILED: No verification obtained")
                        
            else:
                print("No citations found")
                
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    test_fake_citation()
