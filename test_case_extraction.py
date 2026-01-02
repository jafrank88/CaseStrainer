#!/usr/bin/env python3
"""
Test case name extraction specifically
"""

import requests
import json

def test_case_extraction():
    """Test what case names are being extracted for specific citations"""
    
    # This is the problematic text from the user's document
    test_text = """
    In City of Bellevue v. Lorang, 57 P.3d 273 (2002), the court considered city matters.
    In Berst v. Snohomish County, 114 Wn. App. 245 (2002), the court addressed county matters.
    """
    
    print("🔍 Testing case name extraction...")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"\n📊 Found {len(citations)} citations:")
            
            for i, citation in enumerate(citations):
                print(f"\n--- Citation {i+1} ---")
                print(f"Citation: {citation.get('citation', 'N/A')}")
                print(f"Extracted Name: {citation.get('extracted_case_name', 'N/A')}")
                print(f"Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"Verified: {citation.get('verified', 'N/A')}")
                print(f"Source: {citation.get('source', 'N/A')}")
                
                # Check if extraction makes sense
                citation_text = citation.get('citation', '')
                extracted_name = citation.get('extracted_case_name', '')
                
                if citation_text == '57 P.3d 273' and 'Bellevue' not in extracted_name:
                    print(f"❌ WRONG: Should extract 'City of Bellevue v. Lorang' for 57 P.3d 273")
                elif citation_text == '114 Wn. App. 245' and 'Berst' not in extracted_name:
                    print(f"❌ WRONG: Should extract 'Berst v. Snohomish County' for 114 Wn. App. 245")
                else:
                    print(f"✅ CORRECT: Case name matches citation")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_case_extraction()
