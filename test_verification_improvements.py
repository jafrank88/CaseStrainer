#!/usr/bin/env python3
"""
Test verification improvements
"""

import requests
import json

def test_verification_improvements():
    """Test that verification improvements are working"""
    
    test_text = """
    In the case of Foss v. Nat'l Marine Fisheries Serv., 161 F.3d 584 (9th Cir. 1998), the court ruled on fisheries.
    In Berst v. Snohomish County, 114 Wn. App. 245 (2002), the court addressed county matters.
    In City of Bellevue v. Lorang, 57 P.3d 273 (2002), the court considered city matters.
    """
    
    print("🧪 Testing verification improvements...")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            citations = result.get('citations', [])
            print(f"\n📋 Found {len(citations)} citations")
            
            verified_count = 0
            unverified_count = 0
            
            for i, citation in enumerate(citations):
                print(f"\n--- Citation {i+1} ---")
                print(f"Text: {citation.get('citation', 'N/A')}")
                print(f"Verified: {citation.get('verified', 'N/A')}")
                print(f"Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"Source: {citation.get('source', 'N/A')}")
                
                if citation.get('verified', False):
                    verified_count += 1
                else:
                    unverified_count += 1
            
            print(f"\n📊 Summary:")
            print(f"✅ Verified: {verified_count}")
            print(f"❌ Unverified: {unverified_count}")
            print(f"📈 Verification Rate: {verified_count/(verified_count+unverified_count)*100:.1f}%")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_verification_improvements()
