#!/usr/bin/env python3
"""
Test API response to check verification status
"""

import requests
import json

def test_verification_response():
    """Test the API response structure for verification status"""
    
    test_text = """
    In the case of Foss v. Nat'l Marine Fisheries Serv., 161 F.3d 584 (9th Cir. 1998), the court ruled on fisheries.
    In Berst v. Snohomish County, 114 Wn. App. 245 (2002), the court addressed county matters.
    """
    
    print("🧪 Testing verification status in API response...")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"📊 Response keys: {list(result.keys())}")
            
            citations = result.get('citations', [])
            print(f"\n📋 Found {len(citations)} citations")
            
            for i, citation in enumerate(citations[:3]):  # Check first 3
                print(f"\n--- Citation {i+1} ---")
                print(f"Text: {citation.get('citation', 'N/A')}")
                print(f"Verified: {citation.get('verified', 'N/A')}")
                print(f"Is Verified: {citation.get('is_verified', 'N/A')}")
                print(f"True by Parallel: {citation.get('true_by_parallel', 'N/A')}")
                
                if 'metadata' in citation:
                    metadata = citation['metadata']
                    print(f"Verification Status: {metadata.get('verification_status', 'N/A')}")
                    print(f"Verification Source: {metadata.get('verification_source', 'N/A')}")
                
                print(f"Source: {citation.get('source', 'N/A')}")
                print(f"Verification Source: {citation.get('verification_source', 'N/A')}")
                print(f"Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"Canonical Date: {citation.get('canonical_date', 'N/A')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_verification_response()
