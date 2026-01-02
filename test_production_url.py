#!/usr/bin/env python3
"""
Test production API with URL processing (which was working before)
"""

import requests
import json

def test_production_url():
    """Test production API with URL that was getting stuck at 5%"""
    
    print("🔍 TESTING PRODUCTION API - URL PROCESSING")
    print("=" * 50)
    
    # The problematic URL from before
    pdf_url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"
    
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    print("Testing URL processing...")
    print(f"URL: {pdf_url}")
    print()
    
    try:
        response = requests.post(
            api_url,
            json={"url": pdf_url},
            headers={"Content-Type": "application/json"},
            timeout=120  # Longer timeout for URL processing
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} citations:")
            print()
            
            # Show first few citations
            for i, cit in enumerate(citations[:5], 1):
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
            
            if len(citations) > 0:
                print("=" * 50)
                print("🎉 URL PROCESSING IS WORKING!")
                print("✅ The redirect fix resolved the 5% stuck issue")
                
                # Check contamination
                contaminated_count = sum(1 for cit in citations 
                                       if 'BELLEVUE' in cit.get('extracted_case_name', '').upper() 
                                       or 'LORANG' in cit.get('extracted_case_name', '').upper())
                
                if contaminated_count == 0:
                    print("✅ CONTAMINATION FIX IS WORKING!")
                    print("✅ No citations have document primary case name")
                else:
                    print(f"❌ {contaminated_count} citations still have contamination")
            else:
                print("❌ No citations found from URL")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_production_url()
