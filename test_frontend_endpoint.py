#!/usr/bin/env python3
"""
Test the fixed frontend endpoint that should now use enhanced sync processing
"""

import requests
import json

def test_frontend_endpoint():
    print("🧪 Testing Fixed Frontend Endpoint")
    print("=" * 50)
    
    # Test data (same as the frontend)
    test_data = {
        "text": "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"
    }
    
    try:
        # Call the fixed endpoint
        print("📡 Calling /casestrainer/api/analyze endpoint...")
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Request successful!")
            result = response.json()
            
            print("\n🔍 RESPONSE ANALYSIS:")
            print(f"  Status: {result.get('status', 'N/A')}")
            print(f"  Processing Time: {result.get('processing_time_ms', 'N/A')}ms")
            
            # Check if enhanced processing was used
            if 'result' in result:
                result_data = result['result']
                print(f"  Processing Mode: {result_data.get('processing_mode', 'N/A')}")
                print(f"  Citations Found: {len(result_data.get('citations', []))}")
                print(f"  Clusters Created: {len(result_data.get('clusters', []))}")
                
                # Check verification status
                verification_status = result_data.get('verification_status', {})
                print(f"  Verification Queued: {verification_status.get('verification_queued', False)}")
                print(f"  Async Verification: {result_data.get('async_verification_queued', False)}")
                
                # Check first citation for canonical data
                citations = result_data.get('citations', [])
                if citations:
                    first_citation = citations[0]
                    print(f"\n📋 FIRST CITATION ANALYSIS:")
                    print(f"  Citation: {first_citation.get('citation', 'N/A')}")
                    print(f"  Extracted Name: {first_citation.get('extracted_case_name', 'N/A')}")
                    print(f"  Canonical Name: {first_citation.get('canonical_name', 'N/A')}")
                    print(f"  Canonical Date: {first_citation.get('canonical_date', 'N/A')}")
                    print(f"  Verified: {first_citation.get('verified', False)}")
                    print(f"  Source: {first_citation.get('source', 'N/A')}")
                    
                    if first_citation.get('canonical_name'):
                        print("✅ SUCCESS: Canonical metadata populated!")
                    else:
                        print("❌ ISSUE: Canonical metadata still missing")
                        
            else:
                print("❌ No result data in response")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

if __name__ == "__main__":
    test_frontend_endpoint()
