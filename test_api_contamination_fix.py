#!/usr/bin/env python3
"""
Test the actual API endpoint to see if contamination fix is deployed
"""

import requests
import json

def test_api_contamination_fix():
    """Test the API endpoint with the problematic document"""
    
    print("🔍 TESTING API CONTAMINATION FIX")
    print("=" * 50)
    
    # Test document that should trigger contamination
    test_document = """
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION II
    
    CITY OF BELLEVUE v. LORANG
    
    No. 59366-1-II
    
    Filed: November 4, 2002
    
    In this case involving municipal liability, the court considered 
    precedent from Berst v. Snohomish County, 114 Wn. App. 245 and 
    related cases like 57 P.3d 273. Additionally, the court referenced 
    State v. Manussier, 129 Wn.2d 652 in its analysis.
    
    The court also considered federal precedent including 161 F.3d 584 
    in its environmental law analysis.
    """
    
    api_url = "http://localhost:5000/casestrainer/api/analyze"
    
    print("Testing API endpoint...")
    print(f"URL: {api_url}")
    print()
    
    try:
        # Send request to API
        response = requests.post(
            api_url,
            json={"text": test_document},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} citations:")
            print()
            
            for i, cit in enumerate(citations, 1):
                citation_text = cit.get('citation', 'N/A')
                case_name = cit.get('extracted_case_name', 'N/A')
                canonical_name = cit.get('canonical_name', 'N/A')
                verified = cit.get('verified', False)
                
                print(f"  {i}. {citation_text}")
                print(f"     → Extracted: '{case_name}'")
                print(f"     → Canonical: '{canonical_name}'")
                print(f"     → Verified: {verified}")
                
                # Check for contamination
                if 'BELLEVUE' in case_name.upper() or 'LORANG' in case_name.upper():
                    print(f"     ❌ CONTAMINATION - Got primary case name!")
                elif case_name == 'N/A':
                    print(f"     ⚠️  NO EXTRACTION - Better than contamination")
                else:
                    print(f"     ✅ CLEAN - Got local context")
                print()
            
            # Check if contamination fix is working
            contaminated_count = sum(1 for cit in citations 
                                   if 'BELLEVUE' in cit.get('extracted_case_name', '').upper() 
                                   or 'LORANG' in cit.get('extracted_case_name', '').upper())
            
            if contaminated_count == 0:
                print("🎉 CONTAMINATION FIX IS WORKING!")
                print("✅ No citations have the document primary case name")
            else:
                print(f"❌ CONTAMINATION STILL PRESENT!")
                print(f"❌ {contaminated_count} citations have document primary case name")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_api_contamination_fix()
